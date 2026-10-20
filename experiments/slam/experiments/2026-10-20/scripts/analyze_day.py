#!/usr/bin/env python3
"""Figures and numbers for the 2026-10-20 robot04 mapping experiments.

  python3 scripts/analyze_day.py        (from experiments/2026-10-20)

Reads  data/robot_logs/*.jsonl   the explorer's event logs (copied from robot04:~/explore_logs)
       data/pc_maps/*.{yaml,pgm,json}   maps saved by the robot04 mapper app
       data/robot_maps/*.{yaml,pgm}     maps the explorer saved on the robot
Writes figures/maps/<map>.png    each saved map with metric axes, path, goals
       figures/*.png             per-run comparisons
       data/runs.json, data/runs.csv, data/maps.json
"""
import csv
import glob
import json
import math
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
FIG = os.path.join(ROOT, "figures")
os.makedirs(os.path.join(FIG, "maps"), exist_ok=True)

BLUE, RED, GREEN, GREY, ORANGE, INK = "#0000CC", "#CC0633", "#2E7D32", "#8A8A95", "#E07B00", "#1A1A1A"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
                     "font.size": 10, "axes.titlesize": 11, "axes.edgecolor": "#555",
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 200})

# sessions: what changed between groups of runs (environment and outcome, no code changed today)
SESSIONS = [("A", "09:32", "09:41", "Large open area"),
            ("B", "10:09", "10:17", "Long run, large area"),
            ("C", "10:53", "10:55", "Low battery"),
            ("D", "11:49", "12:21", "Bounded test area"),
            ("E", "12:38", "12:57", "Bounded test area, repeat")]


def hhmm(t):
    return time.strftime("%H:%M", time.localtime(t))


def session_of(t):
    s = hhmm(t)
    for key, a, b, _ in SESSIONS:
        if a <= s <= b:
            return key
    return "?"


# ------------------------------------------------------------------ runs
def load_run(path):
    ev = [json.loads(l) for l in open(path) if l.strip()]
    t0 = ev[0]["t"]
    end = next((e for e in ev if e["event"] in ("done", "stop")), ev[-1])
    done = next((e for e in ev if e["event"] == "done"), None)
    goals = [e for e in ev if e["event"] in ("goal_reached", "goal_failed", "frontier_explored")]
    samples = [e for e in ev if e["event"] == "sample"]
    batt = [e["battery_v"] for e in samples if e.get("battery_v")]
    search = [e["search_ms"] for e in ev if e["event"] == "goal_sent" and "search_ms" in e]
    if done:
        why = done.get("why", "")
        outcome = "completed" if why == "back at the start" else "no return"
        if any(e.get("why") == "battery low" for e in ev):
            outcome = "battery low"
    else:
        outcome = "operator stop" if end["event"] == "stop" else "log ends"
    home_t = next((e["t"] for e in ev if e["event"] == "return_home"), None)
    explored = done["explored_m2"] if done and "explored_m2" in done else \
        max([e.get("explored_m2", 0) for e in samples] or [0])
    return {
        "log": os.path.basename(path), "session": session_of(t0), "start": hhmm(t0), "t0": t0,
        "duration_s": round(end["t"] - t0, 1),
        "explore_s": round((home_t or end["t"]) - t0, 1),
        "return_s": round(end["t"] - home_t, 1) if home_t and done else None,
        "distance_m": end["distance_m"], "explored_m2": round(explored, 1),
        "goals_sent": sum(e["event"] == "goal_sent" for e in ev),
        "goals_reached": sum(e["event"] == "goal_reached" and e.get("kind") != "home" for e in ev),
        "goals_explored": sum(e["event"] == "frontier_explored" for e in ev),
        "goals_failed": sum(e["event"] == "goal_failed" for e in ev),
        "outcome": outcome, "end_reason": (done or end).get("why", end["event"]),
        "battery_v": [round(batt[0], 2), round(batt[-1], 2)] if batt else None,
        "search_ms_mean": round(float(np.mean(search)), 1) if search else None,
        "poses": [(e["t"] - t0, e["pose"][0], e["pose"][1]) for e in ev if "pose" in e],
        "area_curve": [(e["t"] - t0, e["explored_m2"]) for e in samples if "explored_m2" in e],
        "goals": [(e["event"], e["goal"][0], e["goal"][1]) for e in goals if e.get("goal")],
        "home": ev[0].get("home"), "t_end": end["t"],
        "battery_curve": [(e["t"], e["battery_v"]) for e in samples if e.get("battery_v")],
    }


