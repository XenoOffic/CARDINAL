import pytest

from language.parser import Parser
from language.semantics import SemanticAnalyzer, SemanticError


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
