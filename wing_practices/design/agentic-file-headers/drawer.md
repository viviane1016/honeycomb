## Drawer

### Why headers

An AI agent reading a file from cold pays full token cost to learn what the file is for. A 5-line header at the top — "what this file does, what calls it, what it exports, when it last changed" — collapses that cost into a glance and saves the full read for cases that need it. Across a non-trivial codebase the savings dominate, and the discipline forces a clear single-line answer to "what is this file for" before the file accretes complexity.

### Comment syntax reference

| Extension | Syntax | Example |
|-----------|--------|---------|
| `.py` | `# …` | `# module: purpose` |
| `.sh` | `# …` | `# script: purpose` |
| `.go` | `// …` | `// package: purpose` |
| `.rs` | `// …` | `// module: purpose` |
| `.rb` | `# …` | `# module: purpose` |
| `.java` | `/** … */` | `/** class: purpose */` |
| `.kt` | `/** … */` | `/** class: purpose */` |
| `.swift` | `/// …` | `/// file: purpose` |
| `.c` | `/* … */` | `/* file: purpose */` |
| `.cpp` | `// …` or `/* … */` | `// file: purpose` |
| `.h` | `/* … */` or `// …` | `/* file: purpose */` |
| `.ts` | `/** … */` | `/** file: purpose */` |
| `.js` | `/** … */` | `/** file: purpose */` |
| `.mjs` | `/** … */` | `/** module: purpose */` |
| `.md` | `<!-- … -->` | `<!-- file: purpose -->` |

### Header format examples

#### Python/Shell example

```python
# llm.py: LLM client wrapper for local and cloud inference.
#
# Provides a unified interface for querying local Qwen/Hermes instances
# (mlx_lm servers on ports 1234/1235) and cloud Claude models via the
# Anthropic SDK. Used by test classifiers and reply composers.
#
# Key exports: LLM, classify, compose
#
# Scout: 2026-05-12T14:32:00Z
```

#### TypeScript/JavaScript example

```typescript
/** api.ts: REST client for the dashboard backend.
 *
 * Wraps fetch() with auth, retry, and JSON parsing. Used by every
 * dashboard component that talks to the server. Errors surface as
 * typed exceptions; callers handle them per-page.
 *
 * Key exports: ApiClient, ApiError, isApiError
 *
 * Scout: 2026-05-12T14:32:00Z
 */
```

#### Markdown example

```markdown
<!-- arch-cells.md: Isolated builder worktrees for safe parallel execution.

Cells are per-builder git worktrees rooted under .bees/<slug>/cells/<NNN>/,
checked out on a per-spec branch. Builders work inside their cell with a
narrowed tool allowlist, commit on success, and a fast-forward ref update
merges to the feature branch.

Scout: 2026-05-13T16:34:00Z -->
```

### Field definitions

**Path + role line**: The first line, formatted as `<filename>: <short role>`. The filename (e.g., `llm.py`, `api.ts`) is the path relative to the repository root or the file's own name when context is unambiguous. The role is a brief description of what the file does and who depends on it.

**Description paragraph**: 2–5 sentences explaining the file's purpose, context, and dependencies. Include what system components call this file or what problem it solves.

**Key exports**: Only for code files (`.py`, `.js`, `.ts`, `.go`, `.rb`, etc.). Lists main public functions, classes, or exported symbols as a comma-separated list. Omit from documentation files (`.md`), configuration files (`.json`, `.yaml`, `.toml`), or shell scripts (`.sh`).

**Timestamp**: ISO-8601 UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) indicating when the header was generated or last verified. Carries the maintenance-mechanism field name in your project (bees uses `Scout: …` because the scout drone owns the regeneration loop; in another project it might be `Touched: …` or `Verified: …`).

### What this room does not cover

The *mechanism* for keeping headers fresh as files change — write-on-absent, staleness detection against commit time, force regeneration, conflict resolution between concurrent agents writing headers — is project-specific. For bees' implementation see `wing_bees/scout-headers`. Other agentic codebases will implement the same hygiene differently; the format above is the part that ports cleanly.
