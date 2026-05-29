<!-- scout-headers.md: migrated from scout-headers.md.

Hall: hall_protocol
tools: [scout]
-->

Scout uses ISO-8601 timestamps in each file's header to detect staleness. Behaviour: **write when absent**, **skip when current** (header timestamp ≥ file last commit), **regenerate when stale** (header timestamp < file last commit), `force` bypasses staleness checks. Scout writes headers in the language-appropriate comment syntax; format and field set defined in `wing_practices/agentic-file-headers`.
