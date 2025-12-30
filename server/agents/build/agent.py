"""
Build Agent Implementation.

Implements the Constructivist tutoring system using the Claude Agent SDK
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
    BuildModeData,
)
from server.api.streaming import SSEEvent, agent_thinking, agent_speaking
from server.agents.base import (
    BaseForgeAgent,
    PhaseTransition,
    Checkpoint,
    CheckpointResponse,
)
from .phases import (
    BuildPhase,
    BuildPhaseContext,
    BUILD_TRANSITIONS,
    Anchor,
    ConstructionSLO,
    ConstructionRound,
)
from .prompts import (
    SYSTEM_PROMPT,
    ANCHOR_DISCOVERY_PROMPT,
    ANCHOR_DISCOVERY_RESUME_PROMPT,
    CLASSIFY_PROMPT,
    CLASSIFY_RESUME_PROMPT,
    SEQUENCE_DESIGN_PROMPT,
    CONSTRUCTION_INITIAL_PROMPT,
    CONSTRUCTION_RESUME_PROMPT,
    CONSTRUCTION_REENTRY_PROMPT,
    SURRENDER_RECOVERY_PROMPT,
    SLO_COMPLETE_PROMPT,
    CONSOLIDATION_PROMPT,
    COMPLETE_PROMPT,
    ANCHOR_CHECKPOINT_MESSAGE,
    CLASSIFY_CHECKPOINT_MESSAGE,
)


class BuildAgent(BaseForgeAgent[BuildPhase, BuildPhaseContext]):
    """
    Build Agent for Knowledge Forge.

    Implements the Constructivist tutoring system using the Claude Agent SDK:
    ANCHOR_DISCOVERY → CLASSIFY → SEQUENCE_DESIGN → CONSTRUCTION → SLO_COMPLETE → CONSOLIDATION → COMPLETE

    With transitions for:
    - Moving to next SLO after construction
    - Returning to anchor discovery if anchor gap detected
    """

    # =========================================================================
    # Abstract Property Implementations
    # =========================================================================

    @property
    def Phase(self) -> type[BuildPhase]:
        return BuildPhase

    @property
    def phase_transitions(self) -> list[PhaseTransition]:
        return BUILD_TRANSITIONS

    @property
    def initial_phase(self) -> BuildPhase:
        return BuildPhase.ANCHOR_DISCOVERY

    @property
    def complete_phase(self) -> BuildPhase:
        return BuildPhase.COMPLETE

    @property
    def agent_type(self) -> str:
        return "build"

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
        """Initialize the agent for a new build journey."""
        await super().initialize(journey_brief)

        # Initialize mode data if not present
        if self.session.build_data is None:
            self.session.build_data = BuildModeData()

        # Create MCP server with custom tools
        self._mcp_server = self._create_mcp_server()

    def _create_phase_context(self) -> BuildPhaseContext:
        """Create the initial phase context."""
        return BuildPhaseContext()

    # =========================================================================
    # MCP Server with Custom Tools
    # =========================================================================

    def _create_mcp_server(self):
        """
        Create an MCP server with custom tools for build phases.

        Tools emit SSE events and update phase context state.
        """
        agent = self

        # Helper to parse list strings from LLM (handles various formats)
        def _parse_list_string(s: Any) -> list[str]:
            """Parse a string into a list. Handles newlines, markdown bullets, JSON arrays."""
            if isinstance(s, list):
                return s
            if not isinstance(s, str):
                return []
            import json
            import re
            s = s.strip()
            # Try JSON array first
            if s.startswith('['):
                try:
                    return json.loads(s)
                except:
                    pass
            # Split by newlines (including escaped newlines)
            lines = re.split(r'\n|\\n', s)
            result = []
            for line in lines:
                # Remove markdown bullet points, dashes, asterisks
                line = re.sub(r'^[\s\-\*•]+', '', line).strip()
                if line:
                    result.append(line)
            return result

        # =================================================================
        # Phase 0: Anchor Discovery Tools
        # =================================================================

        @tool(
            "emit_anchor",
            "Record a discovered anchor from learner's existing knowledge",
            {"description": str, "strength": str, "evidence": str}
        )
        async def emit_anchor(args: dict[str, Any]) -> dict[str, Any]:
            """Record an anchor."""
            anchor = Anchor(
                id=str(uuid.uuid4()),
                description=args["description"],
                strength=args["strength"],
                evidence=args["evidence"],
            )
            agent.phase_context.add_anchor(anchor)

            agent.emitter.emit_sync(SSEEvent(
                type="data.anchor.added",
                payload={
                    "id": anchor.id,
                    "description": anchor.description,
                    "strength": anchor.strength,
                    "evidence": anchor.evidence,
                },
            ))

            return {"content": [{"type": "text", "text": f"Anchor recorded: {anchor.description} ({anchor.strength})"}]}

        @tool(
            "set_primary_anchor",
            "Set the primary anchor to build from",
            {"anchor_id": str}
        )
        async def set_primary_anchor(args: dict[str, Any]) -> dict[str, Any]:
            """Set primary anchor."""
            agent.phase_context.primary_anchor_id = args["anchor_id"]

            agent.emitter.emit_sync(SSEEvent(
                type="data.primary_anchor_set",
                payload={"anchorId": args["anchor_id"]},
            ))

            return {"content": [{"type": "text", "text": f"Primary anchor set to {args['anchor_id']}"}]}

        @tool(
            "mark_anchor_questions_asked",
            "Mark that anchor discovery questions have been presented to the learner. Call this AFTER asking about their experiences, then STOP and WAIT for their response.",
            {}
        )
        async def mark_anchor_questions_asked(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that anchor questions were asked - agent should now wait for response."""
            agent.phase_context.anchor_questions_asked = True
            # Block transitions until user responds
            agent.phase_context.awaiting_user_input = True

            return {"content": [{"type": "text", "text": "Anchor questions presented. STOP and wait for the learner's response about their experiences before proceeding."}]}

        @tool(
            "mark_anchors_confirmed",
            "Mark that anchors have been confirmed by learner. Only call this AFTER the learner has responded.",
            {"summary": str}
        )
        async def mark_anchors_confirmed(args: dict[str, Any]) -> dict[str, Any]:
            """Confirm anchors."""
            # Guard: Don't allow confirmation before user has responded
            if agent.phase_context.awaiting_user_input:
                return {"content": [{"type": "text", "text": "ERROR: Cannot confirm anchors while waiting for user input. Wait for the learner to respond first."}]}

            agent.phase_context.anchors_confirmed = True

            agent.emitter.emit_sync(SSEEvent(
                type="data.anchors_confirmed",
                payload={"summary": args["summary"]},
            ))

            return {"content": [{"type": "text", "text": "Anchors confirmed"}]}

        # =================================================================
        # Phase 1: Classification Tools
        # =================================================================

        @tool(
            "emit_topic_type",
            "Record the topic classification type",
            {"topic_type": str}
        )
        async def emit_topic_type(args: dict[str, Any]) -> dict[str, Any]:
            """Record topic type."""
            agent.phase_context.topic_type = args["topic_type"]

            agent.emitter.emit_sync(SSEEvent(
                type="data.topic_type",
                payload={"topicType": args["topic_type"]},
            ))

            return {"content": [{"type": "text", "text": f"Topic type: {args['topic_type']}"}]}

        @tool(
            "emit_construction_slo",
            "Add a construction SLO. For in_scope and out_of_scope, provide newline-separated bullet points.",
            {
                "statement": str,
                "frame": str,
                "anchor_id": str,
                "in_scope": str,  # Newline-separated bullet points
                "out_of_scope": str,  # Newline-separated bullet points
                "code_mode_likely": bool,
                "estimated_rounds": int,
            }
        )
        async def emit_construction_slo(args: dict[str, Any]) -> dict[str, Any]:
            """Add a construction SLO."""
            in_scope = _parse_list_string(args.get("in_scope", ""))
            out_of_scope = _parse_list_string(args.get("out_of_scope", ""))

            slo = ConstructionSLO(
                id=str(uuid.uuid4()),
                statement=args["statement"],
                frame=args["frame"],
                anchor_id=args["anchor_id"],
                in_scope=in_scope,
                out_of_scope=out_of_scope,
                code_mode_likely=args.get("code_mode_likely", False),
                estimated_rounds=args.get("estimated_rounds", 5),
            )
            agent.phase_context.add_slo(slo)

            agent.emitter.emit_sync(SSEEvent(
                type="data.construction_slo.added",
                payload={
                    "id": slo.id,
                    "statement": slo.statement,
                    "frame": slo.frame,
                    "anchorId": slo.anchor_id,
                    "inScope": slo.in_scope,
                    "outOfScope": slo.out_of_scope,
                    "codeModeLikely": slo.code_mode_likely,
                    "estimatedRounds": slo.estimated_rounds,
                },
            ))

            return {"content": [{"type": "text", "text": f"Construction SLO added: {slo.statement[:50]}..."}]}

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
        # Phase 2: Sequence Design Tools
        # =================================================================

        @tool(
            "emit_construction_sequence",
            "Record the construction sequence for an SLO. scaffolds should be newline-separated.",
            {"slo_id": str, "anchor": str, "bridge": str, "target": str, "scaffolds": str}
        )
        async def emit_construction_sequence(args: dict[str, Any]) -> dict[str, Any]:
            """Record construction sequence."""
            scaffolds = _parse_list_string(args.get("scaffolds", ""))

            agent.phase_context.construction_sequences[args["slo_id"]] = {
                "anchor": args["anchor"],
                "bridge": args["bridge"],
                "target": args["target"],
                "scaffolds": scaffolds,
            }

            agent.emitter.emit_sync(SSEEvent(
                type="data.construction_sequence",
                payload={
                    "sloId": args["slo_id"],
                    "sequence": agent.phase_context.construction_sequences[args["slo_id"]],
                },
            ))

            return {"content": [{"type": "text", "text": f"Construction sequence recorded for SLO {args['slo_id']}"}]}

        @tool(
            "mark_sequences_designed",
            "Mark that all construction sequences are designed",
            {"summary": str}
        )
        async def mark_sequences_designed(args: dict[str, Any]) -> dict[str, Any]:
            """Mark sequences complete."""
            agent.phase_context.sequences_designed = True

            agent.emitter.emit_sync(SSEEvent(
                type="data.sequences_designed",
                payload={"summary": args["summary"]},
            ))

            return {"content": [{"type": "text", "text": "Construction sequences designed"}]}

        # =================================================================
        # Phase 3: Construction Loop Tools
        # =================================================================

        @tool(
            "mark_scaffold_delivered",
            "Mark that a scaffold (question/scenario) has been delivered to the learner. Call this AFTER presenting a scaffold, then STOP and WAIT for the learner's response.",
            {"scaffold_type": str}
        )
        async def mark_scaffold_delivered(args: dict[str, Any]) -> dict[str, Any]:
            """Mark that a scaffold was delivered - agent should now wait for response."""
            scaffold_type = args.get("scaffold_type", "question")
            agent.phase_context.awaiting_user_input = True

            return {"content": [{"type": "text", "text": f"Scaffold ({scaffold_type}) delivered. STOP and wait for the learner's response before evaluating."}]}

        @tool(
            "record_construction_round",
            "Record a construction round AFTER evaluating the learner's response. Do not call this until the learner has responded.",
            {
                "scaffold_type": str,
                "scaffold_content": str,
                "learner_response": str,
                "outcome": str,
                "notes": str,
            }
        )
        async def record_construction_round(args: dict[str, Any]) -> dict[str, Any]:
            """Record construction round."""
            rounds = agent.phase_context.get_current_rounds()
            round_data = ConstructionRound(
                round_num=len(rounds) + 1,
                scaffold_type=args["scaffold_type"],
                scaffold_content=args["scaffold_content"],
                learner_response=args["learner_response"],
                outcome=args["outcome"],
                notes=args.get("notes", ""),
            )
            agent.phase_context.add_construction_round(round_data)

            # Adjust scaffold based on outcome
            if args["outcome"] == "constructed":
                agent.phase_context.decrease_scaffold()
                agent.phase_context.exit_special_mode()
            elif args["outcome"] in ["stuck", "surrendered"]:
                agent.phase_context.increase_scaffold()
                if args["outcome"] == "surrendered":
                    agent.phase_context.enter_surrender_recovery()

            slo = agent.phase_context.get_current_slo()
            agent.emitter.emit_sync(SSEEvent(
                type="data.construction_round",
                payload={
                    "sloId": slo.id if slo else None,
                    "roundNum": round_data.round_num,
                    "scaffoldType": round_data.scaffold_type,
                    "outcome": round_data.outcome,
                    "scaffoldLevel": agent.phase_context.current_scaffold_level,
                    "mode": agent.phase_context.current_mode,
                },
            ))

            return {"content": [{"type": "text", "text": f"Round {round_data.round_num}: {round_data.outcome}"}]}

        @tool(
            "set_scaffold_level",
            "Set the current scaffold level",
            {"level": str}
        )
        async def set_scaffold_level(args: dict[str, Any]) -> dict[str, Any]:
            """Set scaffold level."""
            agent.phase_context.current_scaffold_level = args["level"]

            agent.emitter.emit_sync(SSEEvent(
                type="data.scaffold_level",
                payload={"level": args["level"]},
            ))

            return {"content": [{"type": "text", "text": f"Scaffold level set to {args['level']}"}]}

        @tool(
            "enter_code_mode",
            "Enter code mode for concrete examples",
            {"reason": str}
        )
        async def enter_code_mode(args: dict[str, Any]) -> dict[str, Any]:
            """Enter code mode."""
            agent.phase_context.enter_code_mode()

            agent.emitter.emit_sync(SSEEvent(
                type="data.mode_change",
                payload={"mode": "code", "reason": args["reason"]},
            ))

            return {"content": [{"type": "text", "text": f"Entered code mode: {args['reason']}"}]}

        @tool(
            "emit_surrender_strategy",
            "Record the surrender recovery strategy being used",
            {"strategy": str, "description": str}
        )
        async def emit_surrender_strategy(args: dict[str, Any]) -> dict[str, Any]:
            """Record surrender strategy."""
            agent.phase_context.effective_strategies.append(args["strategy"])

            agent.emitter.emit_sync(SSEEvent(
                type="data.surrender_strategy",
                payload={"strategy": args["strategy"], "description": args["description"]},
            ))

            return {"content": [{"type": "text", "text": f"Using strategy: {args['strategy']}"}]}

        @tool(
            "flag_anchor_gap",
            "Flag that an anchor gap was detected - need to discover new anchor",
            {"gap_description": str}
        )
        async def flag_anchor_gap(args: dict[str, Any]) -> dict[str, Any]:
            """Flag anchor gap for backward transition."""
            agent.phase_context.backward_trigger = "anchor_gap_detected"
            agent.phase_context.backward_trigger_detail = args["gap_description"]

            return {"content": [{"type": "text", "text": f"Anchor gap flagged: {args['gap_description']}"}]}

        @tool(
            "mark_construction_verified",
            "Mark that construction has been verified for current SLO",
            {"verification_summary": str}
        )
        async def mark_construction_verified(args: dict[str, Any]) -> dict[str, Any]:
            """Mark construction verified."""
            agent.phase_context.mark_current_constructed()

            slo = agent.phase_context.get_current_slo()
            agent.emitter.emit_sync(SSEEvent(
                type="data.construction_verified",
                payload={
                    "sloId": slo.id if slo else None,
                    "summary": args["verification_summary"],
                },
            ))

            return {"content": [{"type": "text", "text": "Construction verified"}]}

        # =================================================================
        # Phase 4: SLO Completion Tools
        # =================================================================

        @tool(
            "emit_slo_summary",
            "Emit completion summary for an SLO. effective_scaffolds and key_moments should be newline-separated.",
            {"rounds": int, "surrenders": int, "effective_scaffolds": str, "key_moments": str}
        )
        async def emit_slo_summary(args: dict[str, Any]) -> dict[str, Any]:
            """Emit SLO summary."""
            slo = agent.phase_context.get_current_slo()
            effective_scaffolds = _parse_list_string(args.get("effective_scaffolds", ""))
            key_moments = _parse_list_string(args.get("key_moments", ""))

            agent.emitter.emit_sync(SSEEvent(
                type="data.slo_complete",
                payload={
                    "sloId": slo.id if slo else None,
                    "statement": slo.statement if slo else "",
                    "rounds": args["rounds"],
                    "surrenders": args["surrenders"],
                    "effectiveScaffolds": effective_scaffolds,
                    "keyMoments": key_moments,
                },
            ))

            return {"content": [{"type": "text", "text": "SLO summary emitted"}]}

        @tool(
            "advance_to_next_slo",
            "Advance to the next SLO",
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
                return {"content": [{"type": "text", "text": f"Advanced to next SLO"}]}
            else:
                return {"content": [{"type": "text", "text": "No more SLOs remaining"}]}

        # =================================================================
        # Phase 5: Consolidation Tools
        # =================================================================

        @tool(
            "emit_session_insights",
            "Record session insights from consolidation. All fields should be newline-separated.",
            {"insights": str, "what_worked": str, "what_to_improve": str}
        )
        async def emit_session_insights(args: dict[str, Any]) -> dict[str, Any]:
            """Record session insights."""
            insights = _parse_list_string(args.get("insights", ""))
            what_worked = _parse_list_string(args.get("what_worked", ""))
            what_to_improve = _parse_list_string(args.get("what_to_improve", ""))

            agent.phase_context.session_insights = insights

            agent.emitter.emit_sync(SSEEvent(
                type="data.session_insights",
                payload={
                    "insights": insights,
                    "whatWorked": what_worked,
                    "whatToImprove": what_to_improve,
                },
            ))

            return {"content": [{"type": "text", "text": f"{len(insights)} insights recorded"}]}

        @tool(
            "mark_consolidation_complete",
            "Mark session consolidation as complete",
            {"summary": str}
        )
        async def mark_consolidation_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Mark consolidation complete."""
            agent.phase_context.consolidation_complete = True

            agent.emitter.emit_sync(SSEEvent(
                type="data.consolidation_complete",
                payload={"summary": args["summary"]},
            ))

            return {"content": [{"type": "text", "text": "Consolidation complete"}]}

        # =================================================================
        # Phase 6: Completion Tools
        # =================================================================

        @tool(
            "emit_session_complete",
            "Mark the entire build session as complete. concepts_built should be newline-separated.",
            {"total_slos": int, "total_rounds": int, "concepts_built": str}
        )
        async def emit_session_complete(args: dict[str, Any]) -> dict[str, Any]:
            """Emit session completion."""
            concepts_built = _parse_list_string(args.get("concepts_built", ""))

            agent.emitter.emit_sync(SSEEvent(
                type="data.session_complete",
                payload={
                    "totalSlos": args["total_slos"],
                    "totalRounds": args["total_rounds"],
                    "conceptsBuilt": concepts_built,
                    "completedSloIds": agent.phase_context.completed_slo_ids,
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
            """Retrieve phase context."""
            phase = args["phase_name"].upper()

            if phase == "ANCHORS":
                anchors = [{"id": a.id, "description": a.description, "strength": a.strength} for a in agent.phase_context.anchors]
                return {"content": [{"type": "text", "text": f"Anchors: {anchors}"}]}
            elif phase == "SLOS":
                slos = [{"id": s.id, "statement": s.statement, "frame": s.frame} for s in agent.phase_context.slos]
                return {"content": [{"type": "text", "text": f"SLOs: {slos}"}]}
            elif phase == "CURRENT_SLO":
                slo = agent.phase_context.get_current_slo()
                rounds = agent.phase_context.get_current_rounds()
                return {"content": [{"type": "text", "text": f"Current SLO: {slo}\nRounds: {len(rounds)}\nScaffold: {agent.phase_context.current_scaffold_level}\nMode: {agent.phase_context.current_mode}"}]}
            else:
                return {"content": [{"type": "text", "text": f"Unknown phase: {phase}"}]}

        # Create MCP server with all tools
        return create_sdk_mcp_server(
            name="build-agent",
            version="1.0.0",
            tools=[
                # Phase 0
                emit_anchor,
                set_primary_anchor,
                mark_anchor_questions_asked,
                mark_anchors_confirmed,
                # Phase 1
                emit_topic_type,
                emit_construction_slo,
                mark_slos_presented,
                mark_slos_selected,
                # Phase 2
                emit_construction_sequence,
                mark_sequences_designed,
                # Phase 3
                mark_scaffold_delivered,
                record_construction_round,
                set_scaffold_level,
                enter_code_mode,
                emit_surrender_strategy,
                flag_anchor_gap,
                mark_construction_verified,
                # Phase 4
                emit_slo_summary,
                advance_to_next_slo,
                # Phase 5
                emit_session_insights,
                mark_consolidation_complete,
                # Phase 6
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
        phase: BuildPhase,
        message: str,
        context: dict,
    ) -> AsyncGenerator[SSEEvent, None]:
        """Execute a single phase using the Claude Agent SDK."""

        yield agent_thinking(f"Executing {phase.value} phase...")

        visit_count = self.phase_context.get_visit_count(phase)
        prompt = self._get_phase_prompt(phase, visit_count)
        allowed_tools = self._get_allowed_tools(phase)

        # For interactive phases, include the user's response in the prompt
        is_user_response = message and message != self.journey_brief.original_question
        if is_user_response and phase in [
            BuildPhase.ANCHOR_DISCOVERY,
            BuildPhase.CLASSIFY,
            BuildPhase.CONSTRUCTION,
        ]:
            prompt += f"\n\n**Learner's Response:** {message}"

        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=allowed_tools,
            mcp_servers={"build": self._mcp_server},
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            yield agent_speaking(block.text)
                        elif isinstance(block, ToolUseBlock):
                            pass

                elif isinstance(msg, ResultMessage):
                    break

        # Handle checkpoints
        await self._handle_phase_checkpoint(phase)

    async def _handle_phase_checkpoint(self, phase: BuildPhase) -> None:
        """Handle checkpoint after phase execution."""

        # Skip checkpoints when awaiting user input - the user hasn't responded yet
        # so we shouldn't auto-approve any state changes
        if self.phase_context.awaiting_user_input:
            return

        if phase == BuildPhase.ANCHOR_DISCOVERY and self.phase_context.anchors_confirmed:
            primary = self.phase_context.get_anchor(self.phase_context.primary_anchor_id)
            anchor_list = "\n".join([
                f"- {a.description} ({a.strength})" for a in self.phase_context.anchors
            ])
            checkpoint = Checkpoint(
                id="anchor_approval",
                message=ANCHOR_CHECKPOINT_MESSAGE.format(
                    anchor_list=anchor_list,
                    primary_anchor=primary.description if primary else "(none)",
                ),
                options=["Ready to proceed", "Explore more anchors"],
            )
            await self._handle_checkpoint(checkpoint)

        elif phase == BuildPhase.CLASSIFY and self.phase_context.slos_confirmed:
            slo_list = "\n".join([
                f"{i+1}. {s.statement} (connects to: {self.phase_context.get_anchor(s.anchor_id).description if self.phase_context.get_anchor(s.anchor_id) else 'unknown'})"
                for i, s in enumerate(self.phase_context.slos)
                if s.id in self.phase_context.selected_slo_ids
            ])
            estimated = sum(s.estimated_rounds for s in self.phase_context.slos if s.id in self.phase_context.selected_slo_ids)
            checkpoint = Checkpoint(
                id="classify_approval",
                message=CLASSIFY_CHECKPOINT_MESSAGE.format(
                    slo_list=slo_list,
                    estimated_rounds=estimated,
                ),
                options=["Start building", "Adjust SLOs"],
            )
            await self._handle_checkpoint(checkpoint)

    def _get_allowed_tools(self, phase: BuildPhase) -> list[str]:
        """Get allowed tools for a phase."""
        base_tools = ["mcp__build__get_phase_context"]

        phase_tools = {
            BuildPhase.ANCHOR_DISCOVERY: [
                "mcp__build__emit_anchor",
                "mcp__build__set_primary_anchor",
                "mcp__build__mark_anchor_questions_asked",
                "mcp__build__mark_anchors_confirmed",
            ],
            BuildPhase.CLASSIFY: [
                "mcp__build__emit_topic_type",
                "mcp__build__emit_construction_slo",
                "mcp__build__mark_slos_presented",
                "mcp__build__mark_slos_selected",
            ],
            BuildPhase.SEQUENCE_DESIGN: [
                "mcp__build__emit_construction_sequence",
                "mcp__build__mark_sequences_designed",
            ],
            BuildPhase.CONSTRUCTION: [
                "WebSearch",
                "mcp__build__mark_scaffold_delivered",
                "mcp__build__record_construction_round",
                "mcp__build__set_scaffold_level",
                "mcp__build__enter_code_mode",
                "mcp__build__emit_surrender_strategy",
                "mcp__build__flag_anchor_gap",
                "mcp__build__mark_construction_verified",
            ],
            BuildPhase.SLO_COMPLETE: [
                "mcp__build__emit_slo_summary",
                "mcp__build__advance_to_next_slo",
            ],
            BuildPhase.CONSOLIDATION: [
                "mcp__build__emit_session_insights",
                "mcp__build__mark_consolidation_complete",
            ],
            BuildPhase.COMPLETE: [
                "mcp__build__emit_session_complete",
            ],
        }

        return base_tools + phase_tools.get(phase, [])

    # =========================================================================
    # Prompt Generation
    # =========================================================================

    def _get_phase_prompt(self, phase: BuildPhase, visit_count: int) -> str:
        """Get the prompt for a phase."""

        if phase == BuildPhase.ANCHOR_DISCOVERY:
            # Check if we're resuming mid-discovery (questions asked, waiting for response)
            if self.phase_context.anchor_questions_asked and not self.phase_context.anchors_confirmed:
                # User has responded to anchor questions - use resume prompt
                return ANCHOR_DISCOVERY_RESUME_PROMPT.format(
                    existing_anchors=self._format_anchors(),
                )
            else:
                # First time - present anchor discovery questions
                return ANCHOR_DISCOVERY_PROMPT.format(
                    topic=self.journey_brief.original_question,
                )

        elif phase == BuildPhase.CLASSIFY:
            # Check if we're resuming mid-classification (SLOs presented, waiting for selection)
            if self.phase_context.slos_presented and not self.phase_context.slos_confirmed:
                # User has responded to SLO presentation - use resume prompt
                primary = self.phase_context.get_anchor(self.phase_context.primary_anchor_id)
                slo_list = "\n".join([
                    f"- {s.statement} (frame: {s.frame})"
                    for s in self.phase_context.slos
                ])
                return CLASSIFY_RESUME_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    primary_anchor=primary.description if primary else "(none)",
                    slo_list=slo_list if slo_list else "(no SLOs generated yet)",
                )
            else:
                # First time - generate and present SLOs
                primary = self.phase_context.get_anchor(self.phase_context.primary_anchor_id)
                return CLASSIFY_PROMPT.format(
                    topic=self.journey_brief.original_question,
                    primary_anchor=primary.description if primary else "(none)",
                    anchors=self._format_anchors(),
                )

        elif phase == BuildPhase.SEQUENCE_DESIGN:
            return SEQUENCE_DESIGN_PROMPT.format(
                slos=self._format_slos(),
                anchors=self._format_anchors(),
            )

        elif phase == BuildPhase.CONSTRUCTION:
            slo = self.phase_context.get_current_slo()
            anchor = self.phase_context.get_anchor(slo.anchor_id) if slo else None
            current_rounds = self.phase_context.get_current_rounds()

            if visit_count > 1:
                # Came back via backward transition (e.g., from anchor gap)
                return CONSTRUCTION_REENTRY_PROMPT.format(
                    backward_trigger=self.phase_context.backward_trigger or "",
                    previous_rounds=self._format_rounds(),
                    slo_statement=slo.statement if slo else "",
                    scaffold_level=self.phase_context.current_scaffold_level,
                    mode=self.phase_context.current_mode,
                )
            elif current_rounds:
                # Mid-construction: rounds already recorded, user responded to scaffold
                return CONSTRUCTION_RESUME_PROMPT.format(
                    slo_statement=slo.statement if slo else "",
                    slo_frame=slo.frame if slo else "",
                    anchor_description=anchor.description if anchor else "",
                    scaffold_level=self.phase_context.current_scaffold_level,
                    mode=self.phase_context.current_mode,
                    previous_rounds=self._format_rounds(),
                )
            else:
                # First time entering construction for this SLO
                return CONSTRUCTION_INITIAL_PROMPT.format(
                    slo_statement=slo.statement if slo else "",
                    slo_frame=slo.frame if slo else "",
                    anchor_description=anchor.description if anchor else "",
                    scaffold_level=self.phase_context.current_scaffold_level,
                    mode=self.phase_context.current_mode,
                )

        elif phase == BuildPhase.SLO_COMPLETE:
            slo = self.phase_context.get_current_slo()
            rounds = self.phase_context.get_current_rounds()
            surrenders = sum(1 for r in rounds if r.outcome == "surrendered")
            return SLO_COMPLETE_PROMPT.format(
                slo_statement=slo.statement if slo else "",
                round_count=len(rounds),
                surrender_count=surrenders,
                effective_scaffolds=", ".join(self.phase_context.effective_strategies[-3:]),
            )

        elif phase == BuildPhase.CONSOLIDATION:
            return CONSOLIDATION_PROMPT.format(
                topic=self.journey_brief.original_question,
                completed_slos=len(self.phase_context.completed_slo_ids),
                total_rounds=sum(len(r) for r in self.phase_context.construction_rounds.values()),
                slo_table=self._format_slo_table(),
            )

        elif phase == BuildPhase.COMPLETE:
            return COMPLETE_PROMPT

        return ""

    # =========================================================================
    # Transition Evaluation
    # =========================================================================

    def _evaluate_transition_condition(self, transition: PhaseTransition) -> bool:
        """Check if a specific transition's condition is met."""

        condition = transition.condition

        if condition == "anchors_confirmed":
            return self.phase_context.anchors_confirmed

        elif condition == "slos_selected":
            return self.phase_context.slos_confirmed and len(self.phase_context.selected_slo_ids) > 0

        elif condition == "sequence_designed":
            return self.phase_context.sequences_designed

        elif condition == "construction_verified":
            return self.phase_context.is_construction_verified()

        elif condition == "next_slo_available":
            return self.phase_context.has_next_slo()

        elif condition == "all_slos_complete":
            return not self.phase_context.has_next_slo()

        elif condition == "consolidation_complete":
            return self.phase_context.consolidation_complete

        elif condition == "anchor_gap_detected":
            return self.phase_context.backward_trigger == "anchor_gap_detected"

        return False

    # =========================================================================
    # Formatting Helpers
    # =========================================================================

    def _format_anchors(self) -> str:
        """Format anchors for prompt."""
        lines = [f"- {a.description} ({a.strength})" for a in self.phase_context.anchors]
        return "\n".join(lines) if lines else "No anchors yet"

    def _format_slos(self) -> str:
        """Format SLOs for prompt."""
        selected = [s for s in self.phase_context.slos if s.id in self.phase_context.selected_slo_ids]
        lines = [f"- {s.statement} (frame: {s.frame})" for s in selected]
        return "\n".join(lines) if lines else "No SLOs selected"

    def _format_rounds(self) -> str:
        """Format construction rounds for prompt."""
        rounds = self.phase_context.get_current_rounds()
        lines = [f"Round {r.round_num}: {r.outcome}" for r in rounds[-5:]]
        return "\n".join(lines) if lines else "No rounds yet"

    def _format_slo_table(self) -> str:
        """Format SLO status table for consolidation."""
        lines = []
        for slo in self.phase_context.slos:
            if slo.id in self.phase_context.selected_slo_ids:
                status = self.phase_context.slo_status.get(slo.id, "not_started")
                rounds = len(self.phase_context.construction_rounds.get(slo.id, []))
                lines.append(f"| {slo.statement[:30]}... | {status} | {rounds} |")
        return "\n".join(lines) if lines else "| No SLOs |"

    # =========================================================================
    # Awaiting Input Detection
    # =========================================================================

    def _get_awaiting_input_prompt(self) -> str | None:
        """
        Return a prompt message if the agent is waiting for user input.

        This override provides Build-specific messages for phases that require
        user interaction before continuing.
        """
        phase = self.current_phase

        if phase == BuildPhase.ANCHOR_DISCOVERY:
            # If anchor questions asked but not confirmed, we're waiting for experiences
            if self.phase_context.anchor_questions_asked and not self.phase_context.anchors_confirmed:
                return "Share your experiences with the concepts mentioned above so I can identify good anchors to build from."

        elif phase == BuildPhase.CLASSIFY:
            # If SLOs presented but not confirmed, we're waiting for selection
            if self.phase_context.slos_presented and not self.phase_context.slos_confirmed:
                slo_count = len(self.phase_context.slos)
                return f"I've presented {slo_count} learning objectives. Which would you like to explore? You can select specific ones or say 'all'."

        elif phase == BuildPhase.CONSTRUCTION:
            # During construction, we're always in an interactive loop
            slo = self.phase_context.get_current_slo()
            if slo:
                return f"Working on: {slo.statement[:50]}... Share your thoughts or answer the question above."

        # No specific waiting state
        return None

    # =========================================================================
    # Completion
    # =========================================================================

    def _generate_completion_summary(self) -> str:
        """Generate a summary when build session completes."""
        total_rounds = sum(len(r) for r in self.phase_context.construction_rounds.values())
        return (
            f"Build session complete. "
            f"Constructed {len(self.phase_context.completed_slo_ids)} concepts "
            f"from {len(self.phase_context.anchors)} anchors. "
            f"Total rounds: {total_rounds}."
        )

    # =========================================================================
    # State Persistence
    # =========================================================================

    def _serialize_phase_context(self) -> dict:
        """Serialize phase context to dict."""
        return self.phase_context.to_dict()

    def _restore_phase_context(self, state: dict) -> None:
        """Restore phase context from state."""
        self.phase_context = BuildPhaseContext.from_dict(state)

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
        self._mcp_server = self._create_mcp_server()
