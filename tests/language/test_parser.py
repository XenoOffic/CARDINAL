from language.ast import (
    AgentDeclaration,
    BehaviorDeclaration,
    Literal,
    VariableDeclaration,
)
from language.parser.parser import Parser


def test_parse_hello_agent():
    source = """
    agent HelloAgent {
        behavior greet {
            let message: String = "Hello, CARDINAL";
            return;
        }
    }
    """

    program = Parser.from_source(source).parse()

    assert len(program.declarations) == 1

    agent = program.declarations[0]

    assert isinstance(agent, AgentDeclaration)
    assert agent.name == "HelloAgent"

    assert len(agent.members) == 1

    behavior = agent.members[0]

    assert isinstance(behavior, BehaviorDeclaration)
    assert behavior.name == "greet"

    declaration = behavior.body[0]

    assert isinstance(declaration, VariableDeclaration)
    assert declaration.name == "message"
    assert declaration.type_name == "String"

    assert isinstance(declaration.value, Literal)
    assert declaration.value.value == "Hello, CARDINAL"
