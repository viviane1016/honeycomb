## Guidance

Builders are fully isolated, which means plans and specs must be self-contained. Don't assume the builder can consult project history, ask clarifying questions, or iterate mid-build. If your spec relies on undocumented conventions or project layout, the builder won't have access to that context — or it will be lost when the cell is scrubbed. Document assumptions in the spec, and test the spec's success criteria in the builder's environment, not your own.

Cells being transient is a feature: clean failure recovery without manual directory cleanup. But it means you can't leave side artifacts or temporary build files in the cell expecting them to survive — the next dispatch on the same spec will start with a fresh cell.
