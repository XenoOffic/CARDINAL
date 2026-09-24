from runtime.vm.safety import (
    SafetyCheckStatus,
    SafetyCheckType,
    SafetyGate,
    SafetyGateStatus,
)


def test_all_checks_pass() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=True,
        policy_passed=True,
    )

    assert (
        result.status
        == SafetyGateStatus.APPROVED
    )

    assert result.approved is True
    assert len(result.checks) == 4
    assert result.failed_checks == ()

    assert all(
        check.status
        == SafetyCheckStatus.PASSED
        for check in result.checks
    )


def test_verification_failure_blocks_candidate() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=False,
        resource_limits_passed=True,
        regression_passed=True,
        policy_passed=True,
    )

    assert (
        result.status
        == SafetyGateStatus.BLOCKED
    )

    assert result.approved is False
    assert len(result.failed_checks) == 1

    assert (
        result.failed_checks[0].check_type
        == SafetyCheckType.VERIFICATION
    )


def test_resource_failure_blocks_candidate() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=False,
        regression_passed=True,
        policy_passed=True,
    )

    assert (
        result.status
        == SafetyGateStatus.BLOCKED
    )

    assert (
        result.failed_checks[0].check_type
        == SafetyCheckType.RESOURCE
    )


def test_regression_failure_blocks_candidate() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=False,
        policy_passed=True,
    )

    assert (
        result.status
        == SafetyGateStatus.BLOCKED
    )

    assert (
        result.failed_checks[0].check_type
        == SafetyCheckType.REGRESSION
    )


def test_policy_failure_blocks_candidate() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=True,
        policy_passed=False,
    )

    assert (
        result.status
        == SafetyGateStatus.BLOCKED
    )

    assert (
        result.failed_checks[0].check_type
        == SafetyCheckType.POLICY
    )


def test_multiple_failures_are_reported() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=False,
        resource_limits_passed=False,
        regression_passed=False,
        policy_passed=True,
    )

    assert (
        result.status
        == SafetyGateStatus.BLOCKED
    )

    assert len(
        result.failed_checks
    ) == 3

    failed_types = {
        check.check_type
        for check in result.failed_checks
    }

    assert failed_types == {
        SafetyCheckType.VERIFICATION,
        SafetyCheckType.RESOURCE,
        SafetyCheckType.REGRESSION,
    }


def test_evidence_is_preserved() -> None:
    gate = SafetyGate()

    evidence = {
        "experiment": "exp-001",
        "candidate": "candidate-001",
        "instructions_used": 100,
        "memory_used_bytes": 1024,
    }

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=True,
        policy_passed=True,
        evidence=evidence,
    )

    for check in result.checks:
        assert check.evidence == evidence


def test_missing_evidence_defaults_to_empty_mapping() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=True,
        policy_passed=True,
    )

    for check in result.checks:
        assert check.evidence == {}


def test_gate_is_deterministic() -> None:
    gate = SafetyGate()

    first = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=False,
        policy_passed=True,
    )

    second = gate.evaluate(
        verification_passed=True,
        resource_limits_passed=True,
        regression_passed=False,
        policy_passed=True,
    )

    assert first == second


def test_failed_check_statuses_are_specific() -> None:
    gate = SafetyGate()

    result = gate.evaluate(
        verification_passed=False,
        resource_limits_passed=False,
        regression_passed=False,
        policy_passed=False,
    )

    statuses = {
        check.check_type: check.status
        for check in result.checks
    }

    assert (
        statuses[SafetyCheckType.VERIFICATION]
        == SafetyCheckStatus.FAILED
    )

    assert (
        statuses[SafetyCheckType.RESOURCE]
        == SafetyCheckStatus.BLOCKED
    )

    assert (
        statuses[SafetyCheckType.REGRESSION]
        == SafetyCheckStatus.FAILED
    )

    assert (
        statuses[SafetyCheckType.POLICY]
        == SafetyCheckStatus.BLOCKED
    )
