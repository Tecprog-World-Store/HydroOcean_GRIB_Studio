import numpy as np
from matplotlib.figure import Figure

def time_series_figure(df, product):
    fig = Figure(figsize=(9, 5), tight_layout=True)
    ax = fig.add_subplot(111)

    if product == "Oleaje":
        cols = [c for c in ["Hs_m", "Period_s"] if c in df]
        for c in cols:
            ax.plot(df.index, df[c], marker=".", label=c)
        ax.set_ylabel("Hs (m) / Periodo (s)")
        if "WaveDir_deg" in df:
            ax2 = ax.twinx()
            ax2.plot(df.index, df["WaveDir_deg"], alpha=.45, label="WaveDir_deg")
            ax2.set_ylabel("Dirección (°)")
            ax2.set_ylim(0, 360)
    elif product == "Viento":
        if "WindSpeed_m_s" in df:
            ax.plot(df.index, df["WindSpeed_m_s"], marker=".", label="WindSpeed_m_s")
            ax.set_ylabel("Velocidad (m/s)")
        if "WindDir_from_deg" in df:
            ax2 = ax.twinx()
            ax2.plot(df.index, df["WindDir_from_deg"], alpha=.45, label="WindDir_from_deg")
            ax2.set_ylabel("Dirección desde (°)")
            ax2.set_ylim(0, 360)
    else:
        if "CurrentSpeed_m_s" in df:
            ax.plot(df.index, df["CurrentSpeed_m_s"], marker=".", label="CurrentSpeed_m_s")
            ax.set_ylabel("Velocidad (m/s)")
        if "CurrentDir_to_deg" in df:
            ax2 = ax.twinx()
            ax2.plot(df.index, df["CurrentDir_to_deg"], alpha=.45, label="CurrentDir_to_deg")
            ax2.set_ylabel("Dirección hacia (°)")
            ax2.set_ylim(0, 360)

    ax.set_title(f"{product} — serie temporal ({len(df)} muestras)")
    ax.set_xlabel("Tiempo")
    ax.grid(True, alpha=.25)
    ax.legend(loc="upper left")
    fig.autofmt_xdate()
    return fig

def rose_figure(direction, magnitude, title):
    d = np.asarray(direction, float)
    m = np.asarray(magnitude, float)
    mask = np.isfinite(d) & np.isfinite(m)
    d, m = d[mask] % 360, m[mask]
    if len(d) < 2:
        raise ValueError(
            "La rosa requiere varias muestras. "
            "Un archivo f000 aislado contiene normalmente un solo instante."
        )

    nsector = 16
    edges = np.linspace(0, 360, nsector + 1)
    centers = np.deg2rad((edges[:-1] + edges[1:]) / 2)
    q = np.unique(np.quantile(m, [0, .25, .5, .75, 1]))
    if len(q) < 3:
        q = np.linspace(0, max(float(np.max(m)), 1), 5)
    if q[0] > 0:
        q = np.r_[0, q]

    hist = np.zeros((len(q)-1, nsector))
    for j in range(len(q)-1):
        mm = (m >= q[j]) & (m <= q[j+1] if j == len(q)-2 else m < q[j+1])
        hist[j], _ = np.histogram(d[mm], bins=edges)
    hist = hist / max(hist.sum(), 1) * 100

    fig = Figure(figsize=(7.5, 6.5), tight_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    bottom = np.zeros(nsector)
    for j, vals in enumerate(hist):
        ax.bar(
            centers, vals, width=2*np.pi/nsector*.92, bottom=bottom,
            label=f"{q[j]:.2f}–{q[j+1]:.2f}", alpha=.82
        )
        bottom += vals
    ax.set_title(title, pad=20)
    ax.legend(title="Magnitud", bbox_to_anchor=(1.12, 1.05), loc="upper left")
    return fig
