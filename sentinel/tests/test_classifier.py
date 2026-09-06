"""Unit tests for feature extraction and structured AI incident classification."""

from __future__ import annotations

import json

from sentinel.classifier import (
    EventFeatures,
    classify_features,
    extract_features,
    validate_classification_json,
)


def test_extract_features_empty() -> None:
    features = extract_features([])
    assert features.event_count == 0
    assert features.total_amount_wei == 0
    assert features.velocity_bps == 0


def test_extract_features_with_events() -> None:
    events = [
        {
            "id": "0x123-0",
            "amount": "1000000000000000000",  # 1 ETH
            "who": "0xAlice",
            "blockNumber": 100,
            "timestamp": 1000,
        },
        {
            "id": "0x124-0",
            "amount": "2000000000000000000",  # 2 ETH
            "who": "0xBob",
            "blockNumber": 102,
            "timestamp": 1020,
        },
    ]
    features = extract_features(events, window_seconds=300)
    assert features.event_count == 2
    assert features.total_amount_wei == 3 * 10**18
    assert features.unique_actors == 2
    assert features.latest_block == 102
    assert features.latest_timestamp == 1020
    assert features.max_single_amount_wei == 2 * 10**18


def test_validate_classification_json_valid() -> None:
    payload = json.dumps(
        {
            "severity": "critical",
            "recommended_action": "pause",
            "confidence": 0.95,
            "rationale": "High velocity withdrawal drain detected.",
        }
    )
    res = validate_classification_json(payload)
    assert res.severity == "critical"
    assert res.recommended_action == "pause"
    assert res.confidence == 0.95
    assert res.is_actionable_pause() is True


def test_validate_classification_json_invalid_schema() -> None:
    # Malformed JSON
    res1 = validate_classification_json("not json")
    assert res1.error is not None
    assert res1.is_actionable_pause() is False

    # Unknown severity enum
    bad_enum = json.dumps({"severity": "bad", "recommended_action": "pause", "confidence": 0.9})
    res2 = validate_classification_json(bad_enum)
    assert res2.error is not None
    assert res2.is_actionable_pause() is False


def test_validate_classification_json_low_confidence() -> None:
    payload = json.dumps(
        {
            "severity": "critical",
            "recommended_action": "pause",
            "confidence": 0.75,  # below 0.8 threshold
            "rationale": "Uncertain signal.",
        }
    )
    res = validate_classification_json(payload)
    assert res.confidence == 0.75
    assert res.is_actionable_pause() is False  # fails closed


def test_validate_classification_json_excess_rationale_length() -> None:
    payload = json.dumps(
        {
            "severity": "critical",
            "recommended_action": "pause",
            "confidence": 0.95,
            "rationale": "X" * 300,  # exceeds 240 char limit
        }
    )
    res = validate_classification_json(payload)
    assert res.error is not None
    assert res.is_actionable_pause() is False


def test_catastrophic_input_without_ai_fails_closed() -> None:
    features = EventFeatures(
        event_count=1,
        total_amount_wei=15 * 10**18,  # > 10 ETH threshold
        unique_actors=1,
        window_seconds=60,
        velocity_bps=50000,
        max_single_amount_wei=15 * 10**18,
        latest_block=100,
        latest_timestamp=1000,
    )
    res = classify_features(features)
    assert res.is_catastrophic_override is False
    assert res.error == "AI unavailable"
    assert res.is_actionable_pause() is False


def test_classify_features_high_velocity() -> None:
    features = EventFeatures(
        event_count=4,
        total_amount_wei=5 * 10**18,
        unique_actors=2,
        window_seconds=60,
        velocity_bps=30000,  # 3x baseline
        max_single_amount_wei=2 * 10**18,
        latest_block=100,
        latest_timestamp=1000,
    )
    res = classify_features(features)
    assert res.error == "AI unavailable"
    assert res.is_actionable_pause() is False


def test_classify_features_benign() -> None:
    features = EventFeatures(
        event_count=1,
        total_amount_wei=10**16,  # 0.01 ETH
        unique_actors=1,
        window_seconds=300,
        velocity_bps=100,
        max_single_amount_wei=10**16,
        latest_block=100,
        latest_timestamp=1000,
    )
    res = classify_features(features)
    assert res.severity == "info"
    assert res.recommended_action == "none"
    assert res.is_actionable_pause() is False


def test_classify_features_llm_evaluator_injection() -> None:
    features = EventFeatures(
        event_count=2,
        total_amount_wei=2 * 10**18,
        unique_actors=1,
        window_seconds=60,
        velocity_bps=5000,
        max_single_amount_wei=10**18,
        latest_block=100,
        latest_timestamp=1000,
    )

    def mock_llm(feat_dict: dict) -> str:  # type: ignore[type-arg]
        return json.dumps(
            {
                "severity": "critical",
                "recommended_action": "pause",
                "confidence": 0.92,
                "rationale": "LLM detected rapid drain anomaly.",
            }
        )

    res = classify_features(features, llm_evaluator=mock_llm)
    assert res.severity == "critical"
    assert res.confidence == 0.92
    assert res.is_actionable_pause() is True


def test_classify_features_llm_timeout_fail_closed() -> None:
    features = EventFeatures(
        event_count=2,
        total_amount_wei=2 * 10**18,
        unique_actors=1,
        window_seconds=60,
        velocity_bps=5000,
        max_single_amount_wei=10**18,
        latest_block=100,
        latest_timestamp=1000,
    )

    def crashing_llm(feat_dict: dict) -> str:  # type: ignore[type-arg]
        raise TimeoutError("Model endpoint timed out")

    res = classify_features(features, llm_evaluator=crashing_llm)
    assert res.error is not None
    assert res.is_actionable_pause() is False  # fail closed
