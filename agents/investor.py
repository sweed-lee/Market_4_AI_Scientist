"""
Investor agent implementation.

Investors evaluate strategies and allocate points based on their criteria.
"""

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_agent import BaseAgent
from config.prompts import (
    INVESTOR_STEP1_PROPOSAL_EVALUATION_PROMPT,
    INVESTOR_STEP2_ALLOCATION_PROMPT,
    _BUDGET_REFERENCE_CASES,
)
from utils.dialog_logger import add_dialog


def allocate_integers_proportionally(amounts: Dict[str, float], total: int) -> Dict[str, int]:
    """
    Allocate total amount proportionally among investors, ensuring all allocations are integers
    and sum equals total. Uses largest remainder method.
    
    Args:
        amounts: Dictionary mapping names to their proportional amounts (can be floats)
        total: Total integer amount to allocate
        
    Returns:
        Dictionary mapping names to integer allocations that sum to total
    """
    if not amounts or total <= 0:
        return {name: 0 for name in amounts.keys()}
    
    # Calculate proportional shares
    total_proportional = sum(amounts.values())
    if total_proportional == 0:
        # If all amounts are zero, distribute evenly
        num_items = len(amounts)
        base_allocation = total // num_items
        remainder = total % num_items
        allocations = {name: base_allocation for name in amounts.keys()}
        # Distribute remainder to first few items
        for i, name in enumerate(amounts.keys()):
            if i < remainder:
                allocations[name] += 1
        return allocations
    
    # Calculate base integer allocation for each
    allocations = {}
    remainders = []
    allocated_total = 0
    
    for name, amount in amounts.items():
        if total_proportional > 0:
            proportional_share = (amount / total_proportional) * total
            base_allocation = int(proportional_share)
            remainder = proportional_share - base_allocation
            allocations[name] = base_allocation
            remainders.append((name, remainder))
            allocated_total += base_allocation
        else:
            allocations[name] = 0
            remainders.append((name, 0.0))
    
    # Distribute remainder using largest remainder method
    remainder_amount = total - allocated_total
    if remainder_amount > 0:
        # Sort by remainder (largest first)
        remainders.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder_amount):
            if i < len(remainders):
                allocations[remainders[i][0]] += 1
    
    return allocations


