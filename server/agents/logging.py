"""
Agent conversation logging utility.

Logs all agent interactions to files for debugging:
- Prompts sent to the LLM
- LLM responses (text and tool calls)
- Tool results
- Errors

Log files are stored in server/logs/ with session ID prefix.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def get_agent_logger(session_id: str, agent_type: str) -> logging.Logger:
    """
    Get a logger for an agent session.

    Creates a file handler that writes to:
    server/logs/{session_id[:8]}_{agent_type}_{timestamp}.log
    """
    # Create unique log file name
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short_id = session_id[:8]
    log_file = LOG_DIR / f"{short_id}_{agent_type}_{timestamp}.log"

    # Create logger
    logger_name = f"agent.{short_id}"
    logger = logging.getLogger(logger_name)

    # Only add handler if not already added
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        # File handler
        fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Format: timestamp - level - message
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Also log to console at INFO level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    logger.info(f"Agent log started: {log_file}")
    return logger


def log_prompt(logger: logging.Logger, phase: str, prompt: str) -> None:
    """Log the prompt being sent to the LLM."""
    logger.debug(f"\n{'='*60}\nPHASE: {phase}\n{'='*60}")
    logger.debug(f"PROMPT:\n{prompt[:2000]}{'...[truncated]' if len(prompt) > 2000 else ''}")


def log_llm_response(
    logger: logging.Logger,
    response: Any,
    iteration: int = 0,
) -> None:
    """Log the LLM response including text and tool calls."""
    logger.debug(f"\n{'-'*40}\nLLM RESPONSE (iteration {iteration})\n{'-'*40}")

    # Handle different response formats
    if hasattr(response, 'content'):
        for block in response.content:
            if hasattr(block, 'text'):
                text = block.text
                logger.debug(f"TEXT:\n{text[:1000]}{'...[truncated]' if len(text) > 1000 else ''}")
            elif hasattr(block, 'name'):
                # Tool use block
                logger.debug(f"TOOL CALL: {block.name}")
                if hasattr(block, 'input'):
                    try:
                        input_str = json.dumps(block.input, indent=2)
                        logger.debug(f"TOOL INPUT:\n{input_str[:1000]}{'...[truncated]' if len(input_str) > 1000 else ''}")
                    except Exception:
                        logger.debug(f"TOOL INPUT: {block.input}")
    else:
        logger.debug(f"RAW RESPONSE: {str(response)[:1000]}")


def log_tool_result(
    logger: logging.Logger,
    tool_name: str,
    result: Any,
    is_error: bool = False,
) -> None:
    """Log the result of a tool call."""
    status = "ERROR" if is_error else "SUCCESS"
    logger.debug(f"\nTOOL RESULT ({status}): {tool_name}")

    try:
        result_str = json.dumps(result, indent=2) if isinstance(result, (dict, list)) else str(result)
        logger.debug(f"{result_str[:1000]}{'...[truncated]' if len(result_str) > 1000 else ''}")
    except Exception:
        logger.debug(f"{str(result)[:1000]}")


def log_phase_transition(
    logger: logging.Logger,
    from_phase: str,
    to_phase: str,
    reason: str,
) -> None:
    """Log a phase transition."""
    logger.info(f"PHASE TRANSITION: {from_phase} -> {to_phase} (reason: {reason})")


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """Log an error."""
    logger.error(f"ERROR {context}: {type(error).__name__}: {error}")
    import traceback
    logger.debug(f"TRACEBACK:\n{traceback.format_exc()}")


def log_sdk_turn(
    logger: logging.Logger,
    turn_number: int,
    messages: list,
    tools: list[str],
) -> None:
    """Log a complete SDK turn (messages + available tools)."""
    logger.debug(f"\n{'#'*60}\nSDK TURN {turn_number}\n{'#'*60}")
    logger.debug(f"Available tools: {tools}")

    # Log recent messages
    for i, msg in enumerate(messages[-3:]):  # Last 3 messages
        role = msg.get('role', 'unknown') if isinstance(msg, dict) else getattr(msg, 'role', 'unknown')
        logger.debug(f"Message {i}: role={role}")

        # Try to log content
        content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', None)
        if content:
            if isinstance(content, str):
                logger.debug(f"  content: {content[:500]}...")
            elif isinstance(content, list):
                for block in content[:3]:
                    if hasattr(block, 'text'):
                        logger.debug(f"  text: {block.text[:300]}...")
                    elif hasattr(block, 'name'):
                        logger.debug(f"  tool_use: {block.name}")
