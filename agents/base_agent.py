"""
Base Agent class defining the interface for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the agent.
        
        Args:
            name: Unique name identifier for the agent
            config: Configuration dictionary containing agent-specific settings
        """
        self.name = name
        self.config = config
        self.history = []
    
    @abstractmethod
    def process_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a request and return a response.
        
        Args:
            request: The input request/requirement
            context: Additional context information
            
        Returns:
            Dictionary containing the agent's response
        """
        pass
    
    def add_to_history(self, entry: Dict[str, Any]):
        """Add an entry to the agent's history."""
        self.history.append(entry)
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve the agent's history."""
        return self.history
    
    def reset(self):
        """Reset the agent's state."""
        self.history = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

