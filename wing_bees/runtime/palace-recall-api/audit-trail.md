## Audit trail

Every `palace_recall` call that returns at least one result appends a timestamped block to `.bees/<slug>/honeycomb-trace.md`. The block uses an exclusive file lock so parallel scribes can write safely without corruption.

Example block:

```
