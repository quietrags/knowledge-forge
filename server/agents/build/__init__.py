"""
Build Agent for Knowledge Forge.

Implements the Constructivist tutoring system using the Claude Agent SDK.
"""

from .agent import BuildAgent
from .phases import BuildPhase, BuildPhaseContext, BUILD_TRANSITIONS

__all__ = [
    "BuildAgent",
    "BuildPhase",
    "BuildPhaseContext",
    "BUILD_TRANSITIONS",
]