runs = [load_run(p) for p in sorted(glob.glob(os.path.join(DATA, "robot_logs", "*.jsonl")))]
for i, r in enumerate(runs, 1):
    r["id"] = "R%02d" % i


# ------------------------------------------------------------------ maps
def load_pgm(path):
    with open(path, "rb") as f:
        data = f.read()
    parts, i = [], 0
    while len(parts) < 4:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b"#":
            while data[i:i + 1] != b"\n":
                i += 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        parts.append(data[i:j])
        i = j
    w, h = int(parts[1]), int(parts[2])
    return np.frombuffer(data[i + 1:i + 1 + w * h], np.uint8).reshape(h, w)


def load_map(yaml_path):
    meta = {}
    for line in open(yaml_path):
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    img = load_pgm(os.path.join(os.path.dirname(yaml_path), meta["image"]))
    origin = [float(v) for v in meta["origin"].strip("[]").split(",")]
    return img, float(meta["resolution"]), origin[0], origin[1]


def map_stats(img, res):
    a = res * res
    return {"free_m2": round(float((img == 254).sum()) * a, 1), "occupied_m2": round(float((img == 0).sum()) * a, 1),
            "known_m2": round(float((img != 205).sum()) * a, 1)}


def match_run(saved_t):
    """The run whose log ended last before the map was saved (same SLAM session)."""
    cands = [r for r in runs if r["t0"] < saved_t and r["t_end"] <= saved_t + 5]
    return max(cands, key=lambda r: r["t_end"]) if cands else None


def plot_map(path_png, img, res, ox, oy, run, title, info):
    h, w = img.shape
    shade = np.where(img == 0, 0.0, np.where(img == 254, 1.0, 0.82))
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    ext = (ox, ox + w * res, oy, oy + h * res)
    ax.imshow(shade, cmap="gray", vmin=0, vmax=1, extent=ext, interpolation="nearest")
    if run:
        xy = np.array([(p[1], p[2]) for p in run["poses"]])
        ax.plot(xy[:, 0], xy[:, 1], "-", color=BLUE, lw=1.6, label="robot path (SLAM pose)")
        for kind, color, marker, lab in (("goal_reached", GREEN, "o", "goal reached"),
                                         ("frontier_explored", ORANGE, "s", "frontier seen on the way"),
                                         ("goal_failed", RED, "x", "goal failed")):
            g = [(x, y) for k, x, y in run["goals"] if k == kind]
            if g:
                g = np.array(g)
                ax.scatter(g[:, 0], g[:, 1], c=color, marker=marker, s=28, zorder=4, label=lab,
                           linewidths=1.6 if marker == "x" else 0.5, edgecolors="white" if marker != "x" else None)
        ax.scatter([xy[0, 0]], [xy[0, 1]], marker="*", s=180, c="#F2C200", edgecolors=INK, zorder=5, label="start")
        ax.scatter([xy[-1, 0]], [xy[-1, 1]], marker="D", s=46, c=RED, edgecolors="white", zorder=5, label="end")
    # crop to the known area plus a margin
    known = np.argwhere(img != 205)
    if len(known):
        r0, c0 = known.min(0)
        r1, c1 = known.max(0)
        m = 0.5
        ax.set_xlim(ox + c0 * res - m, ox + (c1 + 1) * res + m)
        ax.set_ylim(oy + (h - r1 - 1) * res - m, oy + (h - r0) * res + m)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.grid(True, color="#5A6CFF", alpha=0.25, lw=0.6)
    ax.set_title(title, loc="left", color=INK)
    ax.text(0.0, -0.12, info.replace(" | ", "\n").replace(", goals", "\ngoals"), transform=ax.transAxes,
            fontsize=8.5, color="#55555F", va="top")
    if run:
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8, frameon=False)
    fig.savefig(path_png, bbox_inches="tight")
    plt.close(fig)


