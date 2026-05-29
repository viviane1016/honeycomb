## Guidance

The non-disruptive merge is why `bees dispatch` refuses to start if you're on the feature branch — it protects you from surprises. If a build fails with merge conflicts, that's a signal that the work isn't actually FF-mergeable (e.g., concurrent builders on the same feature touched overlapping files). Debug the conflict in the cell before retrying; bees doesn't auto-recover from merge failures.
