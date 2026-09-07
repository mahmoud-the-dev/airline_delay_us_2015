"""Plotly / Streamlit visual defaults (Person B)."""

from __future__ import annotations

import colorsys

PLOTLY_TEMPLATE = "plotly_white"

# Distinct categorical colors for the 14 carriers in the 2015 extract.
# Assigned by name, not by rank, so the same airline keeps the same color on every chart.
AIRLINE_PALETTE: dict[str, str] = {
    "Alaska": "#2E86AB",
    "American": "#C0392B",
    "Delta": "#E67E22",
    "Envoy": "#8E44AD",
    "ExpressJet": "#6D4C41",
    "Frontier": "#1E8449",
    "Hawaiian": "#C2185B",
    "JetBlue": "#00ACC1",
    "SkyWest": "#9A7D0A",
    "Southwest": "#F39C12",
    "Spirit": "#1ABC9C",
    "US Airways": "#5D6D7E",
    "United": "#1A5276",
    "Virgin America": "#AD1457",
}


def unique_sorted_labels(values) -> list[str]:
    seen: set[str] = set()
    labels: list[str] = []
    for value in values:
        if value is None:
            continue
        label = str(value).strip()
        if not label or label.lower() == "nan":
            continue
        if label not in seen:
            seen.add(label)
            labels.append(label)
    labels.sort()
    return labels


def qualitative_hex(n: int) -> list[str]:
    """n distinct hex colors. Golden-ratio hues, cycling saturation and lightness."""
    colors: list[str] = []
    seen: set[str] = set()
    i = 0
    while len(colors) < n:
        hue = (i * 0.618033988749895) % 1.0
        sat = 0.58 + 0.22 * ((i * 3) % 3) / 2.0
        light = 0.38 + 0.20 * ((i * 5) % 3) / 2.0
        r, g, b = colorsys.hls_to_rgb(hue, light, sat)
        hex_color = f"#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}"
        if hex_color not in seen:
            seen.add(hex_color)
            colors.append(hex_color)
        i += 1
        if i > max(n * 20, 32):
            break
    return colors


def color_map(names, preset: dict[str, str] | None = None) -> dict[str, str]:
    """Stable unique color per label. Preset names keep those colors; the rest are generated."""
    labels = unique_sorted_labels(names)
    preset = dict(preset or {})
    mapped = {name: preset[name] for name in labels if name in preset}
    missing = [name for name in labels if name not in mapped]
    mapped.update(zip(missing, qualitative_hex(len(missing))))
    return mapped
