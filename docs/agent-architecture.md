# Knowledge Forge — Agent Architecture Pattern

**Version:** 1.0
**Date:** 2025-12-29

This document defines the architectural pattern for all mode agents (Research, Understand, Build). All agents MUST follow this pattern for consistency, debuggability, and maintainability.

---

## Core Principle: Phase Graphs, Not Linear State Machines

Agents operate as **directed graphs** with explicit transitions, not linear state machines. This enables:

1. **Backward transitions** when discovery requires revisiting earlier phases
2. **Phase context persistence** across multiple visits to the same phase
3. **Re-entry behavior** that differs from initial entry
4. **Transparent state** for debugging and resume

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MODE AGENT                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      PHASE GRAPH                                 │   │
│  │                                                                  │   │
│  │   ┌─────────┐      ┌─────────┐      ┌─────────┐                │   │
│  │   │ Phase A │─────►│ Phase B │─────►│ Phase C │───► COMPLETE   │   │
│  │   └─────────┘      └─────────┘      └─────────┘                │   │
│  │        ▲               │                │                       │   │
│  │        │               │                │                       │   │
│  │        └───────────────┴────────────────┘                       │   │
│  │              (backward transitions)                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      PHASE CONTEXT                               │   │
│  │                                                                  │   │
│  │   • Visit counts per phase                                      │   │
│  │   • Accumulated work (questions, answers, concepts)             │   │
│  │   • Transition history                                          │   │
│  │   • Backward trigger (why we returned)                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                │                                        │
│                                ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      PHASE EXECUTOR                              │   │
│  │                                                                  │   │
│  │   1. Get phase-specific prompt (initial vs re-entry)           │   │
│  │   2. Get phase-specific tools                                   │   │
│  │   3. Run agentic loop until exit condition                     │   │
│  │   4. Emit SSE events during execution                          │   │
│  │   5. Check user checkpoint if required                         │   │
│  │   6. Evaluate transitions (forward AND backward)               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Definitions

### What is a Phase?

A phase is a distinct stage of agent work with:

| Property | Description |
|----------|-------------|
| **Name** | Unique identifier (enum value) |
| **Purpose** | What this phase accomplishes |
| **Entry condition** | What must be true to enter |
| **Exit condition** | What must be true to leave (forward) |
| **Backward triggers** | Conditions that send us back to earlier phases |
| **Checkpoint** | Whether user approval is required before proceeding |
| **Tools** | Which tools are available in this phase |
| **SSE events** | What events are emitted during this phase |

### Phase vs Sub-phase

- **Phase**: Major stage visible in agent state (DECOMPOSE, ANSWER, etc.)
- **Sub-phase**: Internal state within a phase (not exposed, implementation detail)

Phases are part of the contract. Sub-phases are implementation details.

---

## Transition Rules

### Transition Definition

```python
@dataclass
class PhaseTransition:
    from_phase: Phase
    to_phase: Phase
    condition: str          # Human-readable condition name
    is_backward: bool       # True for backward transitions
    priority: int = 0       # Higher priority evaluated first
```

### Transition Evaluation Order

1. **Backward transitions** are checked first (higher priority)
2. Within same direction, higher `priority` checked first
3. First matching transition wins
4. If no transition matches, stay in current phase

### Backward Transition Triggers

Backward transitions occur when:

| Trigger Type | Example |
|--------------|---------|
| **Discovery** | New question category discovered during answering |
| **Gap revealed** | Teaching reveals learner needs earlier concept |
| **Synthesis failure** | Can't synthesize without more source material |
| **User request** | User explicitly asks to revisit earlier phase |
| **Validation failure** | Check reveals earlier assessment was wrong |

---

## Phase Context

### Purpose

Phase context tracks state that persists across visits to the same phase. This enables:

1. **Incremental work**: Don't redo what's already done
2. **Re-entry awareness**: Know we've been here before
3. **Debugging**: See full history of phase visits

### Required Fields

Every agent's phase context MUST include:

