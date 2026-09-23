import pytest

from language.parser import Parser
from language.semantics import (
    SemanticAnalyzer,
    SemanticError,
)


def analyze(source: str) -> None:
    program = Parser.from_source(source).parse()
    SemanticAnalyzer().analyze(program)


def test_valid_typed_variable():
    source = """
    agent TestAgent {
        behavior test {
            let message: String = "hello";
            return;
        }
    }
    """

    analyze(source)


def test_invalid_type_assignment():
    source = """
    agent TestAgent {
        behavior test {
            let message: String = 42;
            return;
        }
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_unknown_identifier():
    source = """
    agent TestAgent {
        behavior test {
            let message: String = unknown;
            return;
        }
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_valid_typed_function():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }
    """

    analyze(source)


def test_invalid_function_return_type():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return "hello";
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_missing_function_return():
    source = """
    fn add(a: Int, b: Int) -> Int {
        let result: Int = a + b;
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_valid_function_call():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn calculate() -> Int {
        return add(10, 32);
    }
    """

    analyze(source)


def test_invalid_function_argument_type():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn calculate() -> Int {
        return add("hello", 32);
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_invalid_function_argument_count():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn calculate() -> Int {
        return add(10);
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_unknown_function():
    source = """
    fn calculate() -> Int {
        return does_not_exist(10);
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)


def test_function_return_type_flows_into_variable():
    source = """
    fn add(a: Int, b: Int) -> Int {
        return a + b;
    }

    fn calculate() -> Int {
        let result: Int = add(10, 32);
        return result;
    }
    """

    analyze(source)


def test_invalid_function_result_assignment():
    source = """
    fn text() -> String {
        return "hello";
    }

    fn calculate() -> Int {
        let result: Int = text();
        return result;
    }
    """

    with pytest.raises(SemanticError):
        analyze(source)
