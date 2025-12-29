"""
Research Agent Implementation.

Implements the deep research pipeline using the Claude Agent SDK
and phase graph pattern.

See docs/agent-architecture.md for the architectural specification.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional, Callable, Any, Awaitable
import uuid

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
    tool,
    create_sdk_mcp_server,
)

from server.persistence import (
    JourneyDesignBrief,
    Session,
    ResearchModeData,
    CategoryQuestion,
    Question,
    Source,
    KeyInsight,
    AdjacentQuestion,
    CodeContent,
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


class ResearchAgent(BaseForgeAgent[ResearchPhase, ResearchPhaseContext]):
    """
    Research Agent for Knowledge Forge.

    Executes the deep research pipeline using the Claude Agent SDK:
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
        emit_event: Callable[[SSEEvent], Awaitable[None]],
        checkpoint_handler: Optional[Callable[[Checkpoint], Awaitable[CheckpointResponse]]] = None,
    ):
        super().__init__(session, emit_event, checkpoint_handler)
        self._mcp_server = None

    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """Initialize the agent for a new research journey."""
        await super().initialize(journey_brief)

        # Initialize mode data if not present
        if self.session.research_data is None:
            self.session.research_data = ResearchModeData(
                topic=journey_brief.original_question,
            )

        # Create MCP server with custom tools
        self._mcp_server = self._create_mcp_server()

    def _create_phase_context(self) -> ResearchPhaseContext:
        """Create the initial phase context."""
        return ResearchPhaseContext()

    # =========================================================================
    # MCP Server with Custom Tools
    # =========================================================================

    def _create_mcp_server(self):
        """
        Create an MCP server with custom tools for research phases.

        Tools emit SSE events and update phase context state.
        """
        # Capture reference to agent for tool handlers
        agent = self

        @tool(
            "emit_category",
            "Add a research category to the question tree",
            {"category": str, "insight_question": str}
        )
        async def emit_category(args: dict[str, Any]) -> dict[str, Any]:
            """Add a new research category."""
            category = CategoryQuestion(
                id=str(uuid.uuid4()),
                category=args["category"],
                insight=None,
                question_ids=[],
            )
            agent.phase_context.add_category(category)

            # Emit SSE event
            agent.emitter.emit_sync(SSEEvent(
                type="data.category.added",
                payload=category.model_dump(by_alias=True),
            ))

            return {"content": [{"type": "text", "text": f"Category '{args['category']}' added with ID {category.id}"}]}

        @tool(
            "emit_question",
            "Add a research question to a category",
            {"question": str, "category_id": str, "frame": str, "priority": str}
        )
        async def emit_question(args: dict[str, Any]) -> dict[str, Any]:
            """Add a research question."""
            question = Question(
                id=str(uuid.uuid4()),
                question=args["question"],
                status="open",
                category_id=args["category_id"],
            )
            agent.phase_context.add_question(question)

            # Update category's question_ids
            for cat in agent.phase_context.categories:
                if cat.id == args["category_id"]:
                    cat.question_ids.append(question.id)
                    break

            # Emit SSE event
            agent.emitter.emit_sync(SSEEvent(
                type="data.question.added",
                payload={
                    "question": question.model_dump(by_alias=True),
                    "categoryId": args["category_id"],
                    "frame": args["frame"],
                    "priority": args["priority"],
                },
            ))

            return {"content": [{"type": "text", "text": f"Question added with ID {question.id}"}]}

        @tool(
            "mark_decompose_complete",
            "Mark question decomposition as complete",
            {"summary": str}
        )
        async def mark_decompose_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Signal decomposition is ready for approval."""
            return {"content": [{"type": "text", "text": f"Decomposition complete: {len(agent.phase_context.categories)} categories, {len(agent.phase_context.questions)} questions"}]}

        @tool(
            "emit_answer",
            "Record an answer to a research question",
            {
                "question_id": str,
                "answer": str,
                "sources": list,  # List of source dicts
                "confidence": str,
            }
        )
        async def emit_answer(args: dict[str, Any]) -> dict[str, Any]:
            """Record an answer with sources."""
            question_id = args["question_id"]

            # Find and update the question
            for q in agent.phase_context.questions:
                if q.id == question_id:
                    q.status = "answered"
                    q.answer = args["answer"]
                    q.sources = [Source(**s) for s in args.get("sources", [])]
                    break

            agent.phase_context.mark_question_answered(question_id)

            # Emit SSE event
            agent.emitter.emit_sync(SSEEvent(
                type="data.question.answered",
                payload={
                    "questionId": question_id,
                    "answer": args["answer"],
                    "sources": args.get("sources", []),
                    "confidence": args.get("confidence", "medium"),
                },
            ))

            return {"content": [{"type": "text", "text": f"Answer recorded for question {question_id}"}]}

        @tool(
            "skip_question",
            "Skip a question that cannot be adequately answered",
            {"question_id": str, "reason": str}
        )
        async def skip_question(args: dict[str, Any]) -> dict[str, Any]:
            """Skip a question."""
            agent.phase_context.skipped_question_ids.add(args["question_id"])

            agent.emitter.emit_sync(SSEEvent(
                type="data.question.updated",
                payload={
                    "questionId": args["question_id"],
                    "status": "skipped",
                    "reason": args["reason"],
                },
            ))

            return {"content": [{"type": "text", "text": f"Question {args['question_id']} skipped"}]}

        @tool(
            "flag_new_category",
            "Flag that a new category was discovered during answering",
            {"category_name": str, "reason": str}
        )
        async def flag_new_category(args: dict[str, Any]) -> dict[str, Any]:
            """Trigger backward transition to DECOMPOSE."""
            agent.phase_context.new_category_pending = args["category_name"]
            agent.phase_context.backward_trigger_detail = args["reason"]

            return {"content": [{"type": "text", "text": f"New category flagged: {args['category_name']} - will trigger backward transition"}]}

        @tool(
            "mark_answer_phase_complete",
            "Mark the answer phase as complete",
            {"summary": str}
        )
        async def mark_answer_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Signal answer phase is complete."""
            unanswered = agent.phase_context.get_unanswered_questions()
            if len(unanswered) == 0:
                agent.phase_context.high_priority_complete = True
            return {"content": [{"type": "text", "text": f"Answer phase complete. Remaining: {len(unanswered)} questions"}]}

        @tool(
            "emit_category_insight",
            "Record a synthesized insight for a category",
            {"category_id": str, "insight": str}
        )
        async def emit_category_insight(args: dict[str, Any]) -> dict[str, Any]:
            """Add category insight."""
            category_id = args["category_id"]
            insight = args["insight"]

            for cat in agent.phase_context.categories:
                if cat.id == category_id:
                    cat.insight = insight
                    break

            agent.phase_context.category_insights[category_id] = insight

            agent.emitter.emit_sync(SSEEvent(
                type="data.category.insight",
                payload={"categoryId": category_id, "insight": insight},
            ))

            return {"content": [{"type": "text", "text": f"Insight added for category {category_id}"}]}

        @tool(
            "emit_key_insight",
            "Record a cross-cutting key insight",
            {"title": str, "description": str, "relevance": str}
        )
        async def emit_key_insight(args: dict[str, Any]) -> dict[str, Any]:
            """Add key insight."""
            insight = KeyInsight(
                id=str(uuid.uuid4()),
                title=args["title"],
                description=args["description"],
                relevance=args.get("relevance", ""),
            )

            agent.emitter.emit_sync(SSEEvent(
                type="data.key_insight.added",
                payload=insight.model_dump(by_alias=True),
            ))

            return {"content": [{"type": "text", "text": f"Key insight added: {args['title']}"}]}

        @tool(
            "flag_unanswered_needed",
            "Flag that specific questions must be answered before synthesis",
            {"question_ids": list, "reason": str}
        )
        async def flag_unanswered_needed(args: dict[str, Any]) -> dict[str, Any]:
            """Trigger backward transition to ANSWER."""
            agent.phase_context.unanswered_for_synthesis = args["question_ids"]
            agent.phase_context.backward_trigger_detail = args["reason"]

            return {"content": [{"type": "text", "text": f"Flagged {len(args['question_ids'])} questions needed - will trigger backward transition"}]}

        @tool(
            "mark_synthesis_complete",
            "Mark synthesis phase as complete",
            {"summary": str}
        )
        async def mark_synthesis_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Signal synthesis is complete."""
            agent.phase_context.insights_complete = True
            return {"content": [{"type": "text", "text": "Synthesis complete"}]}

        @tool(
            "emit_adjacent_question",
            "Add an adjacent question to the frontier",
            {"question": str, "discovered_from": str}
        )
        async def emit_adjacent_question(args: dict[str, Any]) -> dict[str, Any]:
            """Add frontier question."""
            aq = AdjacentQuestion(
                id=str(uuid.uuid4()),
                question=args["question"],
                discovered_from=args["discovered_from"],
            )
            agent.phase_context.adjacent_questions.append(aq)

            agent.emitter.emit_sync(SSEEvent(
                type="data.adjacent_question.added",
                payload=aq.model_dump(by_alias=True),
            ))

            return {"content": [{"type": "text", "text": f"Adjacent question added: {args['question'][:50]}..."}]}

        @tool(
            "mark_expand_complete",
            "Mark expansion phase as complete",
            {"summary": str}
        )
        async def mark_expand_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Signal expansion is complete."""
            agent.phase_context.frontier_populated = True
            return {"content": [{"type": "text", "text": f"Expansion complete: {len(agent.phase_context.adjacent_questions)} frontier questions"}]}

        @tool(
            "get_phase_context",
            "Get context from the current or previous phases",
            {"phase_name": str}
        )
        async def get_phase_context(args: dict[str, Any]) -> dict[str, Any]:
            """Retrieve phase context for reference."""
            phase = args["phase_name"].upper()

            if phase == "DECOMPOSE":
                return {"content": [{"type": "text", "text": f"Categories: {agent._format_categories()}\n\nQuestions: {agent._format_questions()}"}]}
            elif phase == "ANSWER":
                return {"content": [{"type": "text", "text": f"Answered: {agent._format_answered_questions()}"}]}
            elif phase == "RISE_ABOVE":
                return {"content": [{"type": "text", "text": f"Insights: {agent._format_insights()}"}]}
            else:
                return {"content": [{"type": "text", "text": f"Unknown phase: {phase}"}]}

        # Create MCP server with all tools
        return create_sdk_mcp_server(
            name="research-agent",
            version="1.0.0",
            tools=[
                emit_category,
                emit_question,
                mark_decompose_complete,
                emit_answer,
                skip_question,
                flag_new_category,
                mark_answer_complete,
                emit_category_insight,
                emit_key_insight,
                flag_unanswered_needed,
                mark_synthesis_complete,
                emit_adjacent_question,
                mark_expand_complete,
                get_phase_context,
            ]
        )

    # =========================================================================
    # Phase Execution using Claude Agent SDK
    # =========================================================================

    async def _execute_phase(
        self,
        phase: ResearchPhase,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute a single phase using the Claude Agent SDK."""

        yield agent_thinking(f"Executing {phase.value} phase...")

        # Get phase-specific configuration
        visit_count = self.phase_context.get_visit_count(phase)
        prompt = self._get_phase_prompt(phase, visit_count)
        allowed_tools = self._get_allowed_tools(phase)

        # Build SDK options
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=allowed_tools,
            mcp_servers={"research": self._mcp_server},
        )

        # Run the agent
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Stream text to frontend
                            yield agent_speaking(block.text)
                        elif isinstance(block, ToolUseBlock):
                            # Tool calls are handled by the SDK
                            # Our MCP tools emit SSE events internally
                            pass

                elif isinstance(message, ResultMessage):
                    # Phase complete
                    break

        # Handle checkpoint if needed
        if phase == ResearchPhase.DECOMPOSE and not self.phase_context.question_tree_approved:
            checkpoint = Checkpoint(
                id="decompose_approval",
                message=self._format_decompose_checkpoint(),
                options=["Proceed", "Add questions", "Remove questions", "Adjust priorities"],
            )

            yield SSEEvent(
                type="phase.checkpoint",
                payload={
                    "checkpointId": checkpoint.id,
                    "message": checkpoint.message,
                    "options": checkpoint.options,
                    "requiresApproval": True,
                },
            )

            response = await self._handle_checkpoint(checkpoint)
            if response.approved:
                self.phase_context.question_tree_approved = True

    def _get_allowed_tools(self, phase: ResearchPhase) -> list[str]:
        """Get allowed tools for a phase."""
        # Base tools available in all phases
        base_tools = [
            "mcp__research__get_phase_context",
        ]

        phase_tools = {
            ResearchPhase.DECOMPOSE: [
                "mcp__research__emit_category",
                "mcp__research__emit_question",
                "mcp__research__mark_decompose_complete",
            ],
            ResearchPhase.ANSWER: [
                "WebSearch",
                "WebFetch",
                "mcp__research__emit_answer",
                "mcp__research__skip_question",
                "mcp__research__flag_new_category",
                "mcp__research__mark_answer_phase_complete",
            ],
            ResearchPhase.RISE_ABOVE: [
                "mcp__research__emit_category_insight",
                "mcp__research__emit_key_insight",
                "mcp__research__flag_unanswered_needed",
                "mcp__research__mark_synthesis_complete",
            ],
            ResearchPhase.EXPAND: [
                "mcp__research__emit_adjacent_question",
                "mcp__research__mark_expand_complete",
            ],
        }

        return base_tools + phase_tools.get(phase, [])

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
            return False  # Handled by other triggers

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
        return self._format_answered_questions()

    def _format_insights(self) -> str:
        """Format category insights for prompt."""
        lines = []
        for cat_id, insight in self.phase_context.category_insights.items():
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
        num_high = len(self.phase_context.questions)  # Simplified
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
        base_state["mode_data"] = {
            "topic": self.journey_brief.original_question if self.journey_brief else "",
        }
        return base_state

    async def restore_state(self, state: dict) -> None:
        """Restore agent from persisted state."""
        await super().restore_state(state)
        # Recreate MCP server for restored agent
        self._mcp_server = self._create_mcp_server()