```python
@dataclass
class BasePhaseContext:
    # Visit tracking
    phase_visits: dict[Phase, int]  # How many times we've visited each phase

    # Transition history
    transition_history: list[TransitionRecord]

    # Current backward trigger (if any)
    backward_trigger: Optional[str]
    backward_trigger_detail: Optional[str]
```

### Agent-Specific Extensions

Each agent extends with phase-specific state:

```python
@dataclass
class ResearchPhaseContext(BasePhaseContext):
    # DECOMPOSE state
    categories: list[CategoryQuestion]
    questions: list[Question]

    # ANSWER state
    answered_questions: list[str]  # Question IDs
    sources: list[Source]

    # RISE_ABOVE state
    category_insights: dict[str, str]

    # EXPAND state
    adjacent_questions: list[AdjacentQuestion]
```

---

## Re-Entry Behavior

### First Visit vs Re-Entry

Agents MUST behave differently on re-entry:

| Aspect | First Visit | Re-Entry |
|--------|-------------|----------|
| **Prompt** | Full initialization prompt | Incremental prompt with context |
| **Scope** | Complete phase work | Only address the backward trigger |
| **SSE** | Normal events | Include "returning to phase" event |
| **User message** | Standard intro | Explain why we're back |

### Re-Entry Prompt Pattern

```python
def get_phase_prompt(self, phase: Phase) -> str:
    visit_count = self.phase_context.phase_visits.get(phase, 0)

    if visit_count == 0:
        return self._get_initial_prompt(phase)
    else:
        return self._get_reentry_prompt(
            phase=phase,
            visit_count=visit_count,
            trigger=self.phase_context.backward_trigger,
            existing_work=self._get_phase_work(phase)
        )
```

### Re-Entry Prompt Template

```
You are returning to the {phase} phase.

**Why we're back:** {backward_trigger}
**Detail:** {backward_trigger_detail}

**Work already completed:**
{existing_work_summary}

**Your task now:**
Address the reason for returning. Do NOT redo work already completed.
Only add/modify what's needed to address: {backward_trigger}
```

---

## Checkpoints (User Approval Gates)

### When Checkpoints Occur

Checkpoints are **blocking** points where the agent pauses for user approval:

| Phase Transition | Checkpoint? | Purpose |
|-----------------|-------------|---------|
| After DECOMPOSE | YES | User approves question tree |
| After ANSWER | Optional | User reviews sources/coverage |
| After RISE_ABOVE | NO | Internal synthesis |
| After EXPAND | NO | Frontier is informational |

### Checkpoint Implementation

```python
async def _execute_checkpoint(self, checkpoint: Checkpoint) -> bool:
    """Execute a blocking checkpoint. Returns True if approved."""

    # Emit checkpoint event
    yield CheckpointEvent(
        checkpoint_id=checkpoint.id,
        message=checkpoint.message,
        options=checkpoint.options,
        requires_approval=True
    )

    # Wait for user response (handled by orchestrator)
    response = await self._wait_for_user_response()

    if response.approved:
        return True
    elif response.action == "modify":
        # User wants changes - stay in current phase
        self._apply_user_modifications(response.modifications)
        return False  # Re-run phase
    else:
        # User rejected - may trigger backward transition
        self.phase_context.backward_trigger = response.rejection_reason
        return False
```

---

## SSE Event Emission

### Event Categories

| Category | Events | When |
|----------|--------|------|
| **Phase** | `phase.changed`, `phase.checkpoint` | Transitions, checkpoints |
| **Agent** | `agent.thinking`, `agent.speaking` | During execution |
| **Data** | `data.question.added`, `data.source.found`, etc. | State updates |
| **Error** | `error` | Failures |

### Backward Transition Events

When transitioning backward, emit:

```python
yield PhaseChangedEvent(
    from_phase=current.value,
    to_phase=target.value,
    is_backward=True,
    reason=self.phase_context.backward_trigger
)

yield AgentThinkingEvent(
    message=f"Returning to {target.value}: {self.phase_context.backward_trigger}"
)
```

