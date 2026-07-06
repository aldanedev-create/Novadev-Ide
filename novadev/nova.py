from __future__ import annotations

"""Package wrapper for the NovaDev 1.1 CLI.

The beginner command remains `python nova.py ...` from the project root. This
file also lets people run `python -m novadev.nova ...` when they prefer module
style commands.
"""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nova import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
