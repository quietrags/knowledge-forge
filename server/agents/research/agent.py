"""
Research Agent Implementation.

Implements the deep research pipeline using the phase graph pattern.
See docs/agent-architecture.md for the architectural specification.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional, Callable

from anthropic import Anthropic

from server.persistence import (
    JourneyDesignBrief,
    Session,
    ResearchModeData,
)
from server.api.streaming import SSEEvent, agent_thinking, agent_speaking
from server.agents.base import (
    BaseForgeAgent,
    PhaseTransition,
    Checkpoint,
    CheckpointResponse,
)
from .phases import (
    ResearchPhase,
    ResearchPhaseContext,
    RESEARCH_TRANSITIONS,
)
from .prompts import (
    SYSTEM_PROMPT,
    DECOMPOSE_INITIAL_PROMPT,
    DECOMPOSE_REENTRY_PROMPT,
    ANSWER_INITIAL_PROMPT,
    ANSWER_REENTRY_PROMPT,
    RISE_ABOVE_INITIAL_PROMPT,
    RISE_ABOVE_REENTRY_PROMPT,
    EXPAND_INITIAL_PROMPT,
    EXPAND_REENTRY_PROMPT,
    DECOMPOSE_CHECKPOINT_MESSAGE,
)
from .tools import (
    get_decompose_tools,
    get_answer_tools,
    get_rise_above_tools,
    get_expand_tools,
    ResearchToolHandler,
)


class ResearchAgent(BaseForgeAgent[ResearchPhase, ResearchPhaseContext]):
    """
    Research Agent for Knowledge Forge.

    Executes the deep research pipeline:
    DECOMPOSE → ANSWER → RISE_ABOVE → EXPAND → COMPLETE

    With backward transitions for:
    - Discovery of new categories during answering
    - Need for more answers during synthesis
    """

    # =========================================================================
    # Abstract Property Implementations
    # =========================================================================

    @property
    def Phase(self) -> type[ResearchPhase]:
        return ResearchPhase

    @property
    def phase_transitions(self) -> list[PhaseTransition]:
        return RESEARCH_TRANSITIONS

    @property
    def initial_phase(self) -> ResearchPhase:
        return ResearchPhase.DECOMPOSE

    @property
    def complete_phase(self) -> ResearchPhase:
        return ResearchPhase.COMPLETE

    @property
    def agent_type(self) -> str:
        return "research"

    # =========================================================================
    # Initialization
    # =========================================================================

    def __init__(
        self,
        session: Session,
        emit_event: Callable[[SSEEvent], None],
        client: Optional[Anthropic] = None,
        checkpoint_handler: Optional[Callable[[Checkpoint], CheckpointResponse]] = None,
    ):
        super().__init__(session, emit_event, client, checkpoint_handler)
        self._tool_handler: Optional[ResearchToolHandler] = None

    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """Initialize the agent for a new research journey."""
        await super().initialize(journey_brief)

        # Initialize mode data if not present
        if self.session.research_data is None:
            self.session.research_data = ResearchModeData(
                topic=journey_brief.original_question,
            )

        # Create tool handler
        self._tool_handler = ResearchToolHandler(
            self.phase_context,
            self.emit,
        )

    def _create_phase_context(self) -> ResearchPhaseContext:
        """Create the initial phase context."""
        return ResearchPhaseContext()

    # =========================================================================
    # Phase Execution
    # =========================================================================

    async def _execute_phase(
        self,
        phase: ResearchPhase,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute a single phase of the research pipeline."""

        if phase == ResearchPhase.DECOMPOSE:
            async for event in self._execute_decompose(message, context):
                yield event
        elif phase == ResearchPhase.ANSWER:
            async for event in self._execute_answer(message, context):
                yield event
        elif phase == ResearchPhase.RISE_ABOVE:
            async for event in self._execute_rise_above(message, context):
                yield event
        elif phase == ResearchPhase.EXPAND:
            async for event in self._execute_expand(message, context):
                yield event

    async def _execute_decompose(
        self,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute the DECOMPOSE phase."""
        yield agent_thinking("Breaking down your question into research categories...")

        # Get appropriate prompt
        visit_count = self.phase_context.get_visit_count(ResearchPhase.DECOMPOSE)
        prompt = self._get_phase_prompt(ResearchPhase.DECOMPOSE, visit_count)

        # Get tools for this phase
        tools = self._get_phase_tools(ResearchPhase.DECOMPOSE)

        # Execute with Claude
        async for event in self._run_agent_loop(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            tools=tools,
        ):
            yield event

        # Handle checkpoint (blocking)
        if not self.phase_context.question_tree_approved:
            checkpoint = Checkpoint(
                id="decompose_approval",
                message=self._format_decompose_checkpoint(),
                options=["Proceed", "Add questions", "Remove questions", "Adjust priorities"],
            )

            # Emit checkpoint event
            yield SSEEvent(
                type="phase.checkpoint",
                payload={
                    "checkpointId": checkpoint.id,
                    "message": checkpoint.message,
                    "options": checkpoint.options,
                    "requiresApproval": True,
                },
            )

            # Wait for user response
            response = await self._handle_checkpoint(checkpoint)

            if response.approved:
                self.phase_context.question_tree_approved = True
            elif response.action == "modify":
                # User wants changes - will stay in this phase
                pass

    async def _execute_answer(
        self,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute the ANSWER phase."""
        unanswered = self.phase_context.get_unanswered_questions()
        yield agent_thinking(f"Researching {len(unanswered)} questions...")

        # Get appropriate prompt
        visit_count = self.phase_context.get_visit_count(ResearchPhase.ANSWER)
        prompt = self._get_phase_prompt(ResearchPhase.ANSWER, visit_count)

        # Get tools for this phase
        tools = self._get_phase_tools(ResearchPhase.ANSWER)

        # Execute with Claude (with web search enabled)
        async for event in self._run_agent_loop(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            tools=tools,
            enable_web_search=True,
        ):
            yield event

    async def _execute_rise_above(
        self,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute the RISE_ABOVE phase."""
        yield agent_thinking("Synthesizing insights from your research...")

        # Get appropriate prompt
        visit_count = self.phase_context.get_visit_count(ResearchPhase.RISE_ABOVE)
        prompt = self._get_phase_prompt(ResearchPhase.RISE_ABOVE, visit_count)

        # Get tools for this phase
        tools = self._get_phase_tools(ResearchPhase.RISE_ABOVE)

        # Execute with Claude
        async for event in self._run_agent_loop(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            tools=tools,
        ):
            yield event

    async def _execute_expand(
        self,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute the EXPAND phase."""
        yield agent_thinking("Discovering adjacent questions for further exploration...")

        # Get appropriate prompt
        visit_count = self.phase_context.get_visit_count(ResearchPhase.EXPAND)
        prompt = self._get_phase_prompt(ResearchPhase.EXPAND, visit_count)

        # Get tools for this phase
        tools = self._get_phase_tools(ResearchPhase.EXPAND)

        # Execute with Claude
        async for event in self._run_agent_loop(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            tools=tools,
        ):
            yield event

    # =========================================================================
    # Agent Loop (Claude API Integration)
    # =========================================================================

    async def _run_agent_loop(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        enable_web_search: bool = False,
    ) -> AsyncGenerator[SSEEvent, None]:
        """
        Run the agentic loop with Claude.

        Handles tool calls, streaming, and state updates.
        """
        messages = [{"role": "user", "content": user_prompt}]

        # Build API call parameters
        api_params = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": messages,
            "tools": tools,
        }

        # Enable web search if requested (uses Claude's built-in connector)
        # Note: In production, this would use the appropriate API parameters
        # for web search integration

        while True:
            # Call Claude API
            response = self.client.messages.create(**api_params)

            # Process response
            assistant_content = []
            has_tool_use = False

            for block in response.content:
                if block.type == "text":
                    # Stream text to UI
                    yield agent_speaking(block.text)
                    assistant_content.append(block)

                elif block.type == "tool_use":
                    has_tool_use = True
                    assistant_content.append(block)

                    # Handle tool call
                    tool_result = await self._tool_handler.handle_tool_call(
                        block.name,
                        block.input,
                    )

                    # Add tool result to messages
                    messages.append({"role": "assistant", "content": assistant_content})
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(tool_result),
                        }],
                    })

            # If no tool use, we're done with this loop
            if not has_tool_use:
                break

            # Continue loop with tool results
            api_params["messages"] = messages
            assistant_content = []

    # =========================================================================
    # Prompt Generation
    # =========================================================================

    def _get_phase_prompt(self, phase: ResearchPhase, visit_count: int) -> str:
        """Get the prompt for a phase (initial or re-entry)."""

        if phase == ResearchPhase.DECOMPOSE:
            if visit_count <= 1:
                return DECOMPOSE_INITIAL_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    learner_context=self.journey_brief.implicit_question or "",
                )
            else:
                return DECOMPOSE_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger,
                    backward_trigger_detail=self.phase_context.backward_trigger_detail or "",
                    existing_categories=self._format_categories(),
                    existing_questions=self._format_questions(),
                )

        elif phase == ResearchPhase.ANSWER:
            if visit_count <= 1:
                return ANSWER_INITIAL_PROMPT.format(
                    categories=self._format_categories(),
                    questions=self._format_questions(),
                )
            else:
                return ANSWER_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger,
                    backward_trigger_detail=self.phase_context.backward_trigger_detail or "",
                    answered_questions=self._format_answered_questions(),
                    unanswered_questions=self._format_unanswered_questions(),
                    unanswered_for_synthesis=self.phase_context.unanswered_for_synthesis,
                )

        elif phase == ResearchPhase.RISE_ABOVE:
            if visit_count <= 1:
                return RISE_ABOVE_INITIAL_PROMPT.format(
                    categories=self._format_categories(),
                    answered_questions=self._format_answered_questions(),
                )
            else:
                return RISE_ABOVE_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger,
                    existing_insights=self._format_insights(),
                    newly_answered_questions=self._format_newly_answered_questions(),
                )

        elif phase == ResearchPhase.EXPAND:
            if visit_count <= 1:
                return EXPAND_INITIAL_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    categories=self._format_categories(),
                    answered_questions=self._format_answered_questions(),
                    category_insights=self._format_insights(),
                )
            else:
                return EXPAND_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger,
                    existing_adjacent_questions=self._format_adjacent_questions(),
                )

        return ""

    def _get_phase_tools(self, phase: ResearchPhase) -> list[dict]:
        """Get available tools for a phase."""
        if phase == ResearchPhase.DECOMPOSE:
            return get_decompose_tools()
        elif phase == ResearchPhase.ANSWER:
            return get_answer_tools()
        elif phase == ResearchPhase.RISE_ABOVE:
            return get_rise_above_tools()
        elif phase == ResearchPhase.EXPAND:
            return get_expand_tools()
        return []

    # =========================================================================
    # Transition Evaluation
    # =========================================================================

    def _evaluate_transition_condition(self, transition: PhaseTransition) -> bool:
        """Check if a specific transition's condition is met."""

        condition = transition.condition

        # Forward transitions
        if condition == "question_tree_approved":
            return self.phase_context.question_tree_approved

        elif condition == "high_priority_questions_answered":
            return self.phase_context.high_priority_complete

        elif condition == "category_insights_generated":
            return self.phase_context.insights_complete

        elif condition == "frontier_populated":
            return self.phase_context.frontier_populated

        # Backward transitions
        elif condition == "new_category_discovered":
            return self.phase_context.should_trigger_backward_to_decompose()

        elif condition == "synthesis_requires_more_answers":
            return self.phase_context.should_trigger_backward_to_answer()

        elif condition == "synthesis_reveals_missing_category":
            # This is a more severe case - caught during synthesis
            return False  # Handled by synthesis_requires_more_answers usually

        return False

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_categories(self) -> str:
        """Format categories for prompt."""
        lines = []
        for cat in self.phase_context.categories:
            lines.append(f"- {cat.category} (ID: {cat.id})")
        return "\n".join(lines) if lines else "No categories yet"

    def _format_questions(self) -> str:
        """Format all questions for prompt."""
        lines = []
        for q in self.phase_context.questions:
            status = "answered" if q.id in self.phase_context.answered_question_ids else "open"
            lines.append(f"- [{status}] {q.question} (ID: {q.id})")
        return "\n".join(lines) if lines else "No questions yet"

    def _format_answered_questions(self) -> str:
        """Format answered questions for prompt."""
        lines = []
        for q in self.phase_context.questions:
            if q.id in self.phase_context.answered_question_ids:
                answer_preview = (q.answer[:100] + "...") if q.answer and len(q.answer) > 100 else q.answer
                lines.append(f"Q: {q.question}\nA: {answer_preview}")
        return "\n\n".join(lines) if lines else "No answered questions yet"

    def _format_unanswered_questions(self) -> str:
        """Format unanswered questions for prompt."""
        unanswered = self.phase_context.get_unanswered_questions()
        lines = [f"- {q.question} (ID: {q.id})" for q in unanswered]
        return "\n".join(lines) if lines else "All questions answered"

    def _format_newly_answered_questions(self) -> str:
        """Format questions answered since last RISE_ABOVE visit."""
        # For now, return all answered - could track more precisely
        return self._format_answered_questions()

    def _format_insights(self) -> str:
        """Format category insights for prompt."""
        lines = []
        for cat_id, insight in self.phase_context.category_insights.items():
            # Find category name
            cat_name = next(
                (c.category for c in self.phase_context.categories if c.id == cat_id),
                cat_id,
            )
            lines.append(f"**{cat_name}**: {insight}")
        return "\n\n".join(lines) if lines else "No insights yet"

    def _format_adjacent_questions(self) -> str:
        """Format adjacent questions for prompt."""
        lines = [f"- {aq.question}" for aq in self.phase_context.adjacent_questions]
        return "\n".join(lines) if lines else "No adjacent questions yet"

    def _format_decompose_checkpoint(self) -> str:
        """Format the decompose checkpoint message."""
        num_high = sum(1 for _ in self.phase_context.questions)  # Simplified
        return DECOMPOSE_CHECKPOINT_MESSAGE.format(
            num_categories=len(self.phase_context.categories),
            num_questions=len(self.phase_context.questions),
            num_high=num_high,
            num_medium=0,
            num_low=0,
            category_summary=self._format_categories(),
            story_arc="Research decomposition complete",
        )

    # =========================================================================
    # Completion
    # =========================================================================

    def _generate_completion_summary(self) -> str:
        """Generate a summary when research completes."""
        return (
            f"Research complete. "
            f"Answered {len(self.phase_context.answered_question_ids)} questions "
            f"across {len(self.phase_context.categories)} categories. "
            f"Generated {len(self.phase_context.category_insights)} insights "
            f"and {len(self.phase_context.adjacent_questions)} frontier questions."
        )

    # =========================================================================
    # State Persistence
    # =========================================================================

    def _serialize_phase_context(self) -> dict:
        """Serialize phase context to dict."""
        return self.phase_context.to_dict()

    def _restore_phase_context(self, state: dict) -> None:
        """Restore phase context from state."""
        self.phase_context = ResearchPhaseContext.from_dict(state)

    def get_state(self) -> dict:
        """Get current state for persistence."""
        base_state = super().get_state()

        # Add research-specific state
        base_state["mode_data"] = {
            "topic": self.journey_brief.original_question if self.journey_brief else "",
        }

        return base_state

    async def restore_state(self, state: dict) -> None:
        """Restore agent from persisted state."""
        await super().restore_state(state)

        # Restore tool handler
        self._tool_handler = ResearchToolHandler(
            self.phase_context,
            self.emit,
        )
