"""Representa los cortes medidos; no ejecuta carga ni lee credenciales."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / "comparacion.json").read_text())
labels = ["12 · activa A", "12 · bypass A", "12 · activa B", "12 · bypass B",
          "24 · activa", "6 · recuperación"]
colors = ["#31678b", "#667085", "#31678b", "#667085", "#b71835", "#22704e"]
fig, axes = plt.subplots(2, 1, figsize=(10.2, 7), layout="constrained")
fig.suptitle("Red House · lecturas en laboratorio local", fontsize=16, weight="bold")
for axis, field, title, unit in (
    (axes[0], "max_p95_ms", "Mayor p95 entre endpoints", "Milisegundos"),
    (axes[1], "rps", "Peticiones medidas por segundo", "HTTP/s"),
):
    values = [row[field] for row in rows]
    bars = axis.bar(labels, values, color=colors, width=.66)
    axis.bar_label(bars, labels=[f"{v:.0f}" if field == "max_p95_ms" else f"{v:.2f}" for v in values], padding=4)
    axis.set(title=title, ylabel=unit, ylim=(0, max(values) * 1.25))
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", alpha=.18)
    axis.set_axisbelow(True)
axes[0].axhline(2000, color="#b71835", linestyle="--", linewidth=1.3, label="Objetivo: p95 < 2.000 ms")
axes[0].legend(loc="upper left", frameon=False)
axes[1].set_xlabel("Usuarios concurrentes y modo de caché, en orden de ejecución")
fig.get_layout_engine().set(rect=(0, .10, 1, .90))
fig.text(.5, .015, "Cero errores en las seis fases. 24 usuarios incumple latencia; estrés de 36 omitido.\n"
         "Generador y servicios en el mismo Mac. Estos percentiles máximos no son percentiles globales.",
         ha="center", fontsize=10)
for extension in ("png", "svg"):
    fig.savefig(ROOT / ("comparacion." + extension), dpi=160, bbox_inches="tight", facecolor="white")
plt.close(fig)
(ROOT / "grafica-entorno.json").write_text(json.dumps({"matplotlib": matplotlib.__version__, "backend": "Agg", "input": "comparacion.json"}, indent=2) + "\n")
