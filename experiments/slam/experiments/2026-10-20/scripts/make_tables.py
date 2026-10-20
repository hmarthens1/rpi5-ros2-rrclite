#!/usr/bin/env python3
"""LaTeX tables for the report, from data/runs.json, data/maps.json, data/sessions.json.

  python3 scripts/make_tables.py        (from experiments/2026-10-20; run analyze_day.py first)
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "report")
os.makedirs(OUT, exist_ok=True)
runs = json.load(open(os.path.join(DATA, "runs.json")))
maps = json.load(open(os.path.join(DATA, "maps.json")))
sessions = json.load(open(os.path.join(DATA, "sessions.json")))


def tex(s):
    return str(s).replace("_", r"\_").replace("%", r"\%")


END = {"back at the start": "home", "stop": "operator stop", "sample": "log ends",
       "could not drive back to the start (Nav2 aborted (status 6))": "return failed"}
with open(os.path.join(OUT, "runs_table.tex"), "w") as f:
    for r in runs:
        end = END.get(r["end_reason"], r["end_reason"])
        if r["outcome"] == "battery low":
            end = "battery low $\\to$ home"
        f.write("%s & %s & %s & %.0f & %.1f & %.0f & %d & %d & %d & %d & %s \\\\\n" % (
            r["id"], r["session"], r["start"], r["duration_s"], r["distance_m"], r["explored_m2"],
            r["goals_sent"], r["goals_reached"], r["goals_explored"], r["goals_failed"], end))
        if r["id"] in ("R04", "R05", "R09", "R14"):
            f.write("\\midrule\n")

with open(os.path.join(OUT, "maps_table.tex"), "w") as f:
    for m in maps:
        timer = ("%.0f / %.0f" % (m["mapping_time_s"], m["explorer_elapsed_s"])) if m["mapping_time_s"] else "--"
        f.write("\\texttt{%s} & %s & %s & %.1f$\\times$%.1f & %.1f & %.1f & %.1f & %.1f & %s \\\\\n" % (
            tex(m["name"].replace("lab_2026-10-20_", "")), m["saved"], m["run"], m["size_m"][0], m["size_m"][1],
            m["known_m2"], m["free_m2"], m["occupied_m2"], m["path_length_m"], timer))

with open(os.path.join(OUT, "sessions_table.tex"), "w") as f:
    for s in sessions:
        f.write("%s & %s & %s & %d & %d & %d / %d & %s & %.1f & %s \\\\\n" % (
            s["session"], s["time"].replace("-", "--"), s["label"], s["n_runs"], s["n_completed"],
            s["goals_failed"], s["goals_sent"], ("%.0f\\%%" % (100 * s["fail_rate"])) if s["fail_rate"] is not None else "--",
            s["distance_m"], ("%.1f min, %.1f m" % (s["completed_mean_min"], s["completed_mean_m"]))
            if s["completed_mean_min"] else "--"))
print("tables written to", OUT)
