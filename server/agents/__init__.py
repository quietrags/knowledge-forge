"""
Knowledge Forge Agents.

This module contains the mode agents (Research, Understand, Build) that
implement the pedagogical approaches for each learning mode.
"""

from .base import BaseForgeAgent, PhaseTransition, BasePhaseContext
from .research import ResearchAgent, ResearchPhase, ResearchPhaseContext
from .understand import UnderstandAgent, UnderstandPhase, UnderstandPhaseContext
from .build import BuildAgent, BuildPhase, BuildPhaseContext
from .factory import (
    create_agent,
    get_or_create_agent,
    save_agent_state,
    get_agent_state_for_restore,
)

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
    # Factory
    "create_agent",
    "get_or_create_agent",
    "save_agent_state",
    "get_agent_state_for_restore",
]