maps = []
for jpath in sorted(glob.glob(os.path.join(DATA, "pc_maps", "*.json"))):
    meta = json.load(open(jpath))
    img, res, ox, oy = load_map(jpath[:-5] + ".yaml")
    saved_t = time.mktime(time.strptime(meta["saved"], "%Y-%m-%d %H:%M:%S"))
    run = match_run(saved_t)
    st = map_stats(img, res)
    m = {"name": meta["name"], "saved": meta["saved"][11:16], "run": run["id"] if run else None,
         "size_m": meta["size_m"], "explored_m2": meta["explored_m2"], "path_length_m": meta["path_length_m"],
         "mapping_time_s": meta.get("mapping_time_s"), "explorer_elapsed_s": meta.get("explorer_elapsed_s"), **st}
    maps.append(m)
    timing = (" | timer %s (explorer %.0f s)" % (meta["mapping_time"], meta["explorer_elapsed_s"])
              if "mapping_time" in meta else "")
    info = ("map %.1f × %.1f m, %.1f m² known (free %.1f, occupied %.1f), app path %.1f m%s"
            % (meta["size_m"][0], meta["size_m"][1], st["known_m2"], st["free_m2"], st["occupied_m2"],
               meta["path_length_m"], timing))
    if run:
        info += "\nrun %s %s: %.1f min, %.1f m driven, goals %d reached / %d seen / %d failed, end: %s" % (
            run["id"], run["start"], run["duration_s"] / 60, run["distance_m"], run["goals_reached"],
            run["goals_explored"], run["goals_failed"], run["end_reason"])
    plot_map(os.path.join(FIG, "maps", meta["name"] + ".png"), img, res, ox, oy, run,
             "%s  (saved %s)" % (meta["name"], meta["saved"][11:16]), info)

# morning session saved no map on the PC: plot the robot's own save for it
for name, rid in (("explore_2026-10-20_09-35-26", "R01"), ("explore_2026-10-20_09-38-20", "R02")):
    img, res, ox, oy = load_map(os.path.join(DATA, "robot_maps", name + ".yaml"))
    run = next(r for r in runs if r["id"] == rid)
    st = map_stats(img, res)
    plot_map(os.path.join(FIG, "maps", name + ".png"), img, res, ox, oy, run,
             "%s  (robot save, run %s)" % (name, rid),
             "%.1f m² known (free %.1f, occupied %.1f)\nrun %s %s: %.1f min, %.1f m driven, goals %d reached / %d failed, end: %s"
             % (st["known_m2"], st["free_m2"], st["occupied_m2"], rid, run["start"], run["duration_s"] / 60,
                run["distance_m"], run["goals_reached"], run["goals_failed"], run["end_reason"]))

# ------------------------------------------------------------------ comparisons
OUTCOME_COLOR = {"completed": GREEN, "operator stop": GREY, "no return": RED, "battery low": ORANGE,
                 "log ends": GREY}
ids = [r["id"] for r in runs]
x = np.arange(len(runs))

fig, axs = plt.subplots(3, 1, figsize=(8.0, 6.6), sharex=True)
for ax, key, scale, lab in ((axs[0], "duration_s", 1 / 60, "duration (min)"),
                            (axs[1], "distance_m", 1, "distance driven (m)"),
                            (axs[2], "explored_m2", 1, "mapped area (m²)")):
    vals = [r[key] * scale for r in runs]
    ax.bar(x, vals, color=[OUTCOME_COLOR[r["outcome"]] for r in runs], width=0.7)
    for xi, v in zip(x, vals):
        ax.text(xi, v, "%.1f" % v if v < 100 else "%.0f" % v, ha="center", va="bottom", fontsize=7.5, color=INK)
    ax.set_ylabel(lab)
    ax.grid(axis="y", alpha=0.3)
    ax.margins(y=0.18)
axs[2].set_xticks(x, ["%s\n%s" % (r["id"], r["start"]) for r in runs], fontsize=7.5)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (GREEN, GREY, RED, ORANGE)]
axs[0].legend(handles, ["completed (back home)", "operator stop", "could not return", "battery low"],
              ncol=4, fontsize=8, loc="upper left", frameon=False, bbox_to_anchor=(0, 1.32))
for key, a, b, _ in SESSIONS:
    idx = [i for i, r in enumerate(runs) if r["session"] == key]
    axs[0].annotate(key, ((idx[0] + idx[-1]) / 2, 1.0), xycoords=("data", "axes fraction"), ha="center",
                    fontsize=10, fontweight="bold", color=BLUE)
    if idx[0] > 0:
        for ax in axs:
            ax.axvline(idx[0] - 0.5, color="#BBB", lw=0.8, ls="--")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "runs_overview.png"))
plt.close(fig)

