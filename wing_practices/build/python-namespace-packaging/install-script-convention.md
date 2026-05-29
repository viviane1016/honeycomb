## Install script convention

`LIB_DIR` in `install.sh` must point to the *namespace parent*, not the
package itself:

```bash
LIB_DIR="$BASE_DIR/lib/bees"   # correct: installs plan.py → ~/.local/lib/bees/plan.py
# not:
LIB_DIR="$BASE_DIR/lib"        # wrong: installs plan.py → ~/.local/lib/plan.py
```
