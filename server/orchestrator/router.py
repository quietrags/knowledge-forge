"""
Question Router for Knowledge Forge.

Handles question analysis and mode routing using two mechanisms:
1. Quick Route: Parse question shape (heuristics)
2. Work Backwards: Design from ideal answer (LLM-powered)
"""

from __future__ import annotations

import re
from typing import Optional
from anthropic import Anthropic

from server.persistence import JourneyDesignBrief, Mode, AnswerType


# =============================================================================
# Question Shape Patterns
# =============================================================================

# Patterns that suggest each mode
BUILD_PATTERNS = [
    r"\bhow do i\b",
    r"\bhow can i\b",
    r"\bhelp me\b",
    r"\bcreate\b",
    r"\bbuild\b",
    r"\bmake\b",
    r"\bimplement\b",
    r"\bwrite\b",
    r"\bget started\b",
    r"\bset up\b",
    r"\bdesign\b",
]

UNDERSTAND_PATTERNS = [
    r"\bwhy\b",
    r"\bwhat'?s the difference\b",
    r"\bhow does\b.*\bwork\b",
    r"\bexplain\b",
    r"\bunderstand\b",
    r"\bwhat happens when\b",
    r"\bwhy does\b",
    r"\bwhat causes\b",
    r"\bhow come\b",
]

RESEARCH_PATTERNS = [
    r"\bwhat is\b",
    r"\bwhat are\b",
    r"\bwhat does\b",
    r"\bwho\b",
    r"\bwhen\b",
    r"\bwhere\b",
    r"\blist\b",
    r"\bcompare\b",
    r"\bwhat .* options\b",
    r"\bwhat approaches\b",
]


# =============================================================================
# Question Router
# =============================================================================

class QuestionRouter:
    """
    Routes questions to the appropriate learning mode.

    Uses heuristics for quick routing and Claude for deeper analysis
    when needed (misalignment detection, work backwards).
    """

    def __init__(self, client: Optional[Anthropic] = None):
        """
        Initialize the router.

        Args:
            client: Anthropic client. If None, will be created when needed.
        """
        self._client = client

    @property
    def client(self) -> Anthropic:
        """Lazy-load Anthropic client."""
        if self._client is None:
            self._client = Anthropic()
        return self._client

    def route_heuristic(self, question: str) -> tuple[Mode, AnswerType]:
        """
        Quick route based on question shape patterns.

        Returns:
            Tuple of (mode, answer_type) based on heuristic matching.
        """
        question_lower = question.lower()

        # Check build patterns first (most specific)
        for pattern in BUILD_PATTERNS:
            if re.search(pattern, question_lower):
                return ("build", "skill")

        # Check understand patterns
        for pattern in UNDERSTAND_PATTERNS:
            if re.search(pattern, question_lower):
                return ("understand", "understanding")

        # Check research patterns
        for pattern in RESEARCH_PATTERNS:
            if re.search(pattern, question_lower):
                return ("research", "facts")

        # Default to research for ambiguous questions
        return ("research", "facts")

    def generate_confirmation(
        self, mode: Mode, answer_type: AnswerType, question: str
    ) -> str:
        """Generate a confirmation message for the user."""
        confirmations = {
            "build": (
                "It sounds like you want to learn how to do something practical. "
                "I'll help you build this skill step by step."
            ),
            "understand": (
                "It sounds like you want to deeply understand this concept. "
                "I'll help you build a clear mental model."
            ),
            "research": (
                "It sounds like you want to research this topic. "
                "I'll help you find and synthesize reliable information."
            ),
        }
        return confirmations[mode]

    def generate_ideal_answer(self, mode: Mode, question: str) -> str:
        """Generate a description of the ideal answer for this question."""
        ideal_answers = {
            "build": (
                "Step-by-step guidance to build this capability "
                "with concrete techniques you can apply."
            ),
            "understand": (
                "A clear mental model with key distinctions and examples "
                "that transform how you think about this."
            ),
            "research": (
                "Well-sourced answers to your questions with key insights "
                "synthesized from reliable sources."
            ),
        }
        return ideal_answers[mode]

    def analyze_quick(self, question: str) -> JourneyDesignBrief:
        """
        Perform quick analysis using heuristics only.

        This is the fast path used when no LLM is needed.
        """
        mode, answer_type = self.route_heuristic(question)

        return JourneyDesignBrief(
            original_question=question,
            ideal_answer=self.generate_ideal_answer(mode, question),
            answer_type=answer_type,
            primary_mode=mode,
            confirmation_message=self.generate_confirmation(mode, answer_type, question),
        )

    async def analyze_with_llm(
        self, question: str, learner_context: Optional[str] = None
    ) -> JourneyDesignBrief:
        """
        Perform deep analysis using Claude to work backwards from ideal answer.

        This detects misalignment and generates more nuanced routing.
        """
        system_prompt = """You are a learning journey designer. Analyze questions to determine the best learning approach.

Your task is to:
1. Determine what the user REALLY needs (not just what they asked for)
2. Design the journey backwards from the ideal answer
3. Detect misalignment between what they said and what they need

Respond in JSON format with these fields:
{
  "originalQuestion": "the original question",
  "idealAnswer": "2-3 sentences describing what a great answer would look like",
  "answerType": "facts" | "understanding" | "skill",
  "primaryMode": "research" | "understand" | "build",
  "secondaryMode": "research" | null (if research is needed to support primary),
  "implicitQuestion": "what they might REALLY be asking (if different)" | null,
  "confirmationMessage": "It sounds like you want to... Is that right?"
}

Guidelines:
- "facts" → User wants information gathered (research mode)
- "understanding" → User wants mental models and conceptual clarity (understand mode)
- "skill" → User wants to be able to do something (build mode)

Watch for misalignment:
- User says "understand" but describes wanting to DO something → skill, build
- User asks "what is" but context suggests they want to CREATE → skill, build
- User asks "how" about mechanisms but not doing → understanding, understand"""

        user_message = f"Question: {question}"
        if learner_context:
            user_message += f"\n\nLearner context: {learner_context}"

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        # Parse JSON response
        import json
        response_text = response.content[0].text

        # Handle code blocks in response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        data = json.loads(response_text.strip())

        return JourneyDesignBrief(
            original_question=data["originalQuestion"],
            ideal_answer=data["idealAnswer"],
            answer_type=data["answerType"],
            primary_mode=data["primaryMode"],
            secondary_mode=data.get("secondaryMode"),
            implicit_question=data.get("implicitQuestion"),
            confirmation_message=data["confirmationMessage"],
        )

    async def analyze(
        self,
        question: str,
        learner_context: Optional[str] = None,
        use_llm: bool = True,
    ) -> JourneyDesignBrief:
        """
        Analyze a question and return a journey design brief.

        Args:
            question: The user's question
            learner_context: Optional context about the learner
            use_llm: Whether to use LLM for deep analysis. If False, uses heuristics only.

        Returns:
            JourneyDesignBrief with routing decision and confirmation message.
        """
        if not use_llm:
            return self.analyze_quick(question)

        try:
            return await self.analyze_with_llm(question, learner_context)
        except Exception:
            # Fall back to heuristics if LLM fails
            return self.analyze_quick(question)
