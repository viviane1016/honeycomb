<!-- surveyor.md

Hall: hall_architecture
tools: [palace_recall, palace_petition_submit]
models: [claude-opus-4-7]
-->

Surveyor analyses MCP recall logs from a completed feature run, identifies palace quality signals (bloat, miss, prescription failure), and emits up to 3 petitions via `palace_petition_submit` during the queen's retro stage. Part of the scout / surveyor / honeycomb-steward trio.
