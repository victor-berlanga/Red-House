"""Comparación sintética de progreso de un hilo durante dos esperas Qt."""
import json
import statistics
import threading
import time
from pathlib import Path

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

app = QApplication([])
results = []
for cycle in range(6):
    mode = ("qwait", "events_sleep")[(cycle + cycle // 2) % 2]
    points = []
    stop = threading.Event()
    ready = threading.Event()

    def worker():
        ready.set()
        while not stop.is_set():
            points.append(time.monotonic())
            time.sleep(0.001)

    thread = threading.Thread(target=worker)
    thread.start()
    ready.wait()
    start = time.monotonic()
    while time.monotonic() - start < 2:
        if mode == "qwait":
            QTest.qWait(20)
        else:
            app.processEvents()
            time.sleep(0.020)
    elapsed = time.monotonic() - start
    stop.set()
    thread.join()
    gaps = [(b - a) * 1000 for a, b in zip(points, points[1:])]
    results.append({"mode": mode, "elapsed_s": round(elapsed, 3), "worker_ticks": len(points), "ticks_per_second": round(len(points) / elapsed, 1), "gap_median_ms": round(statistics.median(gaps), 2), "gap_max_ms": round(max(gaps), 2)})
Path(__file__).with_name("resultados.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
