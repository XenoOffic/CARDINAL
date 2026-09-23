from __future__ import annotations

from dataclasses import dataclass, field

from .instructions import Instruction


@dataclass
class IRFunction:
    """Compiled CARDINAL function."""

    name: str
    parameters: list[str] = field(default_factory=list)
    instructions: list[Instruction] = field(
        default_factory=list
    )

    def emit(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)


@dataclass
class IRBehavior:
    """Compiled behavior belonging to an agent."""

    name: str
    instructions: list[Instruction] = field(
        default_factory=list
    )

    def emit(self, instruction: Instruction) -> None:
        self.instructions.append(instruction)


@dataclass
class IRAgent:
    """Compiled representation of a CARDINAL agent."""

    name: str
    parent: str | None = None

    state: list[str] = field(
        default_factory=list
    )

    initial_state: dict[str, object] = field(
        default_factory=dict
    )

    behaviors: list[IRBehavior] = field(
        default_factory=list
    )

    functions: list[IRFunction] = field(
        default_factory=list
    )

    def add_state(
        self,
        name: str,
        initial_value: object = None,
    ) -> None:
        if name not in self.state:
            self.state.append(name)

        self.initial_state[name] = initial_value

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
    """Complete compiled representation of a CARDINAL program."""

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
