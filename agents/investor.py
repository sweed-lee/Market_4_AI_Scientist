"""
Investor agent implementation.

Investors evaluate strategies and allocate points based on their criteria.
"""

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_agent import BaseAgent
from config.prompts import (
    INVESTOR_STEP1_PROPOSAL_EVALUATION_PROMPT,
    INVESTOR_STEP2_INITIAL_ALLOCATION_PROMPT,
    INVESTOR_STEP2_DEBATE_PROMPT,
    _BUDGET_REFERENCE_CASES,
)
from utils.dialog_logger import add_dialog


def allocate_integers_proportionally(amounts: Dict[str, float], total: int) -> Dict[str, int]:
    """
    Allocate total amount proportionally among investors, ensuring all allocations are integers
    and sum equals total. Uses largest remainder method.
    """
    if not amounts or total <= 0:
        return {name: 0 for name in amounts.keys()}

    total_proportional = sum(amounts.values())
    if total_proportional == 0:
        num_items = len(amounts)
        base_allocation = total // num_items
        remainder = total % num_items
        allocations = {name: base_allocation for name in amounts.keys()}
        for i, name in enumerate(amounts.keys()):
            if i < remainder:
                allocations[name] += 1
        return allocations

    allocations: Dict[str, int] = {}
    remainders = []
    allocated_total = 0

    for name, amount in amounts.items():
        proportional_share = (amount / total_proportional) * total
        base_allocation = int(proportional_share)
        remainder = proportional_share - base_allocation
        allocations[name] = base_allocation
        remainders.append((name, remainder))
        allocated_total += base_allocation

    remainder_amount = total - allocated_total
    if remainder_amount > 0:
        remainders.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder_amount):
            if i < len(remainders):
                allocations[remainders[i][0]] += 1

    return allocations


