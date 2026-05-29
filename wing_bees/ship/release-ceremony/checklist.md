## Checklist

1. **Branches.** Is the merged feature branch gone locally and remotely? Check `git branch -a`. Clean up anything that's no longer needed. Are there other stale branches from older features worth pruning while you're here?

2. **Tags.** Are the tags in a state you're happy with? Consider what the tag list will look like to someone reading it cold — keep markers that tell a story, prune ones that are just noise. If the release tag needs to move (hotfix landed after tagging), now is the time.

3. **Does the release actually work?** For bees itself, run `bees release <tag>` first — this cuts the GitHub release (idempotent: safe to re-run if it already exists). Then run through the project's install or deployment mechanism against the tagged commit and satisfy yourself it works. What "works" means is project-specific; the point is to check before moving on, not to assume CI green equals shippable.

4. **Update your local install?** Do you want to pull this release onto your own machine now? You might not — you could be releasing for others, waiting to see if a hotfix is needed, or simply not ready. Decide consciously rather than by default.
   - If you do update, run `tools/install.sh` **and** `tools/install_skill.sh`. The skill install copies `skills/bees/SKILL.md` (and related files) to `~/.claude/skills/bees/` — without it, the operator's installed skill snapshot lags behind the binary and SKILL.md changes won't take effect until the next manual install.

5. **Issues.** Any issues this release resolves — explicitly referenced in the PR or implicitly fixed — worth closing? GitHub may have auto-closed some; check the ones it might have missed.

6. **Anything left in your working tree?** Housekeeping notes, BACKLOG annotations, doc tweaks that accumulated during the release cycle — worth committing now rather than letting them drift.

7. **Anything else feel unfinished?** Release ceremonies surface things. If something feels off — a doc that didn't land, a follow-up that needs an issue filed, a decision that should be recorded — handle it now or log it somewhere it won't be forgotten.
