"""Shared atomic file-writing utilities to prevent partial or corrupted writes."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def atomic_write_path(target_path: str | Path) -> Iterator[Path]:
    """Yields a temporary file path in target_path's directory and atomically replaces target_path on success."""
    dest = Path(target_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(dest.parent),
        prefix=f".{dest.name}.",
        suffix=".tmp",
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        yield tmp_path
        tmp_path.replace(dest)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise
