from runtime.vm.analysis import (
    RuntimeAnomaly,
)
from runtime.vm.decision import (
    DecisionAction,
    DecisionEngine,
    DecisionEvidence,
    DecisionPriority,
    DecisionReport,
    RuntimeDecision,
)


def make_error_anomaly() -> RuntimeAnomaly:
    return RuntimeAnomaly(
        anomaly_type="high_error_rate",
        severity="warning",
        behavior="think",
        value=0.75,
        threshold=0.25,
        description=(
            "Behavior has a high error rate."
        ),
    )


def make_slow_anomaly() -> RuntimeAnomaly:
    return RuntimeAnomaly(
        anomaly_type="slow_behavior",
        severity="warning",
        behavior="render",
        value=2.5,
        threshold=1.0,
        description=(
            "Behavior is slow."
        ),
    )


def test_runtime_decision_contains_structured_data() -> None:
    decision = RuntimeDecision(
        target="behavior:think",
        action=DecisionAction.INVESTIGATE,
        priority=DecisionPriority.HIGH,
        reason="Repeated failures.",
        confidence=0.95,
    )

    assert decision.target == (
        "behavior:think"
    )

    assert decision.action == (
        DecisionAction.INVESTIGATE
    )

    assert decision.priority == (
        DecisionPriority.HIGH
    )

    assert decision.confidence == 0.95
    assert decision.requires_verification is True


def test_decision_evidence() -> None:
    evidence = DecisionEvidence(
        source="high_error_rate",
        value=0.75,
        description="High error rate.",
    )

    assert evidence.source == (
        "high_error_rate"
    )

    assert evidence.value == 0.75


def test_high_error_rate_creates_investigation() -> None:
    engine = DecisionEngine()

    decision = engine.decide_one(
        make_error_anomaly()
    )

    assert decision is not None

    assert decision.action == (
        DecisionAction.INVESTIGATE
    )

    assert decision.priority == (
        DecisionPriority.HIGH
    )

    assert decision.target == (
        "behavior:think"
    )

    assert decision.requires_verification is True


def test_slow_behavior_creates_monitor_decision() -> None:
    engine = DecisionEngine()

    decision = engine.decide_one(
        make_slow_anomaly()
    )

    assert decision is not None

    assert decision.action == (
        DecisionAction.MONITOR
    )

    assert decision.priority == (
        DecisionPriority.MEDIUM
    )

    assert decision.target == (
        "behavior:render"
    )


def test_unknown_anomaly_requires_verification() -> None:
    anomaly = RuntimeAnomaly(
        anomaly_type="unknown",
        severity="warning",
        agent="Alpha",
        value=10,
        threshold=5,
        description="Unknown condition.",
    )

    engine = DecisionEngine()

    decision = engine.decide_one(
        anomaly
    )

    assert decision is not None

    assert decision.action == (
        DecisionAction.VERIFY
    )

    assert decision.priority == (
        DecisionPriority.LOW
    )

    assert decision.target == (
        "agent:Alpha"
    )


def test_decision_report() -> None:
    engine = DecisionEngine()

    report = engine.decide(
        [
            make_error_anomaly(),
            make_slow_anomaly(),
        ]
    )

    assert isinstance(
        report,
        DecisionReport,
    )

    assert report.count == 2

    assert len(
        report.by_priority(
            DecisionPriority.HIGH
        )
    ) == 1

    assert len(
        report.by_priority(
            DecisionPriority.MEDIUM
        )
    ) == 1


def test_low_confidence_decision_can_be_filtered() -> None:
    engine = DecisionEngine(
        minimum_confidence=0.99
    )

    decision = engine.decide_one(
        make_error_anomaly()
    )

    assert decision is None


def test_decide_filters_low_confidence_decisions() -> None:
    engine = DecisionEngine(
        minimum_confidence=0.99
    )

    report = engine.decide(
        [
            make_error_anomaly(),
            make_slow_anomaly(),
        ]
    )

    assert report.count == 0


def test_invalid_confidence_is_rejected() -> None:
    try:
        RuntimeDecision(
            target="runtime",
            action=DecisionAction.VERIFY,
            priority=DecisionPriority.LOW,
            reason="Test.",
            confidence=2.0,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_empty_target_is_rejected() -> None:
    try:
        RuntimeDecision(
            target="",
            action=DecisionAction.VERIFY,
            priority=DecisionPriority.LOW,
            reason="Test.",
            confidence=0.5,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_empty_reason_is_rejected() -> None:
    try:
        RuntimeDecision(
            target="runtime",
            action=DecisionAction.VERIFY,
            priority=DecisionPriority.LOW,
            reason="",
            confidence=0.5,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_invalid_minimum_confidence_is_rejected() -> None:
    try:
        DecisionEngine(
            minimum_confidence=-0.1
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_engine_does_not_modify_anomaly() -> None:
    anomaly = make_error_anomaly()

    before = anomaly

    engine = DecisionEngine()

    engine.decide_one(anomaly)

    assert anomaly == before
