## Guidance

Builders are isolated for a reason. Plans and specs must be self-contained — don't assume the builder can ask questions or iterate. If your spec relies on undocumented conventions, project layout, or unstated assumptions, the builder will get stuck. The narrowed tool allowlist is intentional too: it prevents accidental `pip install`, `git push`, or `git config` mistakes. If a spec requires something the allowlist doesn't permit, that's a signal to reconsider the approach, not a reason to work around the safety constraint.

Before extending any file, check its line count (`wc -l` or via Read). If the file already exceeds ~500 lines and the spec does not explicitly require editing it, prefer creating a small focused new module and note the decision in the commit message body. Never bundle unrelated concerns into one file just to avoid creating a new file — a small focused new file is preferable to a mixed-concerns extension.
