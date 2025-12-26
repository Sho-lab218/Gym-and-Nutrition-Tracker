def apply_mpl_style(dark=True):
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.figsize": (9, 4.6),
        "font.size": 12,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "-",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "legend.frameon": False,
        "savefig.bbox": "tight",
        "figure.autolayout": True,
        "lines.linewidth": 2.6,
        "lines.markersize": 6,
    })
    if dark:
        bg = "#000000"; card = "#0B0F19"; text = "#E5E7EB"; grid = "#334155"
        cycle = ["#22C55E", "#38BDF8", "#8B5CF6", "#F59E0B", "#F43F5E"]
    else:
        bg = "white"; card = "white"; text = "#0F172A"; grid = "#CBD5E1"
        cycle = ["#2563EB", "#16A34A", "#F59E0B", "#9333EA", "#EF4444"]
    mpl.rcParams.update({
        "text.color": text, "axes.labelcolor": text,
        "xtick.color": text, "ytick.color": text,
        "axes.edgecolor": grid, "grid.color": grid,
        "figure.facecolor": bg, "axes.facecolor": card,
        "axes.prop_cycle": mpl.cycler(color=cycle),
    })