---

## State Persistence

### Serialization Contract

All agents MUST implement `get_state()` and `restore_state()`:

```python
def get_state(self) -> dict:
    return {
        "agent_type": self.agent_type,
        "current_phase": self.current_phase.value,
        "phase_context": self._serialize_phase_context(),
        "transition_history": [
            {
                "from": t.from_phase.value,
                "to": t.to_phase.value,
                "reason": t.reason,
                "is_backward": t.is_backward,
                "timestamp": t.timestamp.isoformat()
            }
            for t in self.transition_history
        ],
        "mode_data": self._get_mode_data()
    }

async def restore_state(self, state: dict) -> None:
    self.current_phase = self.Phase(state["current_phase"])
    self._restore_phase_context(state["phase_context"])
    self._restore_transition_history(state["transition_history"])
    self._restore_mode_data(state["mode_data"])
```

---

## Base Agent Interface

All agents MUST extend this base class:

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator
from enum import Enum

class BaseForgeAgent(ABC):
    """Base class for all Knowledge Forge mode agents."""

    # Subclasses MUST define these
    @property
    @abstractmethod
    def Phase(self) -> type[Enum]:
        """The phase enum for this agent."""
        pass

    @property
    @abstractmethod
    def phase_transitions(self) -> list[PhaseTransition]:
        """All valid transitions (forward and backward)."""
        pass

    @property
    @abstractmethod
    def initial_phase(self) -> Enum:
        """The starting phase."""
        pass

    @property
    @abstractmethod
    def complete_phase(self) -> Enum:
        """The terminal phase."""
        pass

    # Subclasses MUST implement these
    @abstractmethod
    async def _execute_phase(self, phase: Enum) -> AsyncGenerator[SSEEvent, None]:
        """Execute a single phase, yielding SSE events."""
        pass

    @abstractmethod
    def _evaluate_transition_condition(self, transition: PhaseTransition) -> bool:
        """Check if a specific transition's condition is met."""
        pass

    @abstractmethod
    def _get_phase_prompt(self, phase: Enum, visit_count: int) -> str:
        """Get the prompt for a phase (initial or re-entry)."""
        pass

    @abstractmethod
    def _get_phase_tools(self, phase: Enum) -> list[Tool]:
        """Get available tools for a phase."""
        pass

    # Base implementations
    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """Initialize agent for a new journey."""
        self.journey_brief = journey_brief
        self.current_phase = self.initial_phase
        self.phase_context = self._create_phase_context()
        self.transition_history = []

    async def process_message(
        self,
        message: str,
        context: dict
    ) -> AsyncGenerator[SSEEvent, None]:
        """Main processing loop."""
        while self.current_phase != self.complete_phase:
            # Execute current phase
            async for event in self._execute_phase(self.current_phase):
                yield event

            # Evaluate transitions
            next_phase = self._evaluate_transitions()

            if next_phase != self.current_phase:
                # Record transition
                is_backward = self._is_backward_transition(
                    self.current_phase, next_phase
                )
                self._record_transition(
                    self.current_phase, next_phase, is_backward
                )

                # Emit transition event
                yield PhaseChangedEvent(
                    from_phase=self.current_phase.value,
                    to_phase=next_phase.value,
                    is_backward=is_backward,
                    reason=self.phase_context.backward_trigger
                )

                # Update phase
                self.current_phase = next_phase
                self.phase_context.phase_visits[next_phase] = \
                    self.phase_context.phase_visits.get(next_phase, 0) + 1

        # Emit completion
        yield AgentCompleteEvent(
            summary=self._generate_completion_summary()
        )

    def _evaluate_transitions(self) -> Enum:
        """Evaluate all transitions, return next phase."""
        # Sort by priority, backward first
        sorted_transitions = sorted(
            [t for t in self.phase_transitions if t.from_phase == self.current_phase],
            key=lambda t: (-int(t.is_backward), -t.priority)
        )

        for transition in sorted_transitions:
            if self._evaluate_transition_condition(transition):
                if transition.is_backward:
                    self.phase_context.backward_trigger = transition.condition
                return transition.to_phase

        return self.current_phase

    def _is_backward_transition(self, from_phase: Enum, to_phase: Enum) -> bool:
        """Check if a transition is backward."""
        for t in self.phase_transitions:
            if t.from_phase == from_phase and t.to_phase == to_phase:
                return t.is_backward
        return False
