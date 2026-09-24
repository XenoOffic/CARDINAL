from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from .observability import RuntimeEvent, RuntimeHistory


@dataclass(frozen=True)
class BehaviorPerformance:
    """Performance information for one behavior."""

    behavior: str
    executions: int = 0
    completed: int = 0
    errors: int = 0
    average_duration: float = 0.0
    minimum_duration: float = 0.0
    maximum_duration: float = 0.0

    @property
    def error_rate(self) -> float:
        if self.executions == 0:
            return 0.0

        return self.errors / self.executions

    @property
    def success_rate(self) -> float:
        if self.executions == 0:
            return 0.0

        return self.completed / self.executions


@dataclass(frozen=True)
class AgentActivity:
    """Aggregated activity information for one agent."""

    agent: str
    total_events: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    behaviors_started: int = 0
    behaviors_completed: int = 0
    errors: int = 0

    @property
    def total_messages(self) -> int:
        return (
            self.messages_sent
            + self.messages_received
        )


@dataclass(frozen=True)
class RuntimeAnomaly:
    """Detected runtime anomaly."""

    anomaly_type: str
    severity: str
    agent: str | None = None
    behavior: str | None = None
    value: float | int | None = None
    threshold: float | int | None = None
    description: str = ""


@dataclass(frozen=True)
class RuntimeInsight:
    """High-level deterministic runtime insight."""

    insight_type: str
    subject: str
    description: str
    data: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class PerformanceReport:
    """Complete performance analysis report."""

    behaviors: dict[str, BehaviorPerformance] = field(
        default_factory=dict
    )
    agents: dict[str, AgentActivity] = field(
        default_factory=dict
    )
    anomalies: list[RuntimeAnomaly] = field(
        default_factory=list
    )
    insights: list[RuntimeInsight] = field(
        default_factory=list
    )


