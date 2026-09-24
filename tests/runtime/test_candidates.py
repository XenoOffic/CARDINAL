import pytest

from runtime.vm.candidates import (
    CandidateEngine,
    CandidateStatus,
    EvolutionCandidate,
)


def make_candidate(
    identifier: str = "candidate-1",
    benefit: float = 0.9,
    risk: float = 0.1,
) -> EvolutionCandidate:
    return EvolutionCandidate(
        identifier=identifier,
        description="Test evolution candidate.",
        expected_benefit=benefit,
        risk=risk,
    )


def test_candidate_creation() -> None:
    candidate = make_candidate()

    assert candidate.identifier == "candidate-1"
    assert candidate.expected_benefit == 0.9
    assert candidate.risk == 0.1


def test_empty_identifier_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_candidate(identifier="")


def test_empty_description_is_rejected() -> None:
    with pytest.raises(ValueError):
        EvolutionCandidate(
            identifier="candidate",
            description="",
            expected_benefit=0.5,
            risk=0.2,
        )


def test_invalid_benefit_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_candidate(benefit=1.5)


def test_invalid_risk_is_rejected() -> None:
    with pytest.raises(ValueError):
        make_candidate(risk=-0.1)


def test_candidate_score_is_deterministic() -> None:
    engine = CandidateEngine()

    candidate = make_candidate(
        benefit=0.8,
        risk=0.25,
    )

    first = engine.evaluate_one(candidate)
    second = engine.evaluate_one(candidate)

    assert first.score == second.score
    assert first.status == second.status


def test_high_benefit_low_risk_is_eligible() -> None:
    engine = CandidateEngine()

    evaluation = engine.evaluate_one(
        make_candidate(
            benefit=0.9,
            risk=0.1,
        )
    )

    assert evaluation.status == CandidateStatus.ELIGIBLE
    assert evaluation.score == pytest.approx(0.81)


def test_high_risk_candidate_is_rejected() -> None:
    engine = CandidateEngine(
        maximum_risk=0.5,
    )

    evaluation = engine.evaluate_one(
        make_candidate(
            benefit=1.0,
            risk=0.8,
        )
    )

    assert evaluation.status == CandidateStatus.REJECTED
    assert "risk" in evaluation.reason.lower()


def test_low_score_candidate_is_rejected() -> None:
    engine = CandidateEngine(
        minimum_score=0.8,
    )

    evaluation = engine.evaluate_one(
        make_candidate(
            benefit=0.6,
            risk=0.5,
        )
    )

    assert evaluation.status == CandidateStatus.REJECTED
    assert "score" in evaluation.reason.lower()


def test_multiple_candidates_are_evaluated() -> None:
    engine = CandidateEngine()

    candidates = [
        make_candidate(
            identifier="candidate-a",
            benefit=0.9,
            risk=0.1,
        ),
        make_candidate(
            identifier="candidate-b",
            benefit=0.7,
            risk=0.2,
        ),
        make_candidate(
            identifier="candidate-c",
            benefit=0.4,
            risk=0.8,
        ),
    ]

    report = engine.evaluate(candidates)

    assert report.total == 3
    assert len(report.eligible) == 2
    assert len(report.rejected) == 1


def test_best_candidate_is_selected_deterministically() -> None:
    engine = CandidateEngine()

    candidates = [
        make_candidate(
            identifier="candidate-a",
            benefit=0.8,
            risk=0.2,
        ),
        make_candidate(
            identifier="candidate-b",
            benefit=0.95,
            risk=0.1,
        ),
    ]

    report = engine.evaluate(candidates)

    assert report.best is not None
    assert (
        report.best.candidate.identifier
        == "candidate-b"
    )


def test_best_returns_none_when_everything_is_rejected() -> None:
    engine = CandidateEngine(
        maximum_risk=0.1,
    )

    report = engine.evaluate(
        [
            make_candidate(
                identifier="candidate-a",
                benefit=1.0,
                risk=0.9,
            ),
        ]
    )

    assert report.best is None


def test_eligible_candidates_are_separated() -> None:
    engine = CandidateEngine()

    report = engine.evaluate(
        [
            make_candidate(
                identifier="good",
                benefit=0.9,
                risk=0.1,
            ),
            make_candidate(
                identifier="bad",
                benefit=0.2,
                risk=0.9,
            ),
        ]
    )

    assert [
        item.candidate.identifier
        for item in report.eligible
    ] == ["good"]

    assert [
        item.candidate.identifier
        for item in report.rejected
    ] == ["bad"]


def test_empty_candidate_list_is_valid() -> None:
    engine = CandidateEngine()

    report = engine.evaluate([])

    assert report.total == 0
    assert report.best is None
    assert report.eligible == ()
    assert report.rejected == ()


def test_candidate_engine_configuration_is_validated() -> None:
    with pytest.raises(ValueError):
        CandidateEngine(
            minimum_score=1.5,
        )

    with pytest.raises(ValueError):
        CandidateEngine(
            maximum_risk=-0.1,
        )


def test_candidate_metadata_is_preserved() -> None:
    candidate = EvolutionCandidate(
        identifier="candidate",
        description="Metadata test.",
        expected_benefit=0.8,
        risk=0.2,
        metadata={
            "source": "runtime-analysis",
            "version": 1,
        },
    )

    assert candidate.metadata["source"] == (
        "runtime-analysis"
    )
    assert candidate.metadata["version"] == 1


def test_candidate_order_does_not_change_individual_scores() -> None:
    engine = CandidateEngine()

    candidate_a = make_candidate(
        identifier="a",
        benefit=0.8,
        risk=0.2,
    )

    candidate_b = make_candidate(
        identifier="b",
        benefit=0.7,
        risk=0.1,
    )

    first = engine.evaluate(
        [candidate_a, candidate_b]
    )

    second = engine.evaluate(
        [candidate_b, candidate_a]
    )

    scores_first = {
        item.candidate.identifier: item.score
        for item in first.evaluations
    }

    scores_second = {
        item.candidate.identifier: item.score
        for item in second.evaluations
    }

    assert scores_first == scores_second
