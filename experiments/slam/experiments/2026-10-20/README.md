# robot04 mapping experiments, 2026-10-20

18 autonomous exploration runs (Hector SLAM + Nav2 + frontier explorer on the Pi), 09:32-12:57.

| File | What |
|---|---|
| `robot04_experiments_2026-10-20.pdf` | report (source: `report/*.tex`) |
| `robot04_experiments_2026-10-20.pptx` | slides on the `../../robot04_autonomous_mapping.pptx` template (`_slides.pdf`: preview) |
| `figures/maps/*.png` | every saved map with metric axes, robot path, goals, start/end |
| `figures/*.png` | per-run comparisons: overview, goal outcomes, area vs time, battery |
| `data/robot_logs/` | explorer logs from robot04:~/explore_logs |
| `data/robot_maps/`, `data/pc_maps/` | maps saved on the robot / from the mapper app |
| `data/runs.csv`, `runs.json`, `sessions.json`, `maps.json` | the numbers |

Rebuild (from this folder):

    python3 scripts/analyze_day.py && python3 scripts/make_tables.py
    (cd report && pdflatex robot04_experiments_2026-10-20.tex && pdflatex robot04_experiments_2026-10-20.tex)
    python3 deck/build_deck.py
