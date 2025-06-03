import os, sys

def rsrc(rel_path: str) -> str:
    """Return absolute path to a resource.
    Works for development and PyInstaller bundles."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS  # type: ignore
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, rel_path)
