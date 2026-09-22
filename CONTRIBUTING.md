# Contributing to CARDINAL

Thank you for your interest in contributing to CARDINAL.

CARDINAL is an ambitious open-source project focused on building an AI-native programming language, runtime, cognitive architecture, agent system, memory infrastructure, simulation environment, and controlled self-improvement framework.

Contributions of all sizes are welcome.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Repository Structure](#repository-structure)
- [Development Principles](#development-principles)
- [Issues](#issues)
- [Pull Requests](#pull-requests)
- [Commit Messages](#commit-messages)
- [Testing](#testing)
- [Documentation](#documentation)
- [Security](#security)
- [Architecture Changes](#architecture-changes)
- [Experimental Features](#experimental-features)
- [License](#license)

---

# Code of Conduct

All contributors are expected to maintain a respectful and constructive environment.

Contributors should:

- Be respectful to other contributors.
- Focus on technical discussion.
- Accept constructive criticism.
- Avoid harassment or personal attacks.
- Explain architectural disagreements with technical reasoning.
- Help maintain an inclusive development environment.

---

# Getting Started

Before contributing, make sure you have:

- Git
- Python
- Rust
- A modern code editor
- A GitHub account

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/CARDINAL.git
cd CARDINAL

Create a development branch:

git checkout -b feature/your-feature

Make your changes, test them, and commit them.


---

Repository Structure

CARDINAL is designed as a modular system.

CARDINAL/
│
├── language/
├── compiler/
├── runtime/
├── cognition/
├── memory/
├── agents/
├── learning/
├── evolution/
├── sandbox/
├── knowledge/
├── simulation/
├── security/
├── distributed/
├── observability/
├── interfaces/
│
├── tests/
├── benchmarks/
├── examples/
├── docs/
├── configs/
└── scripts/

Each major subsystem should remain as independent and modular as reasonably possible.


---

Development Principles

CARDINAL development follows several core principles.

Modularity

Components should have clear responsibilities and well-defined interfaces.

Avoid unnecessary coupling between subsystems.


---

Reproducibility

Experiments, benchmarks, and important changes should be reproducible whenever possible.


---

Testing

New functionality should include appropriate tests.

Do not rely exclusively on manual testing for important components.


---

Documentation

Public APIs, major architectural decisions, language features, and complex algorithms should be documented.


---

Security

Security must be considered during development rather than added afterward.

Components involving:

code execution

networking

filesystem access

AI agents

model execution

autonomous experimentation

system resources


must be designed with appropriate isolation and permission boundaries.


---

Issues

GitHub Issues can be used for:

Bug reports

Feature requests

Architecture discussions

Documentation problems

Performance problems

Compiler problems

Runtime problems

Research ideas


Before opening an issue, search existing issues to avoid duplicates.


---

Bug Reports

A useful bug report should include:

1. Description of the problem.


2. Expected behavior.


3. Actual behavior.


4. Steps to reproduce.


5. Operating system.


6. CARDINAL version or commit.


7. Relevant logs.


8. Minimal reproduction when possible.



Example:

Component:
Runtime

Version:
commit 1234567

Expected:
Agent process terminates after receiving shutdown event.

Actual:
Process remains active.

Steps:
1. Start runtime.
2. Create agent.
3. Send shutdown event.
4. Observe process.


---

Feature Requests

Feature requests should explain:

What problem the feature solves.

Why it belongs in CARDINAL.

Possible implementation approaches.

Potential architectural consequences.

Security implications when applicable.


Large features should be discussed before implementation.


---

Pull Requests

Before submitting a Pull Request:

1. Make sure your branch is up to date.


2. Run relevant tests.


3. Add tests for new functionality.


4. Update documentation when necessary.


5. Keep the change focused.


6. Explain architectural changes clearly.



Pull Requests should avoid mixing unrelated changes.


---

Commit Messages

Use clear and descriptive commit messages.

Recommended format:

type: short description

Examples:

feat: add cardinal lexer
fix: resolve parser token bug
docs: update runtime architecture
test: add parser regression tests
refactor: simplify AST nodes
perf: optimize scheduler queue
security: restrict sandbox filesystem access

Common types:

feat
fix
docs
test
refactor
perf
build
ci
security
chore


---

Testing

Tests should be placed inside the appropriate directory under:

tests/

Example:

tests/
├── compiler/
├── runtime/
├── cognition/
├── memory/
├── agents/
├── evolution/
└── security/

Run the appropriate test suite before submitting a Pull Request.


---

Benchmarks

Performance-sensitive changes should include benchmarks when appropriate.

Benchmarks should be reproducible and should clearly describe:

Hardware

Software environment

Dataset

Configuration

Baseline

New implementation

Results


Do not claim that an optimization improves performance without measurements.


---

Documentation

Documentation belongs primarily inside:

docs/

Important documentation includes:

Architecture

Language specification

Compiler design

Runtime design

API documentation

Security model

Agent architecture

Memory architecture

Evolution system

Development guides



---

Architecture Changes

Major architectural changes should be discussed before implementation.

Examples include:

Changing the language semantics.

Replacing the runtime architecture.

Introducing a new execution model.

Changing the memory architecture.

Changing the agent model.

Changing the security model.

Introducing distributed execution.

Changing the compiler pipeline.


Large architectural proposals should document:

Problem
Goals
Non-goals
Current architecture
Proposed architecture
Advantages
Disadvantages
Alternatives
Security considerations
Performance considerations
Migration strategy


---

Experimental Features

CARDINAL will contain experimental research systems.

Experimental features must be clearly identified.

Experimental systems should preferably run inside isolated environments.

Examples include:

Autonomous code modification

Automated architecture experiments

Agent self-evaluation

Model optimization

Automatic test generation

Runtime optimization

Evolution experiments


Experimental behavior must not silently replace stable behavior.


---

Self-Improvement Systems

CARDINAL may eventually contain systems capable of generating and testing modifications to parts of the project.

These systems should follow a controlled pipeline:

Analyze
   ↓
Hypothesize
   ↓
Generate Candidate
   ↓
Sandbox
   ↓
Test
   ↓
Benchmark
   ↓
Regression Check
   ↓
Security Check
   ↓
Human/Policy Validation
   ↓
Version

Generated changes must not be assumed to be correct simply because they pass a single test.

Important changes should be reproducible and traceable.


---

Dependencies

New dependencies should be introduced carefully.

Before adding a dependency, consider:

License

Security

Maintenance

Performance

Project maturity

Dependency size

Long-term compatibility

Whether the functionality can reasonably be implemented internally


Avoid unnecessary dependencies.


---

Third-Party Code

Third-party code must comply with its respective license.

Do not copy code into CARDINAL without verifying that its license permits the intended use.

Third-party dependencies should be documented when necessary.


---

Security

Do not publicly disclose sensitive security vulnerabilities through ordinary GitHub Issues.

Please follow the security reporting process described in:

SECURITY.md

Never commit:

API keys

Passwords

Private keys

Access tokens

Personal credentials

Production secrets



---

Experimental AI Systems

AI-generated code and AI-assisted development are allowed.

However, generated code must still:

Be reviewed.

Be tested.

Follow project architecture.

Follow security requirements.

Respect dependency licenses.

Be understandable enough to maintain.


AI-generated output is not automatically considered correct.


---

Code Quality

CARDINAL aims to maintain high standards of:

Correctness

Readability

Maintainability

Performance

Security

Testability

Documentation


Prefer simple and well-tested solutions over unnecessary complexity.


---

Design Philosophy

CARDINAL is intended to evolve over a long period.

Contributors should therefore consider not only whether a change works today, but also:

How it affects future development.

How it affects compatibility.

How it affects security.

How it affects performance.

How it affects other subsystems.

How easily it can be tested.

How easily it can eventually be replaced.



---

License

By contributing to CARDINAL, you agree that your contributions may be distributed under the project's MIT License.

See:

LICENSE

for the complete license text.


---

Thank You

Every contribution helps CARDINAL evolve.

Whether you are fixing a typo, improving documentation, fixing a compiler bug, designing a new subsystem, improving performance, or researching new AI capabilities, your contribution is valuable.

Thank you for helping build CARDINAL.
