"""Persist and load analysis results to/from disk for session recovery."""

import json
import os
import glob
import numpy as np
from datetime import datetime

HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "history")


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)


def save_analysis(midcap_top5: list[dict], smallcap_top5: list[dict], all_data: dict) -> str:
    """
    Save analysis results to a JSON file in the history folder.
    Returns the filepath of the saved file.
    """
    os.makedirs(HISTORY_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"analysis_{timestamp}.json"
    filepath = os.path.join(HISTORY_DIR, filename)

    # Prepare data — strip non-serializable fields
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "midcap_top5": _clean_for_json(midcap_top5),
        "smallcap_top5": _clean_for_json(smallcap_top5),
        "all_data_count": len(all_data) if all_data else 0,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, cls=_NumpyEncoder, ensure_ascii=False)

    # Keep only the last 20 runs to save disk space
    _cleanup_old_files(max_keep=20)

    print(f"[INFO] Analysis saved to {filepath}")
    return filepath


def load_latest_analysis() -> dict | None:
    """
    Load the most recent analysis from history.
    Returns dict with {timestamp, midcap_top5, smallcap_top5} or None.
    """
    if not os.path.exists(HISTORY_DIR):
        return None

    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "analysis_*.json")), reverse=True)
    if not files:
        return None

    return _load_file(files[0])


def load_analysis_by_file(filename: str) -> dict | None:
    """Load a specific analysis file by filename."""
    filepath = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(filepath):
        return None
    return _load_file(filepath)


def list_history() -> list[dict]:
    """
    List all saved analysis runs.
    Returns list of {filename, timestamp, display_name}.
    """
    if not os.path.exists(HISTORY_DIR):
        return []

    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "analysis_*.json")), reverse=True)
    result = []

    for filepath in files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get("timestamp", "Unknown")
            result.append({
                "filename": filename,
                "timestamp": ts,
                "display_name": f"Run: {ts}",
            })
        except Exception:
            result.append({
                "filename": filename,
                "timestamp": "Error",
                "display_name": f"Run: {filename}",
            })

    return result


def _load_file(filepath: str) -> dict | None:
    """Load and parse a single history file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[WARN] Failed to load {filepath}: {e}")
        return None


def _clean_for_json(stocks: list[dict]) -> list[dict]:
    """Remove non-serializable fields (like DataFrames) from stock dicts."""
    cleaned = []
    for stock in stocks:
        s = {}
        for k, v in stock.items():
            if k == "df":
                continue  # Skip DataFrame references
            s[k] = v
        cleaned.append(s)
    return cleaned


def _cleanup_old_files(max_keep: int = 20):
    """Remove oldest history files if more than max_keep exist."""
    files = sorted(glob.glob(os.path.join(HISTORY_DIR, "analysis_*.json")))
    if len(files) > max_keep:
        for f in files[:-max_keep]:
            try:
                os.remove(f)
            except Exception:
                pass
