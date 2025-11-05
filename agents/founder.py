"""
Founder agent implementation.

Founders propose and iterate on strategies/ideas based on feedback.
"""

from typing import Dict, Any
from .base_agent import BaseAgent
from config.prompts import FOUNDER_INITIAL_PROMPT, FOUNDER_ITERATION_PROMPT
from utils.dialog_logger import add_dialog


class Founder(BaseAgent):
    """Founder agent that proposes strategies and iterates based on feedback."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize a Founder agent.
        
        Args:
            name: Name of the founder
            config: Configuration containing 'specialization' and other settings
        """
        super().__init__(name, config)
        self.specialization = config.get('specialization', 'General Strategy')
        self.model = config.get('model')
        self.current_strategy = None
        self.round_scores = []
    
    def generate_strategy(self, requirement: str, llm_callback=None) -> str:
        """
        Generate an initial strategy based on the requirement.
        
        Args:
            requirement: The input requirement
            llm_callback: Function to call LLM with prompt
            
        Returns:
            The generated strategy
        """
        prompt = FOUNDER_INITIAL_PROMPT.format(requirement=requirement)
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_response(requirement)
        
        # Log the dialog
        add_dialog(prompt, response, self.name, 'Founder')
        
        # Extract proposal part from response
        proposal = self._extract_proposal(response)
        
        self.current_strategy = proposal
        self.add_to_history({
            'type': 'initial_strategy',
            'requirement': requirement,
            'strategy': response
        })
        
        return response
    
    def iterate_strategy(self, all_scores: Dict[str, Dict[str, float]], 
                        llm_callback=None, feedback: Dict[str, Any] = None,
                        requirement: str = None) -> str:
        """
        Iterate and refine strategy based on scores and feedback.
        
        Args:
            all_scores: Dictionary mapping founder names to their scores by investor
            llm_callback: Function to call LLM with prompt
            feedback: Dictionary containing feedback context
            requirement: The original requirement/task definition
            
        Returns:
            The refined strategy
        """
        # Get your own scores
        your_scores = all_scores.get(self.name, {})
        your_total = sum(your_scores.values())
        self.round_scores.append(your_total)
        
        # Build scores breakdown
        score_breakdown = "\n".join(
            [f"  - {inv}: {score:.1f} points" 
             for inv, score in your_scores.items()]
        )
        
        # Build all scores summary
        all_scores_str = "\n".join(
            [f"  {name}: {sum(scores.values()):.1f} total" 
             for name, scores in all_scores.items()]
        )
        
        my_prev_round = ''
        others_prev_round = ''
        if feedback:
            my_prev_round = feedback.get('my_prev_round', '')
            others_prev_round = feedback.get('others_prev_round', '')
        
        # Use requirement from feedback or fallback to empty string
        req = requirement if requirement else feedback.get('requirement', '') if feedback else ''
        
        prompt = FOUNDER_ITERATION_PROMPT.format(
            requirement=req,
            my_prev_round=my_prev_round,
            others_prev_round=others_prev_round
        )
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_iteration()
        
        # Log the dialog
        add_dialog(prompt, response, self.name, 'Founder')
        
        # Extract proposal part from response
        proposal = self._extract_proposal(response)
        
        self.current_strategy = proposal
        self.add_to_history({
            'type': 'refined_strategy',
            'your_score': your_total,
            'all_scores': all_scores,
            'refined_strategy': response
        })
        
        return response
    
    def _extract_proposal(self, response: str) -> str:
        """Extract the proposal/evaluation part from formatted response."""
        import re
        # Try to extract content between [PROPOSAL] and [/PROPOSAL]
        match = re.search(r'\[PROPOSAL\](.*?)\[/PROPOSAL\]', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If not found, return the full response (for backward compatibility)
        return response
    
    def _placeholder_response(self, requirement: str) -> str:
        """Placeholder response for testing without LLM."""
        return f"""[THINKING]
Reflecting on the requirement: {requirement}. I need to propose a compelling strategy.
[/THINKING]

[PROPOSAL]
Founder {self.name}'s initial strategy for '{requirement}'. 
Specializing in: {self.specialization}. 
Proposed approach: [Detailed strategy here - implement with LLM]
[/PROPOSAL]"""
    
    def _placeholder_iteration(self) -> str:
        """Placeholder iteration response for testing without LLM."""
        return f"""[THINKING]
Analyzing feedback and refining the strategy.
[/THINKING]

[PROPOSAL]
Founder {self.name}'s refined strategy based on feedback. 
[Refined approach here - implement with LLM]
[/PROPOSAL]"""
    
    def get_current_strategy(self) -> str:
        """Get the current strategy."""
        return self.current_strategy
    
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request - delegates to generate_strategy."""
        strategy = self.generate_strategy(request)
        return {
            'type': 'strategy',
            'content': strategy
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Extend serialization with founder-specific data."""
        base_dict = super().to_dict()
        base_dict.update({
            'specialization': self.specialization,
            'current_strategy': self.current_strategy,
            'total_score': sum(self.round_scores) if self.round_scores else 0,
            'scores_per_round': self.round_scores
        })
        return base_dict

