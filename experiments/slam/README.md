# robot04: autonomous lidar mapping (Hector SLAM + Nav2 + frontier exploration)

**Authors:** Marthens HAKIZIMANA, Amir TAGHAVIPOUR

robot04 is a Hiwonder MentorPi T1 (Raspberry Pi 5 + RRC Lite, tracks, Oradar MS200 lidar)
set up with the labs on this site. Hector SLAM, Nav2 and a frontier explorer run on the Pi;
the PC only watches. The robot code is in
[rpi5-robot-board](https://github.com/hmarthens1/rpi5-robot-board) (`ros2/mentorpi_nav`,
`pc/robot04-mapper`); Lab 04 covers the lidar and Hector SLAM.

| Path | What |
|---|---|
| `robot04_slam_exploration.pdf` | 6-page paper: system, explorer, first unattended run (47 m² in 12.6 min, 30 goals, back to start) |
| `paper/` | its LaTeX source, figures, `make_results_tex.py` (numbers from `data/`) |
| `deck/build_deck.py` | builds the 21-slide seminar deck with speaker notes, `robot04_autonomous_mapping.pptx` (not in the repo) |
| `data/` | first run (2026-10-17): explorer log, saved map, SLAM pose CSV, summaries; `sim_explore.*`: the explorer on a synthetic apartment |
| `experiments/2026-10-20/` | 18 runs in one day: report (PDF + LaTeX), 14-slide deck (slides PDF), every map, logs, analysis scripts — see its README |

Rebuild:

    cd paper && python3 make_results_tex.py && pdflatex robot04_slam_exploration.tex && pdflatex robot04_slam_exploration.tex
    python3 deck/build_deck.py          # needs the MSE804 seminar template (BASE in the script), python-pptx
    cd experiments/2026-10-20 && python3 scripts/analyze_day.py && python3 scripts/make_tables.py && python3 deck/build_deck.py
