#!/usr/bin/env python3
"""Feature extraction for agentic payment-fraud transcripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


DATA_FILES = [
    "flagship1_injections.jsonl",
    "flagship2_poisonings.jsonl",
    "flagship3_bias.jsonl",
    "legitimate_conversations.jsonl",
]

URGENCY_WORDS = {
    "urgent",
    "urgently",
    "immediately",
    "now",
    "today",
    "tonight",
    "asap",
    "deadline",
    "expires",
    "late",
    "before",
    "pending",
    "window",
    "closes",
}

TRUST_WORDS = {
    "trust",
    "safe",
    "verified",
    "verification",
    "confirm",
    "confirmed",
    "support",
    "help",
    "appreciate",
    "cooperating",
    "remember",
    "connection",
}

AUTHORITY_WORDS = {
    "compliance",
    "support",
    "bank",
    "security",
    "audit",
    "verification",
    "management",
    "property",
    "office",
    "case",
    "policy",
    "settlement",
}

ROMANCE_WORDS = {
    "matched",
    "profile",
    "smile",
    "connection",
    "embarrassed",
    "hotel",
    "clinic",
    "travel",
    "friday",
    "photos",
}

EXTERNAL_INSTRUCTION_WORDS = {
    "route",
    "routing",
    "override",
    "settlement",
    "clearing",
    "ledger",
    "processor",
    "reference",
    "supersedes",
    "memo",
}

STEERING_WORDS = {
    "recommend",
    "recommending",
    "default",
    "preferred",
    "single best",
    "aaa",
    "sponsored",
    "suppress",
    "steers",
    "allocation",
}


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSONL file into transcript dictionaries."""
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_default_datasets(data_dir: str | Path = "generate/data") -> list[dict[str, Any]]:
    """Load all standard defender training datasets that exist."""
    base = Path(data_dir)
    rows: list[dict[str, Any]] = []
    for filename in DATA_FILES:
        path = base / filename
        if path.exists():
            rows.extend(load_jsonl(path))
    return rows


def transcript_text(transcript: dict[str, Any]) -> str:
    return "\n".join(turn.get("content", "") for turn in transcript.get("turns", []))


def count_terms(text: str, terms: set[str]) -> int:
    lowered = text.lower()
    total = 0
    for term in terms:
        total += len(re.findall(rf"\b{re.escape(term.lower())}\b", lowered))
    return total


def role_count(transcript: dict[str, Any], role: str) -> int:
    return sum(1 for turn in transcript.get("turns", []) if turn.get("role") == role)


def source_flags(source: str | None) -> dict[str, int]:
    source = source or ""
    return {
        "source_external_content": int(source == "external_content"),
        "source_user_explicit": int(source == "user_explicit"),
        "source_agent_inferred": int(source == "agent_inferred"),
    }


def introduced_by_flags(role: str | None) -> dict[str, int]:
    role = role or ""
    return {
        "payee_by_user": int(role == "user"),
        "payee_by_attacker": int(role == "attacker"),
        "payee_by_tool_result": int(role == "tool_result"),
        "payee_by_agent": int(role in {"agent", "assistant"}),
    }


def extract_features(transcript: dict[str, Any]) -> dict[str, float | int]:
    """Convert one transcript into numeric ML features."""
    details = transcript.get("transfer_details") or {}
    text = transcript_text(transcript)
    amount = details.get("amount") or 0
    payee_first = transcript.get("payee_first_mentioned_turn")
    payment_turn = transcript.get("payment_requested_turn")
    payee_lag = 0
    if isinstance(payee_first, int) and isinstance(payment_turn, int):
        payee_lag = max(0, payment_turn - payee_first)

    features: dict[str, float | int] = {
        "turn_count": int(transcript.get("turn_count") or len(transcript.get("turns", []))),
        "amount": float(amount),
        "amount_over_500": int(float(amount) > 500),
        "amount_over_1000": int(float(amount) > 1000),
        "final_transfer_attempted": int(bool(transcript.get("final_transfer_attempted"))),
        "known_payee": int(bool(transcript.get("known_payee", False))),
        "new_payee": int(not bool(transcript.get("known_payee", False))),
        "payee_lag_turns": payee_lag,
        "attacker_turns": role_count(transcript, "attacker"),
        "tool_result_turns": role_count(transcript, "tool_result"),
        "agent_tool_call_turns": role_count(transcript, "agent_tool_call"),
        "urgency_word_count": count_terms(text, URGENCY_WORDS),
        "trust_word_count": count_terms(text, TRUST_WORDS),
        "authority_word_count": count_terms(text, AUTHORITY_WORDS),
        "romance_word_count": count_terms(text, ROMANCE_WORDS),
        "external_instruction_count": count_terms(text, EXTERNAL_INSTRUCTION_WORDS),
        "recommendation_steering_count": count_terms(text, STEERING_WORDS),
        "competing_options_suppressed": int(bool(transcript.get("competing_options_suppressed", False))),
    }
    features.update(source_flags(details.get("source_of_instruction")))
    features.update(introduced_by_flags(transcript.get("payee_introduced_by")))
    return features


def build_feature_table(transcripts: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Build X/y tables and return feature column ordering."""
    records = [extract_features(row) for row in transcripts]
    frame = pd.DataFrame.from_records(records).fillna(0)
    labels = pd.Series([1 if row.get("ground_truth_label") == "fraud" else 0 for row in transcripts], name="label")
    columns = sorted(frame.columns)
    return frame[columns], labels, columns


if __name__ == "__main__":
    data = load_default_datasets()
    x_table, y, feature_columns = build_feature_table(data)
    print(f"Loaded {len(data)} transcripts")
    print(f"Feature columns ({len(feature_columns)}):")
    for column in feature_columns:
        print(f"- {column}")
    print("Label counts:")
    print(y.value_counts().to_string())
