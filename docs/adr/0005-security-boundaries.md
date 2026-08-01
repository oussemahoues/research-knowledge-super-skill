# ADR 0005: Untrusted-source security boundary

## Decision

Treat all retrieved content as untrusted data. Acquisition workers are read-only. Source content never enters system instructions and never gains authority to request tools, credentials, or state changes.

## Controls

- tool allowlists per role
- content hashing and immutable snapshots
- injection-risk metadata and quarantine
- credential and system-context exclusion
- logged network destinations
- adversarial fixtures and canaries
- explicit approval for high-consequence conclusions
