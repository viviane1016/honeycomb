## Inline excerpt: release-ceremony.md

> Inline excerpt from `honeycomb/wing_bees/release-ceremony.md` — copy at time of writing, may drift; see the source room for canonical text.

> **Branches.** Is the merged feature branch gone locally and remotely? Check `git branch -a`. Clean up anything that's no longer needed. Are there other stale branches from older features worth pruning while you're here?
>
> **Tags.** Are the tags in a state you're happy with? Consider what the tag list will look like to someone reading it cold — keep markers that tell a story, prune ones that are just noise. If the release tag needs to move (hotfix landed after tagging), now is the time.
>
> **Issues.** Any issues this release resolves — explicitly referenced in the PR or implicitly fixed — worth closing? GitHub may have auto-closed some; check the ones it might have missed.
>
> **Anything left in your working tree?** Housekeeping notes, BACKLOG annotations, doc tweaks that accumulated during the release cycle — worth committing now rather than letting them drift.

The cartographer's cleanup pass mechanises the issue-triage and BACKLOG-housekeeping portions of this checklist. Branch and tag hygiene remain operator-driven; the cartographer does not delete branches or move tags.
