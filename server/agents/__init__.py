"""
Knowledge Forge Agents.

This module contains the mode agents (Research, Understand, Build) that
implement the pedagogical approaches for each learning mode.
"""

from .base import BaseForgeAgent, PhaseTransition, BasePhaseContext
from .research import ResearchAgent, ResearchPhase, ResearchPhaseContext

__all__ = [
    # Base
    "BaseForgeAgent",
    "PhaseTransition",
    "BasePhaseContext",
    # Research
    "ResearchAgent",
    "ResearchPhase",
    "ResearchPhaseContext",
]