```

---

## Agent-Specific Phase Graphs

### Research Agent

```
Phases: DECOMPOSE → ANSWER → RISE_ABOVE → EXPAND → COMPLETE

Backward transitions:
  ANSWER → DECOMPOSE: "new_category_discovered"
  RISE_ABOVE → ANSWER: "synthesis_requires_more_answers"
  RISE_ABOVE → DECOMPOSE: "synthesis_reveals_missing_category"

Checkpoints:
  After DECOMPOSE: User approves question tree (BLOCKING)
  After ANSWER: User reviews coverage (OPTIONAL)
```

### Understand Agent

```
Phases: CALIBRATE → DIAGNOSE → TEACH → (loop) → COMPLETE

Backward transitions:
  DIAGNOSE → CALIBRATE: "calibration_was_inaccurate"
  TEACH → CALIBRATE: "fundamental_prerequisite_gap"
  TEACH → DIAGNOSE: "check_question_failed"

Checkpoints:
  After CALIBRATE: User confirms knowledge state (BLOCKING)
  After each SLO: User sees summary (INFORMATIONAL)
```

### Build Agent

```
Phases: GROUNDING → MAKING → COMPLETE

Backward transitions:
  MAKING → GROUNDING: "conceptual_gap_discovered"

Checkpoints:
  After GROUNDING: User ready to proceed (BLOCKING)
```

---

## Tool Wrapping Pattern

All tools MUST be wrapped for SSE event emission:

```python
class ToolWrapper:
    """Wraps tools to emit SSE events on invocation."""

    def __init__(self, tool: Tool, event_emitter: Callable):
        self.tool = tool
        self.emit = event_emitter

    async def __call__(self, **kwargs) -> Any:
        # Emit tool start
        self.emit(ToolStartEvent(
            tool_name=self.tool.name,
            parameters=kwargs
        ))

        try:
            result = await self.tool(**kwargs)

            # Emit tool success
            self.emit(ToolSuccessEvent(
                tool_name=self.tool.name,
                result_summary=self._summarize(result)
            ))

            return result
        except Exception as e:
            # Emit tool error
            self.emit(ToolErrorEvent(
                tool_name=self.tool.name,
                error=str(e)
            ))
            raise
```

---

## Testing Requirements

All agents MUST have tests for:

1. **Phase progression**: Forward transitions work correctly
2. **Backward transitions**: Each backward trigger causes correct transition
3. **Re-entry behavior**: Prompts differ on re-entry
4. **Checkpoint handling**: Blocking checkpoints work
5. **State persistence**: `get_state()` and `restore_state()` round-trip
6. **SSE events**: Correct events emitted at each stage

---

## Implementation Checklist

When implementing a new agent:

- [ ] Define `Phase` enum with all phases including COMPLETE
- [ ] Define `phase_transitions` list with all forward and backward transitions
- [ ] Implement `PhaseContext` dataclass with agent-specific state
- [ ] Implement `_execute_phase()` for each phase
- [ ] Implement `_get_phase_prompt()` with initial and re-entry variants
- [ ] Implement `_get_phase_tools()` for each phase
- [ ] Implement `_evaluate_transition_condition()` for all transitions
- [ ] Implement checkpoints where required
- [ ] Wrap all tools for SSE emission
- [ ] Implement `get_state()` and `restore_state()`
- [ ] Write tests for all transitions and re-entry scenarios

---

## Example: Research Agent Implementation

See `server/agents/research/agent.py` for the reference implementation following this pattern.
