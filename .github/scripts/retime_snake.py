#!/usr/bin/env python3
"""Retiming pass for Platane/snk SVG output.

Contribution-heavy parts of the route get more time; long travel stretches
get less time. The original path and contribution cells remain unchanged.
"""
from pathlib import Path
import re

# Original timeline landmarks from the generated contribution-snake route.
# Dense/eating sections (24-42%, 50-65%) are slowed down. Long travel
# sections are accelerated. Tune these weights to change the effect.
SEGMENTS = [
    (0.0, 24.0, 0.65),   # fast travel
    (24.0, 42.0, 1.50),  # slow while crossing contribution clusters
    (42.0, 50.0, 0.70),  # fast travel
    (50.0, 65.0, 1.50),  # slow while crossing contribution clusters
    (65.0, 92.0, 0.45),  # very fast travel across sparse cells
    (92.0, 100.0, 0.70), # fast return / loop
]

def remap_percent(value: float) -> float:
    total_weight = sum((end - start) * weight for start, end, weight in SEGMENTS)
    elapsed = 0.0
    for start, end, weight in SEGMENTS:
        if value <= end:
            clamped = max(start, value)
            elapsed += (clamped - start) * weight
            return elapsed / total_weight * 100.0
        elapsed += (end - start) * weight
    return 100.0

def retime_svg(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    match = re.search(r"(<style[^>]*>)(.*?)(</style>)", source, flags=re.S)
    if not match:
        raise RuntimeError(f"No embedded CSS found in {path}")

    css = match.group(2)
    # Only rewrite keyframe selectors (a percentage followed by ',' or '{'),
    # not gradient offsets or any other SVG attributes.
    selector_pattern = re.compile(r"(?<![\\w.-])(\\d+(?:\\.\\d+)?)%(?=\\s*(?:,|\\{))")

    def replace_selector(m: re.Match) -> str:
        old = float(m.group(1))
        new = remap_percent(old)
        return f"{new:.4f}%"

    tuned_css = selector_pattern.sub(replace_selector, css)
    updated = source[:match.start(2)] + tuned_css + source[match.end(2):]
    if updated == source:
        raise RuntimeError(f"No keyframe percentages were retimed in {path}")
    path.write_text(updated, encoding="utf-8")
    print(f"Retimed snake animation: {path}")

for svg in (
    Path("dist/github-contribution-grid-snake.svg"),
    Path("dist/github-contribution-grid-snake-dark.svg"),
):
    retime_svg(svg)
