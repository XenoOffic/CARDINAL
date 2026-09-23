from __future__ import annotations

from dataclasses import dataclass, field

from .instructions import Instruction


@dataclass
class IRFunction:
    """
    Compiled CARDINAL function.

    A function owns its own instruction stream and parameters.
    """

    name: str
    parameters: list[str] = field(default_factory=list)
    instructions: list[Instruction] = field(
        default_factory=list
    )

    def emit(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)


@dataclass
class IRBehavior:
    """
    Compiled behavior belonging to an agent.

    A behavior is intentionally separate from a normal function.
    This distinction becomes important when CARDINAL gains:
    - scheduling
    - autonomous execution
    - event triggers
    - priorities
    - goals
    - cognition
    """

    name: str
    instructions: list[Instruction] = field(
        default_factory=list
    )

    def emit(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)


@dataclass
class IRAgent:
    """
    Compiled representation of a CARDINAL agent.

    The agent contains:
    - its identity
    - optional parent agent
    - persistent state declarations
    - executable behaviors
    - functions belonging to the agent
    """

    name: str
    parent: str | None = None

    state: list[str] = field(
        default_factory=list
    )

    behaviors: list[IRBehavior] = field(
        default_factory=list
    )

    functions: list[IRFunction] = field(
        default_factory=list
    )

    def add_state(self, name: str) -> None:
        if name not in self.state:
            self.state.append(name)

    def add_behavior(
        self,
        behavior: IRBehavior,
    ) -> None:
        self.behaviors.append(behavior)

    def add_function(
        self,
        function: IRFunction,
    ) -> None:
        self.functions.append(function)

    def get_behavior(
        self,
        name: str,
    ) -> IRBehavior | None:
        for behavior in self.behaviors:
            if behavior.name == name:
                return behavior

        return None

    def get_function(
        self,
        name: str,
    ) -> IRFunction | None:
        for function in self.functions:
            if function.name == name:
                return function

        return None


@dataclass
class IRModule:
    """
    Complete compiled representation of a CARDINAL program.

    The module can contain:
    - normal functions
    - autonomous agents
    """

    name: str = "main"

    functions: list[IRFunction] = field(
        default_factory=list
    )

    agents: list[IRAgent] = field(
        default_factory=list
    )

    def add_function(
        self,
        function: IRFunction,
    ) -> None:
        self.functions.append(function)

    def add_agent(
        self,
        agent: IRAgent,
    ) -> None:
        self.agents.append(agent)

    def get_function(
        self,
        name: str,
    ) -> IRFunction | None:
        for function in self.functions:
            if function.name == name:
                return function

        return None

    def get_agent(
        self,
        name: str,
    ) -> IRAgent | None:
        for agent in self.agents:
            if agent.name == name:
                return agent

        return None
