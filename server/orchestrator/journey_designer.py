"""
Journey Designer for Knowledge Forge.

Wraps routing logic and handles journey initialization based on the design brief.
"""

from __future__ import annotations

from typing import Optional
from anthropic import Anthropic

from server.persistence import (
    JourneyDesignBrief,
    Session,
    SessionStore,
    Mode,
    ResearchModeData,
    UnderstandModeData,
    BuildModeData,
    Narrative,
    CategoryQuestion,
)
from .router import QuestionRouter


class JourneyDesigner:
    """
    Designs and initializes learning journeys.

    Combines question routing with session initialization
    to create a fully prepared journey.
    """

    def __init__(
        self,
        store: Optional[SessionStore] = None,
        client: Optional[Anthropic] = None,
    ):
        """
        Initialize the journey designer.

        Args:
            store: Session store for creating sessions
            client: Anthropic client for LLM-powered analysis
        """
        self.store = store or SessionStore()
        self.router = QuestionRouter(client)

    async def analyze_question(
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
            use_llm: Whether to use LLM for deep analysis

        Returns:
            JourneyDesignBrief with routing decision
        """
        return await self.router.analyze(question, learner_context, use_llm)

    def initialize_session(
        self,
        brief: JourneyDesignBrief,
        mode: Optional[Mode] = None,
    ) -> Session:
        """
        Create and initialize a session based on the journey brief.

        Args:
            brief: The journey design brief
            mode: Override mode (if user selected alternative)

        Returns:
            Initialized Session with mode-specific data
        """
        final_mode = mode or brief.primary_mode

        # Create session with brief
        session = self.store.create(
            journey_brief=brief,
            mode=final_mode,
        )

        # Initialize mode-specific data
        self._initialize_mode_data(session, brief)

        # Save session
        self.store.save(session)

        return session

    def _initialize_mode_data(
        self,
        session: Session,
        brief: JourneyDesignBrief,
    ) -> None:
        """Initialize mode-specific data structures."""
        if session.mode == "research":
            session.research_data = ResearchModeData(
                topic=brief.original_question,
                meta=f"Research journey: {brief.ideal_answer}",
                essay=Narrative(),
                categories=[],
                questions=[],
                key_insights=[],
                adjacent_questions=[],
            )
        elif session.mode == "understand":
            session.understand_data = UnderstandModeData(
                essay=Narrative(
                    prior="",
                    delta="",
                    full=f"<h2>Understanding: {brief.original_question}</h2>",
                ),
                assumptions=[],
                concepts=[],
                models=[],
            )
        elif session.mode == "build":
            session.phase = "grounding"
            session.build_data = BuildModeData(
                narrative=Narrative(
                    prior="",
                    delta="",
                    full=f"<h2>Building: {brief.original_question}</h2>",
                ),
                constructs=[],
                decisions=[],
                capabilities=[],
            )
            session.grounding_concepts = []
            session.grounding_ready = False

    def get_initial_agent_prompt(
        self,
        session: Session,
        brief: JourneyDesignBrief,
    ) -> str:
        """
        Generate the initial prompt to kick off the agent.

        This gives the agent context about what the user wants
        and how to proceed.
        """
        if session.mode == "research":
            return f"""User wants to research: {brief.original_question}

Ideal answer: {brief.ideal_answer}

Begin by decomposing this into key questions. Create 3-5 categories
of questions that will help answer the user's query.

For each category:
1. Identify 2-3 specific questions
2. Consider what sources would be most helpful
3. Note any adjacent questions that might emerge"""

        elif session.mode == "understand":
            return f"""User wants to understand: {brief.original_question}

Ideal answer: {brief.ideal_answer}

Begin by surfacing assumptions the user might have about this topic.
Then help them develop clear concepts and distinctions.

Focus on:
1. What assumptions might they have that could block understanding?
2. What are the key concepts they need to grasp?
3. What distinctions will clarify their thinking?"""

        elif session.mode == "build":
            return f"""User wants to build: {brief.original_question}

Ideal answer: {brief.ideal_answer}

This is a BUILD journey with two phases:

PHASE 1: GROUNDING (current)
Help the user grasp the minimal concepts needed to build well.
- What concepts do they need to understand first?
- What assumptions might lead them astray?
- What distinctions matter for this build?

When grounding is sufficient, transition to PHASE 2: MAKING.

PHASE 2: MAKING
- Identify constructs (building blocks)
- Make decisions (trade-offs)
- Develop capabilities (what they can now do)"""

        return ""
