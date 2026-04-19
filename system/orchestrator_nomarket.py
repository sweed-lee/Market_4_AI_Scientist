"""
No-market orchestrator for ablation experiments.

Keeps founder/investor roles and visibility graph, but removes scoring,
budget allocation, and investment-round mechanics.
"""

from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.founder_nomarket import FounderNoMarket
from agents.investor_nomarket import InvestorGroupNoMarket

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    def tqdm(iterable=None, total=None, desc=None, position=None, leave=None):
        if iterable is None:
            class _Dummy:
                def update(self, n=1):
                    return None

                def close(self):
                    return None

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

            return _Dummy()
        return iterable


class SystemOrchestratorNoMarket:
    """Orchestrates multi-round proposal refinement without market dynamics."""

    def __init__(
        self,
        founders: List[FounderNoMarket],
        investor_groups: List[InvestorGroupNoMarket],
        config: Dict[str, Any],
        llm_callback: Callable = None,
    ):
        self.founders = founders
        self.investor_groups = investor_groups
        self.config = config
        self.llm_callback = llm_callback

        system_cfg = config.get("system", {})
        self.num_rounds = system_cfg.get("num_rounds", 3)
        self.verbose = bool(system_cfg.get("verbose", False))

        self.graph_mode = config.get("graph_mode", "all")
        graphs = config.get("interaction_graphs", {})
        self.interaction_graph: Dict[str, List[str]] = graphs.get(self.graph_mode, {})

        self.history: List[Dict[str, Any]] = []
        self.requirement = None

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)

    def _evaluate_groups(
        self,
        *,
        proposals: Dict[str, str],
        titles: Dict[str, str],
        budgets: Dict[str, int],
        founder_requirements: Dict[str, str],
        prototypes: Dict[str, str],
        current_round: int,
    ) -> Dict[str, Dict[str, Any]]:
        group_feedback: Dict[str, Dict[str, Any]] = {}

        def _eval_group(group: InvestorGroupNoMarket) -> Dict[str, Any]:
            visible_nodes = set(self.interaction_graph.get(group.name, []))
            visible_founders = set(proposals.keys()) & visible_nodes
            if not visible_founders:
                return {}
            visible_proposals = {name: proposals[name] for name in visible_founders}
            visible_titles = {name: titles.get(name, "") for name in visible_founders}
            visible_budgets = {name: int(budgets.get(name, 0)) for name in visible_founders}
            visible_prototypes = {name: prototypes.get(name, "") for name in visible_founders}
            visible_requirements = {name: founder_requirements.get(name, "") for name in visible_founders}
            return group.evaluate_visible_proposals(
                strategies=visible_proposals,
                llm_callback=self.llm_callback,
                requirement=None,
                founder_requirements=visible_requirements,
                titles=visible_titles,
                budgets=visible_budgets,
                prototypes=visible_prototypes,
                current_round=current_round,
            )

        with ThreadPoolExecutor() as executor:
            future_to_group = {executor.submit(_eval_group, group): group for group in self.investor_groups}
            for future in as_completed(future_to_group):
                group = future_to_group[future]
                group_feedback[group.name] = future.result()
        return group_feedback

    def _build_round_scores_from_feedback(
        self, investor_feedback: Dict[str, Dict[str, Any]], founder_names: List[str]
    ) -> Dict[str, Dict[str, float]]:
        all_scores: Dict[str, Dict[str, float]] = {}
        for group in self.investor_groups:
            gfb = investor_feedback.get(group.name, {})
            per_founder: Dict[str, float] = {}
            for founder_name in founder_names:
                info = gfb.get(founder_name, {})
                per_advices = info.get("per_investor_advices", {}) if isinstance(info, dict) else {}
                per_founder[founder_name] = float(len(per_advices))
            all_scores[group.name] = per_founder
        return all_scores

    def _initial_round(self, founder_requirements: Dict[str, str]) -> Dict[str, Any]:
        self._log("Round 1: Initial Proposal")
        strategies: Dict[str, str] = {}
        proposals: Dict[str, str] = {}
        titles: Dict[str, str] = {}
        budgets: Dict[str, int] = {}
        prototypes: Dict[str, str] = {}

        def _gen(founder: FounderNoMarket) -> Dict[str, Any]:
            founder.current_round = 1
            founder.generate_strategy(None, self.llm_callback)
            return {
                "proposal": founder.get_current_strategy(),
                "title": founder.get_current_title(),
                "budget": founder.get_current_budget(),
                "prototype": founder.get_current_prototype(),
            }

        with ThreadPoolExecutor() as executor:
            future_to_founder = {executor.submit(_gen, founder): founder for founder in self.founders}
            for future in as_completed(future_to_founder):
                founder = future_to_founder[future]
                result = future.result()
                proposals[founder.name] = result["proposal"]
                strategies[founder.name] = result["proposal"]
                titles[founder.name] = result["title"]
                budgets[founder.name] = result["budget"]
                prototypes[founder.name] = result["prototype"]

        investor_feedback = self._evaluate_groups(
            proposals=proposals,
            titles=titles,
            budgets=budgets,
            founder_requirements=founder_requirements,
            prototypes=prototypes,
            current_round=1,
        )
        all_scores = self._build_round_scores_from_feedback(investor_feedback, [f.name for f in self.founders])
        founder_scores = {
            founder.name: sum(all_scores.get(group.name, {}).get(founder.name, 0.0) for group in self.investor_groups)
            for founder in self.founders
        }

        return {
            "round": 1,
            "strategies": strategies,
            "proposals": proposals,
            "titles": titles,
            "budgets": budgets,
            "prototypes": prototypes,
            "all_scores": all_scores,
            "founder_scores": founder_scores,
            "investor_feedback": investor_feedback,
            "investment_history": {},
        }

    def _iteration_round(self, round_num: int) -> Dict[str, Any]:
        self._log(f"Iteration Round {round_num}")
        prev_round = self.history[-1]
        founder_requirements: Dict[str, str] = {f.name: getattr(f, "instruction", "") for f in self.founders}
        fb_prev = prev_round.get("investor_feedback", {})

        strategies: Dict[str, str] = {}
        proposals: Dict[str, str] = {}
        titles: Dict[str, str] = {}
        budgets: Dict[str, int] = {}
        prototypes: Dict[str, str] = {}

        def _build_and_iterate(founder: FounderNoMarket) -> Dict[str, Any]:
            founder.current_round = round_num
            your_name = founder.name
            my_topic = founder_requirements.get(your_name, "")

            visible_groups = {
                g.name
                for g in self.investor_groups
                if your_name in self.interaction_graph.get(g.name, [])
            }
            my_feedback_lines = []
            for group in self.investor_groups:
                gname = group.name
                if gname not in visible_groups:
                    continue
                per_group = fb_prev.get(gname, {}).get(your_name, {})
                detail = per_group.get("detail", per_group.get("summary", "")) if per_group else ""
                if detail:
                    my_feedback_lines.append(f"- {gname}:\n{detail}")

            my_prev_round = (
                f"Title: {prev_round.get('titles', {}).get(your_name, '')}\n"
                f"Topic: {my_topic}\n"
                f"Proposal:\n{prev_round.get('proposals', {}).get(your_name, '')}\n"
                f"Budget: {prev_round.get('budgets', {}).get(your_name, 0)} tokens\n"
                "Evaluator Feedback:\n"
                + ("\n".join(my_feedback_lines) if my_feedback_lines else "(no feedback)")
            )

            visible_others = {
                other.name
                for other in self.founders
                if other.name != your_name and other.name in self.interaction_graph.get(your_name, [])
            }
            others_lines: List[str] = []
            for other in self.founders:
                if other.name not in visible_others:
                    continue
                others_lines.append(f"\n[{other.name}]")
                others_lines.append(f"Title: {prev_round.get('titles', {}).get(other.name, '')}")
                others_lines.append(f"Topic: {founder_requirements.get(other.name, '')}")
                others_lines.append(f"Budget: {prev_round.get('budgets', {}).get(other.name, 0)} tokens")
                others_lines.append("Evaluator Feedback:")
                has_any = False
                for group in self.investor_groups:
                    gname = group.name
                    if other.name not in self.interaction_graph.get(gname, []):
                        continue
                    per_group = fb_prev.get(gname, {}).get(other.name, {})
                    summary = per_group.get("summary", "") if per_group else ""
                    if summary:
                        has_any = True
                        others_lines.append(f"  - {gname}: {summary}")
                if not has_any:
                    others_lines.append("  - (no feedback)")
            others_prev_round = "\n".join(others_lines)

            founder.iterate_strategy(
                all_scores={},
                llm_callback=self.llm_callback,
                feedback={"my_prev_round": my_prev_round, "others_prev_round": others_prev_round},
                requirement=self.requirement,
            )
            return {
                "proposal": founder.get_current_strategy(),
                "title": founder.get_current_title(),
                "budget": founder.get_current_budget(),
                "prototype": founder.get_current_prototype(),
            }

        with ThreadPoolExecutor() as executor:
            future_to_founder = {
                executor.submit(_build_and_iterate, founder): founder for founder in self.founders
            }
            for future in as_completed(future_to_founder):
                founder = future_to_founder[future]
                result = future.result()
                proposals[founder.name] = result["proposal"]
                strategies[founder.name] = result["proposal"]
                titles[founder.name] = result["title"]
                budgets[founder.name] = result["budget"]
                prototypes[founder.name] = result["prototype"]

        investor_feedback = self._evaluate_groups(
            proposals=proposals,
            titles=titles,
            budgets=budgets,
            founder_requirements=founder_requirements,
            prototypes=prototypes,
            current_round=round_num,
        )
        all_scores = self._build_round_scores_from_feedback(investor_feedback, [f.name for f in self.founders])
        founder_scores = {
            founder.name: sum(all_scores.get(group.name, {}).get(founder.name, 0.0) for group in self.investor_groups)
            for founder in self.founders
        }

        return {
            "round": round_num,
            "strategies": strategies,
            "proposals": proposals,
            "titles": titles,
            "budgets": budgets,
            "prototypes": prototypes,
            "all_scores": all_scores,
            "founder_scores": founder_scores,
            "investor_feedback": investor_feedback,
            "investment_history": {},
        }

    def _calculate_final_scores(self) -> Dict[str, float]:
        if not self.history:
            return {founder.name: 0.0 for founder in self.founders}
        final_scores = {founder.name: 0.0 for founder in self.founders}
        for round_data in self.history:
            founder_scores = round_data.get("founder_scores", {})
            for founder_name in final_scores.keys():
                final_scores[founder_name] += float(founder_scores.get(founder_name, 0.0))
        return final_scores

    def run(self) -> Dict[str, Any]:
        founder_requirements: Dict[str, str] = {f.name: getattr(f, "instruction", "") for f in self.founders}

        for major_round in tqdm(range(1, self.num_rounds + 1), desc="major_round", position=0):
            if major_round == 1:
                round_results = self._initial_round(founder_requirements)
            else:
                round_results = self._iteration_round(major_round)
            self.history.append(round_results)

        final_scores = self._calculate_final_scores()
        winner = max(final_scores.items(), key=lambda x: x[1]) if final_scores else ("", 0.0)
        return {
            "winner": winner[0],
            "winner_score": winner[1],
            "final_scores": final_scores,
            "all_rounds": self.history,
            "requirements": founder_requirements,
            "investment_history": {},
            "mode": "no_market_ablation",
        }

    def reset(self):
        for founder in self.founders:
            founder.reset()
        for group in self.investor_groups:
            group.reset()
        self.history = []

