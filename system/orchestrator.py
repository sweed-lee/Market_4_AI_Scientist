"""
System orchestrator for managing multi-agent competition.

Coordinates Founders and Investors across multiple rounds.
"""

from typing import List, Dict, Any, Callable
from agents.founder import Founder
from agents.investor import Investor
import json


class SystemOrchestrator:
    """Orchestrates the multi-agent system for multi-round competition."""
    
    def __init__(self, founders: List[Founder], investors: List[Investor],
                 config: Dict[str, Any], llm_callback: Callable = None):
        """
        Initialize the orchestrator.
        
        Args:
            founders: List of Founder agents
            investors: List of Investor agents
            config: System configuration
            llm_callback: Function to call LLM API (optional)
        """
        self.founders = founders
        self.investors = investors
        self.config = config
        self.llm_callback = llm_callback
        self.num_rounds = config.get('num_rounds', 3)
        self.max_points = config.get('max_investor_points', 100)
        self.history = []
        self.requirement = None  # Store requirement for use in iterations
    
    def run(self, requirement: str) -> Dict[str, Any]:
        """
        Run the full multi-round competition.
        
        Args:
            requirement: The input requirement to address
            
        Returns:
            Complete results including winner and all round data
        """
        self.requirement = requirement  # Store requirement for use in iterations
        
        print(f"Starting multi-agent system for requirement: {requirement}")
        print(f"Founders: {[f.name for f in self.founders]}")
        print(f"Investors: {[i.name for i in self.investors]}")
        print(f"Number of rounds: {self.num_rounds}\n")
        
        # Round 1: Initial strategies
        round_results = self._initial_round(requirement)
        self.history.append(round_results)
        
        # Subsequent rounds: Iteration
        for round_num in range(2, self.num_rounds + 1):
            print(f"\n{'='*60}")
            print(f"Round {round_num}")
            print(f"{'='*60}")
            
            round_results = self._iteration_round(round_num)
            self.history.append(round_results)
        
        # Calculate final winner
        final_scores = self._calculate_final_scores()
        winner = max(final_scores.items(), key=lambda x: x[1])
        
        results = {
            'winner': winner[0],
            'winner_score': winner[1],
            'final_scores': final_scores,
            'all_rounds': self.history,
            'requirement': requirement
        }
        
        self._print_summary(results)
        
        return results
    
    def _initial_round(self, requirement: str) -> Dict[str, Any]:
        """Execute the initial round where founders propose strategies."""
        print(f"\n{'='*60}")
        print("Round 1: Initial Strategy Proposal")
        print(f"{'='*60}")
        
        strategies = {}
        proposals = {}
        
        # Each founder generates initial strategy
        for founder in self.founders:
            print(f"\n{founder.name} is generating strategy...")
            strategy = founder.generate_strategy(requirement, self.llm_callback)
            strategies[founder.name] = strategy
            # Proposal-only (without THINKING) pulled from founder state
            proposals[founder.name] = founder.get_current_strategy()
            print(f"{founder.name}'s strategy: {strategy[:200]}...")
        
        # Each investor evaluates all strategies
        all_scores = {}
        investor_feedback = {}
        for investor in self.investors:
            print(f"\n{investor.name} is evaluating strategies...")
            scores = investor.evaluate_strategies(strategies, self.max_points, self.llm_callback, requirement)
            all_scores[investor.name] = scores
            # collect feedback (read from BaseAgent.history)
            fb = investor.history[-1].get('feedback', {})
            investor_feedback[investor.name] = fb
            print(f"{investor.name} allocated: {scores}")
        
        # Aggregate scores for each founder
        founder_scores = {}
        for founder in self.founders:
            total_score = sum(all_scores[inv.name].get(founder.name, 0) 
                            for inv in self.investors)
            founder_scores[founder.name] = total_score
        
        round_data = {
            'round': 1,
            'strategies': strategies,
            'proposals': proposals,
            'all_scores': all_scores,
            'founder_scores': founder_scores,
            'investor_feedback': investor_feedback
        }
        
        self._print_round_summary(round_data)
        
        return round_data
    
    def _iteration_round(self, round_num: int) -> Dict[str, Any]:
        """Execute an iteration round where founders refine strategies."""
        print(f"\nIteration Round {round_num}")
        
        # Get previous round's scores
        prev_round = self.history[-1]
        all_scores = prev_round['all_scores']
        
        # Founders iterate on their strategies
        strategies = {}
        proposals = {}
        for founder in self.founders:
            print(f"\n{founder.name} is refining strategy...")
            # Build previous round context views for founder
            fb_prev = prev_round.get('investor_feedback', {})
            your_name = founder.name
            # Your previous round block
            detailed_lines = []
            for inv in self.investors:
                inv_name = inv.name
                per_inv = fb_prev.get(inv_name, {}).get(your_name, {})
                if per_inv:
                    detailed_lines.append(f"- {inv_name}: {per_inv.get('points', 0):.1f} pts | {per_inv.get('detail', per_inv.get('summary', ''))}")
            my_total = sum(all_scores[inv.name].get(your_name, 0) for inv in self.investors)
            my_prev_round = f"Proposal:\n{prev_round.get('proposals', {}).get(your_name, '')}\nTotal: {my_total:.1f}\nEvaluations:\n" + ("\n".join(detailed_lines) if detailed_lines else "(no evaluations)")

            # Others previous round block
            others_lines = []
            for other in self.founders:
                if other.name == your_name:
                    continue
                other_total = sum(all_scores[inv.name].get(other.name, 0) for inv in self.investors)
                others_lines.append(f"\n[{other.name}]\nProposal:\n{prev_round.get('proposals', {}).get(other.name, '')}\nTotal: {other_total:.1f}\nEvaluations:")
                for inv in self.investors:
                    inv_name = inv.name
                    per_inv = fb_prev.get(inv_name, {}).get(other.name, {})
                    if per_inv:
                        others_lines.append(f"  - {inv_name}: {per_inv.get('points', 0):.1f} pts | {per_inv.get('summary', '')}")
            others_prev_round = "\n".join(others_lines)
            strategy = founder.iterate_strategy(all_scores, self.llm_callback, feedback={
                'my_prev_round': my_prev_round,
                'others_prev_round': others_prev_round,
                'requirement': self.requirement
            }, requirement=self.requirement)
            strategies[founder.name] = strategy
            proposals[founder.name] = founder.get_current_strategy()
            print(f"{founder.name}'s refined strategy: {strategy[:200]}...")
        
        # Investors update their evaluation strategy (optional)
        # and evaluate again
        all_scores_new = {}
        investor_feedback = {}
        for investor in self.investors:
            print(f"\n{investor.name} is evaluating strategies...")
            # Update evaluation strategy based on results (optional)
            # investor.update_evaluation_strategy(prev_round, self.llm_callback)
            
            scores = investor.evaluate_strategies(strategies, self.max_points, self.llm_callback, self.requirement)
            all_scores_new[investor.name] = scores
            fb = investor.history[-1].get('feedback', {})
            investor_feedback[investor.name] = fb
            print(f"{investor.name} allocated: {scores}")
        
        # Aggregate scores
        founder_scores = {}
        for founder in self.founders:
            total_score = sum(all_scores_new[inv.name].get(founder.name, 0) 
                            for inv in self.investors)
            founder_scores[founder.name] = total_score
        
        round_data = {
            'round': round_num,
            'strategies': strategies,
            'proposals': proposals,
            'all_scores': all_scores_new,
            'founder_scores': founder_scores,
            'investor_feedback': investor_feedback
        }
        
        self._print_round_summary(round_data)
        
        return round_data
    
    def _calculate_final_scores(self) -> Dict[str, float]:
        """Calculate final scores - use only the last round (not cumulative)."""
        if not self.history:
            return {founder.name: 0 for founder in self.founders}
        
        # Use only the last round's scores
        last_round = self.history[-1]
        return last_round['founder_scores']
    
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
        for investor in self.investors:
            investor.reset()
        self.history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get complete history of all rounds."""
        return self.history

