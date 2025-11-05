"""
Investor agent implementation.

Investors evaluate strategies and allocate points based on their criteria.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from config.prompts import INVESTOR_EVALUATION_PROMPT
from utils.dialog_logger import add_dialog


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
    
    def evaluate_strategies(self, strategies: Dict[str, str], 
                           max_points: int, llm_callback=None,
                           requirement: str = None) -> Dict[str, float]:
        """
        Evaluate multiple strategies and allocate points.
        
        Args:
            strategies: Dictionary mapping founder names to their strategies
            max_points: Total points available for allocation
            llm_callback: Function to call LLM with prompt
            requirement: The original requirement/task definition
            
        Returns:
            Dictionary mapping founder names to their allocated points
        """
        # Build strategies list string
        strategies_list = "\n\n".join(
            [f"{name}:\n{strategy}" for name, strategy in strategies.items()]
        )
        
        prompt = INVESTOR_EVALUATION_PROMPT.format(
            requirement=requirement if requirement else '',
            max_points=max_points,
            num_strategies=len(strategies),
            criteria=self.criteria,
            philosophy=self.philosophy,
            strategies_list=strategies_list
        )
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_evaluation(strategies, max_points)
        
        # Log the dialog
        add_dialog(prompt, response, self.name, 'Investor')
        
        # Extract sections
        summaries_text = self._extract_section(response, 'SUMMARIES')
        details_text = self._extract_section(response, 'DETAILS')
        allocations_text = self._extract_section(response, 'ALLOCATIONS')
        
        # Parse pieces
        parsed_scores = self._parse_scores(allocations_text, list(strategies.keys()))
        parsed_summaries = self._parse_mapping(summaries_text, list(strategies.keys()))
        parsed_details = self._parse_mapping(details_text, list(strategies.keys()))
        
        self.add_to_history({
            'type': 'evaluation',
            'strategies': strategies,
            'scores': parsed_scores,
            'feedback': {
                name: {
                    'summary': parsed_summaries.get(name, ''),
                    'detail': parsed_details.get(name, ''),
                    'points': parsed_scores.get(name, 0.0),
                } for name in strategies.keys()
            }
        })
        
        return parsed_scores
    
    def update_evaluation_strategy(self, round_results: Dict[str, Any], 
                                  llm_callback=None) -> Dict[str, Any]:
        """
        Update evaluation strategy based on round results.
        
        Args:
            round_results: Results from the completed round
            llm_callback: Function to call LLM with prompt
            
        Returns:
            Updated criteria and philosophy
        """
        prompt = INVESTOR_STRATEGY_UPDATE_PROMPT.format(
            current_criteria=self.criteria,
            current_philosophy=self.philosophy,
            round_results=str(round_results)
        )
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            updated = llm_callback(prompt, model=self.model)
        else:
            updated = self._placeholder_strategy_update()
        
        # Update criteria and philosophy
        # In real implementation, parse the LLM response
        self.criteria = updated.get('criteria', self.criteria)
        self.philosophy = updated.get('philosophy', self.philosophy)
        
        self.add_to_history({
            'type': 'strategy_update',
            'old_criteria': self.criteria,
            'old_philosophy': self.philosophy,
            'updated': updated
        })
        
        return {'criteria': self.criteria, 'philosophy': self.philosophy}
    
    def _extract_section(self, response: str, section: str) -> str:
        """Extract a tagged section (SUMMARIES, DETAILS, ALLOCATIONS)."""
        import re
        pattern = rf'\[{section}\](.*?)\[/{section}\]'
        match = re.search(pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response
    
    def _parse_scores(self, scores_text: str, founder_names: List[str]) -> Dict[str, float]:
        """
        Parse scores from LLM text response.
        
        Args:
            scores_text: LLM response text with scores
            founder_names: List of founder names
            
        Returns:
            Dictionary mapping founder names to scores
        """
        import re
        
        # Placeholder parsing - in real implementation, use regex or structured output
        scores = {}
        for name in founder_names:
            # Simple extraction - find the name and extract the number
            pattern = rf"{name}:\s*(\d+(?:\.\d+)?)"
            match = re.search(pattern, scores_text)
            scores[name] = float(match.group(1))
        
        return scores

    def _parse_mapping(self, text: str, founder_names: List[str]) -> Dict[str, str]:
        """Parse simple 'Name: value' mappings."""
        import re
        mapping: Dict[str, str] = {}
        for name in founder_names:
            pattern = rf"{name}:\s*(.+)"
            match = re.search(pattern, text)
            if match:
                mapping[name] = match.group(1).strip()
        return mapping
    
    def _placeholder_evaluation(self, strategies: Dict[str, str], 
                               max_points: int) -> str:
        """Placeholder evaluation for testing without LLM."""
        import random
        print("warning: using placeholder evaluation")
        # Distribute points randomly
        points = [random.random() for _ in strategies]
        points = [p * max_points for p in points]
        
        result = []
        for name, score in zip(strategies.keys(), points):
            result.append(f"{name}: {score:.1f} points")
        
        evaluation_text = "\n".join(result)
        
        return f"""[THINKING]
Analyzing strategies and allocating points based on my criteria.
[/THINKING]

[EVALUATION]
{evaluation_text}
[/EVALUATION]"""
    
    def _placeholder_strategy_update(self) -> Dict[str, str]:
        """Placeholder strategy update for testing without LLM."""
        return {
            'criteria': self.criteria + ' (updated)',
            'philosophy': self.philosophy + ' (refined)'
        }
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request - delegates to evaluate_strategies."""
        if context and 'strategies' in context:
            scores = self.evaluate_strategies(context['strategies'], 100)
            return {'type': 'evaluation', 'scores': scores}
        return {'type': 'error', 'message': 'No strategies provided'}
    
    def to_dict(self) -> Dict[str, Any]:
        """Extend serialization with investor-specific data."""
        base_dict = super().to_dict()
        base_dict.update({
            'criteria': self.criteria,
            'philosophy': self.philosophy,
        })
        return base_dict

