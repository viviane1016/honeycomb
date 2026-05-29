## Guidance

If you see "dispatch lock held" errors, it means another `bees dispatch` on the same feature is running (or crashed while holding the lock). Either wait for it to finish, or if you believe it's stuck, remove `.bees/<slug>/dispatch.lock` manually. The lock is defensive — it prevents bugs, not corruptions. If you remove the lock while a dispatch is running, behavior is undefined and likely bad; only do this when you're sure the process is gone.