class Investor(BaseAgent):
    """Investor agent that evaluates strategies and allocates points."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.criteria = config.get("criteria", "General evaluation")
        self.philosophy = config.get("philosophy", "Balanced investment approach")
        self.model = config.get("model")
        self.evaluation_history = []

    def evaluate_single_proposal(
        self,
        founder_name: str,
        title: str,
        proposal: str,
        budget_val: int,
        investor_budget: int,
        llm_callback=None,
        requirement: str = None,
        founder_requirement: str = None,
        budget_tolerance_percent: float = 0.1,
        investment_history: str = None,
        current_investment_round: int = 1,
        prototype: str = "",
    ) -> Dict[str, Any]:
        """Evaluate one founder's standalone proposal in step 1."""
        budget_lower = int(budget_val * (1 - budget_tolerance_percent))
        budget_upper = int(budget_val * (1 + budget_tolerance_percent))
        founder_block = (
            f"{founder_name}:\n"
            f"Requirement: {founder_requirement or ''}\n"
            f"Title: {title or ''}\n"
            f"Budget: {int(budget_val)} tokens (range: {budget_lower}-{budget_upper} tokens, +/-{budget_tolerance_percent * 100:.0f}%)\n"
            f"Proposal:\n{proposal or ''}"
        )
        if prototype:
            founder_block += f"\nPrototype:\n{prototype}"

        prompt = INVESTOR_STEP1_PROPOSAL_EVALUATION_PROMPT.format(
            requirement=requirement if requirement else (founder_requirement or ""),
            criteria=self.criteria,
            philosophy=self.philosophy,
            investment_history=investment_history or "**Investment History:** No previous investment history available.",
            current_investment_round=current_investment_round,
            investor_budget=int(investor_budget),
            budget_reference_cases=_BUDGET_REFERENCE_CASES,
            founder_block=founder_block,
        )

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_single_proposal_eval(investor_budget)

        add_dialog(prompt, response, self.name, "Investor", dialog_type="step1_single_proposal_eval")

        output_text = self._extract_section(response, "OUTPUT")
        parsed = self._parse_key_values(output_text)
        score = float(parsed.get("Score", 0.0))
        advice = str(parsed.get("InvestmentAdvice", "")).strip()

        import math

        if not math.isfinite(score):
            score = 0.0
        score = max(0.0, min(100.0, score))
        return {"score": score, "investment_advice": advice}

    def allocate_step2_with_stance(
        self,
        *,
        candidates: List[Dict[str, Any]],
        budget: int,
        llm_callback=None,
        requirement: str = None,
        investment_history: str = None,
        current_investment_round: int = 1,
        budget_tolerance_percent: float = 0.1,
        retry_hint: str = None,
        debate_round_index: int = 0,
        peer_discussion_context: str = None,
    ) -> Dict[str, Any]:
        """Run one step-2 subround and return allocations plus a short stance."""
        names = [c["name"] for c in candidates]
        parts = []
        for c in candidates:
            parts.append(
                "\n".join(
                    [
                        f'{c["name"]}:',
                        f'Title: {c.get("title","")}',
                        f'ProjectBudget: {int(c.get("budget",0))} (bounds: {int(c.get("lower_bound",0))}-{int(c.get("upper_bound",0))})',
                        f'TotalAccumulatedAcceptedSoFar: {int(c.get("total_accumulated_accepted",0))}',
                        f'GroupAccumulatedAcceptedSoFar: {int(c.get("group_accumulated_accepted",0))}',
                        f'YourAccumulatedPlannedSoFar: {int(c.get("investor_accumulated_planned",0))}',
                        f'YourStep1Score: {float(c.get("step1_score",0.0)):.1f}/100',
                        f'YourStep1InvestmentAdvice: {c.get("step1_advice","")}',
                    ]
                )
            )
        candidates_list = "\n\n".join(parts)

        retry_hint_text = (retry_hint or "").strip()
        if retry_hint_text:
            retry_hint_text = (
                "**CRITICAL - Your previous allocation was invalid and rejected:**\n"
                f"{retry_hint_text}\n\n"
                f"Please correct your allocation. The total must still equal exactly {int(budget)}."
            )

        if debate_round_index <= 0:
            prompt = INVESTOR_STEP2_INITIAL_ALLOCATION_PROMPT.format(
                requirement=requirement or "",
                criteria=self.criteria,
                philosophy=self.philosophy,
                investment_history=investment_history or "**Investment History:** No previous investment history available.",
                current_investment_round=current_investment_round,
                budget=int(budget),
                budget_tolerance_percent=budget_tolerance_percent * 100,
                budget_reference_cases=_BUDGET_REFERENCE_CASES,
                retry_hint=retry_hint_text,
                candidates_list=candidates_list,
            )
            dialog_type = "step2_initial_allocation"
        else:
            prompt = INVESTOR_STEP2_DEBATE_PROMPT.format(
                requirement=requirement or "",
                criteria=self.criteria,
                philosophy=self.philosophy,
                investment_history=investment_history or "**Investment History:** No previous investment history available.",
                current_investment_round=current_investment_round,
                debate_round_index=int(debate_round_index),
                budget=int(budget),
                budget_tolerance_percent=budget_tolerance_percent * 100,
                budget_reference_cases=_BUDGET_REFERENCE_CASES,
                candidates_list=candidates_list,
                peer_discussion_context=peer_discussion_context or "No peer discussion context available.",
                retry_hint=retry_hint_text,
            )
            dialog_type = f"step2_debate_round_{int(debate_round_index)}"

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_step2_with_stance(names, budget, debate_round_index)

        add_dialog(prompt, response, self.name, "Investor", dialog_type=dialog_type)

        alloc_text = self._extract_section(response, "ALLOCATIONS")
        stance_text = self._extract_section(response, "STANCE").strip()
        allocations = self._parse_allocations(alloc_text, names)
        return {"allocations": allocations, "stance": stance_text}

    def _extract_section(self, response: str, section: str) -> str:
        """Extract a tagged section from a response."""
        import re

        pattern = rf"\[{section}\](.*?)\[/{section}\]"
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response

    def _parse_key_values(self, text: str) -> Dict[str, str]:
        """Parse simple 'Key: value' pairs from a text blob."""
        import re

        out: Dict[str, str] = {}
        for line in (text or "").splitlines():
            match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$", line)
            if match:
                out[match.group(1)] = match.group(2)
        return out

    def _parse_allocations(self, text: str, names: List[str]) -> Dict[str, float]:
        """Parse 'Name: number' allocations for a fixed set of candidate names."""
        import re

        out: Dict[str, float] = {}
        for name in names:
            pattern = rf"{re.escape(name)}:\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, text or "")
            out[name] = float(match.group(1)) if match else 0.0
        return out

    def _placeholder_single_proposal_eval(self, investor_budget: int) -> str:
        """Placeholder for step-1 eval when no LLM callback is provided."""
        import random

        score = random.randint(0, 100)
        advice = (
            "This proposal describes a concrete product and target use-case with a plausible implementation approach. "
            "Strengths: clear user value and reasonable scope; weaknesses: some details are underspecified and the validation plan could be sharper. "
            "Key risks/unknowns: feasibility of the hardest component, integration complexity, and whether the market demand matches the feature set."
        )
        return f"""[THINKING]
Evaluating single proposal (placeholder).
[/THINKING]

[OUTPUT]
Score: {score}
InvestmentAdvice: {advice}
[/OUTPUT]"""

    def _placeholder_step2_with_stance(self, names: List[str], budget: int, debate_round_index: int = 0) -> str:
        """Placeholder for step-2 subrounds when no LLM callback is provided."""
        if not names:
            return "[STANCE]\nNo candidates.\n[/STANCE]\n[ALLOCATIONS]\n[/ALLOCATIONS]"
        base = budget // len(names)
        rem = budget - base * len(names)
        allocs = []
        for i, name in enumerate(names):
            value = base + (1 if i < rem else 0)
            allocs.append(f"{name}: {float(value):.2f}")
        stance = (
            "Initial view: balanced exploratory split across shortlisted projects."
            if debate_round_index <= 0
            else "Updated after discussion: keeping a balanced allocation with minor peer-informed adjustments."
        )
        return (
            "[THINKING]\nPlaceholder step2 allocation with stance.\n[/THINKING]\n\n"
            f"[STANCE]\n{stance}\n[/STANCE]\n\n"
            "[ALLOCATIONS]\n" + "\n".join(allocs) + "\n[/ALLOCATIONS]"
        )

    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        return {"type": "error", "message": "Unsupported request type for Investor."}

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({"criteria": self.criteria, "philosophy": self.philosophy})
        return base_dict


