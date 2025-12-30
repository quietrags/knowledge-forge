"""
Understand Agent Implementation.

Implements the Socratic tutoring system using the Claude Agent SDK
and phase graph pattern.

See docs/agent-architecture.md for the architectural specification.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional, Callable, Any, Awaitable
import uuid
import logging

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

from server.agents.logging import (
    get_agent_logger,
    log_prompt,
    log_llm_response,
    log_tool_result,
    log_phase_transition,
    log_error,
)

from server.persistence import (
    JourneyDesignBrief,
    Session,
    UnderstandModeData,
    SLO,
    KnowledgeStateFacet,
)
from server.api.streaming import SSEEvent, agent_thinking, agent_speaking
from server.agents.base import (
    BaseForgeAgent,
    PhaseTransition,
    Checkpoint,
    CheckpointResponse,
)
from .phases import (
    UnderstandPhase,
    UnderstandPhaseContext,
    UNDERSTAND_TRANSITIONS,
)
from .prompts import (
    SYSTEM_PROMPT,
    SELF_ASSESS_PROMPT,
    CONFIGURE_PROMPT,
    CONFIGURE_RESUME_PROMPT,
    CLASSIFY_INITIAL_PROMPT,
    CLASSIFY_RESUME_PROMPT,
    CALIBRATE_INITIAL_PROMPT,
    CALIBRATE_RESUME_PROMPT,
    CALIBRATE_REENTRY_PROMPT,
    DIAGNOSE_INITIAL_PROMPT,
    DIAGNOSE_REENTRY_PROMPT,
    SLO_COMPLETE_PROMPT,
    COMPLETE_PROMPT,
    CONFIGURE_CHECKPOINT_MESSAGE,
    CLASSIFY_CHECKPOINT_MESSAGE,
    CALIBRATE_CHECKPOINT_MESSAGE,
)


class UnderstandAgent(BaseForgeAgent[UnderstandPhase, UnderstandPhaseContext]):
    """
    Understand Agent for Knowledge Forge.

    Implements the Socratic tutoring system using the Claude Agent SDK:
    SELF_ASSESS → CONFIGURE → CLASSIFY → CALIBRATE → DIAGNOSE → SLO_COMPLETE → COMPLETE

    With transitions for:
    - Moving to next SLO after completion
    - Returning to calibration for new SLO
    """

    # =========================================================================
    # Abstract Property Implementations
    # =========================================================================

    @property
    def Phase(self) -> type[UnderstandPhase]:
        return UnderstandPhase

    @property
    def phase_transitions(self) -> list[PhaseTransition]:
        return UNDERSTAND_TRANSITIONS

    @property
    def initial_phase(self) -> UnderstandPhase:
        return UnderstandPhase.SELF_ASSESS

    @property
    def complete_phase(self) -> UnderstandPhase:
        return UnderstandPhase.COMPLETE

    @property
    def agent_type(self) -> str:
        return "understand"

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
        self._logger: Optional[logging.Logger] = None

    async def initialize(self, journey_brief: JourneyDesignBrief) -> None:
        """Initialize the agent for a new understanding journey."""
        await super().initialize(journey_brief)

        # Initialize logging
        self._logger = get_agent_logger(self.session.id, "understand")
        self._logger.info(f"Initialized understand agent for: {journey_brief.original_question}")

        # Initialize mode data if not present
        if self.session.understand_data is None:
            self.session.understand_data = UnderstandModeData()

        # Create MCP server with custom tools
        self._mcp_server = self._create_mcp_server()

    def _create_phase_context(self) -> UnderstandPhaseContext:
        """Create the initial phase context."""
        return UnderstandPhaseContext()

    # =========================================================================
    # MCP Server with Custom Tools
    # =========================================================================

    def _create_mcp_server(self):
        """
        Create an MCP server with custom tools for understand phases.

        Tools emit SSE events and update phase context state.
        """
        # Capture reference to agent for tool handlers
        agent = self

        # =================================================================
        # Stage 0: Knowledge Self-Assessment Tools
        # =================================================================

        @tool(
            "emit_knowledge_confidence",
            "Record the tutor's knowledge confidence level for the topic",
            {"confidence": str, "topic_brief": str, "aspects_to_skip": list}
        )
        async def emit_knowledge_confidence(args: dict[str, Any]) -> dict[str, Any]:
            """Record knowledge confidence assessment."""
            agent.phase_context.knowledge_confidence = args["confidence"]
            if args.get("topic_brief"):
                agent.phase_context.topic_brief = {"summary": args["topic_brief"]}
            if args.get("aspects_to_skip"):
                agent.phase_context.aspects_to_skip = args["aspects_to_skip"]

            agent.emitter.emit_sync(SSEEvent(
                type="data.knowledge_confidence",
                payload={
                    "confidence": args["confidence"],
                    "topicBrief": args.get("topic_brief", ""),
                    "aspectsToSkip": args.get("aspects_to_skip", []),
                },
            ))

            return {"content": [{"type": "text", "text": f"Knowledge confidence set to {args['confidence']}"}]}

        # =================================================================
        # Stage 0.5: Session Configuration Tools
        # =================================================================

        @tool(
            "emit_session_config",
            "Record the learner's session preferences. Only call this AFTER the learner has responded with their preferences.",
            {"pace": str, "style": str, "learner_context": str}
        )
        async def emit_session_config(args: dict[str, Any]) -> dict[str, Any]:
            """Record session configuration."""
            # Guard: Don't allow setting config before user has responded
            if agent.phase_context.awaiting_user_input:
                return {"content": [{"type": "text", "text": "ERROR: Cannot set session config while waiting for user input. Wait for the learner to respond first."}]}

            agent.phase_context.pace = args.get("pace", "standard")
            agent.phase_context.style = args.get("style", "balanced")
            agent.phase_context.learner_context = args.get("learner_context", "")
            agent.phase_context.session_configured = True

            agent.emitter.emit_sync(SSEEvent(
                type="data.session_config",
                payload={
                    "pace": agent.phase_context.pace,
                    "style": agent.phase_context.style,
                    "learnerContext": agent.phase_context.learner_context,
                },
            ))

            return {"content": [{"type": "text", "text": f"Session configured: pace={args['pace']}, style={args['style']}"}]}

        @tool(
            "mark_config_questions_asked",
            "Mark that configuration questions have been presented to the learner. Call this AFTER presenting pace/style/context options, then STOP and WAIT for the learner's response.",
            {}
        )
        async def mark_config_questions_asked(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that config questions were asked - agent should now wait for response."""
            agent.phase_context.config_questions_asked = True
            # Block transitions until user responds
            agent.phase_context.awaiting_user_input = True

            return {"content": [{"type": "text", "text": "Configuration questions presented. STOP and wait for the learner's response before proceeding."}]}

        # =================================================================
        # Stage 1: Topic Classification and SLO Tools
        # =================================================================

        @tool(
            "emit_topic_type",
            "Record the topic classification type",
            {"topic_type": str}
        )
        async def emit_topic_type(args: dict[str, Any]) -> dict[str, Any]:
            """Record topic type classification."""
            agent.phase_context.topic_type = args["topic_type"]

            agent.emitter.emit_sync(SSEEvent(
                type="data.topic_type",
                payload={"topicType": args["topic_type"]},
            ))

            return {"content": [{"type": "text", "text": f"Topic classified as {args['topic_type']}"}]}

        @tool(
            "emit_slo",
            "Add a Single Learning Objective to the list. For in_scope and out_of_scope, provide a newline-separated string of bullet points.",
            {
                "statement": str,
                "frame": str,
                "in_scope": str,  # Newline-separated bullet points
                "out_of_scope": str,  # Newline-separated bullet points
                "sample_transfer_check": str,
                "estimated_rounds": int,
            }
        )
        async def emit_slo(args: dict[str, Any]) -> dict[str, Any]:
            """Add an SLO to the list."""
            # Parse string inputs into lists (handle various formats)
            def parse_list_string(s: Any) -> list[str]:
                if isinstance(s, list):
                    return s
                if not isinstance(s, str):
                    return []
                # Handle markdown bullets, JSON arrays, or plain newlines
                import json
                import re
                s = s.strip()
                # Try JSON array first
                if s.startswith('['):
                    try:
                        return json.loads(s)
                    except:
                        pass
                # Split by newlines and clean up bullets
                lines = re.split(r'\n|\\n', s)
                result = []
                for line in lines:
                    line = re.sub(r'^[\s\-\*•]+', '', line).strip()
                    if line:
                        result.append(line)
                return result

            in_scope = parse_list_string(args.get("in_scope", ""))
            out_of_scope = parse_list_string(args.get("out_of_scope", ""))

            slo = SLO(
                id=str(uuid.uuid4()),
                statement=args["statement"],
                frame=args["frame"],
                in_scope=in_scope,
                out_of_scope=out_of_scope,
                sample_transfer_check=args.get("sample_transfer_check", ""),
                estimated_rounds=args.get("estimated_rounds", 4),
            )
            agent.phase_context.add_slo(slo)

            agent.emitter.emit_sync(SSEEvent(
                type="data.slo.added",
                payload=slo.model_dump(by_alias=True),
            ))

            return {"content": [{"type": "text", "text": f"SLO added: {args['statement'][:50]}..."}]}

        @tool(
            "mark_slos_presented",
            "Mark that SLOs have been presented to the learner for selection. Call this AFTER presenting all SLOs, then STOP and WAIT for the learner to select which ones they want.",
            {}
        )
        async def mark_slos_presented(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that SLOs were presented - agent should now wait for selection."""
            agent.phase_context.slos_presented = True
            # Block transitions until user responds
            agent.phase_context.awaiting_user_input = True

            slo_count = len(agent.phase_context.slos)
            return {"content": [{"type": "text", "text": f"{slo_count} SLOs presented. STOP and wait for the learner to select which ones they want before proceeding."}]}

        @tool(
            "mark_slos_selected",
            "Mark which SLOs the learner has selected. Pass 'all' to select all SLOs, or a comma-separated list of SLO IDs. Only call this AFTER the learner has responded.",
            {"selected_slo_ids": str}  # "all" or comma-separated IDs
        )
        async def mark_slos_selected(args: dict[str, Any]) -> dict[str, Any]:
            """Record selected SLOs."""
            # Guard: Don't allow selection before user has responded
            if agent.phase_context.awaiting_user_input:
                return {"content": [{"type": "text", "text": "ERROR: Cannot select SLOs while waiting for user input. Wait for the learner to respond first."}]}

            # Parse the input - handle "all" or comma-separated IDs
            raw = args.get("selected_slo_ids", "all")
            if isinstance(raw, list):
                selected_ids = raw
            elif raw.lower().strip() == "all":
                selected_ids = [s.id for s in agent.phase_context.slos]
            else:
                selected_ids = [s.strip() for s in raw.split(",") if s.strip()]

            agent.phase_context.selected_slo_ids = selected_ids
            agent.phase_context.slos_confirmed = True

            agent.emitter.emit_sync(SSEEvent(
                type="data.slos_selected",
                payload={"selectedSloIds": selected_ids},
            ))

            return {"content": [{"type": "text", "text": f"{len(selected_ids)} SLOs selected"}]}

        # =================================================================
        # Stage 2: Triple Calibration Tools
        # =================================================================

        @tool(
            "mark_probe_question_asked",
            "Mark that a probe question has been asked to the learner. Call this AFTER presenting a probe question (feynman, minimal_example, or boundary), then STOP and WAIT for the learner's response.",
            {"probe_type": str}
        )
        async def mark_probe_question_asked(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that a probe question was asked - agent should now wait for response."""
            probe_type = args.get("probe_type", "unknown")
            agent.phase_context.awaiting_user_input = True

            return {"content": [{"type": "text", "text": f"Probe question ({probe_type}) presented. STOP and wait for the learner's response before evaluating."}]}

        @tool(
            "update_facet_status",
            "Update the knowledge state for a facet after a calibration probe",
            {"facet": str, "status": str, "evidence": str}
        )
        async def update_facet_status(args: dict[str, Any]) -> dict[str, Any]:
            """Update facet status from calibration."""
            agent.phase_context.update_facet_status(
                facet=args["facet"],
                status=args["status"],
                evidence=args["evidence"],
            )

            slo = agent.phase_context.get_current_slo()
            agent.emitter.emit_sync(SSEEvent(
                type="data.facet_updated",
                payload={
                    "sloId": slo.id if slo else None,
                    "facet": args["facet"],
                    "status": args["status"],
                    "evidence": args["evidence"],
                },
            ))

            return {"content": [{"type": "text", "text": f"Facet {args['facet']} updated to {args['status']}"}]}

        @tool(
            "record_probe_result",
            "Record the result of a calibration probe. Call this after evaluating each probe response. probe_type must be 'feynman', 'minimal_example', or 'boundary'. result should be 'strong', 'partial', or 'weak'.",
            {"probe_type": str, "result": str, "reasoning": str}
        )
        async def record_probe_result(args: dict[str, Any]) -> dict[str, Any]:
            """Record calibration probe result for state tracking."""
            probe_type = args["probe_type"]
            result = args["result"]
            reasoning = args.get("reasoning", "")

            # Record the probe result
            agent.phase_context.record_probe_result(probe_type, result)

            slo = agent.phase_context.get_current_slo()
            remaining = agent.phase_context.get_remaining_probes()

            agent.emitter.emit_sync(SSEEvent(
                type="data.probe_result",
                payload={
                    "sloId": slo.id if slo else None,
                    "probeType": probe_type,
                    "result": result,
                    "reasoning": reasoning,
                    "remainingProbes": remaining,
                },
            ))

            if len(remaining) == 0:
                return {"content": [{"type": "text", "text": f"Probe '{probe_type}' recorded as {result}. All 3 probes complete - call mark_calibration_complete to proceed."}]}
            else:
                return {"content": [{"type": "text", "text": f"Probe '{probe_type}' recorded as {result}. Remaining probes: {remaining}. Continue with next probe."}]}

        @tool(
            "mark_calibration_complete",
            "Mark that Triple Calibration is complete for current SLO. Only call after all 3 probes are done.",
            {"summary": str}
        )
        async def mark_calibration_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Signal calibration complete."""
            agent.phase_context.current_slo_calibrated = True

            slo = agent.phase_context.get_current_slo()
            state = agent.phase_context.get_current_knowledge_state()

            agent.emitter.emit_sync(SSEEvent(
                type="data.calibration_complete",
                payload={
                    "sloId": slo.id if slo else None,
                    "knowledgeState": {
                        f: s.model_dump(by_alias=True) for f, s in state.items()
                    } if state else {},
                },
            ))

            return {"content": [{"type": "text", "text": f"Calibration complete: {args['summary']}"}]}

        # =================================================================
        # Stage 3: Diagnostic Loop Tools
        # =================================================================

        @tool(
            "mark_diagnostic_question_asked",
            "Mark that a diagnostic question has been asked to the learner. Call this AFTER presenting a diagnostic question, then STOP and WAIT for the learner's response.",
            {"facet": str}
        )
        async def mark_diagnostic_question_asked(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that a diagnostic question was asked - agent should now wait for response."""
            facet = args.get("facet", "unknown")
            agent.phase_context.awaiting_user_input = True

            return {"content": [{"type": "text", "text": f"Diagnostic question (facet: {facet}) presented. STOP and wait for the learner's response before evaluating."}]}

        @tool(
            "record_diagnostic_result",
            "Record the result of a diagnostic round",
            {"facet": str, "result": str, "is_transfer": bool}
        )
        async def record_diagnostic_result(args: dict[str, Any]) -> dict[str, Any]:
            """Record diagnostic round result."""
            facet = args["facet"]
            result = args["result"]  # "pass" or "fail"
            is_transfer = args.get("is_transfer", False)

            # Update counters
            agent.phase_context.increment_round(facet)

            if result == "pass":
                agent.phase_context.record_pass(is_transfer=is_transfer)
            else:
                agent.phase_context.record_fail()

            counters = agent.phase_context.get_current_counters()
            slo = agent.phase_context.get_current_slo()

            agent.emitter.emit_sync(SSEEvent(
                type="data.diagnostic_result",
                payload={
                    "sloId": slo.id if slo else None,
                    "facet": facet,
                    "result": result,
                    "isTransfer": is_transfer,
                    "counters": counters,
                },
            ))

            return {"content": [{"type": "text", "text": f"Round recorded: {facet} {result}. Counters: {counters}"}]}

        @tool(
            "mark_mastery_achieved",
            "Mark that mastery criteria have been met for current SLO",
            {"summary": str}
        )
        async def mark_mastery_achieved(args: dict[str, Any]) -> dict[str, Any]:
            """Signal mastery achieved."""
            slo = agent.phase_context.get_current_slo()
            counters = agent.phase_context.get_current_counters()

            agent.emitter.emit_sync(SSEEvent(
                type="data.mastery_achieved",
                payload={
                    "sloId": slo.id if slo else None,
                    "counters": counters,
                    "summary": args["summary"],
                },
            ))

            return {"content": [{"type": "text", "text": f"Mastery achieved: {args['summary']}"}]}

        # =================================================================
        # Stage 4: SLO Completion Tools
        # =================================================================

        @tool(
            "emit_slo_summary",
            "Emit the completion summary for an SLO. key_breakthroughs should be a newline-separated string.",
            {
                "starting_state": str,
                "ending_state": str,
                "key_breakthroughs": str,  # Newline-separated breakthroughs
                "rounds": int,
                "passes": int,
                "transfer_passes": int,
            }
        )
        async def emit_slo_summary(args: dict[str, Any]) -> dict[str, Any]:
            """Emit SLO completion summary."""
            import re
            slo = agent.phase_context.get_current_slo()

            # Parse key_breakthroughs from string to list
            raw = args.get("key_breakthroughs", "")
            if isinstance(raw, list):
                breakthroughs = raw
            else:
                lines = re.split(r'\n|\\n', raw)
                breakthroughs = [re.sub(r'^[\s\-\*•]+', '', line).strip() for line in lines if line.strip()]

            agent.emitter.emit_sync(SSEEvent(
                type="data.slo_complete",
                payload={
                    "sloId": slo.id if slo else None,
                    "sloStatement": slo.statement if slo else "",
                    "startingState": args["starting_state"],
                    "endingState": args["ending_state"],
                    "keyBreakthroughs": breakthroughs,
                    "rounds": args["rounds"],
                    "passes": args["passes"],
                    "transferPasses": args["transfer_passes"],
                },
            ))

            return {"content": [{"type": "text", "text": f"SLO summary emitted"}]}

        @tool(
            "advance_to_next_slo",
            "Advance to the next SLO in the learning plan",
            {}
        )
        async def advance_to_next_slo(args: dict[str, Any]) -> dict[str, Any]:
            """Advance to next SLO."""
            success = agent.phase_context.advance_to_next_slo()

            if success:
                next_slo = agent.phase_context.get_current_slo()
                agent.emitter.emit_sync(SSEEvent(
                    type="data.slo_transition",
                    payload={
                        "nextSloId": next_slo.id if next_slo else None,
                        "nextSloStatement": next_slo.statement if next_slo else "",
                    },
                ))
                return {"content": [{"type": "text", "text": f"Advanced to next SLO: {next_slo.statement if next_slo else 'none'}"}]}
            else:
                return {"content": [{"type": "text", "text": "No more SLOs remaining"}]}

        @tool(
            "skip_current_slo",
            "Skip the current SLO (learner requested)",
            {"reason": str}
        )
        async def skip_current_slo(args: dict[str, Any]) -> dict[str, Any]:
            """Skip current SLO."""
            slo = agent.phase_context.get_current_slo()
            agent.phase_context.skip_current_slo()

            agent.emitter.emit_sync(SSEEvent(
                type="data.slo_skipped",
                payload={
                    "sloId": slo.id if slo else None,
                    "reason": args["reason"],
                },
            ))

            return {"content": [{"type": "text", "text": f"SLO skipped: {args['reason']}"}]}

        # =================================================================
        # Stage 5: Session Completion Tools
        # =================================================================

        @tool(
            "emit_session_complete",
            "Mark the entire understanding session as complete",
            {"total_rounds": int, "slos_completed": int, "slos_skipped": int}
        )
        async def emit_session_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Emit session completion."""
            agent.emitter.emit_sync(SSEEvent(
                type="data.session_complete",
                payload={
                    "totalRounds": args["total_rounds"],
                    "slosCompleted": args["slos_completed"],
                    "slosSkipped": args["slos_skipped"],
                    "completedSloIds": agent.phase_context.completed_slo_ids,
                    "skippedSloIds": agent.phase_context.skipped_slo_ids,
                },
            ))

            return {"content": [{"type": "text", "text": "Session complete"}]}

        # =================================================================
        # Utility Tools
        # =================================================================

        @tool(
            "get_phase_context",
            "Get context from current or previous phases",
            {"phase_name": str}
        )
        async def get_phase_context(args: dict[str, Any]) -> dict[str, Any]:
            """Retrieve phase context for reference."""
            phase = args["phase_name"].upper()

            if phase == "SLOS":
                slos = [s.model_dump(by_alias=True) for s in agent.phase_context.slos]
                return {"content": [{"type": "text", "text": f"SLOs: {slos}"}]}
            elif phase == "CURRENT_SLO":
                slo = agent.phase_context.get_current_slo()
                counters = agent.phase_context.get_current_counters()
                state = agent.phase_context.get_current_knowledge_state()
                return {"content": [{"type": "text", "text": f"Current SLO: {slo.model_dump(by_alias=True) if slo else None}\nCounters: {counters}\nState: {state}"}]}
            elif phase == "CONFIG":
                return {"content": [{"type": "text", "text": f"Config: pace={agent.phase_context.pace}, style={agent.phase_context.style}, context={agent.phase_context.learner_context}"}]}
            else:
                return {"content": [{"type": "text", "text": f"Unknown phase: {phase}"}]}

        # Create MCP server with all tools
        return create_sdk_mcp_server(
            name="understand-agent",
            version="1.0.0",
            tools=[
                # Stage 0
                emit_knowledge_confidence,
                # Stage 0.5
                emit_session_config,
                # Stage 0.5 (additional)
                mark_config_questions_asked,
                # Stage 1
                emit_topic_type,
                emit_slo,
                mark_slos_presented,
                mark_slos_selected,
                # Stage 2
                mark_probe_question_asked,
                update_facet_status,
                record_probe_result,
                mark_calibration_complete,
                # Stage 3
                mark_diagnostic_question_asked,
                record_diagnostic_result,
                mark_mastery_achieved,
                # Stage 4
                emit_slo_summary,
                advance_to_next_slo,
                skip_current_slo,
                # Stage 5
                emit_session_complete,
                # Utility
                get_phase_context,
            ]
        )

    # =========================================================================
    # Phase Execution using Claude Agent SDK
    # =========================================================================

    async def _execute_phase(
        self,
        phase: UnderstandPhase,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute a single phase using the Claude Agent SDK."""

        yield agent_thinking(f"Executing {phase.value} phase...")

        # Get phase-specific configuration
        visit_count = self.phase_context.get_visit_count(phase)
        prompt = self._get_phase_prompt(phase, visit_count)
        allowed_tools = self._get_allowed_tools(phase)

        # For interactive phases, include the user's response in the prompt
        # (Don't include the original question on the first call)
        is_user_response = message and message != self.journey_brief.original_question
        if is_user_response and phase in [
            UnderstandPhase.CONFIGURE,
            UnderstandPhase.CLASSIFY,
            UnderstandPhase.CALIBRATE,
            UnderstandPhase.DIAGNOSE,
        ]:
            prompt += f"\n\n**Learner's Response:** {message}"

        # Log phase execution start
        if self._logger:
            log_prompt(self._logger, phase.value, prompt)
            self._logger.debug(f"Allowed tools: {allowed_tools}")

        # Build SDK options
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=allowed_tools,
            mcp_servers={"understand": self._mcp_server},
        )

        # Run the agent
        msg_count = 0
        try:
            async with ClaudeSDKClient(options=options) as client:
                await client.query(prompt)

                async for msg in client.receive_response():
                    msg_count += 1

                    if isinstance(msg, AssistantMessage):
                        # Log the LLM response
                        if self._logger:
                            log_llm_response(self._logger, msg, msg_count)

                        for block in msg.content:
                            if isinstance(block, TextBlock):
                                # Stream text to frontend
                                yield agent_speaking(block.text)
                            elif isinstance(block, ToolUseBlock):
                                # Log tool call
                                if self._logger:
                                    self._logger.debug(f"TOOL CALL: {block.name}")
                                    if hasattr(block, 'input'):
                                        import json
                                        try:
                                            self._logger.debug(f"  Input: {json.dumps(block.input, indent=2)[:500]}")
                                        except:
                                            self._logger.debug(f"  Input: {block.input}")

                    elif isinstance(msg, ResultMessage):
                        # Log phase completion
                        if self._logger:
                            self._logger.info(f"Phase {phase.value} complete after {msg_count} messages")
                        break

        except Exception as e:
            if self._logger:
                log_error(self._logger, e, f"during phase {phase.value}")
            raise

        # Handle checkpoints if needed
        await self._handle_phase_checkpoint(phase)

    async def _handle_phase_checkpoint(self, phase: UnderstandPhase) -> None:
        """Handle checkpoint after phase execution."""

        # Skip checkpoints when awaiting user input - the user hasn't responded yet
        # so we shouldn't auto-approve any state changes
        if self.phase_context.awaiting_user_input:
            return

        if phase == UnderstandPhase.CONFIGURE and not self.phase_context.session_configured:
            checkpoint = Checkpoint(
                id="configure_approval",
                message=CONFIGURE_CHECKPOINT_MESSAGE.format(
                    pace=self.phase_context.pace,
                    style=self.phase_context.style,
                    learner_context=self.phase_context.learner_context or "(none provided)",
                ),
                options=["Ready to begin", "Adjust preferences"],
            )
            response = await self._handle_checkpoint(checkpoint)
            if response.approved:
                self.phase_context.session_configured = True

        elif phase == UnderstandPhase.CLASSIFY and not self.phase_context.slos_confirmed:
            slo_list = "\n".join([
                f"{i+1}. {s.statement}" for i, s in enumerate(self.phase_context.slos)
            ])
            checkpoint = Checkpoint(
                id="classify_approval",
                message=CLASSIFY_CHECKPOINT_MESSAGE.format(
                    slo_list=slo_list,
                    slo_count=len(self.phase_context.slos),
                    estimated_rounds=len(self.phase_context.slos) * 10,
                ),
                options=["Proceed with plan", "Adjust SLOs"],
            )
            response = await self._handle_checkpoint(checkpoint)
            if response.approved:
                # Select all SLOs by default
                self.phase_context.selected_slo_ids = [s.id for s in self.phase_context.slos]
                self.phase_context.slos_confirmed = True

        elif phase == UnderstandPhase.CALIBRATE and self.phase_context.current_slo_calibrated:
            state = self.phase_context.get_current_knowledge_state()
            facet_table = "\n".join([
                f"| {f.capitalize()} | {s.status} | {s.evidence[:50]}... |"
                for f, s in (state or {}).items()
            ])
            weakest = [f for f, s in (state or {}).items() if s.status in ["missing", "shaky"]]

            checkpoint = Checkpoint(
                id="calibrate_approval",
                message=CALIBRATE_CHECKPOINT_MESSAGE.format(
                    facet_table=facet_table,
                    weakest_facets=", ".join(weakest) if weakest else "none identified",
                ),
                options=["Start diagnostic rounds", "Re-calibrate"],
            )
            await self._handle_checkpoint(checkpoint)

    def _get_allowed_tools(self, phase: UnderstandPhase) -> list[str]:
        """Get allowed tools for a phase."""
        base_tools = [
            "mcp__understand__get_phase_context",
        ]

        phase_tools = {
            UnderstandPhase.SELF_ASSESS: [
                "WebSearch",
                "mcp__understand__emit_knowledge_confidence",
            ],
            UnderstandPhase.CONFIGURE: [
                "mcp__understand__emit_session_config",
                "mcp__understand__mark_config_questions_asked",
            ],
            UnderstandPhase.CLASSIFY: [
                "mcp__understand__emit_topic_type",
                "mcp__understand__emit_slo",
                "mcp__understand__mark_slos_presented",
                "mcp__understand__mark_slos_selected",
            ],
            UnderstandPhase.CALIBRATE: [
                "mcp__understand__mark_probe_question_asked",
                "mcp__understand__update_facet_status",
                "mcp__understand__record_probe_result",
                "mcp__understand__mark_calibration_complete",
            ],
            UnderstandPhase.DIAGNOSE: [
                "WebSearch",
                "mcp__understand__mark_diagnostic_question_asked",
                "mcp__understand__update_facet_status",
                "mcp__understand__record_diagnostic_result",
                "mcp__understand__mark_mastery_achieved",
            ],
            UnderstandPhase.SLO_COMPLETE: [
                "mcp__understand__emit_slo_summary",
                "mcp__understand__advance_to_next_slo",
                "mcp__understand__skip_current_slo",
            ],
            UnderstandPhase.COMPLETE: [
                "mcp__understand__emit_session_complete",
            ],
        }

        return base_tools + phase_tools.get(phase, [])

    # =========================================================================
    # Prompt Generation
    # =========================================================================

    def _get_phase_prompt(self, phase: UnderstandPhase, visit_count: int) -> str:
        """Get the prompt for a phase (initial or re-entry)."""

        if phase == UnderstandPhase.SELF_ASSESS:
            return SELF_ASSESS_PROMPT.format(
                topic=self.journey_brief.original_question,
            )

        elif phase == UnderstandPhase.CONFIGURE:
            # Check if we're resuming mid-configuration (questions asked, waiting for response)
            print(f"[DEBUG] _get_phase_prompt CONFIGURE: config_questions_asked={self.phase_context.config_questions_asked}, session_configured={self.phase_context.session_configured}")
            if self.phase_context.config_questions_asked and not self.phase_context.session_configured:
                # User has responded to config questions - use resume prompt
                print(f"[DEBUG] Returning CONFIGURE_RESUME_PROMPT")
                return CONFIGURE_RESUME_PROMPT
            else:
                # First time - present config options
                print(f"[DEBUG] Returning CONFIGURE_PROMPT (initial)")
                return CONFIGURE_PROMPT

        elif phase == UnderstandPhase.CLASSIFY:
            # Check if we're resuming mid-classification (SLOs presented, waiting for selection)
            if self.phase_context.slos_presented and not self.phase_context.slos_confirmed:
                # User has responded to SLO presentation - use resume prompt
                slo_list = "\n".join([
                    f"- {s.statement} (frame: {s.frame})"
                    for s in self.phase_context.slos
                ])
                return CLASSIFY_RESUME_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    slo_list=slo_list if slo_list else "(no SLOs generated yet)",
                )
            else:
                # First time - generate and present SLOs
                return CLASSIFY_INITIAL_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    learner_context=self.phase_context.learner_context or "(none provided)",
                )

        elif phase == UnderstandPhase.CALIBRATE:
            slo = self.phase_context.get_current_slo()
            probe_results = self.phase_context.get_current_probe_results()
            remaining = self.phase_context.get_remaining_probes()

            # Check if we're resuming mid-calibration (some probes done, some remaining)
            if probe_results and remaining:
                # Format probe progress for display
                probe_progress = "\n".join([
                    f"- {probe}: {result}" for probe, result in probe_results.items()
                ])
                return CALIBRATE_RESUME_PROMPT.format(
                    slo_statement=slo.statement if slo else "",
                    slo_frame=slo.frame if slo else "",
                    probe_progress=probe_progress if probe_progress else "(none yet)",
                    remaining_probes=", ".join(remaining),
                )
            elif visit_count <= 1:
                # First time entering calibration for this SLO
                return CALIBRATE_INITIAL_PROMPT.format(
                    slo_statement=slo.statement if slo else "",
                    slo_frame=slo.frame if slo else "",
                )
            else:
                # Re-entry means new SLO (previous SLO completed)
                prev_slo_id = self.phase_context.completed_slo_ids[-1] if self.phase_context.completed_slo_ids else None
                prev_slo = next((s for s in self.phase_context.slos if s.id == prev_slo_id), None)
                return CALIBRATE_REENTRY_PROMPT.format(
                    previous_slo=prev_slo.statement if prev_slo else "(previous SLO)",
                    slo_statement=slo.statement if slo else "",
                    slo_frame=slo.frame if slo else "",
                )

        elif phase == UnderstandPhase.DIAGNOSE:
            slo = self.phase_context.get_current_slo()
            state = self.phase_context.get_current_knowledge_state()
            counters = self.phase_context.get_current_counters()

            if visit_count <= 1:
                return DIAGNOSE_INITIAL_PROMPT.format(
                    slo_statement=slo.statement if slo else "",
                    knowledge_state=self._format_knowledge_state(state),
                    counters=self._format_counters(counters),
                )
            else:
                return DIAGNOSE_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger or "",
                    backward_trigger_detail=self.phase_context.backward_trigger_detail or "",
                    slo_statement=slo.statement if slo else "",
                    knowledge_state=self._format_knowledge_state(state),
                    counters=self._format_counters(counters),
                )

        elif phase == UnderstandPhase.SLO_COMPLETE:
            slo = self.phase_context.get_current_slo()
            state = self.phase_context.get_current_knowledge_state()
            counters = self.phase_context.get_current_counters()

            return SLO_COMPLETE_PROMPT.format(
                slo_statement=slo.statement if slo else "",
                knowledge_state=self._format_knowledge_state(state),
                counters=self._format_counters(counters),
            )

        elif phase == UnderstandPhase.COMPLETE:
            return COMPLETE_PROMPT.format(
                topic=self.journey_brief.original_question,
                completed_count=len(self.phase_context.completed_slo_ids),
                total_count=len(self.phase_context.selected_slo_ids),
                skipped_slos=", ".join(self.phase_context.skipped_slo_ids) or "none",
            )

        return ""

    def _get_awaiting_input_prompt(self) -> str:
        """Get a phase-specific prompt for when awaiting user input."""
        phase = self.current_phase

        if phase == UnderstandPhase.CONFIGURE:
            return "Please share your learning preferences (pace, style, and any relevant context)."

        elif phase == UnderstandPhase.CLASSIFY:
            slo_count = len(self.phase_context.slos)
            return f"I've generated {slo_count} learning objectives. Which would you like to explore? (Type 'all' for all, or specify which ones)"

        elif phase == UnderstandPhase.CALIBRATE:
            remaining = self.phase_context.get_remaining_probes()
            if remaining:
                return f"Please respond to the probe question above. ({len(remaining)} probes remaining)"
            return "Please respond to my question above."

        elif phase == UnderstandPhase.DIAGNOSE:
            return "Please respond to the diagnostic question above."

        return "I'm waiting for your response to continue."

    # =========================================================================
    # Transition Evaluation
    # =========================================================================

    def _evaluate_transition_condition(self, transition: PhaseTransition) -> bool:
        """Check if a specific transition's condition is met."""

        condition = transition.condition

        # Forward transitions
        if condition == "knowledge_confidence_established":
            return self.phase_context.knowledge_confidence in ["HIGH", "MEDIUM"]

        elif condition == "session_preferences_set":
            return self.phase_context.session_configured

        elif condition == "slos_selected":
            return self.phase_context.slos_confirmed and len(self.phase_context.selected_slo_ids) > 0

        elif condition == "calibration_complete":
            return self.phase_context.current_slo_calibrated

        elif condition == "mastery_criteria_met":
            return self.phase_context.is_mastery_criteria_met()

        elif condition == "next_slo_available":
            return self.phase_context.has_next_slo()

        elif condition == "all_slos_complete":
            return not self.phase_context.has_next_slo()

        # Backward transitions
        elif condition == "slo_skipped_needs_recalibration":
            # If an SLO was just skipped and there's a next one
            return False  # Handled by advance_to_next_slo

        return False

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_knowledge_state(self, state: Optional[dict[str, KnowledgeStateFacet]]) -> str:
        """Format knowledge state for prompt."""
        if not state:
            return "No knowledge state available"

        lines = []
        for facet, facet_state in state.items():
            lines.append(f"- {facet}: {facet_state.status} (evidence: {facet_state.evidence[:50]}...)")
        return "\n".join(lines)

    def _format_counters(self, counters: Optional[dict]) -> str:
        """Format counters for prompt."""
        if not counters:
            return "No counters available"

        return (
            f"total_rounds: {counters.get('total_rounds', 0)}, "
            f"consecutive_passes: {counters.get('consecutive_passes', 0)}, "
            f"transfer_passes: {counters.get('transfer_passes', 0)}, "
            f"facet_rounds: {counters.get('facet_rounds', {})}"
        )

    # =========================================================================
    # Completion
    # =========================================================================

    def _generate_completion_summary(self) -> str:
        """Generate a summary when understanding session completes."""
        total_rounds = sum(
            c.get("total_rounds", 0)
            for c in self.phase_context.slo_counters.values()
        )
        return (
            f"Understanding session complete. "
            f"Completed {len(self.phase_context.completed_slo_ids)} of "
            f"{len(self.phase_context.selected_slo_ids)} SLOs. "
            f"Total rounds: {total_rounds}. "
            f"Skipped: {len(self.phase_context.skipped_slo_ids)}."
        )

    # =========================================================================
    # State Persistence
    # =========================================================================

    def _serialize_phase_context(self) -> dict:
        """Serialize phase context to dict."""
        return self.phase_context.to_dict()

    def _restore_phase_context(self, state: dict) -> None:
        """Restore phase context from state."""
        self.phase_context = UnderstandPhaseContext.from_dict(state)

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
        # Reinitialize logger for restored agent
        self._logger = get_agent_logger(self.session.id, self.agent_type)
        self._logger.info(f"Agent restored from state: phase={self.current_phase}")
