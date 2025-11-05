"""
Multi-Agent System for Founder-Investor Collaboration

This module provides a framework for multi-agent systems where
Founders propose ideas and Investors evaluate and allocate resources.
"""

from .base_agent import BaseAgent
from .founder import Founder
from .investor import Investor

__all__ = ['BaseAgent', 'Founder', 'Investor']

