from __future__ import annotations

from compiler.ir import IRGenerator, IRModule
from language.parser import Parser
from language.semantics import SemanticAnalyzer
from runtime.vm import VM


class CardinalPipeline:
    """End-to-end CARDINAL compilation and execution pipeline."""

    def compile(self, source: str) -> IRModule:
        program = Parser.from_source(source).parse()

        SemanticAnalyzer().analyze(program)

        return IRGenerator().generate(program)

    def run(self, source: str) -> object | None:
        module = self.compile(source)

        if not module.functions:
            return None

        main = next(
            (
                function
                for function in module.functions
                if function.name == "main"
            ),
            module.functions[0],
        )

        return VM().execute(main, module)
