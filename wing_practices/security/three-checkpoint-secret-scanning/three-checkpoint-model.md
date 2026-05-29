## Three-checkpoint model

Apply secret scanning at three gates in any pipeline that handles untrusted or generated content:

- **Entry gate** — scan untrusted input before passing it to a processing component. If a hit is detected, quarantine (write a `.suspect` file) and exit non-zero rather than proceeding. This prevents a malicious or accidentally poisoned input from travelling further into the pipeline.
- **Output gate** — scan generated output before persisting it or forwarding it to the next component. A processing component that echoes input may inadvertently reproduce a secret it received. Scanning output catches this before the artifact is written to disk or sent onward.
- **Boundary gate** — scan any artifact that crosses a trust boundary (written to disk, sent to an external service, included in a commit). This is the last line of defence before exposure.

The same response applies at every gate: quarantine the artifact by writing a `.suspect` file in place of the intended output, and exit non-zero. Never silently continue past a detected secret.
