import numpy as np
import matplotlib.pyplot as plt

def plot_directional_rose(direction_deg, magnitude, title, bins=16, speed_bins=None):
    direction = np.asarray(direction_deg, dtype=float)
    magnitude = np.asarray(magnitude, dtype=float)

    mask = np.isfinite(direction) & np.isfinite(magnitude)
    direction = direction[mask] % 360
    magnitude = magnitude[mask]

    if direction.size == 0:
        raise ValueError("No hay datos válidos para generar la rosa.")

    sector_edges = np.linspace(0, 360, bins + 1)
    sector_centers = np.deg2rad((sector_edges[:-1] + sector_edges[1:]) / 2)
    width = 2 * np.pi / bins * 0.92

    if speed_bins is None:
        finite = magnitude[np.isfinite(magnitude)]
        qs = np.unique(np.nanquantile(finite, [0, .25, .5, .75, 1]))
        if len(qs) < 3:
            mx = max(float(np.nanmax(finite)), 1.0)
            speed_bins = np.linspace(0, mx, 5)
        else:
            speed_bins = qs
        if speed_bins[0] > 0:
            speed_bins = np.r_[0.0, speed_bins]

    hist = np.zeros((len(speed_bins)-1, bins), dtype=float)
    for i in range(len(speed_bins)-1):
        if i == len(speed_bins)-2:
            smask = (magnitude >= speed_bins[i]) & (magnitude <= speed_bins[i+1])
        else:
            smask = (magnitude >= speed_bins[i]) & (magnitude < speed_bins[i+1])
        counts, _ = np.histogram(direction[smask], bins=sector_edges)
        hist[i] = counts

    if hist.sum() > 0:
        hist = hist / hist.sum() * 100.0

    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)

    bottom = np.zeros(bins)
    for i, row in enumerate(hist):
        label = f"{speed_bins[i]:.2f}–{speed_bins[i+1]:.2f}"
        bars = ax.bar(sector_centers, row, width=width, bottom=bottom, label=label, alpha=0.82)
        bottom += row

    ax.set_title(title, pad=20)
    ax.set_rlabel_position(225)
    ax.set_ylabel("Frecuencia (%)")
    ax.legend(title="Magnitud", bbox_to_anchor=(1.18, 1.05), loc="upper left")
    fig.tight_layout()
    return fig