class InvestorGroup:
    """
    A group of investors that evaluate strategies individually and then
    aggregate their scores into a single group score.
    """

    def __init__(
        self,
        name: str,
        investors: List[Investor],
        total_capital: float = 100.0,
        k_selection: int = None,
        round1_max_workers: int = None,
        step2_debate_rounds: int = 0,
    ):
        self.name = name
        self.investors = investors
        self.initial_capital = int(round(total_capital))
        self.total_capital = int(round(total_capital))
        self.k_selection = k_selection
        self.round1_max_workers = round1_max_workers
        self.step2_debate_rounds = max(0, int(step2_debate_rounds or 0))
        self.step1_cache: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []

    def run_step1_evaluations(
        self,
        strategies: Dict[str, str],
        llm_callback=None,
        requirement: str = None,
        founder_requirements: Dict[str, str] = None,
        titles: Dict[str, str] = None,
        budgets: Dict[str, int] = None,
        budget_tolerance_percent: float = 0.1,
        investment_history: str = None,
        current_investment_round: int = 1,
        prototypes: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Run step 1 once per major round and cache the per-proposal evaluations."""
        budgets = budgets or {}
        founder_requirements = founder_requirements or {}
        titles = titles or {}
        prototypes = prototypes or {}

        num_investors = len(self.investors)
        if num_investors == 0 or not strategies:
            self.step1_cache = {
                "per_investor_scores": {},
                "per_investor_advices": {},
                "aggregated_scores": {fname: 0.0 for fname in (strategies or {}).keys()},
            }
            return self.step1_cache

        investor_budget = int(self.total_capital // num_investors) if self.total_capital > 0 else 0
        history_summary = investment_history or "**Investment History:** No previous investment history available."

        per_investor_scores: Dict[str, Dict[str, float]] = {}
        per_investor_advices: Dict[str, Dict[str, str]] = {}
        aggregated_scores: Dict[str, float] = {founder_name: 0.0 for founder_name in strategies.keys()}

        founder_names = list(strategies.keys())
        tasks = [(inv, fname) for inv in self.investors for fname in founder_names]
        max_workers = self.round1_max_workers if self.round1_max_workers is not None else min(32, max(1, len(tasks)))

        def _eval_pair(inv: Investor, fname: str) -> Dict[str, Any]:
            return inv.evaluate_single_proposal(
                founder_name=fname,
                title=titles.get(fname, ""),
                proposal=strategies.get(fname, ""),
                budget_val=int(budgets.get(fname, 0)),
                investor_budget=int(investor_budget),
                llm_callback=llm_callback,
                requirement=requirement,
                founder_requirement=founder_requirements.get(fname, ""),
                budget_tolerance_percent=budget_tolerance_percent,
                investment_history=history_summary,
                current_investment_round=current_investment_round,
                prototype=prototypes.get(fname, ""),
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(_eval_pair, inv, fname): (inv, fname) for inv, fname in tasks}
            for future in as_completed(future_map):
                inv, fname = future_map[future]
                result = future.result()
                per_investor_scores.setdefault(inv.name, {})[fname] = float(result.get("score", 0.0))
                per_investor_advices.setdefault(inv.name, {})[fname] = str(result.get("investment_advice", "") or "")
                aggregated_scores[fname] += float(result.get("score", 0.0))

        self.step1_cache = {
            "per_investor_scores": per_investor_scores,
            "per_investor_advices": per_investor_advices,
            "aggregated_scores": aggregated_scores,
        }
        return self.step1_cache

    def evaluate_strategies_single_round(
        self,
        strategies: Dict[str, str],
        llm_callback=None,
        requirement: str = None,
        founder_requirements: Dict[str, str] = None,
        titles: Dict[str, str] = None,
        budgets: Dict[str, int] = None,
        budget_tolerance_percent: float = 0.1,
        investment_history: str = None,
        current_investment_round: int = 1,
        prototypes: Dict[str, str] = None,
        total_accumulated_accepted: Dict[str, int] = None,
        group_accumulated_accepted: Dict[str, int] = None,
        max_allocation_retries: int = 3,
    ) -> Dict[str, float]:
        """
        Evaluate strategies in a single investment round.

        Step-1 is cached outside the investment-round loop.
        Step-2 now contains debate subrounds where the initial allocation is the first subround.
        The configured debate-round count includes that initial allocation subround.
        """
        budgets = budgets or {}
        founder_requirements = founder_requirements or {}
        titles = titles or {}
        prototypes = prototypes or {}
        total_accumulated_accepted = total_accumulated_accepted or {}
        group_accumulated_accepted = group_accumulated_accepted or {}

        if not self.step1_cache:
            self.run_step1_evaluations(
                strategies=strategies,
                llm_callback=llm_callback,
                requirement=requirement,
                founder_requirements=founder_requirements,
                titles=titles,
                budgets=budgets,
                budget_tolerance_percent=budget_tolerance_percent,
                investment_history=investment_history,
                current_investment_round=current_investment_round,
                prototypes=prototypes,
            )

        per_investor_scores: Dict[str, Dict[str, float]] = self.step1_cache.get("per_investor_scores", {})
        per_investor_advices: Dict[str, Dict[str, str]] = self.step1_cache.get("per_investor_advices", {})
        aggregated_scores_all: Dict[str, float] = self.step1_cache.get("aggregated_scores", {})
        aggregated_scores: Dict[str, float] = {
            fname: float(aggregated_scores_all.get(fname, 0.0)) for fname in strategies.keys()
        }

        num_investors = len(self.investors)
        if num_investors == 0 or self.total_capital < 10 or not strategies:
            return {name: 0.0 for name in strategies.keys()}

        budget_per_investor = self.total_capital // num_investors
        history_summary = investment_history or "**Investment History:** No previous investment history available."

        selected_founders = list(strategies.keys())
        if self.k_selection is not None and self.k_selection < len(strategies):
            sorted_founders = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)
            selected_founders = [name for name, _ in sorted_founders[: self.k_selection]]

        investor_planned_so_far: Dict[str, Dict[str, int]] = {inv.name: {} for inv in self.investors}
        for inv in self.investors:
            acc = {fname: 0 for fname in strategies.keys()}
            for history_entry in self.history:
                per_inv = (history_entry.get("per_investor_allocations") or {}).get(inv.name, {})
                for fname, amount in (per_inv or {}).items():
                    if fname in acc:
                        acc[fname] += int(round(float(amount)))
            investor_planned_so_far[inv.name] = acc

        def _is_valid(inv_alloc: Dict[str, float], names: List[str], budget_limit: int) -> bool:
            import math

            total = 0.0
            for name in names:
                value = float(inv_alloc.get(name, 0.0))
                if not math.isfinite(value) or value < 0:
                    return False
                total += value
            return abs(total - float(budget_limit)) <= 1e-3

        def _build_candidate_list(inv: Investor) -> List[Dict[str, Any]]:
            out = []
            for fname in selected_founders:
                budget_val = int(budgets.get(fname, 0))
                out.append(
                    {
                        "name": fname,
                        "title": titles.get(fname, ""),
                        "budget": budget_val,
                        "lower_bound": int(budget_val * (1 - budget_tolerance_percent)),
                        "upper_bound": int(budget_val * (1 + budget_tolerance_percent)),
                        "total_accumulated_accepted": int(total_accumulated_accepted.get(fname, 0)),
                        "group_accumulated_accepted": int(group_accumulated_accepted.get(fname, 0)),
                        "investor_accumulated_planned": int(investor_planned_so_far.get(inv.name, {}).get(fname, 0)),
                        "step1_score": float(per_investor_scores.get(inv.name, {}).get(fname, 0.0)),
                        "step1_advice": str(per_investor_advices.get(inv.name, {}).get(fname, "") or ""),
                    }
                )
            return out

        def _format_peer_context(previous_round_outputs: Dict[str, Dict[str, Any]], current_inv_name: str) -> str:
            parts = []
            for peer in self.investors:
                peer_output = previous_round_outputs.get(peer.name, {})
                allocations = peer_output.get("allocations", {}) or {}
                stance = str(peer_output.get("stance", "") or "").strip()
                marker = " [THIS WAS YOUR PREVIOUS VIEW]" if peer.name == current_inv_name else ""
                alloc_lines = [f"  - {fname}: {float(allocations.get(fname, 0.0)):.2f}" for fname in selected_founders]
                parts.append(
                    "\n".join(
                        [
                            f"{peer.name}{marker}",
                            f"Specialty: {getattr(peer, 'criteria', '')}",
                            f"Attitude: {stance or 'No explanation provided.'}",
                            "Allocations:",
                            *alloc_lines,
                        ]
                    )
                )
            return "\n\n".join(parts)

        def _run_one_subround(
            inv: Investor,
            debate_round_index: int,
            previous_round_outputs: Dict[str, Dict[str, Any]],
        ) -> Dict[str, Any]:
            budget_limit = int(budget_per_investor)
            retry_hint = ""
            result = None
            for attempt in range(max_allocation_retries + 1):
                result = inv.allocate_step2_with_stance(
                    candidates=_build_candidate_list(inv),
                    budget=budget_limit,
                    llm_callback=llm_callback,
                    requirement=requirement,
                    investment_history=history_summary,
                    current_investment_round=current_investment_round,
                    budget_tolerance_percent=budget_tolerance_percent,
                    retry_hint=retry_hint if attempt > 0 else None,
                    debate_round_index=debate_round_index,
                    peer_discussion_context=(
                        _format_peer_context(previous_round_outputs, inv.name) if debate_round_index > 0 else None
                    ),
                )
                alloc = (result or {}).get("allocations", {}) or {}
                if _is_valid(alloc, selected_founders, budget_limit):
                    return result
                total = sum(float(alloc.get(name, 0.0)) for name in selected_founders)
                retry_hint = (
                    f"Your total allocation was {total:.0f} but your budget is {budget_limit}. "
                    f"The sum of all allocations must equal exactly {budget_limit}."
                )
            return result or {"allocations": {}, "stance": ""}

        debate_transcript: List[Dict[str, Any]] = []
        prior_outputs: Dict[str, Dict[str, Any]] = {}
        invalid_allocation = False
        configured_debate_rounds = max(1, int(self.step2_debate_rounds or 0))
        effective_debate_rounds = configured_debate_rounds if num_investors > 1 else 1
        total_subrounds = effective_debate_rounds

        for subround_idx in range(total_subrounds):
            subround_outputs: Dict[str, Dict[str, Any]] = {}
            with ThreadPoolExecutor() as executor:
                future_to_inv = {
                    executor.submit(_run_one_subround, inv, subround_idx, prior_outputs): inv
                    for inv in self.investors
                }
                for future in as_completed(future_to_inv):
                    inv = future_to_inv[future]
                    result = future.result()
                    alloc = (result or {}).get("allocations", {}) or {}
                    if not _is_valid(alloc, selected_founders, int(budget_per_investor)):
                        invalid_allocation = True
                        break
                    full_alloc = {name: 0.0 for name in strategies.keys()}
                    for fname, amount in alloc.items():
                        full_alloc[fname] = float(amount)
                    subround_outputs[inv.name] = {
                        "allocations": full_alloc,
                        "stance": str((result or {}).get("stance", "") or "").strip(),
                    }
            if invalid_allocation:
                break
            debate_transcript.append(
                {
                    "subround_index": subround_idx,
                    "subround_type": "initial_allocation" if subround_idx == 0 else "discussion",
                    "per_investor_outputs": subround_outputs,
                }
            )
            prior_outputs = subround_outputs

        if invalid_allocation:
            zero_investments = {name: 0.0 for name in strategies.keys()}
            self.history.append(
                {
                    "type": "single_round_evaluation",
                    "round": current_investment_round,
                    "strategies": strategies,
                    "budgets": budgets,
                    "selected_founders": selected_founders,
                    "round1_scores": per_investor_scores,
                    "round1_aggregated_scores": aggregated_scores,
                    "step2_debate_rounds": int(self.step2_debate_rounds),
                    "effective_step2_debate_rounds": int(effective_debate_rounds),
                    "step2_subrounds": debate_transcript,
                    "per_investor_allocations": {},
                    "per_investor_stances": {},
                    "investments": zero_investments,
                    "feedback": {},
                    "invalid_allocation": True,
                }
            )
            return zero_investments

        per_investor_investments: Dict[str, Dict[str, float]] = {}
        per_investor_stances: Dict[str, str] = {}
        for inv in self.investors:
            inv_output = prior_outputs.get(inv.name, {})
            per_investor_investments[inv.name] = inv_output.get(
                "allocations",
                {name: 0.0 for name in strategies.keys()},
            )
            per_investor_stances[inv.name] = str(inv_output.get("stance", "") or "").strip()

        round_investments: Dict[str, float] = {founder_name: 0.0 for founder_name in strategies.keys()}
        for investor_investments in per_investor_investments.values():
            for founder_name, investment in investor_investments.items():
                if founder_name in round_investments:
                    round_investments[founder_name] += float(investment)

        round_investments = {name: float(int(round(amount))) for name, amount in round_investments.items()}

        group_total_invested_this_round = sum(round_investments.values())
        self.total_capital -= group_total_invested_this_round
        if self.total_capital < 0:
            self.total_capital = 0

        round_feedback: Dict[str, Dict[str, Any]] = {}
        investors_meta = {inv.name: {"criteria": getattr(inv, "criteria", "")} for inv in self.investors}
        for founder_name in strategies.keys():
            r1_scores = (
                {inv.name: float(per_investor_scores.get(inv.name, {}).get(founder_name, 0.0)) for inv in self.investors}
                if per_investor_scores
                else {}
            )

            r1_scores_text_plain = ""
            r1_specialties_text = ""
            if r1_scores:
                r1_parts_plain = []
                r1_specialties = []
                for inv in self.investors:
                    crit = getattr(inv, "criteria", "")
                    if crit:
                        r1_specialties.append(crit)
                    r1_parts_plain.append(f"{inv.name}: {r1_scores.get(inv.name, 0.0):.1f}/100")
                r1_scores_text_plain = "; ".join(r1_parts_plain)
                seen = set()
                r1_specialties_unique = []
                for specialty in r1_specialties:
                    if specialty and specialty not in seen:
                        seen.add(specialty)
                        r1_specialties_unique.append(specialty)
                r1_specialties_text = ", ".join(r1_specialties_unique)

            adv_lines = []
            for investor in self.investors:
                advice = per_investor_advices.get(investor.name, {}).get(founder_name, "")
                if advice:
                    adv_lines.append(f"{investor.name}: {advice}")
            stance_lines = []
            for investor in self.investors:
                stance = per_investor_stances.get(investor.name, "")
                if stance:
                    stance_lines.append(f"{investor.name} FinalStep2Stance: {stance}")
            detail_parts = []
            if adv_lines:
                detail_parts.append("\n".join(adv_lines))
            if stance_lines:
                detail_parts.append("\n".join(stance_lines))
            detail_text = "\n".join(detail_parts)
            summary_text = (detail_text[:200] + "...") if len(detail_text) > 200 else detail_text

            round_feedback[founder_name] = {
                "summary": summary_text,
                "detail": detail_text,
                "investment": float(round_investments.get(founder_name, 0.0)),
                "round1_proposal_scores": r1_scores,
                "round1_proposal_scores_plain_text": r1_scores_text_plain,
                "round1_specialties_text": r1_specialties_text,
                "round1_aggregated_score": float(aggregated_scores.get(founder_name, 0.0)) if aggregated_scores else 0.0,
                "selected_in_round1": bool(founder_name in selected_founders),
                "investors_meta": investors_meta,
                "step2_final_stances": per_investor_stances,
            }

        round_history_entry = {
            "type": "single_round_evaluation",
            "round": current_investment_round,
            "strategies": strategies,
            "budgets": budgets,
            "selected_founders": selected_founders,
            "round1_scores": per_investor_scores,
            "round1_aggregated_scores": aggregated_scores,
            "investors_meta": investors_meta,
            "step2_debate_rounds": int(self.step2_debate_rounds),
            "effective_step2_debate_rounds": int(effective_debate_rounds),
            "step2_subrounds": debate_transcript,
            "per_investor_allocations": per_investor_investments,
            "per_investor_stances": per_investor_stances,
            "investments": round_investments,
            "feedback": round_feedback,
        }
        self.history.append(round_history_entry)
        return round_investments

    def evaluate_strategies(
        self,
        strategies: Dict[str, str],
        max_points: int = None,
        llm_callback=None,
        requirement: str = None,
        founder_requirements: Dict[str, str] = None,
        titles: Dict[str, str] = None,
        k: int = None,
        budgets: Dict[str, int] = None,
        budget_tolerance_percent: float = 0.1,
        max_rounds: int = 5,
        previous_major_round_history: str = None,
    ) -> Dict[str, float]:
        """Deprecated compatibility wrapper."""
        return self.evaluate_strategies_single_round(
            strategies=strategies,
            llm_callback=llm_callback,
            requirement=requirement,
            founder_requirements=founder_requirements,
            titles=titles,
            budgets=budgets,
            budget_tolerance_percent=budget_tolerance_percent,
            investment_history=previous_major_round_history,
            current_investment_round=1,
        )

    def reset(self):
        """Reset all underlying investors and group history."""
        for investor in self.investors:
            investor.reset()
        self.history = []
        self.total_capital = self.initial_capital
        self.step1_cache = {}