class Investor(BaseAgent):
    """Investor agent that evaluates strategies and allocates points."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize an Investor agent.
        
        Args:
            name: Name of the investor
            config: Configuration containing 'criteria', 'philosophy'
        """
        super().__init__(name, config)
        self.criteria = config.get('criteria', 'General evaluation')
        self.philosophy = config.get('philosophy', 'Balanced investment approach')
        self.model = config.get('model')
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
        """
        Step 1 (new system): Evaluate ONE founder's full proposal (formerly round-2 content).
        Returns a score (0-100) and a concise written evaluation (no explicit investment intensity).
        """
        budget_lower = int(budget_val * (1 - budget_tolerance_percent))
        budget_upper = int(budget_val * (1 + budget_tolerance_percent))
        founder_block = (
            f"{founder_name}:\n"
            f"Requirement: {founder_requirement or ''}\n"
            f"Title: {title or ''}\n"
            f"Budget: {int(budget_val)} tokens (range: {budget_lower}-{budget_upper} tokens, ±{budget_tolerance_percent*100:.0f}%)\n"
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

        # Clamp/clean
        import math
        if not math.isfinite(score):
            score = 0.0
        score = max(0.0, min(100.0, score))

        return {
            "score": score,
            "investment_advice": advice,
        }

    def allocate_step2(
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
    ) -> Dict[str, float]:
        """
        Step 2 (new system): Given shortlisted candidates and step-1 artifacts,
        call LLM to allocate this investor's budget across them.

        candidates items must include:
          - name
          - title
          - budget
          - lower_bound, upper_bound
          - total_accumulated_accepted
          - group_accumulated_accepted
          - investor_accumulated_planned
          - step1_score
          - step1_advice
        """
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
            retry_hint_text = f"**CRITICAL - Your previous allocation was invalid and rejected:**\n{retry_hint_text}\n\nPlease correct your allocation. The total must still equal exactly {int(budget)}."

        prompt = INVESTOR_STEP2_ALLOCATION_PROMPT.format(
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

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_step2_allocation(names, budget)

        add_dialog(prompt, response, self.name, "Investor", dialog_type="step2_allocation")

        alloc_text = self._extract_section(response, "ALLOCATIONS")
        allocations = self._parse_allocations(alloc_text, names)
        return allocations
    
    def _extract_section(self, response: str, section: str) -> str:
        """Extract a tagged section (SUMMARIES, DETAILS, ALLOCATIONS)."""
        import re
        pattern = rf'\[{section}\](.*?)\[/{section}\]'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response
    
    # Note: legacy multi-candidate parsing helpers were removed as the new system
    # evaluates one proposal per dialog and allocates based on short suggestions.

    def _parse_key_values(self, text: str) -> Dict[str, str]:
        """
        Parse simple 'Key: value' pairs from a text blob.
        Used for step-1 single proposal evaluation output.
        """
        import re

        out: Dict[str, str] = {}
        # Match lines like "Score: 78" or "SuggestedInvestment: 120.5"
        for line in (text or "").splitlines():
            m = re.match(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
        return out

    def _parse_allocations(self, text: str, names: List[str]) -> Dict[str, float]:
        """Parse 'Name: number' allocations for a fixed set of candidate names."""
        import re
        out: Dict[str, float] = {}
        for n in names:
            pattern = rf"{re.escape(n)}:\s*(\d+(?:\.\d+)?)"
            m = re.search(pattern, text or "")
            out[n] = float(m.group(1)) if m else 0.0
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

    def _placeholder_step2_allocation(self, names: List[str], budget: int) -> str:
        """Placeholder for step-2 allocation when no LLM callback is provided."""
        if not names:
            return "[ALLOCATIONS]\n[/ALLOCATIONS]"
        # Simple even split
        base = budget // len(names)
        rem = budget - base * len(names)
        allocs = []
        for i, n in enumerate(names):
            v = base + (1 if i < rem else 0)
            allocs.append(f"{n}: {float(v):.2f}")
        return "[THINKING]\nPlaceholder step2 allocation.\n[/THINKING]\n\n[ALLOCATIONS]\n" + "\n".join(allocs) + "\n[/ALLOCATIONS]"
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request (legacy hook)."""
        return {'type': 'error', 'message': 'Unsupported request type for Investor.'}
    
    def to_dict(self) -> Dict[str, Any]:
        """Extend serialization with investor-specific data."""
        base_dict = super().to_dict()
        base_dict.update({
            'criteria': self.criteria,
            'philosophy': self.philosophy,
        })
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
    ):
        """
        Initialize an InvestorGroup.

        Args:
            name: Name of the investor group
            investors: List of Investor instances in this group
            total_capital: Total capital available for this group (default: 100.0)
        """
        self.name = name
        self.investors = investors
        self.initial_capital = int(round(total_capital))  # Store initial capital for reset
        self.total_capital = int(round(total_capital))  # Key member variable: total capital remaining
        self.k_selection = k_selection  # group-local top-k selection (new system)
        self.round1_max_workers = round1_max_workers  # optional override
        # Step-1 cache (run once per major round; reused across investment rounds)
        self.step1_cache: Dict[str, Any] = {}
        self.history: List[Dict[str, Any]] = []  # Minimal history for feedback and previous round info

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
        """
        STEP 1 (run once per major round, outside the investment-round loop):
        Evaluate each visible investor-founder pair on the full proposal and cache results.
        """
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

        # Notional per-investor budget (framing only)
        investor_budget = int(self.total_capital // num_investors) if self.total_capital > 0 else 0
        history_summary = investment_history or "**Investment History:** No previous investment history available."

        per_investor_scores: Dict[str, Dict[str, float]] = {}
        per_investor_advices: Dict[str, Dict[str, str]] = {}
        # No "investment intensity" is produced in step-1; only evaluation text + score.
        aggregated_scores: Dict[str, float] = {founder_name: 0.0 for founder_name in strategies.keys()}

        founder_names = list(strategies.keys())
        inv_list = list(self.investors)
        tasks = [(inv, fname) for inv in inv_list for fname in founder_names]

        max_workers = self.round1_max_workers
        if max_workers is None:
            max_workers = min(32, max(1, len(tasks)))

        def _eval_pair(inv: Investor, fname: str) -> Dict[str, Any]:
            return inv.evaluate_single_proposal(
                founder_name=fname,
                title=titles.get(fname, "") if titles else "",
                proposal=strategies.get(fname, ""),
                budget_val=int((budgets or {}).get(fname, 0)),
                investor_budget=int(investor_budget),
                llm_callback=llm_callback,
                requirement=requirement,
                founder_requirement=(founder_requirements or {}).get(fname, ""),
                budget_tolerance_percent=budget_tolerance_percent,
                investment_history=history_summary,
                current_investment_round=current_investment_round,
                prototype=(prototypes or {}).get(fname, ""),
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
        Evaluate strategies in a single investment round (called by orchestrator).
        
        Two-step system in a single investment round:
        - Step 1 is expected to be run ONCE outside the investment-round loop via run_step1_evaluations()
          and cached on the group.
        - Step 2 runs inside the investment-round loop and uses cached step-1 scores/advice.
        
        Args:
            strategies: Mapping from founder name to strategy text (proposals)
            llm_callback: LLM callback
            requirement: Requirement text (deprecated; kept for compatibility)
            founder_requirements: Mapping from founder name to requirement text
            titles: Mapping from founder name to title text (for round 1)
            k: Number of candidates to select in round 1 per investor
            budgets: Mapping from founder name to budget (int, in tokens)
            budget_tolerance_percent: Percentage tolerance for budget range (default: 0.1 = 10%)
            investment_history: Investment history text for this major round
            current_investment_round: Current investment round number
            
        Returns:
            Investments per founder for this group in this round.
        """
        budgets = budgets or {}
        founder_requirements = founder_requirements or {}
        titles = titles or {}
        prototypes = prototypes or {}
        total_accumulated_accepted = total_accumulated_accepted or {}
        group_accumulated_accepted = group_accumulated_accepted or {}
        # Load cached step-1 artifacts (computed outside the loop).
        if not self.step1_cache:
            # Backward-compatible fallback: compute step-1 once if missing.
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
        aggregated_scores: Dict[str, float] = {fname: float(aggregated_scores_all.get(fname, 0.0)) for fname in strategies.keys()}
        
        num_investors = len(self.investors)
        if num_investors == 0:
            return {name: 0.0 for name in strategies.keys()}
        
        # Check if group has remaining budget (treat < 10 as exhausted)
        if self.total_capital < 10:
            return {name: 0.0 for name in strategies.keys()}
        
        if not strategies:
            return {name: 0.0 for name in strategies.keys()}
        # quiet by default (tqdm in orchestrator shows progress)
        
        # Calculate budget per investor (equal weight for all investors in the group)
        budget_per_investor = self.total_capital // num_investors
        # Note: remainder is kept at group level, not distributed
        
        # Build investment history summary
        history_summary = investment_history or "**Investment History:** No previous investment history available."
        
        # Step 2a: Select top-k founders based on aggregated step-1 scores
        selected_founders = list(strategies.keys())
        k = self.k_selection
        if k is not None and k < len(strategies):
            sorted_founders = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)
            selected_founders = [name for name, _ in sorted_founders[:k]]
        
        # Step 2b: Call LLM per investor to allocate its equal budget share across selected founders.
        # Track investor's accumulated planned allocations so far (within this group, before this round).
        investor_planned_so_far: Dict[str, Dict[str, int]] = {inv.name: {} for inv in self.investors}
        for inv in self.investors:
            acc: Dict[str, int] = {fname: 0 for fname in strategies.keys()}
            for h in self.history:
                per_inv = (h.get("per_investor_allocations") or {}).get(inv.name, {})
                for fname, amt in (per_inv or {}).items():
                    if fname in acc:
                        acc[fname] += int(round(float(amt)))
            investor_planned_so_far[inv.name] = acc

        per_investor_investments: Dict[str, Dict[str, float]] = {}
        invalid_allocation = False

        def _is_valid(inv_alloc: Dict[str, float], names: List[str], budget_limit: int) -> bool:
            import math
            total = 0.0
            for n in names:
                v = float(inv_alloc.get(n, 0.0))
                if not math.isfinite(v) or v < 0:
                    return False
                total += v
            # Require exact spend (within tiny epsilon)
            return abs(total - float(budget_limit)) <= 1e-3

        def _alloc_one(inv: Investor) -> Dict[str, float]:
            cand_list = []
            for fname in selected_founders:
                b = int(budgets.get(fname, 0))
                lb = int(b * (1 - budget_tolerance_percent))
                ub = int(b * (1 + budget_tolerance_percent))
                cand_list.append(
                    {
                        "name": fname,
                        "title": titles.get(fname, ""),
                        "budget": b,
                        "lower_bound": lb,
                        "upper_bound": ub,
                        "total_accumulated_accepted": int(total_accumulated_accepted.get(fname, 0)),
                        "group_accumulated_accepted": int(group_accumulated_accepted.get(fname, 0)),
                        "investor_accumulated_planned": int(investor_planned_so_far.get(inv.name, {}).get(fname, 0)),
                        "step1_score": float(per_investor_scores.get(inv.name, {}).get(fname, 0.0)),
                        "step1_advice": str(per_investor_advices.get(inv.name, {}).get(fname, "") or ""),
                    }
                )
            budget_limit = int(budget_per_investor)
            retry_hint = ""
            alloc = None
            for attempt in range(max_allocation_retries + 1):
                alloc = inv.allocate_step2(
                    candidates=cand_list,
                    budget=budget_limit,
                    llm_callback=llm_callback,
                    requirement=requirement,
                    investment_history=history_summary,
                    current_investment_round=current_investment_round,
                    budget_tolerance_percent=budget_tolerance_percent,
                    retry_hint=retry_hint if attempt > 0 else None,
                )
                if _is_valid(alloc, selected_founders, budget_limit):
                    return alloc
                total = sum(float(alloc.get(n, 0)) for n in selected_founders)
                retry_hint = (
                    f"Your total allocation was {total:.0f} but your budget is {budget_limit}. "
                    f"The sum of all allocations must equal exactly {budget_limit}."
                )
            return alloc

        with ThreadPoolExecutor() as executor:
            future_to_inv = {executor.submit(_alloc_one, inv): inv for inv in self.investors}
            for future in as_completed(future_to_inv):
                inv = future_to_inv[future]
                alloc = future.result()
                if not _is_valid(alloc, selected_founders, int(budget_per_investor)):
                    invalid_allocation = True
                    break
                full_alloc = {name: 0.0 for name in strategies.keys()}
                for fname, amt in alloc.items():
                    full_alloc[fname] = float(amt)
                per_investor_investments[inv.name] = full_alloc

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
                    "per_investor_allocations": {},
                    "investments": zero_investments,
                    "feedback": {},
                    "invalid_allocation": True,
                }
            )
            return zero_investments
        
        # Aggregate investments per founder (round to integers)
        # This is the group's investment for each founder (sum of all investors in the group)
        round_investments: Dict[str, float] = {
            founder_name: 0.0 for founder_name in strategies.keys()
        }
        for investor_investments in per_investor_investments.values():
            for founder_name, investment in investor_investments.items():
                if founder_name in round_investments:
                    round_investments[founder_name] += float(investment)
        
        # Round all investments to integers
        round_investments = {name: float(int(round(amount))) for name, amount in round_investments.items()}
        
        # Calculate total group investment for this round (will be deducted after orchestrator processes refunds)
        group_total_invested_this_round = sum(round_investments.values())
        
        # Deduct all investments from group capital (will be adjusted at orchestrator level with refunds)
        self.total_capital -= group_total_invested_this_round
        if self.total_capital < 0:
            self.total_capital = 0
        
        # Collect feedback for this round (step-1 scores + written evaluations)
        round_feedback: Dict[str, Dict[str, Any]] = {}
        investors_meta = {inv.name: {"criteria": getattr(inv, "criteria", "")} for inv in self.investors}
        for founder_name in strategies.keys():
            # Step-1 proposal scores are available even if the founder is not selected for allocation.
            r1_scores = {
                inv.name: float(per_investor_scores.get(inv.name, {}).get(founder_name, 0.0))
                for inv in self.investors
            } if per_investor_scores else {}
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
                # Unique while preserving order
                seen = set()
                r1_specialties_unique = []
                for s in r1_specialties:
                    if s and s not in seen:
                        seen.add(s)
                        r1_specialties_unique.append(s)
                r1_specialties_text = ", ".join(r1_specialties_unique)

            # Step-1 advice per investor (short paragraph by design)
            adv_lines = []
            for investor in self.investors:
                a = per_investor_advices.get(investor.name, {}).get(founder_name, "")
                if a:
                    adv_lines.append(f"{investor.name}: {a}")
            detail_text = "\n".join(adv_lines) if adv_lines else ""
            # Summary: keep it short (first ~200 chars) to avoid bloating founder prompts.
            summary_text = (detail_text[:200] + "…") if len(detail_text) > 200 else detail_text

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
            }
        
        # Store round history for feedback
        round_history_entry = {
            "type": "single_round_evaluation",
            "round": current_investment_round,
            "strategies": strategies,
            "budgets": budgets,
            "selected_founders": selected_founders,
            "round1_scores": per_investor_scores,
            "round1_aggregated_scores": aggregated_scores,
            "investors_meta": investors_meta,
            "per_investor_allocations": per_investor_investments,
            "investments": round_investments,
            "feedback": round_feedback,
        }
        self.history.append(round_history_entry)
        
        return round_investments
    
    def evaluate_strategies(
        self,
        strategies: Dict[str, str],
        max_points: int = None,  # Deprecated, kept for backward compatibility
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
        """
        DEPRECATED: This method is kept for backward compatibility but should not be used.
        Investment rounds are now controlled by SystemOrchestrator.
        Use evaluate_strategies_single_round() instead.
        """
        # For backward compatibility, delegate to single round (but this should not be called)
        return self.evaluate_strategies_single_round(
            strategies=strategies,
            llm_callback=llm_callback,
            requirement=requirement,
            founder_requirements=founder_requirements,
            titles=titles,
            k=k,
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
        self.total_capital = self.initial_capital  # Reset capital to initial value

