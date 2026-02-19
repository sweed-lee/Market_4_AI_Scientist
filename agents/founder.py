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
        # Each founder now has its own instruction/task bound from config
        self.instruction = config.get('instruction', '')
        self.current_strategy = None
        self.current_title = None
        self.current_budget = None
        self.current_prototype = None  # Current prototype code framework
        self.current_round = None  # Current round number for dialog logging
        # Key member variables
        self.total_budget = 0  # Total budget (from proposal)
        self.accumulated_investment = 0  # Total investment received (accepted amount)
        self.round_scores = []  # Track scores per round
    
    def generate_strategy(self, requirement: str = None, llm_callback=None,
                         num_investor_groups: int = 0, capital_per_group: float = 0.0,
                         num_competitors: int = 0) -> str:
        """
        Generate an initial strategy based on the requirement.
        
        Args:
            requirement: The input requirement. If None, use this founder's
                         configured instruction.
            llm_callback: Function to call LLM with prompt
            num_investor_groups: Number of investor groups in the market
            capital_per_group: Average capital per investor group
            num_competitors: Number of competitors in the market
            
        Returns:
            The generated strategy
        """
        # Use founder-specific instruction if no explicit requirement is given
        req = requirement if requirement is not None else self.instruction
        from config.prompts import _BUDGET_REFERENCE_CASES
        # prompt = FOUNDER_INITIAL_PROMPT.format(
        #     requirement=req,
        #     num_investor_groups=num_investor_groups,
        #     capital_per_group=capital_per_group,
        #     num_competitors=num_competitors,
        #     budget_reference_cases=_BUDGET_REFERENCE_CASES
        # )
        prompt = FOUNDER_INITIAL_PROMPT.format(
            requirement=req,
            num_investor_groups="unknown",
            capital_per_group="unknown",
            num_competitors="unknown",
            budget_reference_cases=_BUDGET_REFERENCE_CASES
        )
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_response(req)
        
        # Log the dialog
        add_dialog(prompt, response, self.name, 'Founder', 
                  round_num=self.current_round, dialog_type='initial')
        
        # Extract title, budget, proposal, and prototype parts from response
        title = self._extract_title(response)
        budget = self._extract_budget(response)
        proposal = self._extract_proposal(response)
        prototype = self._extract_prototype(response)
        
        self.current_strategy = proposal
        self.current_title = title
        self.current_budget = budget
        self.current_prototype = prototype
        self.total_budget = budget  # Update total budget
        self.add_to_history({
            'type': 'initial_strategy',
            'requirement': req,
            'strategy': response,
            'title': title,
            'budget': budget,
            'proposal': proposal,
            'prototype': prototype
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
        
        # Use founder-specific instruction by default; allow override if provided
        if requirement is not None:
            req = requirement
        else:
            req = self.instruction
        
        from config.prompts import _BUDGET_REFERENCE_CASES
        # prompt = FOUNDER_ITERATION_PROMPT.format(
        #     requirement=req,
        #     my_prev_round=my_prev_round,
        #     others_prev_round=others_prev_round,
        #     num_investor_groups=feedback.get('num_investor_groups', 0) if feedback else 0,
        #     capital_per_group=feedback.get('capital_per_group', 0.0) if feedback else 0.0,
        #     num_competitors=feedback.get('num_competitors', 0) if feedback else 0,
        #     budget_reference_cases=_BUDGET_REFERENCE_CASES
        # )
        prompt = FOUNDER_ITERATION_PROMPT.format(
            requirement=req,
            my_prev_round=my_prev_round,
            others_prev_round=others_prev_round,
            num_investor_groups="unknown",
            capital_per_group="unknown",
            num_competitors="unknown",
            budget_reference_cases=_BUDGET_REFERENCE_CASES
        )
        
        # If no LLM callback provided, use a placeholder response
        if llm_callback:
            response = llm_callback(prompt, model=self.model)
        else:
            response = self._placeholder_iteration()
        
        # Log the dialog
        add_dialog(prompt, response, self.name, 'Founder', 
                  round_num=self.current_round, dialog_type='iteration')
        
        # Extract title, budget, proposal, and prototype parts from response
        title = self._extract_title(response)
        budget = self._extract_budget(response)
        proposal = self._extract_proposal(response)
        prototype = self._extract_prototype(response)
        
        self.current_strategy = proposal
        self.current_title = title
        self.current_budget = budget
        self.current_prototype = prototype
        self.total_budget = budget  # Update total budget
        self.add_to_history({
            'type': 'refined_strategy',
            'your_score': your_total,
            'all_scores': all_scores,
            'refined_strategy': response,
            'title': title,
            'budget': budget,
            'proposal': proposal,
            'prototype': prototype
        })
        
        return response
    
    def _extract_title(self, response: str) -> str:
        """Extract the title part from formatted response."""
        import re
        # Try to extract content between [TITLE] and [/TITLE]
        match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', response, re.DOTALL)
        # 临时修正，针对个别模型没有[/TITLE]
        if not match:
            match = re.search(r'\[TITLE\](.*)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If not found, return empty string
        return ""
    
    def _extract_budget(self, response: str) -> int:
        """Extract the budget (integer) from formatted response."""
        import re
        # Try to extract content between [BUDGET] and [/BUDGET]
        match = re.search(r'\[BUDGET\](.*?)\[/BUDGET\]', response, re.DOTALL)
        # 临时修正，针对个别模型没有[/BUDGET]
        if not match:
            match = re.search(r'\[BUDGET\](.*)', response, re.DOTALL)
        if match:
            budget_text = match.group(1).strip()
            # Extract integer from the text
            numbers = re.findall(r'\d+', budget_text)
            if numbers:
                return int(numbers[0])  # Take the first number found
        # If not found, return 0 as default
        return 0
    
    def _extract_proposal(self, response: str) -> str:
        """Extract the proposal/evaluation part from formatted response."""
        import re
        # Try to extract content between [PROPOSAL] and [/PROPOSAL]
        match = re.search(r'\[PROPOSAL\](.*?)\[/PROPOSAL\]', response, re.DOTALL)
        # 临时修正，针对个别模型没有[/PROPOSAL]
        if not match:
            match = re.search(r'\[PROPOSAL\](.*?)(?=\[PROTOTYPE\]|$)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If not found, return the full response (for backward compatibility)
        return response
    
    def _extract_prototype(self, response: str) -> str:
        """Extract the prototype part from formatted response."""
        import re
        match = re.search(r'\[PROTOTYPE\](.*?)\[/PROTOTYPE\]', response, re.DOTALL)
        if not match:
            match = re.search(r'\[PROTOTYPE\](.*)', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # If not found, return empty string
        return ""
    
    def _placeholder_response(self, requirement: str) -> str:
        """Placeholder response for testing without LLM."""
        return f"""[THINKING]
Reflecting on the requirement: {requirement}. I need to propose a compelling strategy.
[/THINKING]

[TITLE]
Founder {self.name}'s Strategy for {requirement}
[/TITLE]

[BUDGET]
50000
[/BUDGET]

[PROPOSAL]
Founder {self.name}'s initial strategy for '{requirement}'. 
Specializing in: {self.specialization}. 
Proposed approach: [Detailed strategy here - implement with LLM]
[/PROPOSAL]

[PROTOTYPE]
# Module 1: Core Functionality
# Functionality: Implement core features
# Token requirement: 10000 tokens
def core_module():
    pass
[/PROTOTYPE]"""
    
    def _placeholder_iteration(self) -> str:
        """Placeholder iteration response for testing without LLM."""
        return f"""[THINKING]
Analyzing feedback and refining the strategy.
[/THINKING]

[TITLE]
Founder {self.name}'s Refined Strategy
[/TITLE]

[BUDGET]
50000
[/BUDGET]

[PROPOSAL]
Founder {self.name}'s refined strategy based on feedback. 
[Refined approach here - implement with LLM]
[/PROPOSAL]

[PROTOTYPE]
# Module 1: Core Functionality
# Functionality: Implement core features
# Token requirement: 10000 tokens
def core_module():
    pass
[/PROTOTYPE]"""
    
    def get_current_strategy(self) -> str:
        """Get the current strategy."""
        return self.current_strategy
    
    def get_current_title(self) -> str:
        """Get the current title."""
        return self.current_title if self.current_title else ""
    
    def get_current_budget(self) -> int:
        """Get the current budget."""
        return self.current_budget if self.current_budget is not None else 0
    
    def get_current_prototype(self) -> str:
        """Get the current prototype."""
        return self.current_prototype if self.current_prototype else ""
    
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

