from runtime.vm.analysis import (
    AgentActivity,
    BehaviorPerformance,
    RuntimeAnalyzer,
    RuntimeAnomaly,
    RuntimeInsight,
)
from runtime.vm.observability import (
    RuntimeHistory,
)


def make_history() -> RuntimeHistory:
    history = RuntimeHistory()

    history.record(
        "agent.spawned",
        agent="Alpha",
    )

    history.record(
        "agent.started",
        agent="Alpha",
    )

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "behavior.completed",
        agent="Alpha",
        behavior="think",
    )

    history.record(
        "message.sent",
        agent="Alpha",
    )

    history.record(
        "message.received",
        agent="Alpha",
    )

    history.record(
        "event.processed",
        agent="Alpha",
        behavior="think",
    )

    return history


def test_behavior_performance() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    performance = (
        analyzer.behavior_performance(
            "think"
        )
    )

    assert isinstance(
        performance,
        BehaviorPerformance,
    )

    assert performance.executions == 1
    assert performance.completed == 1
    assert performance.errors == 0
    assert performance.error_rate == 0.0
    assert performance.success_rate == 1.0


def test_agent_activity() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    activity = analyzer.agent_activity(
        "Alpha"
    )

    assert isinstance(
        activity,
        AgentActivity,
    )

    assert activity.total_events == 3
    assert activity.messages_sent == 1
    assert activity.messages_received == 1
    assert activity.behaviors_started == 1
    assert activity.behaviors_completed == 1
    assert activity.errors == 0
    assert activity.total_messages == 2


def test_high_error_rate_anomaly() -> None:
    history = make_history()

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="unstable",
    )

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="unstable",
    )

    analyzer = RuntimeAnalyzer(
        history
    )

    anomalies = analyzer.detect_anomalies()

    assert any(
        anomaly.anomaly_type
        == "high_error_rate"
        for anomaly in anomalies
    )

    assert all(
        isinstance(
            anomaly,
            RuntimeAnomaly,
        )
        for anomaly in anomalies
    )


def test_no_anomaly_for_successful_behavior() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    anomalies = analyzer.detect_anomalies()

    assert anomalies == []


def test_behavior_with_only_errors_has_full_error_rate() -> None:
    history = RuntimeHistory()

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="broken",
    )

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="broken",
    )

    analyzer = RuntimeAnalyzer(
        history
    )

    performance = (
        analyzer.behavior_performance(
            "broken"
        )
    )

    assert performance.executions == 1
    assert performance.completed == 0
    assert performance.errors == 1
    assert performance.error_rate == 1.0


def test_report_contains_behaviors_and_agents() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    report = analyzer.report()

    assert "think" in report.behaviors
    assert "Alpha" in report.agents
    assert report.anomalies == []


def test_generate_insights_from_errors() -> None:
    history = RuntimeHistory()

    history.record(
        "behavior.started",
        agent="Alpha",
        behavior="broken",
    )

    history.record(
        "runtime.error",
        agent="Alpha",
        behavior="broken",
    )

    analyzer = RuntimeAnalyzer(
        history
    )

    insights = analyzer.generate_insights()

    assert len(insights) == 1

    insight = insights[0]

    assert isinstance(
        insight,
        RuntimeInsight,
    )

    assert insight.insight_type == (
        "reliability"
    )

    assert insight.subject == "broken"


def test_missing_behavior_returns_empty_statistics() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    performance = (
        analyzer.behavior_performance(
            "unknown"
        )
    )

    assert performance.executions == 0
    assert performance.completed == 0
    assert performance.errors == 0
    assert performance.error_rate == 0.0
    assert performance.success_rate == 0.0


def test_missing_agent_returns_empty_statistics() -> None:
    analyzer = RuntimeAnalyzer(
        make_history()
    )

    activity = analyzer.agent_activity(
        "unknown"
    )

    assert activity.agent == "unknown"
    assert activity.total_events == 0
    assert activity.messages_sent == 0
    assert activity.messages_received == 0


def test_invalid_error_threshold() -> None:
    try:
        RuntimeAnalyzer(
            make_history(),
            error_rate_threshold=1.5,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_invalid_duration_threshold() -> None:
    try:
        RuntimeAnalyzer(
            make_history(),
            duration_threshold=-1.0,
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected ValueError"
    )


def test_analyzer_is_read_only() -> None:
    history = make_history()

    before = list(history.events)

    analyzer = RuntimeAnalyzer(
        history
    )

    analyzer.report()
    analyzer.detect_anomalies()
    analyzer.generate_insights()

    after = list(history.events)

    assert after == before
