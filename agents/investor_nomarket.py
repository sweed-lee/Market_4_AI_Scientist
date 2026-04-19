"""
Investor agents for the no-market ablation setting.
"""

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.investor import Investor
from config.prompts_nomarket import INVESTOR_ADVICE_PROMPT_NOMARKET
from utils.dialog_logger import add_dialog


class InvestorNoMarket(Investor):
    """Investor evaluator that only outputs textual advice (no score/allocation)."""

    def advise_single_proposal(
        self,
        founder_name: str,
        title: str,
        proposal: str,
        budget_val: int,
        llm_callback=None,
        requirement: str = None,
        founder_requirement: str = None,
        prototype: str = "",
    ) -> Dict[str, Any]:
        founder_block = (
            f"{founder_name}:\n"
            f"Requirement: {founder_requirement or ''}\n"
            f"Title: {title or ''}\n"
            f"Budget: {int(budget_val)} tokens\n"
            f"Proposal:\n{proposal or ''}"
        )
        if prototype:
            founder_block += f"\nPrototype:\n{prototype}"

        prompt = INVESTOR_ADVICE_PROMPT_NOMARKET.format(
            requirement=requirement if requirement else (founder_requirement or ""),
            criteria=self.criteria,
            philosophy=self.philosophy,
            founder_block=founder_block,
        )

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_advice()

        add_dialog(prompt, response, self.name, "Investor", dialog_type="advice_nomarket")

        output_text = self._extract_section(response, "OUTPUT")
        parsed = self._parse_key_values(output_text)
        advice = str(parsed.get("Advice", "")).strip()
        if not advice:
            advice = output_text.strip()
        return {"advice": advice}

    def _placeholder_advice(self) -> str:
        return """[THINKING]
Evaluating proposal quality and practical risks.
[/THINKING]

[OUTPUT]
Advice: The proposal has a clear direction and implementation outline, with good potential value. Its strengths are focus and modular structure, while weaknesses are limited validation detail and uncertain edge-case handling. Main risks include feasibility of the hardest module and integration complexity. Improve by adding explicit milestones, measurable success metrics, and a sharper risk mitigation plan.
[/OUTPUT]"""


class InvestorGroupNoMarket:
    """Investor group that only produces evaluator feedback for visible proposals."""

    def __init__(self, name: str, investors: List[InvestorNoMarket]):
        self.name = name
        self.investors = investors
        self.history: List[Dict[str, Any]] = []

    def evaluate_visible_proposals(
        self,
        *,
        strategies: Dict[str, str],
        llm_callback=None,
        requirement: str = None,
        founder_requirements: Dict[str, str] = None,
        titles: Dict[str, str] = None,
        budgets: Dict[str, int] = None,
        prototypes: Dict[str, str] = None,
        current_round: int = 1,
    ) -> Dict[str, Dict[str, Any]]:
        founder_requirements = founder_requirements or {}
        titles = titles or {}
        budgets = budgets or {}
        prototypes = prototypes or {}

        round_feedback: Dict[str, Dict[str, Any]] = {fname: {} for fname in strategies.keys()}
        if not self.investors or not strategies:
            return round_feedback

        per_investor_advices: Dict[str, Dict[str, str]] = {}
        tasks = [(inv, fname) for inv in self.investors for fname in strategies.keys()]

        def _eval(inv: InvestorNoMarket, fname: str) -> Dict[str, Any]:
            return inv.advise_single_proposal(
                founder_name=fname,
                title=titles.get(fname, ""),
                proposal=strategies.get(fname, ""),
                budget_val=int(budgets.get(fname, 0)),
                llm_callback=llm_callback,
                requirement=requirement,
                founder_requirement=founder_requirements.get(fname, ""),
                prototype=prototypes.get(fname, ""),
            )

        with ThreadPoolExecutor(max_workers=min(32, max(1, len(tasks)))) as executor:
            future_map = {executor.submit(_eval, inv, fname): (inv, fname) for inv, fname in tasks}
            for future in as_completed(future_map):
                inv, fname = future_map[future]
                result = future.result()
                per_investor_advices.setdefault(inv.name, {})[fname] = str(result.get("advice", "") or "")

        investors_meta = {inv.name: {"criteria": getattr(inv, "criteria", "")} for inv in self.investors}
        for founder_name in strategies.keys():
            lines = []
            per_founder: Dict[str, str] = {}
            for investor in self.investors:
                advice = per_investor_advices.get(investor.name, {}).get(founder_name, "")
                if advice:
                    per_founder[investor.name] = advice
                    lines.append(f"{investor.name}: {advice}")
            detail = "\n".join(lines)
            summary = (detail[:200] + "...") if len(detail) > 200 else detail
            round_feedback[founder_name] = {
                "summary": summary,
                "detail": detail,
                "per_investor_advices": per_founder,
                "investors_meta": investors_meta,
            }

        self.history.append(
            {
                "type": "nomarket_evaluation_round",
                "round": int(current_round),
                "feedback": round_feedback,
            }
        )
        return round_feedback

    def reset(self):
        for investor in self.investors:
            investor.reset()
        self.history = []