fig, ax = plt.subplots(figsize=(8.0, 3.0))
reached = np.array([r["goals_reached"] for r in runs])
seen = np.array([r["goals_explored"] for r in runs])
failed = np.array([r["goals_failed"] for r in runs])
ax.bar(x, reached, color=GREEN, width=0.7, label="reached")
ax.bar(x, seen, bottom=reached, color=ORANGE, width=0.7, label="frontier seen on the way")
ax.bar(x, failed, bottom=reached + seen, color=RED, width=0.7, label="failed (Nav2 aborted / timeout)")
ax.set_xticks(x, ["%s\n%s" % (r["id"], r["start"]) for r in runs], fontsize=7.5)
ax.set_ylabel("goals")
ax.grid(axis="y", alpha=0.3)
ax.legend(fontsize=8, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "goal_outcomes.png"))
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 3.4))
done_runs = [r for r in runs if r["outcome"] == "completed" and r["duration_s"] > 30]
cmap = plt.get_cmap("viridis")
for i, r in enumerate(done_runs):
    c = np.array(r["area_curve"])
    ax.plot(c[:, 0] / 60, c[:, 1], "-", color=cmap(i / max(1, len(done_runs) - 1)), lw=1.8,
            label="%s %s (%.0f m², %.1f min)" % (r["id"], r["start"], r["explored_m2"], r["duration_s"] / 60))
ax.set_xlabel("time since Explore (min)")
ax.set_ylabel("mapped area (m²)")
ax.grid(alpha=0.3)
ax.legend(fontsize=7.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "area_vs_time.png"))
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.4, 2.8))
for r in runs:
    c = np.array(r["battery_curve"])
    if len(c):
        ax.plot([time.localtime(t).tm_hour + time.localtime(t).tm_min / 60 + time.localtime(t).tm_sec / 3600
                 for t in c[:, 0]], c[:, 1], ".", ms=3, color=OUTCOME_COLOR[r["outcome"]])
ax.axhline(7.0, color=RED, ls="--", lw=1)
ax.text(9.4, 7.02, "explorer's battery_min_v = 7.0 V", color=RED, fontsize=8, va="bottom")
ax.set_xlabel("time of day (h)")
ax.set_ylabel("battery (V)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "battery.png"))
plt.close(fig)

# ------------------------------------------------------------------ tables
drop = ("poses", "area_curve", "goals", "battery_curve", "t0", "t_end", "home")
json.dump([{k: v for k, v in r.items() if k not in drop} for r in runs],
          open(os.path.join(DATA, "runs.json"), "w"), indent=1)
json.dump(maps, open(os.path.join(DATA, "maps.json"), "w"), indent=1)
cols = ["id", "session", "start", "duration_s", "explore_s", "return_s", "distance_m", "explored_m2", "goals_sent",
        "goals_reached", "goals_explored", "goals_failed", "outcome", "end_reason", "search_ms_mean", "log"]
with open(os.path.join(DATA, "runs.csv"), "w", newline="") as f:
    wr = csv.writer(f)
    wr.writerow(cols)
    for r in runs:
        wr.writerow([r[c] for c in cols])
for r in runs:
    print("%s %s %s %-13s %5.1f min %5.1f m %6.1f m² g %d/%d/%d bat %s  %s" % (
        r["id"], r["session"], r["start"], r["outcome"], r["duration_s"] / 60, r["distance_m"], r["explored_m2"],
        r["goals_reached"], r["goals_explored"], r["goals_failed"], r["battery_v"], r["end_reason"]))
for m in maps:
    print(m)

# ------------------------------------------------------------------ per session
sessions = []
for key, a, b, label in SESSIONS:
    rs = [r for r in runs if r["session"] == key]
    done = [r for r in rs if r["outcome"] == "completed"]
    sent = sum(r["goals_sent"] for r in rs)
    failed = sum(r["goals_failed"] for r in rs)
    sessions.append({
        "session": key, "label": label, "time": "%s-%s" % (a, b), "runs": [r["id"] for r in rs],
        "n_runs": len(rs), "n_completed": len(done), "goals_sent": sent, "goals_failed": failed,
        "fail_rate": round(failed / sent, 2) if sent else None,
        "distance_m": round(sum(r["distance_m"] for r in rs), 1),
        "drive_min": round(sum(r["duration_s"] for r in rs) / 60, 1),
        "completed_mean_min": round(float(np.mean([r["duration_s"] for r in done])) / 60, 2) if done else None,
        "completed_mean_m": round(float(np.mean([r["distance_m"] for r in done])), 1) if done else None,
        "completed_mean_speed": round(float(np.mean([r["distance_m"] / r["duration_s"] for r in done])), 3)
        if done else None,
        "return_s_mean": round(float(np.mean([r["return_s"] for r in done if r["return_s"]])), 1)
        if any(r["return_s"] for r in done) else None})
json.dump(sessions, open(os.path.join(DATA, "sessions.json"), "w"), indent=1)
for s in sessions:
    print(s)
print("total distance %.1f m, total explorer time %.1f min" % (sum(r["distance_m"] for r in runs),
                                                             sum(r["duration_s"] for r in runs) / 60))
