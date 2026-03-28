"""
Multi-Agent System for Founder-Investor Collaboration

This module provides a framework for multi-agent systems where
Founders propose ideas and Investors evaluate and allocate resources.
Investor groups coordinate step-1 evaluation and step-2 debate-based allocation.
"""

from .base_agent import BaseAgent
from .founder import Founder
from .investor import Investor, InvestorGroup

__all__ = ["BaseAgent", "Founder", "Investor", "InvestorGroup"]
