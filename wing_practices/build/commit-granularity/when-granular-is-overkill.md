## When granular is overkill

- Atomic edits that genuinely can't be split (rename across two files, bump a version + update a single doc that references it, fix a typo + its test).
- Throwaway/scratch branches that will be squashed flat at PR time and never bisected.
- Edits where splitting forces you into broken intermediate states (e.g. signature change + every callsite — those must commit together to keep the tree green).
