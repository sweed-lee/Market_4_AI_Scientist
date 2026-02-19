"""
System orchestrator for managing multi-agent competition.

Coordinates Founders and Investors across multiple rounds.
"""

from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from agents.founder import Founder
from agents.investor import InvestorGroup, allocate_integers_proportionally
import json
from pathlib import Path

from system.checkpointing import build_checkpoint, save_checkpoint_file

try:
    from tqdm import tqdm  # type: ignore
except Exception:  # pragma: no cover
    # Fallback when tqdm is not installed
    def tqdm(iterable=None, total=None, desc=None, position=None, leave=None):
        if iterable is None:
            class _Dummy:
                def update(self, n=1):  # noqa: D401
                    return None
                def close(self):
                    return None
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc, tb):
                    return False
            return _Dummy()
        return iterable


class SystemOrchestrator:
    """Orchestrates the multi-agent system for multi-round competition."""
    
    def __init__(self, founders: List[Founder], investor_groups: List[InvestorGroup],
                 config: Dict[str, Any], llm_callback: Callable = None):
        """
        Initialize the orchestrator.
        
        Args:
            founders: List of Founder agents
            investor_groups: List of InvestorGroup agents
            config: Full configuration (root DEFAULT_CONFIG dict)
            llm_callback: Function to call LLM API (optional)
        """
        self.founders = founders
        self.investor_groups = investor_groups
        self.config = config
        self.llm_callback = llm_callback

        # System-level settings
        system_cfg = config.get('system', {})
        self.num_rounds = system_cfg.get('num_rounds', 3)
        self.max_points = system_cfg.get('max_investor_points', 100)
        # Budget tolerance for founder budgets (percentage, e.g., 0.1 = 10%)
        self.budget_tolerance_percent = system_cfg.get('budget_tolerance_percent', 0.1)
        # Maximum number of investment rounds per evaluation
        self.max_investment_rounds = system_cfg.get('max_investment_rounds', 5)
        # Max retries for investor allocation when validation fails (e.g., total != budget)
        self.max_allocation_retries = system_cfg.get('max_allocation_retries', 3)
        # Checkpoint settings (optional)
        self.enable_checkpoints = bool(system_cfg.get("enable_checkpoints", False))
        self.checkpoint_dir = system_cfg.get("checkpoint_dir", "checkpoints")
        # Logging verbosity (default: quiet; tqdm shows progress)
        self.verbose = bool(system_cfg.get("verbose", False))

        # Interaction graph (who can see / interact with whom)
        self.graph_mode = config.get('graph_mode', 'all')
        graphs = config.get('interaction_graphs', {})
        self.interaction_graph: Dict[str, List[str]] = graphs.get(self.graph_mode, {})

        self.history = []
        self.requirement = None  # Store requirement for use in iterations

    def _maybe_save_checkpoint(self, *, kind: str, major_round: int, payload: Dict[str, Any]) -> None:
        """Optionally save a checkpoint if enabled."""
        if not self.enable_checkpoints:
            return
        ckpt = build_checkpoint(
            kind=kind,
            config=self.config,
            orchestrator=self,
            major_round=major_round,
            payload=payload,
        )
        fname = f"{kind}_major_round_{major_round}_{ckpt['timestamp_utc']}.json"
        path = str(Path(self.checkpoint_dir) / fname)
        save_checkpoint_file(path, ckpt)

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(msg)
    
    def _run_investment_rounds(
        self,
        strategies: Dict[str, str],
        titles: Dict[str, str],
        budgets: Dict[str, int],
        founder_requirements: Dict[str, str],
        previous_major_round_history: str = None,
        prototypes: Dict[str, str] = None,
        major_round: int = 1,
    ) -> Dict[str, Any]:
        """
        Run multiple investment rounds until all groups exhaust capital or reach max rounds.
        
        Returns:
            Dictionary containing:
            - all_scores: {group_name: {founder_name: total_investment}}
            - investor_feedback: {group_name: {founder_name: feedback}}
            - investment_history: {investment_round_N: {...}}
        """
        all_scores: Dict[str, Dict[str, float]] = {group.name: {} for group in self.investor_groups}
        all_investor_feedback: Dict[str, Dict[str, Any]] = {group.name: {} for group in self.investor_groups}
        investment_history: Dict[str, Dict[str, Any]] = {}
        
        # Track which founders are still in the market (not exited)
        remaining_founders = set(strategies.keys())
        
        # Track accumulated investments per founder (across all investment rounds)
        accumulated_investments_per_founder: Dict[str, int] = {name: 0 for name in strategies.keys()}
        
        # Track investment history for building history summary
        current_major_round_history: List[Dict[str, Any]] = []

        # === STEP 1 (run once outside the investment-round loop): cache proposal evaluations ===
        # We evaluate each group on its visible founders once, and reuse the cached
        # score/advice artifacts for all subsequent investment rounds.
        step1_groups = [g for g in self.investor_groups if g.total_capital >= 10]
        if step1_groups and remaining_founders:
            # Build a history summary for step-1 (previous major round only; current major is empty here)
            step1_history_parts = []
            if previous_major_round_history:
                step1_history_parts.append("**Previous Major Round Investment History:**")
                step1_history_parts.append(previous_major_round_history)
                step1_history_parts.append("")
            step1_history_summary = "\n".join(step1_history_parts) if step1_history_parts else "**Investment History:** No previous investment history available."

            def _run_group_step1(group: InvestorGroup) -> None:
                visible_nodes = set(self.interaction_graph.get(group.name, []))
                visible_founders = remaining_founders & visible_nodes
                if not visible_founders:
                    group.step1_cache = {}
                    return
                visible_strategies = {fname: strategies[fname] for fname in visible_founders}
                visible_titles = {fname: titles.get(fname, "") for fname in visible_founders}
                visible_budgets = {fname: budgets.get(fname, 0) for fname in visible_founders}
                visible_prototypes = {fname: (prototypes or {}).get(fname, "") for fname in visible_founders}
                group.run_step1_evaluations(
                    visible_strategies,
                    self.llm_callback,
                    None,
                    {k: v for k, v in founder_requirements.items() if k in visible_founders},
                    visible_titles,
                    visible_budgets,
                    self.budget_tolerance_percent,
                    step1_history_summary,
                    1,
                    visible_prototypes,
                )

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(_run_group_step1, g) for g in step1_groups]
                for f in as_completed(futures):
                    f.result()
        
        # Investment rounds loop (progress shown via tqdm)
        with tqdm(total=self.max_investment_rounds, desc=f"investment_round (major {major_round})", position=1, leave=False) as inv_pbar:
            for investment_round in range(1, self.max_investment_rounds + 1):
                # Check if any founders remain
                if not remaining_founders:
                    break
                
                # Check if any groups have remaining capital (treat < 10 as exhausted)
                groups_with_capital = [
                    g for g in self.investor_groups 
                    if g.total_capital >= 10
                ]
                if not groups_with_capital:
                    break
                
                # Build investment history summary for this round
                history_parts = []
                if previous_major_round_history:
                    history_parts.append("**Previous Major Round Investment History:**")
                    history_parts.append(previous_major_round_history)
                    history_parts.append("")
                
                if current_major_round_history:
                    history_parts.append(f"**Current Major Round Investment History (completed {len(current_major_round_history)} rounds so far):**")
                    for round_entry in current_major_round_history:
                        round_entry_num = round_entry.get('round', 0)
                        history_parts.append(f"\nInvestment Round {round_entry_num}:")
                        if 'founders' in round_entry:
                            for founder_name, founder_data in round_entry['founders'].items():
                                planned = founder_data.get('total_planned_invested', 0)
                                accepted = founder_data.get('total_accepted', 0)
                                refunded = founder_data.get('total_refunded', 0)
                                history_parts.append(
                                    f"  - {founder_name}: Planned {int(planned)} tokens, Accepted {int(accepted)} tokens, Refunded {int(refunded)} tokens"
                                )
                
                history_summary = "\n".join(history_parts) if history_parts else "**Investment History:** No previous investment history available."
                
                # All groups evaluate in parallel for this investment round
                round_investments: Dict[str, Dict[str, float]] = {}  # {group_name: {founder_name: investment}}
                round_feedback: Dict[str, Dict[str, Any]] = {}
                
                def _eval_group_single_round(group: InvestorGroup) -> Dict[str, Any]:
                    # Get visible founders for this group (only those still in market)
                    visible_nodes = set(self.interaction_graph.get(group.name, []))
                    visible_founders = remaining_founders & visible_nodes
                    
                    if not visible_founders:
                        return {"investments": {}, "feedback": {}}
                    
                    visible_strategies = {fname: strategies[fname] for fname in visible_founders}
                    visible_titles = {fname: titles[fname] for fname in visible_founders}
                    visible_budgets = {fname: budgets[fname] for fname in visible_founders}
                    visible_prototypes = {}
                    if prototypes:
                        visible_prototypes = {fname: prototypes.get(fname, '') for fname in visible_founders}
                    
                    investments = group.evaluate_strategies_single_round(
                        visible_strategies,
                        self.llm_callback,
                        None,
                        {k: v for k, v in founder_requirements.items() if k in visible_founders},
                        visible_titles,
                        visible_budgets,
                        self.budget_tolerance_percent,
                        history_summary,
                        investment_round,
                        visible_prototypes,
                        # Accumulated investment context (before this round)
                        {fname: int(accumulated_investments_per_founder.get(fname, 0)) for fname in visible_founders},
                        {fname: int(all_scores.get(group.name, {}).get(fname, 0.0)) for fname in visible_founders},
                        max_allocation_retries=self.max_allocation_retries,
                    )
                    
                    # Get feedback from group's last history entry
                    fb = {}
                    if group.history:
                        last_entry = group.history[-1]
                        fb = last_entry.get("feedback", {})
                    
                    return {"investments": investments, "feedback": fb}
                
                with ThreadPoolExecutor() as executor:
                    future_to_group = {
                        executor.submit(_eval_group_single_round, group): group
                        for group in groups_with_capital
                    }
                    for future in as_completed(future_to_group):
                        group = future_to_group[future]
                        result = future.result()
                        round_investments[group.name] = result["investments"]
                        round_feedback[group.name] = result["feedback"]
                
                # Process investments across all groups: check budget limits and handle refunds
                # Step 1: Collect raw investments from all groups for this round
                all_group_investments_this_round: Dict[str, Dict[str, int]] = {}  # {founder_name: {group_name: investment}}
                for group_name, group_investments in round_investments.items():
                    for founder_name, investment in group_investments.items():
                        if founder_name not in all_group_investments_this_round:
                            all_group_investments_this_round[founder_name] = {}
                        all_group_investments_this_round[founder_name][group_name] = int(round(investment))
                
                # Step 2: Process budget limits and calculate accepted/refunded amounts
                group_refunds_this_round: Dict[str, Dict[str, int]] = {}  # {founder_name: {group_name: refund_amount}}
                final_accepted_investments_this_round: Dict[str, Dict[str, int]] = {}  # {founder_name: {group_name: accepted}}
                exited_founders_this_round = []
                
                for founder_name in list(remaining_founders):
                    if founder_name not in budgets:
                        continue
                    
                    budget = int(budgets[founder_name])
                    lower_bound = int(budget * (1 - self.budget_tolerance_percent))
                    upper_bound = int(budget * (1 + self.budget_tolerance_percent))
                    
                    # Get investments from this round only
                    round_investment_dict = all_group_investments_this_round.get(founder_name, {})
                    round_total = sum(round_investment_dict.values())
                    
                    if round_total == 0:
                        # No investment this round, skip
                        final_accepted_investments_this_round[founder_name] = {}
                        group_refunds_this_round[founder_name] = {}
                        continue
                    
                    # Get current accumulated investment (before this round)
                    current_accumulated = accumulated_investments_per_founder[founder_name]
                    total_after_round = current_accumulated + round_total
                    
                    if total_after_round >= upper_bound:
                        # >= upper_bound: Allocate up to upper_bound proportionally, return excess
                        # Calculate how much we can accept from this round to reach upper_bound
                        remaining_to_upper = upper_bound - current_accumulated
                        if remaining_to_upper > 0:
                            # Allocate remaining_to_upper proportionally from this round's investments
                            accepted_this_round = allocate_integers_proportionally(round_investment_dict, remaining_to_upper)
                            excess_this_round = {g: round_investment_dict[g] - accepted_this_round.get(g, 0) 
                                                for g in round_investment_dict.keys()}
                        else:
                            # Already exceeded upper bound, all this round's investments are excess
                            accepted_this_round = {g: 0 for g in round_investment_dict.keys()}
                            excess_this_round = round_investment_dict.copy()
                        
                        final_accepted_investments_this_round[founder_name] = accepted_this_round
                        group_refunds_this_round[founder_name] = excess_this_round
                        # Update accumulated to upper_bound
                        accumulated_investments_per_founder[founder_name] = upper_bound
                        exited_founders_this_round.append(founder_name)
                    elif total_after_round >= lower_bound:
                        # Within bounds: All investments accepted, no refunds
                        final_accepted_investments_this_round[founder_name] = round_investment_dict.copy()
                        group_refunds_this_round[founder_name] = {group_name: 0 for group_name in round_investment_dict.keys()}
                        # Update accumulated
                        accumulated_investments_per_founder[founder_name] = total_after_round
                        # Founder exits if reached lower bound (success)
                        exited_founders_this_round.append(founder_name)
                    else:
                        # < lower_bound: All investments accepted for now, but founder continues
                        final_accepted_investments_this_round[founder_name] = round_investment_dict.copy()
                        group_refunds_this_round[founder_name] = {group_name: 0 for group_name in round_investment_dict.keys()}
                        # Update accumulated
                        accumulated_investments_per_founder[founder_name] = total_after_round
                
                # Step 3: Update group capitals (add back refunds)
                for founder_name, group_acceptances in final_accepted_investments_this_round.items():
                    for group_name, accepted_amount in group_acceptances.items():
                        refund_amount = group_refunds_this_round[founder_name].get(group_name, 0)
                        
                        for group in self.investor_groups:
                            if group.name == group_name:
                                # Add back refund (since original was already deducted in evaluate_strategies_single_round)
                                group.total_capital += refund_amount
                                break
                
                # Step 4: Accumulated investments are already updated in Step 2 above
                
                # Step 5: Update remaining founders (remove exited ones)
                remaining_founders -= set(exited_founders_this_round)
                
                # Step 6: Update all_scores with accumulated investments
                for founder_name in strategies.keys():
                    for group in self.investor_groups:
                        if founder_name in self.interaction_graph.get(group.name, []):
                            # Sum up accepted investments from all rounds for this group
                            if founder_name not in all_scores[group.name]:
                                all_scores[group.name][founder_name] = 0.0
                            # Add this round's accepted investment from this group
                            accepted = final_accepted_investments_this_round.get(founder_name, {}).get(group.name, 0)
                            all_scores[group.name][founder_name] += float(accepted)
                
                # Step 7: Merge feedback
                for group_name, fb in round_feedback.items():
                    all_investor_feedback[group_name].update(fb)
                
                # Step 8: Record investment history for this round
                # Gather per-investor allocations for this round from each group's last history entry
                per_group_per_investor_allocations_this_round: Dict[str, Dict[str, Dict[str, float]]] = {}
                for group in self.investor_groups:
                    if hasattr(group, "history") and group.history:
                        last_h = group.history[-1]
                        if last_h.get("round") == investment_round:
                            per_group_per_investor_allocations_this_round[group.name] = last_h.get("per_investor_allocations", {}) or {}
    
                round_history_entry = {
                    'round': investment_round,
                    'investor_groups': {},
                    'investors': {},
                    'founders': {}
                }
                
                # Record group-level statistics
                for group in self.investor_groups:
                    group_invested = sum(all_group_investments_this_round.get(fname, {}).get(group.name, 0) 
                                       for fname in strategies.keys())
                    group_accepted = sum(final_accepted_investments_this_round.get(fname, {}).get(group.name, 0) 
                                       for fname in strategies.keys())
                    group_refunded = sum(group_refunds_this_round.get(fname, {}).get(group.name, 0) 
                                        for fname in strategies.keys())
                    
                    round_history_entry['investor_groups'][group.name] = {
                        # capital_before: at recording time group.total_capital = capital_after (post Step 3).
                        # capital_after = capital_before - accepted, so capital_before = capital_after + accepted.
                        'capital_before': group.total_capital + group_accepted,
                        'total_planned_invested': group_invested,
                        'total_accepted': group_accepted,
                        'total_refunded': group_refunded,
                        'capital_after': group.total_capital
                    }
                
                # Record founder-level statistics
                for founder_name in strategies.keys():
                    budget_val = int(budgets.get(founder_name, 0) or 0)
                    lower_bound = int(budget_val * (1 - self.budget_tolerance_percent)) if budget_val else 0
                    upper_bound = int(budget_val * (1 + self.budget_tolerance_percent)) if budget_val else 0
                    total_planned = int(sum(all_group_investments_this_round.get(founder_name, {}).values()))
                    total_accepted = int(sum(final_accepted_investments_this_round.get(founder_name, {}).values()))
                    total_refunded = int(sum(group_refunds_this_round.get(founder_name, {}).values()))
                    round_history_entry['founders'][founder_name] = {
                        'total_budget': budget_val,
                        'lower_bound': lower_bound,
                        'upper_bound': upper_bound,
                        'accumulated_investment': accumulated_investments_per_founder[founder_name],
                        'total_planned_invested': total_planned,
                        'total_accepted': total_accepted,
                        'total_refunded': total_refunded,
                        'per_group': {
                            group.name: {
                                'invested': all_group_investments_this_round.get(founder_name, {}).get(group.name, 0),
                                'accepted': final_accepted_investments_this_round.get(founder_name, {}).get(group.name, 0),
                                'refunded': group_refunds_this_round.get(founder_name, {}).get(group.name, 0)
                            }
                            for group in self.investor_groups
                            if group.name in all_group_investments_this_round.get(founder_name, {})
                        }
                    }
    
                # Record investor-level statistics (planned vs accepted vs refunded), using step-2 per-investor allocations
                for group in self.investor_groups:
                    group_name = group.name
                    inv_allocs = per_group_per_investor_allocations_this_round.get(group_name, {})
                    if not inv_allocs:
                        continue
                    # capital_before = capital_after + accepted (same as group-level stats above)
                    group_accepted = sum(final_accepted_investments_this_round.get(fname, {}).get(group_name, 0) for fname in strategies.keys())
                    capital_before = int(group.total_capital + group_accepted)
                    inv_names = [inv.name for inv in getattr(group, "investors", [])]
                    num_inv = len(inv_names) if inv_names else max(1, len(inv_allocs))
                    budget_per_investor = int(capital_before // num_inv) if num_inv else 0
    
                    round_history_entry["investors"][group_name] = {
                        "budget_per_investor": budget_per_investor,
                        "investors": {},
                    }
    
                    # For each investor, compute integer planned allocations per founder that sum to group planned invested per founder,
                    # then split accepted/refunded proportionally.
                    for inv_name, per_founder_alloc in inv_allocs.items():
                        inv_entry = {
                            "planned_total": 0,
                            "accepted_total": 0,
                            "refunded_total": 0,
                            "per_founder": {},
                        }
                        round_history_entry["investors"][group_name]["investors"][inv_name] = inv_entry
    
                    for founder_name, per_group in all_group_investments_this_round.items():
                        group_planned_total = int(per_group.get(group_name, 0))
                        if group_planned_total <= 0:
                            continue
                        # Raw floats from LLM allocations (per-investor)
                        raw = {inv_name: float((inv_allocs.get(inv_name, {}) or {}).get(founder_name, 0.0)) for inv_name in inv_allocs.keys()}
                        planned_by_inv = allocate_integers_proportionally(raw, group_planned_total)
    
                        accepted_total_fg = int(final_accepted_investments_this_round.get(founder_name, {}).get(group_name, 0))
                        accepted_by_inv = allocate_integers_proportionally({k: float(v) for k, v in planned_by_inv.items()}, accepted_total_fg)
    
                        for inv_name, planned_amt in planned_by_inv.items():
                            accepted_amt = int(accepted_by_inv.get(inv_name, 0))
                            refunded_amt = int(planned_amt - accepted_amt)
                            inv_entry = round_history_entry["investors"][group_name]["investors"][inv_name]
                            inv_entry["per_founder"][founder_name] = {
                                "planned": int(planned_amt),
                                "accepted": int(accepted_amt),
                                "refunded": int(refunded_amt),
                            }
                            inv_entry["planned_total"] += int(planned_amt)
                            inv_entry["accepted_total"] += int(accepted_amt)
                            inv_entry["refunded_total"] += int(refunded_amt)
                
                current_major_round_history.append(round_history_entry)
                investment_history[f"investment_round_{investment_round}"] = round_history_entry
                inv_pbar.update(1)
        
        return {
            "all_scores": all_scores,
            "investor_feedback": all_investor_feedback,
            "investment_history": investment_history,
            "accumulated_investments": accumulated_investments_per_founder,
        }
    
    def _format_previous_major_round_history(self, investment_history: Dict[str, Any]) -> str:
        """Format previous major round investment history for display."""
        if not investment_history:
            return None
        
        parts = []
        parts.append("**Previous Major Round Investment Results:**")
        
        # Extract final accumulated investments from the last investment round
        round_keys = sorted([k for k in investment_history.keys() if k.startswith('investment_round_')], 
                          key=lambda x: int(x.split('_')[-1]))
        if round_keys:
            last_round = investment_history[round_keys[-1]]
            if 'founders' in last_round:
                for founder_name, founder_data in last_round['founders'].items():
                    accumulated = founder_data.get('accumulated_investment', 0)
                    budget = founder_data.get('total_budget', 0)
                    lower_bound = int(budget * (1 - self.budget_tolerance_percent)) if budget > 0 else 0
                    if accumulated >= lower_bound:
                        parts.append(f"  - {founder_name}: ✓ SUCCESS (Investment: {int(accumulated)} tokens >= lower bound: {lower_bound} tokens)")
            else:
                        parts.append(f"  - {founder_name}: ✗ FAILURE (Investment: {int(accumulated)} tokens < lower bound: {lower_bound} tokens)")
        
        return "\n".join(parts) if parts else None
    
    def _get_previous_major_round_history(self, group) -> str:
        """Extract and format previous major round investment history for a group (simplified)."""
        # This method is kept for backward compatibility but is no longer used
        # History is now formatted at orchestrator level
        return None
    
    def _collect_investment_history(self, major_round: int) -> Dict[str, Dict[str, Any]]:
        """
        Legacy method - kept for backward compatibility but no longer used.
        
        Investment history is now collected directly in _run_investment_rounds() method
        during each investment round (see Step 8 in that method).
        """
        return {}
    
    
    def run(self) -> Dict[str, Any]:
        """
        Run the full multi-round competition.
            
        Returns:
            Complete results including winner and all round data
        """
        # Build per-founder requirements (tasks)
        founder_requirements: Dict[str, str] = {
            f.name: getattr(f, "instruction", "") for f in self.founders
        }
        
        # quiet by default; enable system.verbose for detailed prints
        
        # Major rounds loop (progress shown via tqdm)
        for major_round in tqdm(range(1, self.num_rounds + 1), desc="major_round", position=0):
            if major_round == 1:
                round_results = self._initial_round(founder_requirements)
            else:
                round_results = self._iteration_round(major_round)
            self.history.append(round_results)
        
        # Calculate final winner
        final_scores = self._calculate_final_scores()
        winner = max(final_scores.items(), key=lambda x: x[1])
        
        # Collect all investment history across all major rounds
        all_investment_history = {}
        for major_round in range(1, self.num_rounds + 1):
            major_round_key = f"major_round_{major_round}"
            all_investment_history[major_round_key] = {}
            
            # Get investment history from round data
            if major_round <= len(self.history):
                round_data = self.history[major_round - 1]
                if 'investment_history' in round_data:
                    all_investment_history[major_round_key] = round_data['investment_history']
        
        results = {
            'winner': winner[0],
            'winner_score': winner[1],
            'final_scores': final_scores,
            'all_rounds': self.history,
            'requirements': founder_requirements,
            'investment_history': all_investment_history  # Detailed investment history by major round
        }
        
        if self.verbose:
            self._print_summary(results)
        
        return results
    
    def _initial_round(self, founder_requirements: Dict[str, str]) -> Dict[str, Any]:
        """Execute the initial round where founders propose strategies."""
        self._log("Round 1: Initial Strategy Proposal")
        
        # Reset investor groups and founders for new major round
        for group in self.investor_groups:
            group.total_capital = group.initial_capital
            group.history = []
        for founder in self.founders:
            founder.accumulated_investment = 0
        
        strategies: Dict[str, str] = {}
        proposals: Dict[str, str] = {}
        titles: Dict[str, str] = {}
        budgets: Dict[str, int] = {}
        prototypes: Dict[str, str] = {}

        # === Founder提出阶段：并行生成初始策略 ===
        def _gen_strategy(f: Founder) -> Dict[str, str]:
            # quiet by default
            
            # Set current round for dialog logging
            f.current_round = 1
            
            # Calculate market information for this founder
            visible_groups = [
                g for g in self.investor_groups
                if f.name in self.interaction_graph.get(g.name, [])
            ]
            num_investor_groups = len(visible_groups)
            capital_per_group = sum(g.total_capital for g in visible_groups) / len(visible_groups) if visible_groups else 0.0
            
            visible_competitors = {
                other.name
                for other in self.founders
                if other.name != f.name
                and other.name in self.interaction_graph.get(f.name, [])
            }
            num_competitors = len(visible_competitors)
            
            # Each founder uses its own requirement/instruction from config
            strategy_text = f.generate_strategy(
                None, 
                self.llm_callback,
                num_investor_groups=num_investor_groups,
                capital_per_group=capital_per_group,
                num_competitors=num_competitors
            )
            proposal_only = f.get_current_strategy()
            title_only = f.get_current_title()
            budget_only = f.get_current_budget()
            prototype_only = f.get_current_prototype()
            # quiet by default
            return {"strategy": strategy_text, "proposal": proposal_only, "title": title_only, "budget": budget_only, "prototype": prototype_only}

        with ThreadPoolExecutor() as executor:
            future_to_founder = {
                executor.submit(_gen_strategy, founder): founder
                for founder in self.founders
            }
            for future in as_completed(future_to_founder):
                founder = future_to_founder[future]
                result = future.result()
                # For downstream investors, we only want the clean proposal
                # (without [THINKING]) as the visible "strategy".
                strategies[founder.name] = result["proposal"]
                proposals[founder.name] = result["proposal"]
                titles[founder.name] = result.get("title", "")
                budgets[founder.name] = result.get("budget", 0)
                prototypes[founder.name] = result.get("prototype", "")

        # === Investor评审阶段：运行多轮投资循环 ===
        # Get previous major round history (None for first round)
        previous_history = None
        if len(self.history) > 0:
            # Build previous history from last major round
            prev_round_data = self.history[-1]
            if 'investment_history' in prev_round_data:
                previous_history = self._format_previous_major_round_history(prev_round_data['investment_history'])
        # Checkpoint A: founders have submitted; before investor evaluation
        self._maybe_save_checkpoint(
            kind="founder_submitted",
            major_round=1,
            payload={
                "strategies": strategies,
                "proposals": proposals,
                "titles": titles,
                "budgets": budgets,
                "prototypes": prototypes,
                "founder_requirements": founder_requirements,
                "previous_major_round_history": previous_history,
            },
        )
        
        investment_result = self._run_investment_rounds(
            strategies,
            titles,
            budgets,
                founder_requirements,
                previous_history,
            prototypes,
            major_round=1,
            )
        
        all_scores = investment_result["all_scores"]
        investor_feedback = investment_result["investor_feedback"]
        investment_history = investment_result["investment_history"]
        accumulated_investments = investment_result["accumulated_investments"]
        
        # Update founder accumulated investments
        for founder in self.founders:
            founder.accumulated_investment = accumulated_investments.get(founder.name, 0)
        
        # Aggregate scores for each founder
        founder_scores = {}
        for founder in self.founders:
            total_score = 0.0
            for group in self.investor_groups:
                if founder.name in self.interaction_graph.get(group.name, []):
                    total_score += all_scores.get(group.name, {}).get(founder.name, 0.0)
            founder_scores[founder.name] = total_score
        
        round_data = {
            'round': 1,
            'strategies': strategies,
            'proposals': proposals,
            'titles': titles,
            'budgets': budgets,
            'budget_bounds': {
                name: {
                    "budget": int(budgets.get(name, 0) or 0),
                    "lower_bound": int((budgets.get(name, 0) or 0) * (1 - self.budget_tolerance_percent)),
                    "upper_bound": int((budgets.get(name, 0) or 0) * (1 + self.budget_tolerance_percent)),
                }
                for name in budgets.keys()
            },
            'prototypes': prototypes,
            'all_scores': all_scores,
            'founder_scores': founder_scores,
            'investor_feedback': investor_feedback,
            'investment_history': investment_history
        }

        # Checkpoint B: investor evaluation done; before next major round
        self._maybe_save_checkpoint(
            kind="investor_evaluated",
            major_round=1,
            payload={
                "round_data": round_data,
            },
        )
        
        if self.verbose:
            self._print_round_summary(round_data)
        
        return round_data
    
    def _iteration_round(self, round_num: int) -> Dict[str, Any]:
        """Execute an iteration round where founders refine strategies."""
        self._log(f"Iteration Round {round_num}")
        
        # Reset investor groups and founders for new major round
        for group in self.investor_groups:
            group.total_capital = group.initial_capital
            group.history = []
        for founder in self.founders:
            founder.accumulated_investment = 0
        
        # Get previous round's scores
        prev_round = self.history[-1]
        all_scores = prev_round['all_scores']
        # Per-founder requirements are stored in the top-level config and
        # bound into each founder instance; rebuild mapping for passing to
        # investor groups.
        founder_requirements: Dict[str, str] = {
            f.name: getattr(f, "instruction", "") for f in self.founders
        }
        
        # Founders iterate on their strategies（founder提出阶段 - 迭代），并行执行
        strategies = {}
        proposals = {}
        titles = {}
        budgets = {}
        prototypes = {}

        def _build_and_iterate(founder: Founder) -> Dict[str, Any]:
            # quiet by default
            
            # Set current round for dialog logging
            founder.current_round = round_num
            
            fb_prev = prev_round.get("investor_feedback", {})
            your_name = founder.name

            # Your previous round block
            detailed_lines = []
            # Add explicit topic line (per-founder requirement/instruction)
            my_topic = founder_requirements.get(your_name, "")
            visible_groups = {
                g.name
                for g in self.investor_groups
                if your_name in self.interaction_graph.get(g.name, [])
            }
            for group in self.investor_groups:
                inv_name = group.name
                if inv_name not in visible_groups:
                    continue
                per_inv = fb_prev.get(inv_name, {}).get(your_name, {})
                if per_inv:
                    r1_scores_plain = per_inv.get("round1_proposal_scores_plain_text", "")
                    r1_specialties = per_inv.get("round1_specialties_text", "")
                    r1_block = ""
                    if r1_scores_plain:
                        # Inject config specialties (investor.criteria) into the header, not as a literal word.
                        # Example:
                        # "Investor proposal scoring (Innovation and novelty, Market fit, Feasibility): Investor_1: 76.0/100; Investor_2: 64.0/100; ..."
                        if r1_specialties:
                            r1_block = f" | Investor proposal scoring ({r1_specialties}): {r1_scores_plain}"
                        else:
                            r1_block = f" | Investor proposal scoring: {r1_scores_plain}"
                    group_total_accepted = float(all_scores.get(inv_name, {}).get(your_name, 0.0))
                    detailed_lines.append(
                        f"- {inv_name}: accepted {group_total_accepted:.2f} | "
                        f"{per_inv.get('detail', per_inv.get('summary', ''))}"
                        f"{r1_block}"
                    )
            my_total = sum(
                all_scores.get(group.name, {}).get(your_name, 0.0)
                for group in self.investor_groups
                if group.name in visible_groups
            )
            # Get previous round success/failure status (legacy, kept for backward compatibility)
            prev_success_failure = ""
            if round_num > 1:
                # Get success/failure from previous round's investor groups
                for group in self.investor_groups:
                    if your_name in self.interaction_graph.get(group.name, []):
                        if hasattr(group, 'history') and group.history:
                            last_summary = group.history[-1]
                            if 'final_success_failure' in last_summary:
                                status = last_summary['final_success_failure'].get(your_name, '')
                                accumulated = last_summary.get('accumulated_investments', {}).get(your_name, 0)
                                budget = last_summary.get('budgets', {}).get(your_name, 0)
                                lower_bound = int(budget * (1 - self.budget_tolerance_percent)) if budget > 0 else 0
                                if status == "success":
                                    prev_success_failure = f"\nPrevious Round Result: ✓ SUCCESS (Accumulated investment: {accumulated} tokens >= lower bound: {lower_bound} tokens)"
                                elif status == "failure":
                                    prev_success_failure = f"\nPrevious Round Result: ✗ FAILURE (Accumulated investment: {accumulated} tokens < lower bound: {lower_bound} tokens)"
                                break
            
            # Build my_prev_round: Title + Proposal + Budget + All investor scores and detailed feedback
            my_title = prev_round.get('titles', {}).get(your_name, '')
            my_proposal = prev_round.get('proposals', {}).get(your_name, '')
            my_budget = prev_round.get('budgets', {}).get(your_name, 0)
            my_lower = int(my_budget * (1 - self.budget_tolerance_percent)) if my_budget else 0
            my_upper = int(my_budget * (1 + self.budget_tolerance_percent)) if my_budget else 0
            my_status = ""
            if my_budget:
                if my_total >= my_upper:
                    my_status = f"Status: capped (>= upper bound {my_upper})"
                elif my_total >= my_lower:
                    my_status = f"Status: funded (>= lower bound {my_lower})"
                else:
                    my_status = f"Status: underfunded (< lower bound {my_lower})"
            my_prev_round = (
                f"Title: {my_title}\n"
                f"Topic: {my_topic}\n"
                f"Proposal:\n{my_proposal}\n"
                f"Budget: {my_budget} tokens (bounds: {my_lower}-{my_upper}, ±{self.budget_tolerance_percent*100:.0f}%)\n"
                f"Total Investment Accepted: {my_total:.2f} tokens\n"
                + (f"{my_status}\n" if my_status else "")
                + "All Investor Evaluations:\n"
                + ("\n".join(detailed_lines) if detailed_lines else "(no evaluations)")
                + prev_success_failure
            )

            # Others previous round block: Title + Budget + Investor summaries and scores
            others_lines = []
            visible_others = {
                other.name
                for other in self.founders
                if other.name != your_name
                and other.name in self.interaction_graph.get(your_name, [])
            }
            for other in self.founders:
                if other.name not in visible_others:
                    continue
                other_title = prev_round.get('titles', {}).get(other.name, '')
                other_budget = prev_round.get('budgets', {}).get(other.name, 0)
                other_lower = int(other_budget * (1 - self.budget_tolerance_percent)) if other_budget else 0
                other_upper = int(other_budget * (1 + self.budget_tolerance_percent)) if other_budget else 0
                other_topic = founder_requirements.get(other.name, "")
                # Calculate total investment for this other founder
                other_total = sum(
                    all_scores.get(group.name, {}).get(other.name, 0.0)
                    for group in self.investor_groups
                    if other.name in self.interaction_graph.get(group.name, [])
                )
                other_status = ""
                if other_budget:
                    if other_total >= other_upper:
                        other_status = f"Status: capped (>= upper bound {other_upper})"
                    elif other_total >= other_lower:
                        other_status = f"Status: funded (>= lower bound {other_lower})"
                    else:
                        other_status = f"Status: underfunded (< lower bound {other_lower})"
                others_lines.append(f"\n[{other.name}]")
                others_lines.append(f"Title: {other_title}")
                others_lines.append(f"Topic: {other_topic}")
                others_lines.append(f"Budget: {other_budget} tokens (bounds: {other_lower}-{other_upper}, ±{self.budget_tolerance_percent*100:.0f}%)")
                others_lines.append(f"Total Investment Accepted: {other_total:.2f} tokens")
                if other_status:
                    others_lines.append(other_status)
                others_lines.append("Investor Evaluations:")
                # Only show investors that evaluated this founder
                for group in self.investor_groups:
                    inv_name = group.name
                    if other.name not in self.interaction_graph.get(inv_name, []):
                        continue
                    per_inv = fb_prev.get(inv_name, {}).get(other.name, {})
                    if per_inv:
                        r1_scores_plain = per_inv.get("round1_proposal_scores_plain_text", "")
                        r1_specialties = per_inv.get("round1_specialties_text", "")
                        r1_block = ""
                        if r1_scores_plain:
                            if r1_specialties:
                                r1_block = f" | Investor proposal scoring ({r1_specialties}): {r1_scores_plain}"
                            else:
                                r1_block = f" | Investor proposal scoring: {r1_scores_plain}"
                        group_total_accepted = float(all_scores.get(inv_name, {}).get(other.name, 0.0))
                        others_lines.append(
                            f"  - {inv_name}: accepted {group_total_accepted:.2f} | "
                            f"{per_inv.get('summary', '')}"
                            f"{r1_block}"
                        )
            others_prev_round = "\n".join(others_lines)
            
            # Calculate market information for this founder
            visible_groups = [
                g for g in self.investor_groups
                if your_name in self.interaction_graph.get(g.name, [])
            ]
            num_investor_groups = len(visible_groups)
            capital_per_group = sum(g.total_capital for g in visible_groups) / len(visible_groups) if visible_groups else 0.0
            num_competitors = len(visible_others)

            strategy = founder.iterate_strategy(
                all_scores,
                self.llm_callback,
                feedback={
                    "my_prev_round": my_prev_round,
                    "others_prev_round": others_prev_round,
                    "requirement": self.requirement,
                    "num_investor_groups": num_investor_groups,
                    "capital_per_group": capital_per_group,
                    "num_competitors": num_competitors,
                },
                requirement=self.requirement,
            )
            proposal_only = founder.get_current_strategy()
            title_only = founder.get_current_title()
            budget_only = founder.get_current_budget()
            prototype_only = founder.get_current_prototype()
            # quiet by default
            return {"strategy": strategy, "proposal": proposal_only, "title": title_only, "budget": budget_only, "prototype": prototype_only}

        with ThreadPoolExecutor() as executor:
            future_to_founder = {
                executor.submit(_build_and_iterate, founder): founder
                for founder in self.founders
            }
            for future in as_completed(future_to_founder):
                founder = future_to_founder[future]
                result = future.result()
                # 同样，迭代轮中传给 investors 的也只保留 proposal 部分
                strategies[founder.name] = result["proposal"]
                proposals[founder.name] = result["proposal"]
                titles[founder.name] = result.get("title", "")
                budgets[founder.name] = result.get("budget", 0)
                prototypes[founder.name] = result.get("prototype", "")

        # === Investor评审阶段：运行多轮投资循环 ===
        # Get previous major round history
        previous_history = None
        if len(self.history) > 0:
            prev_round_data = self.history[-1]
            if 'investment_history' in prev_round_data:
                previous_history = self._format_previous_major_round_history(prev_round_data['investment_history'])

        # Checkpoint A: founders have submitted; before investor evaluation
        self._maybe_save_checkpoint(
            kind="founder_submitted",
            major_round=round_num,
            payload={
                "strategies": strategies,
                "proposals": proposals,
                "titles": titles,
                "budgets": budgets,
                "prototypes": prototypes,
                "founder_requirements": founder_requirements,
                "previous_major_round_history": previous_history,
            },
        )
        
        investment_result = self._run_investment_rounds(
            strategies,
            titles,
            budgets,
                founder_requirements,
                previous_history,
            prototypes,
            major_round=round_num,
            )
        
        all_scores_new = investment_result["all_scores"]
        investor_feedback = investment_result["investor_feedback"]
        investment_history = investment_result["investment_history"]
        accumulated_investments = investment_result["accumulated_investments"]
        
        # Update founder accumulated investments
        for founder in self.founders:
            founder.accumulated_investment = accumulated_investments.get(founder.name, 0)
        
        # Aggregate scores for each founder
        founder_scores = {}
        for founder in self.founders:
            total_score = 0.0
            for group in self.investor_groups:
                if founder.name in self.interaction_graph.get(group.name, []):
                    total_score += all_scores_new.get(group.name, {}).get(founder.name, 0.0)
            founder_scores[founder.name] = total_score
        
        round_data = {
            'round': round_num,
            'strategies': strategies,
            'proposals': proposals,
            'titles': titles,
            'budgets': budgets,
            'budget_bounds': {
                name: {
                    "budget": int(budgets.get(name, 0) or 0),
                    "lower_bound": int((budgets.get(name, 0) or 0) * (1 - self.budget_tolerance_percent)),
                    "upper_bound": int((budgets.get(name, 0) or 0) * (1 + self.budget_tolerance_percent)),
                }
                for name in budgets.keys()
            },
            'prototypes': prototypes,
            'all_scores': all_scores_new,
            'founder_scores': founder_scores,
            'investor_feedback': investor_feedback,
            'investment_history': investment_history
        }

        # Checkpoint B: investor evaluation done; before next major round
        self._maybe_save_checkpoint(
            kind="investor_evaluated",
            major_round=round_num,
            payload={
                "round_data": round_data,
            },
        )
        
        if self.verbose:
            self._print_round_summary(round_data)
        
        return round_data
    
    def _calculate_final_scores(self) -> Dict[str, float]:
        """Calculate final scores - use accumulated investments from all investor groups."""
        if not self.history:
            return {founder.name: 0 for founder in self.founders}
        
        # Calculate final scores from accumulated investments across all investor groups
        # Get accumulated investments from each group's last evaluation
        final_scores = {founder.name: 0.0 for founder in self.founders}
        
        for group in self.investor_groups:
            if hasattr(group, 'history') and group.history:
                last_summary = group.history[-1]
                accumulated_investments = last_summary.get('accumulated_investments', {})
                # Only count investments for founders visible to this group
                for founder in self.founders:
                    if founder.name in self.interaction_graph.get(group.name, []):
                        final_scores[founder.name] += float(accumulated_investments.get(founder.name, 0))
        
        return final_scores
    
    def _print_round_summary(self, round_data: Dict[str, Any]):
        """Print summary of a round."""
        print(f"\nRound {round_data['round']} Summary:")
        print("-" * 60)
        for founder_name, score in sorted(round_data['founder_scores'].items(), 
                                          key=lambda x: x[1], reverse=True):
            print(f"{founder_name}: {score:.1f} points")
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print final competition summary."""
        print(f"\n{'='*60}")
        print("COMPETITION FINAL RESULTS")
        print(f"{'='*60}")
        print(f"\nWinner: {results['winner']}")
        print(f"Winner Score: {results['winner_score']:.1f}")
        print(f"\nFinal Rankings:")
        sorted_scores = sorted(results['final_scores'].items(), 
                              key=lambda x: x[1], reverse=True)
        for rank, (founder_name, score) in enumerate(sorted_scores, 1):
            print(f"{rank}. {founder_name}: {score:.1f} points")
    
    def reset(self):
        """Reset all agents."""
        for founder in self.founders:
            founder.reset()
        for group in self.investor_groups:
            group.reset()
        self.history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get complete history of all rounds."""
        return self.history

