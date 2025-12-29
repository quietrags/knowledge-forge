"""
Knowledge Forge Agents.

This module contains the mode agents (Research, Understand, Build) that
implement the pedagogical approaches for each learning mode.
"""

from .base import BaseForgeAgent, PhaseTransition, BasePhaseContext
from .research import ResearchAgent, ResearchPhase, ResearchPhaseContext
from .understand import UnderstandAgent, UnderstandPhase, UnderstandPhaseContext
from .build import BuildAgent, BuildPhase, BuildPhaseContext

__all__ = [
    # Base
    "BaseForgeAgent",
    "PhaseTransition",
    "BasePhaseContext",
    # Research
    "ResearchAgent",
    "ResearchPhase",
    "ResearchPhaseContext",
    # Understand
    "UnderstandAgent",
    "UnderstandPhase",
    "UnderstandPhaseContext",
    # Build
    "BuildAgent",
    "BuildPhase",
    "BuildPhaseContext",
]
