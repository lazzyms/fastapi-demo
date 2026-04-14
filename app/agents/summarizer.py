"""Agent 1: Thread Summarizer using map-reduce over message chunks.

Strategy:
  1. Split messages into chunks of CHUNK_SIZE to handle arbitrarily large threads
     without exceeding context limits.
  2. Summarize each chunk individually, preserving temporal ordering context
     ("messages X–Y of Z in this thread").
  3. Combine all chunk summaries into a single coherent thread summary.

This ensures sequencing and context are preserved regardless of thread length.
"""

import logging
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.schemas.emails import ThreadMessage

logger = logging.getLogger(__name__)

CHUNK_SIZE = 10


def _get_llm() -> ChatAnthropic:
    if not settings.model_name or not settings.model_name.strip():
        raise ValueError(
            "MODEL_NAME is not set. Configure MODEL_NAME in your .env file "
            "to enable email thread summarization."
        )

    if not settings.anthropic_api_key or not settings.anthropic_api_key.strip():
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Configure ANTHROPIC_API_KEY in your "
            ".env file to enable email thread summarization."
        )

    return ChatAnthropic(
        model=settings.model_name,
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class SummarizerState(TypedDict):
    messages: list[ThreadMessage]
    chunk_summaries: list[str]
    final_summary: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def chunk_messages_node(state: SummarizerState) -> SummarizerState:
    """No-op: chunking happens inside summarize_chunks_node. Passes state through."""
    return state


def summarize_chunks_node(state: SummarizerState) -> SummarizerState:
    """Summarize each chunk of messages preserving order and context."""
    messages = state["messages"]
    total = len(messages)
    llm = _get_llm()
    chunk_summaries: list[str] = []

    for start in range(0, total, CHUNK_SIZE):
        end = min(start + CHUNK_SIZE, total)
        chunk = messages[start:end]
        chunk_num = start // CHUNK_SIZE + 1
        total_chunks = (total + CHUNK_SIZE - 1) // CHUNK_SIZE

        formatted = _format_messages_for_prompt(chunk, start + 1, total)

        response = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You are an expert email analyst. Summarize the following email messages "
                        "from an email thread, preserving the chronological flow and key context. "
                        "Note who said what and when. Be concise but comprehensive."
                    )
                ),
                HumanMessage(
                    content=(
                        f"These are messages {start + 1}–{end} of {total} in the email thread "
                        f"(chunk {chunk_num} of {total_chunks}).\n\n"
                        f"{formatted}\n\n"
                        "Summarize this portion of the thread, capturing key points, decisions, "
                        "questions, and tone. Preserve the sequence of events."
                    )
                ),
            ]
        )

        chunk_summaries.append(str(response.content))
        logger.debug(
            "Summarized chunk %d/%d (%d messages)", chunk_num, total_chunks, len(chunk)
        )

    return {**state, "chunk_summaries": chunk_summaries}


def combine_summaries_node(state: SummarizerState) -> SummarizerState:
    """Combine chunk summaries into a single coherent thread summary."""
    chunk_summaries = state["chunk_summaries"]

    if len(chunk_summaries) == 1:
        # Single chunk — no need for a second LLM call
        return {**state, "final_summary": chunk_summaries[0]}

    llm = _get_llm()
    numbered = "\n\n".join(
        f"[Part {i + 1} of {len(chunk_summaries)}]\n{s}"
        for i, s in enumerate(chunk_summaries)
    )

    response = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert email analyst. You will receive summaries of sequential "
                    "parts of an email thread. Combine them into a single, coherent narrative "
                    "summary that preserves the full chronological story, key decisions, action "
                    "items, and any outstanding questions."
                )
            ),
            HumanMessage(
                content=(
                    f"Below are the summaries of each part of the email thread in order:\n\n"
                    f"{numbered}\n\n"
                    "Write a single unified summary of the entire email thread from start to finish, "
                    "maintaining the sequence of events and capturing all important information."
                )
            ),
        ]
    )

    return {**state, "final_summary": str(response.content)}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    graph = StateGraph(SummarizerState)
    graph.add_node("chunk_messages", chunk_messages_node)
    graph.add_node("summarize_chunks", summarize_chunks_node)
    graph.add_node("combine_summaries", combine_summaries_node)

    graph.set_entry_point("chunk_messages")
    graph.add_edge("chunk_messages", "summarize_chunks")
    graph.add_edge("summarize_chunks", "combine_summaries")
    graph.add_edge("combine_summaries", END)

    return graph.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_summarizer(messages: list[ThreadMessage]) -> str:
    """Summarize all messages in a thread using map-reduce over chunks.

    Args:
        messages: Ordered list of ThreadMessage objects (position 1 = oldest).

    Returns:
        A single coherent summary string of the entire thread.
    """
    if not messages:
        return ""

    if len(messages) == 1:
        m = messages[0]
        return f"Single message from {m.sender} on {m.date}: {m.body[:500]}"

    initial_state: SummarizerState = {
        "messages": messages,
        "chunk_summaries": [],
        "final_summary": "",
    }

    result = _get_graph().invoke(initial_state)
    return result["final_summary"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_messages_for_prompt(
    messages: list[ThreadMessage], start_pos: int, total: int
) -> str:
    lines: list[str] = []
    for i, msg in enumerate(messages):
        lines.append(
            f"--- Message {start_pos + i} of {total} ---\n"
            f"From: {msg.sender}\n"
            f"Date: {msg.date}\n"
            f"Subject: {msg.subject}\n"
            f"Body:\n{msg.body}\n"
        )
    return "\n".join(lines)
