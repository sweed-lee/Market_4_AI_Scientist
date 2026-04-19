"""
Founder agent for the no-market ablation setting.
"""

from typing import Dict, Any

from agents.founder import Founder
from config.prompts_nomarket import (
    FOUNDER_INITIAL_PROMPT_NOMARKET,
    FOUNDER_ITERATION_PROMPT_NOMARKET,
    _BUDGET_REFERENCE_CASES,
)
from utils.dialog_logger import add_dialog


class FounderNoMarket(Founder):
    """Founder that iterates on evaluator feedback without market dynamics."""

    def generate_strategy(
        self,
        requirement: str = None,
        llm_callback=None,
        num_investor_groups: int = 0,
        capital_per_group: float = 0.0,
        num_competitors: int = 0,
    ) -> str:
        req = requirement if requirement is not None else self.instruction
        prompt = FOUNDER_INITIAL_PROMPT_NOMARKET.format(
            requirement=req,
            budget_reference_cases=_BUDGET_REFERENCE_CASES,
        )

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_response(req)

        add_dialog(
            prompt,
            response,
            self.name,
            "Founder",
            round_num=self.current_round,
            dialog_type="initial_nomarket",
        )

        title = self._extract_title(response)
        budget = self._extract_budget(response)
        proposal = self._extract_proposal(response)
        prototype = self._extract_prototype(response)

        self.current_strategy = proposal
        self.current_title = title
        self.current_budget = budget
        self.current_prototype = prototype
        self.total_budget = budget
        self.add_to_history(
            {
                "type": "initial_strategy_nomarket",
                "requirement": req,
                "strategy": response,
                "title": title,
                "budget": budget,
                "proposal": proposal,
                "prototype": prototype,
            }
        )
        return response

    def iterate_strategy(
        self,
        all_scores: Dict[str, Dict[str, float]],
        llm_callback=None,
        feedback: Dict[str, Any] = None,
        requirement: str = None,
    ) -> str:
        my_prev_round = ""
        others_prev_round = ""
        if feedback:
            my_prev_round = feedback.get("my_prev_round", "")
            others_prev_round = feedback.get("others_prev_round", "")

        req = requirement if requirement is not None else self.instruction
        prompt = FOUNDER_ITERATION_PROMPT_NOMARKET.format(
            requirement=req,
            my_prev_round=my_prev_round,
            others_prev_round=others_prev_round,
            budget_reference_cases=_BUDGET_REFERENCE_CASES,
        )

        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_iteration()

        add_dialog(
            prompt,
            response,
            self.name,
            "Founder",
            round_num=self.current_round,
            dialog_type="iteration_nomarket",
        )

        title = self._extract_title(response)
        budget = self._extract_budget(response)
        proposal = self._extract_proposal(response)
        prototype = self._extract_prototype(response)

        self.current_strategy = proposal
        self.current_title = title
        self.current_budget = budget
        self.current_prototype = prototype
        self.total_budget = budget
        self.add_to_history(
            {
                "type": "refined_strategy_nomarket",
                "refined_strategy": response,
                "title": title,
                "budget": budget,
                "proposal": proposal,
                "prototype": prototype,
            }
        )
        return response

