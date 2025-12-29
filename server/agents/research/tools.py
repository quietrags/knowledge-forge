"""
Research Agent Tools.

Defines the tools available to the Research Agent, wrapped for SSE event emission.
Uses Claude's built-in web search and Context7 for documentation.
"""

from typing import Callable, Optional
import json

from server.api.streaming import SSEEvent


# =============================================================================
# Tool Definitions (Anthropic format)
# =============================================================================

def get_decompose_tools() -> list[dict]:
    """Get tools available in DECOMPOSE phase."""
    return [
        {
            "name": "emit_category",
            "description": "Emit a new research category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The category name",
                    },
                    "insight_question": {
                        "type": "string",
                        "description": "The overarching question for this category",
                    },
                },
                "required": ["category", "insight_question"],
            },
        },
        {
            "name": "emit_question",
            "description": "Emit a research question within a category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The research question",
                    },
                    "category_id": {
                        "type": "string",
                        "description": "ID of the category this belongs to",
                    },
                    "frame": {
                        "type": "string",
                        "enum": ["WHAT", "WHY", "HOW", "WHEN", "CODE", "PITFALL"],
                        "description": "The question frame type",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Question priority",
                    },
                },
                "required": ["question", "category_id", "frame", "priority"],
            },
        },
        {
            "name": "mark_decompose_complete",
            "description": "Mark decomposition as complete, ready for user approval",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of the question tree",
                    },
                },
                "required": ["summary"],
            },
        },
    ]


def get_answer_tools() -> list[dict]:
    """Get tools available in ANSWER phase."""
    return [
        {
            "name": "web_search",
            "description": "Search the web for information. Use for general research queries.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "resolve_library_id",
            "description": "Resolve a library name to a Context7 library ID for documentation lookup",
            "input_schema": {
                "type": "object",
                "properties": {
                    "library_name": {
                        "type": "string",
                        "description": "The library name to resolve (e.g., 'langchain', 'fastapi')",
                    },
                    "query": {
                        "type": "string",
                        "description": "Context about what you want to find",
                    },
                },
                "required": ["library_name", "query"],
            },
        },
        {
            "name": "query_docs",
            "description": "Query documentation for a specific library using its Context7 ID",
            "input_schema": {
                "type": "object",
                "properties": {
                    "library_id": {
                        "type": "string",
                        "description": "The Context7 library ID (e.g., '/langchain-ai/langchain')",
                    },
                    "query": {
                        "type": "string",
                        "description": "What you want to find in the docs",
                    },
                },
                "required": ["library_id", "query"],
            },
        },
        {
            "name": "emit_answer",
            "description": "Emit an answer to a research question",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question_id": {
                        "type": "string",
                        "description": "ID of the question being answered",
                    },
                    "answer": {
                        "type": "string",
                        "description": "The researched answer",
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "credibility": {
                                    "type": "string",
                                    "enum": ["primary", "high", "medium", "low"],
                                },
                                "snippet": {"type": "string"},
                            },
                            "required": ["title", "credibility"],
                        },
                        "description": "Sources supporting the answer",
                    },
                    "code_example": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string"},
                            "content": {"type": "string"},
                            "language": {"type": "string"},
                        },
                        "description": "Optional code example",
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Confidence in the answer based on source quality",
                    },
                },
                "required": ["question_id", "answer", "sources", "confidence"],
            },
        },
        {
            "name": "skip_question",
            "description": "Skip a question that cannot be adequately answered",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question_id": {
                        "type": "string",
                        "description": "ID of the question to skip",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why the question is being skipped",
                    },
                },
                "required": ["question_id", "reason"],
            },
        },
        {
            "name": "flag_new_category",
            "description": "Flag that a new category was discovered during answering",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category_name": {
                        "type": "string",
                        "description": "Name of the discovered category",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why this category is needed",
                    },
                },
                "required": ["category_name", "reason"],
            },
        },
        {
            "name": "mark_answer_phase_complete",
            "description": "Mark the answer phase as complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of answers gathered",
                    },
                },
                "required": ["summary"],
            },
        },
    ]


def get_rise_above_tools() -> list[dict]:
    """Get tools available in RISE_ABOVE phase."""
    return [
        {
            "name": "emit_category_insight",
            "description": "Emit a synthesized insight for a category",
            "input_schema": {
                "type": "object",
                "properties": {
                    "category_id": {
                        "type": "string",
                        "description": "ID of the category",
                    },
                    "insight": {
                        "type": "string",
                        "description": "The synthesized insight",
                    },
                },
                "required": ["category_id", "insight"],
            },
        },
        {
            "name": "emit_key_insight",
            "description": "Emit a cross-cutting key insight",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the insight",
                    },
                    "description": {
                        "type": "string",
                        "description": "Full description of the insight",
                    },
                    "relevance": {
                        "type": "string",
                        "description": "Which questions/categories this relates to",
                    },
                },
                "required": ["title", "description", "relevance"],
            },
        },
        {
            "name": "flag_unanswered_needed",
            "description": "Flag that specific questions must be answered before synthesis can complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs of questions that need answers",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Why these are needed for synthesis",
                    },
                },
                "required": ["question_ids", "reason"],
            },
        },
        {
            "name": "mark_synthesis_complete",
            "description": "Mark synthesis as complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of insights generated",
                    },
                },
                "required": ["summary"],
            },
        },
    ]


