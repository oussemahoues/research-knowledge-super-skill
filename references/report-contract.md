# Report contract

## Markers

Every factual paragraph includes one or more claim markers and source markers:

```text
The standard requires X under condition Y. [C:claim:abc123] [S:source:def456#p12]
```

- `[C:<claim-id>]` resolves to a `Claim` node.
- `[S:<source-id>#<locator>]` resolves to a `Source` record and a supporting or contradicting `EvidenceSpan`.
- Inference paragraphs begin with `Inference:` and cite every premise claim.

## Required sections

1. Title
2. Research scope and as-of date
3. Executive findings
4. Detailed findings
5. Contested or conflicting evidence
6. Limitations
7. Unresolved research gaps
8. Source register

Do not include a factual statement merely to improve narrative flow. Unsupported connective tissue must be framed as interpretation or removed.
