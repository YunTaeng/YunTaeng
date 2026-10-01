"""Render data/contributions.json into an animated terminal-style heatmap SVG."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "contributions.json"
OUT_PATH = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT = 40
TOP = 64
COL_DELAY_MS = 45
ROW_DELAY_MS = 22
DURATION_MS = 900
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def weekday_sunday_first(d):
    return (d.weekday() + 1) % 7


def cell_color(day, max_count):
    level = day["level"]
    # promote the busiest days to the extra top shade
    if level >= 4 and max_count > 0 and day["count"] >= max_count and max_count > 1:
        return PALETTE[5]
    return PALETTE[min(level, 4)]


def build_cells(days, max_count):
    first = date.fromisoformat(days[0]["date"])
    origin = first.toordinal() - weekday_sunday_first(first)
    cells, month_marks, last_month = [], [], None
    for day in days:
        d = date.fromisoformat(day["date"])
        col = (d.toordinal() - origin) // 7
        row = weekday_sunday_first(d)
        x, y = LEFT + col * STEP, TOP + row * STEP
        delay = col * COL_DELAY_MS + row * ROW_DELAY_MS
        title = f"{day['count']} contributions on {day['date']}"
        cells.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
            f'fill="{cell_color(day, max_count)}" style="animation-delay:{delay}ms">'
            f"<title>{title}</title></rect>"
        )
        if row == 0 and d.month != last_month:
            month_marks.append((x, MONTHS[d.month - 1]))
            last_month = d.month
    return cells, month_marks, col + 1


def render(data):
    days = data["days"]
    max_count = max(d["count"] for d in days)
    cells, month_marks, cols = build_cells(days, max_count)
    width = LEFT + cols * STEP + 16
    height = TOP + 7 * STEP + 44

    month_svg = "".join(
        f'<text x="{x}" y="{TOP - 8}" class="lbl">{name}</text>' for x, name in month_marks
    )
    day_svg = "".join(
        f'<text x="6" y="{TOP + row * STEP + CELL - 1}" class="lbl">{name}</text>'
        for row, name in DAY_LABELS.items()
    )
    legend_x = width - 16 - (len(PALETTE[:5]) * STEP) - 64
    legend = "".join(
        f'<rect x="{legend_x + 30 + i * STEP}" y="{height - 26}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        for i, c in enumerate(PALETTE[:5])
    )
    summary = (
        f"{data['total']} contributions in the last year  |  "
        f"current streak: {data['current_streak']}d  |  longest streak: {data['longest_streak']}d"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{summary}">
<style>
.bg{{fill:#0d1117}}
.lbl{{font:10px {FONT};fill:#7d8590}}
.sum{{font:11px {FONT};fill:#8b949e}}
.c{{opacity:0;transform-box:fill-box;animation:pop {DURATION_MS}ms cubic-bezier(.22,.61,.36,1) forwards}}
@keyframes pop{{from{{opacity:0;transform:translate(-6px,-10px) scale(.6)}}60%{{opacity:1}}to{{opacity:1;transform:translate(0,0) scale(1)}}}}
@media (prefers-reduced-motion:reduce){{.c{{animation:none;opacity:1}}}}
</style>
<rect class="bg" width="{width}" height="{height}" rx="8"/>
<text x="16" y="34" class="sum">{summary}</text>
{month_svg}
{day_svg}
{''.join(cells)}
<text x="{legend_x}" y="{height - 17}" class="lbl">Less</text>
{legend}
<text x="{legend_x + 30 + 5 * STEP + 4}" y="{height - 17}" class="lbl">More</text>
</svg>
"""


def main():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUT_PATH.write_text(render(data), encoding="utf-8")
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
