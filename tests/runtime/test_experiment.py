import pytest

from runtime.vm.experiment import (
    Experiment,
    ExperimentCandidate,
    ExperimentEngine,
    ExperimentHypothesis,
    ExperimentReport,
    ExperimentResult,
    ExperimentStatus,
    VerificationCriteria,
    VerificationStatus,
)


def make_experiment() -> Experiment:
    return Experiment(
        identifier="exp-001",
        hypothesis=ExperimentHypothesis(
            statement=(
                "Reducing unnecessary work "
                "improves execution time."
            ),
            rationale=(
                "Runtime analysis detected "
                "elevated duration."
            ),
            expected_outcome=(
                "Execution becomes faster."
            ),
        ),
        candidate=ExperimentCandidate(
            identifier="candidate-001",
            description=(
                "Optimized execution strategy."
            ),
            metadata={
                "version": 1,
            },
        ),
        criteria=(
            VerificationCriteria(
                name="duration",
                expected=1.0,
                operator="<=",
            ),
        ),
    )


def test_hypothesis_contains_required_data() -> None:
    hypothesis = ExperimentHypothesis(
        statement="Test hypothesis.",
        rationale="Observed evidence.",
        expected_outcome="Improvement.",
    )

    assert hypothesis.statement == (
        "Test hypothesis."
    )

    assert hypothesis.rationale == (
        "Observed evidence."
    )


def test_candidate_contains_metadata() -> None:
    candidate = ExperimentCandidate(
        identifier="candidate",
        description="Candidate change.",
        metadata={
            "version": 2,
        },
    )

    assert candidate.identifier == (
        "candidate"
    )

    assert candidate.metadata["version"] == 2


def test_experiment_starts_as_proposed() -> None:
    experiment = make_experiment()

    assert experiment.status == (
        ExperimentStatus.PROPOSED
    )

    assert experiment.verification == (
        VerificationStatus.NOT_VERIFIED
    )


def test_experiment_start() -> None:
    experiment = make_experiment()

    experiment.start()

    assert experiment.status == (
        ExperimentStatus.RUNNING
    )


def test_experiment_records_result() -> None:
    experiment = make_experiment()

    experiment.start()

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=0.8,
            passed=True,
            details="Within threshold.",
        )
    )

    assert len(
        experiment.results
    ) == 1

    assert experiment.results[0].passed is True


def test_successful_experiment_verifies() -> None:
    experiment = make_experiment()

    experiment.start()

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=0.8,
            passed=True,
        )
    )

    verification = experiment.verify()

    assert verification == (
        VerificationStatus.VERIFIED
    )

    assert experiment.status == (
        ExperimentStatus.PASSED
    )


def test_failed_experiment_is_rejected() -> None:
    experiment = make_experiment()

    experiment.start()

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=2.0,
            passed=False,
        )
    )

    verification = experiment.verify()

    assert verification == (
        VerificationStatus.REJECTED
    )

    assert experiment.status == (
        ExperimentStatus.FAILED
    )


def test_empty_results_fail_verification() -> None:
    experiment = make_experiment()

    experiment.start()

    verification = experiment.verify()

    assert verification == (
        VerificationStatus.REJECTED
    )

    assert experiment.status == (
        ExperimentStatus.FAILED
    )


def test_experiment_can_be_explicitly_rejected() -> None:
    experiment = make_experiment()

    experiment.reject()

    assert experiment.status == (
        ExperimentStatus.REJECTED
    )

    assert experiment.verification == (
        VerificationStatus.REJECTED
    )


def test_engine_registers_experiment() -> None:
    engine = ExperimentEngine()
    experiment = make_experiment()

    engine.register(experiment)

    assert engine.get(
        "exp-001"
    ) is experiment


def test_engine_rejects_duplicate_identifier() -> None:
    engine = ExperimentEngine()

    engine.register(
        make_experiment()
    )

    with pytest.raises(ValueError):
        engine.register(
            make_experiment()
        )


def test_engine_starts_experiment() -> None:
    engine = ExperimentEngine()

    engine.register(
        make_experiment()
    )

    experiment = engine.start(
        "exp-001"
    )

    assert experiment.status == (
        ExperimentStatus.RUNNING
    )


def test_engine_verifies_experiment() -> None:
    engine = ExperimentEngine()
    experiment = make_experiment()

    engine.register(experiment)
    engine.start("exp-001")

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=0.5,
            passed=True,
        )
    )

    result = engine.verify(
        "exp-001"
    )

    assert result == (
        VerificationStatus.VERIFIED
    )


def test_engine_report() -> None:
    engine = ExperimentEngine()
    experiment = make_experiment()

    engine.register(experiment)
    engine.start("exp-001")

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=0.5,
            passed=True,
        )
    )

    report = engine.report(
        "exp-001"
    )

    assert isinstance(
        report,
        ExperimentReport,
    )

    assert report.total_results == 1
    assert report.passed_results == 1
    assert report.failed_results == 0
    assert report.success_rate == 1.0


def test_experiment_rejects_empty_identifier() -> None:
    with pytest.raises(ValueError):
        Experiment(
            identifier="",
            hypothesis=ExperimentHypothesis(
                statement="a",
                rationale="b",
                expected_outcome="c",
            ),
            candidate=ExperimentCandidate(
                identifier="candidate",
                description="candidate",
            ),
            criteria=(
                VerificationCriteria(
                    name="test",
                    expected=True,
                ),
            ),
        )


def test_criterion_rejects_unknown_operator() -> None:
    with pytest.raises(ValueError):
        VerificationCriteria(
            name="metric",
            expected=1,
            operator="invalid",
        )


def test_result_cannot_be_recorded_before_start() -> None:
    experiment = make_experiment()

    with pytest.raises(RuntimeError):
        experiment.record_result(
            ExperimentResult(
                metric="duration",
                actual=1.0,
                passed=True,
            )
        )


def test_experiment_cannot_start_twice() -> None:
    experiment = make_experiment()

    experiment.start()

    with pytest.raises(RuntimeError):
        experiment.start()


def test_completed_experiment_cannot_be_rejected() -> None:
    experiment = make_experiment()

    experiment.start()

    experiment.record_result(
        ExperimentResult(
            metric="duration",
            actual=0.5,
            passed=True,
        )
    )

    experiment.verify()

    with pytest.raises(RuntimeError):
        experiment.reject()


def test_engine_unknown_experiment() -> None:
    engine = ExperimentEngine()

    with pytest.raises(KeyError):
        engine.get("unknown")