def get_expand_tools() -> list[dict]:
    """Get tools available in EXPAND phase."""
    return [
        {
            "name": "emit_adjacent_question",
            "description": "Emit an adjacent question for the frontier",
            "input_schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The adjacent question",
                    },
                    "discovered_from": {
                        "type": "string",
                        "description": "Which answered question triggered this",
                    },
                },
                "required": ["question", "discovered_from"],
            },
        },
        {
            "name": "mark_expand_complete",
            "description": "Mark expansion as complete",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of frontier questions",
                    },
                },
                "required": ["summary"],
            },
        },
    ]


# =============================================================================
# Tool Result Handlers
# =============================================================================

class ResearchToolHandler:
    """
    Handles tool invocations for the Research Agent.

    Processes tool calls, updates state, and emits SSE events.
    """

    def __init__(
        self,
        phase_context: "ResearchPhaseContext",
        emit_event: Callable[[SSEEvent], None],
    ):
        self.ctx = phase_context
        self.emit = emit_event

    async def handle_tool_call(
        self,
        tool_name: str,
        tool_input: dict,
    ) -> dict:
        """
        Handle a tool call and return the result.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            Tool result as a dictionary
        """
        handler = getattr(self, f"_handle_{tool_name}", None)
        if handler:
            return await handler(tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    # =========================================================================
    # DECOMPOSE Phase Handlers
    # =========================================================================

    async def _handle_emit_category(self, input: dict) -> dict:
        """Handle emit_category tool."""
        from server.persistence import CategoryQuestion
        import uuid

        category = CategoryQuestion(
            id=str(uuid.uuid4()),
            category=input["category"],
            insight=None,  # Will be filled in RISE_ABOVE
            question_ids=[],
        )

        self.ctx.add_category(category)

        self.emit(SSEEvent(
            type="data.category.added",
            payload=category.model_dump(by_alias=True),
        ))

        return {"category_id": category.id, "status": "created"}

    async def _handle_emit_question(self, input: dict) -> dict:
        """Handle emit_question tool."""
        from server.persistence import Question
        import uuid

        question = Question(
            id=str(uuid.uuid4()),
            question=input["question"],
            status="open",
            category_id=input["category_id"],
        )

        # Store priority in a metadata field (not in base Question model)
        # We track this in phase context
        self.ctx.add_question(question)

        # Update category's question_ids
        for cat in self.ctx.categories:
            if cat.id == input["category_id"]:
                cat.question_ids.append(question.id)
                break

        self.emit(SSEEvent(
            type="data.question.added",
            payload={
                "question": question.model_dump(by_alias=True),
                "categoryId": input["category_id"],
                "frame": input["frame"],
                "priority": input["priority"],
            },
        ))

        return {"question_id": question.id, "status": "created"}

    async def _handle_mark_decompose_complete(self, input: dict) -> dict:
        """Handle mark_decompose_complete tool."""
        # Don't set question_tree_approved here - wait for checkpoint
        return {
            "status": "ready_for_approval",
            "summary": input["summary"],
            "num_categories": len(self.ctx.categories),
            "num_questions": len(self.ctx.questions),
        }

    # =========================================================================
    # ANSWER Phase Handlers
    # =========================================================================

    async def _handle_web_search(self, input: dict) -> dict:
        """Handle web_search tool - this is a pass-through to Claude's web search."""
        # This tool is handled by the Anthropic API's built-in web search
        # We just emit an event for UI feedback
        self.emit(SSEEvent(
            type="agent.thinking",
            payload={"message": f"Searching: {input['query']}"},
        ))
        return {"status": "search_delegated_to_claude"}

    async def _handle_resolve_library_id(self, input: dict) -> dict:
        """Handle resolve_library_id tool - Context7 integration."""
        self.emit(SSEEvent(
            type="agent.thinking",
            payload={"message": f"Resolving library: {input['library_name']}"},
        ))
        # Actual resolution happens via MCP - this is a marker
        return {"status": "resolution_delegated_to_context7"}

    async def _handle_query_docs(self, input: dict) -> dict:
        """Handle query_docs tool - Context7 documentation query."""
        self.emit(SSEEvent(
            type="agent.thinking",
            payload={"message": f"Querying docs: {input['query']}"},
        ))
        return {"status": "query_delegated_to_context7"}

    async def _handle_emit_answer(self, input: dict) -> dict:
        """Handle emit_answer tool."""
        from server.persistence import Source, CodeContent

        question_id = input["question_id"]

        # Find and update the question
        for q in self.ctx.questions:
            if q.id == question_id:
                q.status = "answered"
                q.answer = input["answer"]
                q.sources = [
                    Source(**s) for s in input.get("sources", [])
                ]
                if input.get("code_example"):
                    q.code = CodeContent(**input["code_example"])
                break

        self.ctx.mark_question_answered(question_id)

        self.emit(SSEEvent(
            type="data.question.answered",
            payload={
                "questionId": question_id,
                "answer": input["answer"],
                "sources": input.get("sources", []),
                "confidence": input.get("confidence", "medium"),
            },
        ))

        return {"status": "answered", "question_id": question_id}

    async def _handle_skip_question(self, input: dict) -> dict:
        """Handle skip_question tool."""
        question_id = input["question_id"]
        self.ctx.skipped_question_ids.add(question_id)

        self.emit(SSEEvent(
            type="data.question.updated",
            payload={
                "questionId": question_id,
                "status": "skipped",
                "reason": input["reason"],
            },
        ))

        return {"status": "skipped", "question_id": question_id}

    async def _handle_flag_new_category(self, input: dict) -> dict:
        """Handle flag_new_category tool - triggers backward transition."""
        self.ctx.new_category_pending = input["category_name"]
        self.ctx.backward_trigger_detail = input["reason"]

        return {
            "status": "flagged",
            "will_trigger": "backward_transition_to_decompose",
        }

    async def _handle_mark_answer_phase_complete(self, input: dict) -> dict:
        """Handle mark_answer_phase_complete tool."""
        unanswered = self.ctx.get_unanswered_questions()

        if len(unanswered) == 0:
            self.ctx.high_priority_complete = True
            return {"status": "complete", "summary": input["summary"]}
        else:
            return {
                "status": "incomplete",
                "remaining": len(unanswered),
                "summary": input["summary"],
            }

    # =========================================================================
    # RISE_ABOVE Phase Handlers
    # =========================================================================

    async def _handle_emit_category_insight(self, input: dict) -> dict:
        """Handle emit_category_insight tool."""
        category_id = input["category_id"]
        insight = input["insight"]

        # Update category
        for cat in self.ctx.categories:
            if cat.id == category_id:
                cat.insight = insight
                break

        self.ctx.category_insights[category_id] = insight

        self.emit(SSEEvent(
            type="data.category.insight",
            payload={
                "categoryId": category_id,
                "insight": insight,
            },
        ))

        return {"status": "insight_added", "category_id": category_id}

    async def _handle_emit_key_insight(self, input: dict) -> dict:
        """Handle emit_key_insight tool."""
        from server.persistence import KeyInsight
        import uuid

        insight = KeyInsight(
            id=str(uuid.uuid4()),
            title=input["title"],
            description=input["description"],
            relevance=input.get("relevance", ""),
        )

        self.emit(SSEEvent(
            type="data.key_insight.added",
            payload=insight.model_dump(by_alias=True),
        ))

        return {"status": "insight_added", "insight_id": insight.id}

    async def _handle_flag_unanswered_needed(self, input: dict) -> dict:
        """Handle flag_unanswered_needed tool - triggers backward transition."""
        self.ctx.unanswered_for_synthesis = input["question_ids"]
        self.ctx.backward_trigger_detail = input["reason"]

        return {
            "status": "flagged",
            "will_trigger": "backward_transition_to_answer",
        }

    async def _handle_mark_synthesis_complete(self, input: dict) -> dict:
        """Handle mark_synthesis_complete tool."""
        self.ctx.insights_complete = True
        return {"status": "complete", "summary": input["summary"]}

    # =========================================================================
    # EXPAND Phase Handlers
    # =========================================================================

    async def _handle_emit_adjacent_question(self, input: dict) -> dict:
        """Handle emit_adjacent_question tool."""
        from server.persistence import AdjacentQuestion
        import uuid

        aq = AdjacentQuestion(
            id=str(uuid.uuid4()),
            question=input["question"],
            discovered_from=input["discovered_from"],
        )

        self.ctx.adjacent_questions.append(aq)

        self.emit(SSEEvent(
            type="data.adjacent_question.added",
            payload=aq.model_dump(by_alias=True),
        ))

        return {"status": "added", "question_id": aq.id}

    async def _handle_mark_expand_complete(self, input: dict) -> dict:
        """Handle mark_expand_complete tool."""
        self.ctx.frontier_populated = True
        return {"status": "complete", "summary": input["summary"]}
