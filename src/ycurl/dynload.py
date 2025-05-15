from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

Hook = Callable[..., Any]


def load_hooks(app_root: Path) -> dict[str, Hook]:
    """Return dict of hook functions found in <app_root>/app.py."""
    mod_path = app_root / "app.py"
    if not mod_path.exists():
        return {}

    spec = importlib.util.spec_from_file_location("ycurl_app_hooks", mod_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        return {}

    hooks: dict[str, Hook] = {}
    for name in ("after_config", "before_prepare", "after_prepare", "after_response"):
        if hasattr(module, name):
            hooks[name] = getattr(module, name)
    return hooks
