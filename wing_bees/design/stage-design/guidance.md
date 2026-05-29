## Guidance

**When to use design.** Design is occasional, not routine. Good triggers: a big feature or refactor where the approach isn't settled; pulling in a batch of issues or backlog items and wanting to think through the architecture before writing briefings; a question surfaced mid-delivery that warrants stepping back. A useful signal: if you'd want an ADR to capture the decision, design is worth running. If the approach is already clear, go straight to plan — design is not a required step.

**Topic file quality.** The topic does not need to be exhaustive. A clear question ("how should we invoke models?"), a named tension ("queen tool access vs pre-assembly"), or a pointer to an existing doc to review and extend are all good inputs. The actor will browse to fill in context.

**Multiple ADRs.** A single design session may produce several ADRs — many architectural conversations span multiple orthogonal decisions. This is expected and correct. Review all of them before committing; they may have dependencies on each other.

**ADR format.** Each ADR follows the established format: title, date, status (`Proposed`), Context, Decision, Consequences (positive/negative), Alternatives considered, Sequencing. The design actor proposes numbering; the operator confirms at review. If a number is already taken, the actor increments.

**The human gate.** Read the proposed ADRs as if a future team member will use them to understand why a decision was made. If the reasoning is unclear, push back before committing. `Status: Proposed` means under consideration; change to `Accepted` when committed.

**Recommended briefing output.** If the session ends with a clear implementation path, the actor's recommended briefing is a starting point — edit it before passing to `bees plan`. The actor does not know everything about your constraints; the briefing should reflect your current thinking, not just the actor's.