class RuntimeAnalyzer:
    """
    Deterministic analysis engine for CARDINAL runtime history.

    The analyzer is read-only. It never changes runtime state,
    agent state, source code, or execution policy.
    """

    def __init__(
        self,
        history: RuntimeHistory,
        *,
        error_rate_threshold: float = 0.25,
        duration_threshold: float = 1.0,
    ) -> None:
        if not 0.0 <= error_rate_threshold <= 1.0:
            raise ValueError(
                "error_rate_threshold must be between 0 and 1."
            )

        if duration_threshold < 0:
            raise ValueError(
                "duration_threshold cannot be negative."
            )

        self.history = history
        self.error_rate_threshold = (
            error_rate_threshold
        )
        self.duration_threshold = (
            duration_threshold
        )

    def behavior_performance(
        self,
        behavior_name: str,
    ) -> BehaviorPerformance:
        events = self.history.filter()

        starts: list[RuntimeEvent] = [
            event
            for event in events
            if (
                event.event_type
                == "behavior.started"
                and event.behavior
                == behavior_name
            )
        ]

        completions: list[RuntimeEvent] = [
            event
            for event in events
            if (
                event.event_type
                == "behavior.completed"
                and event.behavior
                == behavior_name
            )
        ]

        errors: list[RuntimeEvent] = [
            event
            for event in events
            if (
                event.event_type
                == "runtime.error"
                and event.behavior
                == behavior_name
            )
        ]

        durations = self._behavior_durations(
            starts,
            completions,
        )

        return BehaviorPerformance(
            behavior=behavior_name,
            executions=len(starts),
            completed=len(completions),
            errors=len(errors),
            average_duration=(
                mean(durations)
                if durations
                else 0.0
            ),
            minimum_duration=(
                min(durations)
                if durations
                else 0.0
            ),
            maximum_duration=(
                max(durations)
                if durations
                else 0.0
            ),
        )

    def agent_activity(
        self,
        agent_name: str,
    ) -> AgentActivity:
        events = self.history.filter(
            agent=agent_name
        )

        total_events = 0
        messages_sent = 0
        messages_received = 0
        behaviors_started = 0
        behaviors_completed = 0
        errors = 0

        for event in events:
            if event.event_type in {
                "agent.spawned",
                "agent.started",
                "agent.stopped",
                "event.processed",
            }:
                total_events += 1

            elif event.event_type == "message.sent":
                messages_sent += 1

            elif event.event_type == "message.received":
                messages_received += 1

            elif event.event_type == "behavior.started":
                behaviors_started += 1

            elif event.event_type == "behavior.completed":
                behaviors_completed += 1

            elif event.event_type == "runtime.error":
                errors += 1

        return AgentActivity(
            agent=agent_name,
            total_events=total_events,
            messages_sent=messages_sent,
            messages_received=messages_received,
            behaviors_started=behaviors_started,
            behaviors_completed=behaviors_completed,
            errors=errors,
        )

    def detect_anomalies(
        self,
    ) -> list[RuntimeAnomaly]:
        anomalies: list[RuntimeAnomaly] = []

        behavior_names = {
            event.behavior
            for event in self.history.events
            if event.behavior is not None
        }

        for behavior_name in sorted(
            behavior_names
        ):
            performance = (
                self.behavior_performance(
                    behavior_name
                )
            )

            if (
                performance.executions > 0
                and performance.error_rate
                >= self.error_rate_threshold
            ):
                anomalies.append(
                    RuntimeAnomaly(
                        anomaly_type="high_error_rate",
                        severity="warning",
                        behavior=behavior_name,
                        value=performance.error_rate,
                        threshold=(
                            self.error_rate_threshold
                        ),
                        description=(
                            f"Behavior '{behavior_name}' "
                            "has an elevated error rate."
                        ),
                    )
                )

            if (
                performance.average_duration
                > self.duration_threshold
            ):
                anomalies.append(
                    RuntimeAnomaly(
                        anomaly_type="slow_behavior",
                        severity="warning",
                        behavior=behavior_name,
                        value=(
                            performance.average_duration
                        ),
                        threshold=(
                            self.duration_threshold
                        ),
                        description=(
                            f"Behavior '{behavior_name}' "
                            "has an elevated average "
                            "execution duration."
                        ),
                    )
                )

        return anomalies

    def generate_insights(
        self,
    ) -> list[RuntimeInsight]:
        insights: list[RuntimeInsight] = []

        anomalies = self.detect_anomalies()

        for anomaly in anomalies:
            if (
                anomaly.anomaly_type
                == "high_error_rate"
            ):
                insights.append(
                    RuntimeInsight(
                        insight_type="reliability",
                        subject=(
                            anomaly.behavior
                            or "runtime"
                        ),
                        description=(
                            "Repeated execution failures "
                            "were observed."
                        ),
                        data={
                            "error_rate": anomaly.value,
                            "threshold": anomaly.threshold,
                        },
                    )
                )

            elif (
                anomaly.anomaly_type
                == "slow_behavior"
            ):
                insights.append(
                    RuntimeInsight(
                        insight_type="performance",
                        subject=(
                            anomaly.behavior
                            or "runtime"
                        ),
                        description=(
                            "A behavior shows elevated "
                            "average execution duration."
                        ),
                        data={
                            "average_duration": anomaly.value,
                            "threshold": anomaly.threshold,
                        },
                    )
                )

        return insights

    def report(self) -> PerformanceReport:
        behavior_names = sorted(
            {
                event.behavior
                for event in self.history.events
                if event.behavior is not None
            }
        )

        agent_names = sorted(
            {
                event.agent
                for event in self.history.events
                if event.agent is not None
            }
        )

        behaviors = {
            name: self.behavior_performance(name)
            for name in behavior_names
        }

        agents = {
            name: self.agent_activity(name)
            for name in agent_names
        }

        anomalies = self.detect_anomalies()

        insights = self.generate_insights()

        return PerformanceReport(
            behaviors=behaviors,
            agents=agents,
            anomalies=anomalies,
            insights=insights,
        )

    @staticmethod
    def _behavior_durations(
        starts: list[RuntimeEvent],
        completions: list[RuntimeEvent],
    ) -> list[float]:
        durations: list[float] = []

        completion_index = 0

        for start in starts:
            while (
                completion_index
                < len(completions)
                and completions[
                    completion_index
                ].timestamp
                < start.timestamp
            ):
                completion_index += 1

            if completion_index >= len(completions):
                break

            completion = completions[
                completion_index
            ]

            duration = (
                completion.timestamp
                - start.timestamp
            )

            if duration >= 0:
                durations.append(duration)

            completion_index += 1

        return durations
