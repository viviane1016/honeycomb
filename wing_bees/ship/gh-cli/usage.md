## Usage

Bees invokes `gh pr create` at the ship stage to open a single PR per feature, with a body assembled from the plan's context section plus spec links. `bees status` uses `gh pr view` to check whether a PR is open and its merge state. Future stages (retro, debug) will use `gh issue create` to file follow-up actions. Operators see this as seamless; the GitHub layer is transparent once you've authenticated with `gh auth login`.
