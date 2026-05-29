## Cross-spec gap detection

The queen reads every spec's `## Scope` section to extract declared output symbols (functions, classes, modules) and output files. She then identifies specs that declare those symbols or files as inputs, and traces whether the diff correctly connects producer to consumer.

Mismatches surface as concerns: a symbol declared as output by spec 002 but absent from the diff; a file expected by spec 004's scope that was never written; an API contract that shifted between what one spec promised and what another consumed. Each concern cites the producer spec, the consumer spec, and the missing or mismatched artifact.
