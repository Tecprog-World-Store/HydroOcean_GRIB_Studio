import matplotlib.pyplot as plt

def plot_timeseries(df, columns, title, ylabel=""):
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in columns:
        if col in df.columns:
            ax.plot(df.index, df[col], label=col)
    ax.set_title(title)
    ax.set_xlabel("Tiempo / muestra")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    return fig
