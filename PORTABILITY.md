# Portability

The repository contains the canonical Claude plugin surface and a framework-compatible `.claude/harness-config.yaml`. The source contracts are host-neutral: skills, JSON schemas, Python libraries, references, and eval fixtures may be carried unchanged.

## Claude Code

Use the plugin root directly. Commands, agents, skills, and hooks are native.

## Codex

Translate commands to human-invoked workflow skills, preserve each skill directory, and install agent definitions as companion agent configuration. Keep `disable-model-invocation` semantics for the three top-level commands.

## Antigravity

Translate agents and commands to its native plugin directories. Register only lifecycle events whose payload exposes the path and content fields required by the guards. Preserve unsupported hook implementations as source proof and state the enforcement gap in the portability manifest.

## Framework regeneration

Run the user's harness framework against `.claude/harness-config.yaml`. Generated files must be compared with the checked-in surfaces; semantic differences require review, while formatting-only target adaptations are acceptable. Never flatten all targets into one directory.
