#!/usr/bin/env python3
"""Retiming pass for Platane/snk SVG output.

Contribution-heavy parts of the route get more time; long travel stretches
get less time. The original path and contribution cells remain unchanged.
"""
from pathlib import Path
import re

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
        raise RuntimeError(f"No embedded CSS found in {path}")

    css = match.group(2)
    selector_pattern = re.compile(r"(?<![\\w.-])(\\d+(?:\\.\\d+)?)%(?=\\s*(?:,|\\{))")

    def replace_selector(m: re.Match) -> str:
        return f"{remap_percent(float(m.group(1))):.4f}%"

    tuned_css = selector_pattern.sub(replace_selector, css)
    if tuned_css == css:
        # platane/snk can emit SVGs without CSS keyframes in future versions.
        # Don't fail the entire generation when there is nothing to retime.
        print(f"No CSS keyframe selectors found; leaving {path} unchanged")
        return

    # The generated files may be read-only in the action container. Path.write_text
    # opens the original with truncation and fails on read-only files; writing to a
    # temporary file then replacing the target works when the directory is writable.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        source[:match.start(2)] + tuned_css + source[match.end(2):],
        encoding="utf-8",
    )
    temporary.replace(path)
    print(f"Retimed snake animation: {path}")


for svg in (
    Path("dist/github-contribution-grid-snake.svg"),
    Path("dist/github-contribution-grid-snake-dark.svg"),
):
    retime_svg(svg)
