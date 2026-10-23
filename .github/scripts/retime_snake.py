#!/usr/bin/env python3
"""Tune keyframe timing in generated snake SVGs without failing on read-only outputs."""
from pathlib import Path
import re
import os
import tempfile

SEGMENTS = [
    (0.0, 24.0, 0.65),
    (24.0, 42.0, 1.50),
    (42.0, 50.0, 0.70),
    (50.0, 65.0, 1.50),
    (65.0, 92.0, 0.45),
    (92.0, 100.0, 0.70),
]


def remap_percent(value: float) -> float:
    total_weight = sum((end - start) * weight for start, end, weight in SEGMENTS)
    elapsed = 0.0
    for start, end, weight in SEGMENTS:
        if value <= end:
            elapsed += (max(start, value) - start) * weight
            return elapsed / total_weight * 100.0
        elapsed += (end - start) * weight
    return 100.0


def retime_svg(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    match = re.search(r"(<style[^>]*>)(.*?)(</style>)", source, flags=re.S)
    if not match:
        print(f"No embedded CSS found; leaving {path} unchanged")
        return

    css = match.group(2)
    selector_pattern = re.compile(r"(?<![\w.-])(\d+(?:\.\d+)?)%(?=\s*(?:,|\{))")

    def replace_selector(m: re.Match) -> str:
        return f"{remap_percent(float(m.group(1))):.4f}%"

    tuned_css = selector_pattern.sub(replace_selector, css)
    if tuned_css == css:
        print(f"No CSS keyframe selectors to retime in {path}; leaving unchanged")
        return

    new_content = source[:match.start(2)] + tuned_css + source[match.end(2):]
    # Use the same directory so os.replace stays on the same filesystem.
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(new_content)
        # chmod action outputs may be read-only, but the containing dist directory is writable.
        os.chmod(temp_name, 0o644)
        os.replace(temp_name, path)
        print(f"Retimed snake animation: {path}")
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


for svg in (
    Path("dist/github-contribution-grid-snake.svg"),
    Path("dist/github-contribution-grid-snake-dark.svg"),
):
    retime_svg(svg)
