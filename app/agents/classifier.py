"""Agent 2: Thread Classifier using structured output.

Receives a thread summary and classifies it into exactly one of the
CUSTOM_GMAIL_LABELS using a constrained structured output response.

Labels:
  - action_needed  : Requires a reply, decision, or follow-up action
  - fyi            : Informational — useful to read but no action required
  - unimportant    : Low-value email that can be deprioritised or archived
  - predicted_spam : Likely unwanted, promotional, or automated email
"""

import logging
from typing import Literal
from typing_extensions import TypedDict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from app.core.config import settings, CUSTOM_GMAIL_LABELS

logger = logging.getLogger(__name__)

MODEL_NAME = "claude-3-5-haiku-20241022"

GmailLabel = Literal["action_needed", "fyi", "unimportant", "predicted_spam"]


class LabelOutput(BaseModel):
    label: GmailLabel
    reasoning: str


def _get_llm() -> ChatAnthropic:
    return ChatAnthropic(
        model=MODEL_NAME,
        api_key=settings.anthropic_api_key,
        max_tokens=512,
    )


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class ClassifierState(TypedDict):
    summary: str
    label: str
    reasoning: str


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def classify_node(state: ClassifierState) -> ClassifierState:
    """Classify the thread summary into one of the custom Gmail labels."""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(LabelOutput)

    label_descriptions = (
        "- action_needed: The thread requires a reply, decision, approval, or follow-up task.\n"
        "- fyi: Informational content that is relevant and worth reading, but needs no action.\n"
        "- unimportant: Low-priority email — no action needed and low informational value.\n"
        "- predicted_spam: Promotional, automated, unsolicited, or irrelevant email."
    )

    response: LabelOutput = structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are an expert email classifier. Given a summary of an email thread, "
                    "classify it into exactly one of the following labels:\n\n"
                    f"{label_descriptions}\n\n"
                    "Choose the label that best reflects the primary nature of the thread. "
                    "If the thread requires any action from the recipient, prefer 'action_needed'."
                )
            ),
            HumanMessage(
                content=(
                    f"Thread summary:\n\n{state['summary']}\n\n"
                    "Classify this thread and briefly explain your reasoning."
                )
            ),
        ]
    )

    logger.debug("Classified as '%s': %s", response.label, response.reasoning)
    return {**state, "label": response.label, "reasoning": response.reasoning}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def _build_graph() -> StateGraph:
    graph = StateGraph(ClassifierState)
    graph.add_node("classify", classify_node)
    graph.set_entry_point("classify")
    graph.add_edge("classify", END)
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


def run_classifier(summary: str) -> str:
    """Classify a thread summary into one of the custom Gmail labels.

    Args:
        summary: The full thread summary produced by Agent 1.

    Returns:
        One of: "action_needed", "fyi", "unimportant", "predicted_spam".
    """
    if not summary:
        return "unimportant"

    initial_state: ClassifierState = {
        "summary": summary,
        "label": "",
        "reasoning": "",
    }

    result = _get_graph().invoke(initial_state)
    label = result["label"]

    # Safety guard: ensure the label is always one of the valid values
    if label not in CUSTOM_GMAIL_LABELS:
        logger.warning("Unexpected label '%s', defaulting to 'unimportant'", label)
        return "unimportant"

    return label
