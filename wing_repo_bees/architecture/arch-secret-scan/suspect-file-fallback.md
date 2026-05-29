## Suspect-file fallback

When a gate writes a `.suspect` file, it places it at the path where the intended artefact would have been written, with `.suspect` appended — for example, `plan.md.suspect` instead of `plan.md`. The intended artefact is never written. The `.suspect` file is preserved for operator inspection.

Extraction-gate hits (queen-file-proposal, petitions) are an exception: the `.suspect` file is written but the stage continues rather than exiting. This allows the rest of the plan stage to complete while flagging the suspicious secondary artefact for operator review.

Injection-gate hits (queen-file) are a second exception: no file is written and the stage continues silently, because the injection is optional context rather than a required pipeline output.
