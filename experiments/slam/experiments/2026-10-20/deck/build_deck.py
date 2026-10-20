#!/usr/bin/env python3
"""Builds robot04_experiments_2026-10-20.pptx on the robot04_autonomous_mapping.pptx template.

The template's title slide is kept and rewritten; its header bar, page number and lab footers are
copied onto every new slide (helpers from SLAM/deck/build_deck.py, same palette and font).

  python3 deck/build_deck.py      (from experiments/2026-10-20, after scripts/analyze_day.py)
"""
import copy
import json
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "..", "..", "..", "robot04_autonomous_mapping.pptx")   # the template deck
FIG = os.path.join(HERE, "..", "figures")
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "robot04_experiments_2026-10-20.pptx")

BLUE = RGBColor(0x00, 0x00, 0xCC)
RED = RGBColor(0xCC, 0x06, 0x33)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x55, 0x55, 0x5F)
TINT = RGBColor(0xEC, 0xEC, 0xFA)
RTINT = RGBColor(0xFB, 0xE9, 0xED)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Times New Roman"
KEEP = ("TextBox 2", "Title 1", "TextBox 13", "TextBox 14")     # header bar, page no., footers

RUNS = {r["id"]: r for r in json.load(open(os.path.join(DATA, "runs.json")))}
MAPS = json.load(open(os.path.join(DATA, "maps.json")))
SES = {s["session"]: s for s in json.load(open(os.path.join(DATA, "sessions.json")))}


# ------------------------------------------------------------------ deck surgery
def runs_text(par, text):
    rs = par.runs
    rs[0].text = text
    for r in rs[1:]:
        r._r.getparent().remove(r._r)


def authors(par, names):
    """One name per line, each in the paragraph's first run's font."""
    runs_text(par, names[0])
    last = par.runs[0]._r
    for name in names[1:]:
        br = par._p.add_br()
        last.addnext(br)
        last = copy.deepcopy(par.runs[0]._r)
        br.addnext(last)
        last.text = name


def new_content_slide(prs, template):
    s = prs.slides.add_slide(template.slide_layout)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    for sh in template.shapes:
        if sh.name in KEEP:
            s.shapes._spTree.append(copy.deepcopy(sh._element))
    return s


def drop_slide(prs, slide):
    sld_ids = prs.slides._sldIdLst
    for sid in list(sld_ids):
        if prs.slides.part.related_part(sid.rId) is slide.part:
            prs.part.drop_rel(sid.rId)
            sld_ids.remove(sid)
            return


def header(slide, n, title, sub):
    for sh in slide.shapes:
        if sh.name == "TextBox 2":
            ps = sh.text_frame.paragraphs
            runs_text(ps[0], title)
            runs_text(ps[1], sub)
        elif sh.name == "Title 1":
            runs_text(sh.text_frame.paragraphs[0], str(n))


# ------------------------------------------------------------------ drawing helpers
def text(slide, x, y, w, h, paras, size=16, color=INK, bold=False, italic=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.05, space=6):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, "margin_" + side, Inches(margin))
    for i, p in enumerate(paras):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = align
        par.space_after = Pt(space)
        runs = [(r, {}) if isinstance(r, str) else r for r in p] if isinstance(p, list) else [(p, {})]
        for t, o in runs:
            r = par.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = o.get("color", color)
    return tb


def box(slide, x, y, w, h, fill=TINT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(1.5)
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.text_frame.text = ""
    return s


def circle_num(slide, x, y, d, label, fill=BLUE):
    c = box(slide, x, y, d, d, fill=fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, "margin_" + side, 0)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = FONT
    r.font.size = Pt(int(d * 26))
    r.font.bold = True
    r.font.color.rgb = WHITE
    return c


def arrow(slide, x1, y1, x2, y2, color=BLUE, width=2.0):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return c


def picture(slide, path, x, y, w=None, h=None):
    kw = {}
    if w:
        kw["width"] = Inches(w)
    if h:
        kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def fit_picture(slide, path, x, y, w, h):
    """Largest picture that fits the box, centred in it."""
    from PIL import Image
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    pw, ph = iw * k, ih * k
    return picture(slide, path, x + (w - pw) / 2, y + (h - ph) / 2, w=pw, h=ph)


def takeaway(slide, y, msg, h=0.75):
    box(slide, 0.55, y, 8.9, h, fill=TINT)
    text(slide, 0.75, y, 8.5, h, [msg], size=17, italic=True, color=BLUE, anchor=MSO_ANCHOR.MIDDLE, space=0)


def stat(slide, x, y, w, h, big, small, color=RED):
    box(slide, x, y, w, h, fill=TINT)
    text(slide, x + 0.1, y + 0.05, w - 0.2, 0.6, [big], size=28, bold=True, color=color, space=0)
    text(slide, x + 0.1, y + 0.67, w - 0.2, h - 0.7, [small], size=12, space=0)


def card(slide, x, y, w, h, title, body, title_color=BLUE, fill=TINT, size=12, line=None):
    box(slide, x, y, w, h, fill=fill, line=line)
    text(slide, x + 0.1, y + 0.06, w - 0.2, 0.4, [title], size=15, bold=True, color=title_color, space=0)
    text(slide, x + 0.1, y + 0.46, w - 0.2, h - 0.5, body if isinstance(body, list) else [body],
         size=size, color=GREY, space=3)


def notes(slide, t):
    slide.notes_slide.notes_text_frame.text = t


def fmt(v, nd=1):
    return ("%%.%df" % nd) % v if isinstance(v, (int, float)) else "?"


# ------------------------------------------------------------------ build
prs = Presentation(BASE)
orig = list(prs.slides)
title_slide, content_template = orig[0], orig[1]
n = 1
def table(slide, x, y, w, rows, col_w, size=11, row_h=0.3, header=True, bold_first=False):
    """rows: list of lists of str; first row is the header when header=True."""
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(row_h * len(rows)))
    t = shp.table
    tblPr = t._tbl.tblPr
    for k in ("firstRow", "bandRow"):
        tblPr.set(k, "0")
    style = tblPr.find(qn("a:tableStyleId"))
    if style is not None:
        tblPr.remove(style)
    for j, cw in enumerate(col_w):
        t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(row_h)
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.06)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            head = header and i == 0
            c.fill.fore_color.rgb = BLUE if head else (TINT if i % 2 else WHITE)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = ""
            r = p.add_run()
            r.text = v
            r.font.name = FONT
            r.font.size = Pt(size)
            r.font.bold = head or (bold_first and j == 0)
            r.font.color.rgb = WHITE if head else (BLUE if bold_first and j == 0 else INK)
    return shp



# ------------------------------------------------------------------ build
MAPFIG = os.path.join(FIG, "maps")
prs = Presentation(BASE)
orig = list(prs.slides)
title_slide, content_template = orig[0], orig[1]
n = 1


def add(title, sub):
    global n
    n += 1
    s = new_content_slide(prs, content_template)
    header(s, n, title, sub)
    return s


def run_line(r):
    return "%s %s: %.1f min, %.1f m, %d reached / %d failed" % (
        r["id"], r["start"], r["duration_s"] / 60, r["distance_m"], r["goals_reached"], r["goals_failed"])


total_m = sum(r["distance_m"] for r in RUNS.values())
total_min = sum(r["duration_s"] for r in RUNS.values()) / 60
completed = [r for r in RUNS.values() if r["outcome"] == "completed"]

# 1 title
for sh in title_slide.shapes:
    if sh.name == "Title 1":
        runs_text(sh.text_frame.paragraphs[0], "robot04 Mapping Experiments: 20 October 2026")
    elif sh.name == "Date Placeholder 3":
        runs_text(sh.text_frame.paragraphs[-1], "18 autonomous exploration runs · Hector SLAM, Nav2 and frontier "
                                                "exploration on a Raspberry Pi 5 · robot04 (MentorPi T1)")
    elif sh.name == "TextBox 3":
        authors(sh.text_frame.paragraphs[2], ["Marthens HAKIZIMANA", "Amir TAGHAVIPOUR"])
notes(title_slide, "Results of one day of autonomous mapping tests with robot04: what ran, how each run ended, "
      "the maps that were saved and what to fix next.")

# 2 the day at a glance
s = add("The Day at a Glance", "20 October 2026, 09:32 – 12:57")
for i, (big, small) in enumerate([("%d" % len(RUNS), "autonomous runs"),
                                  ("%.0f m" % total_m, "driven by the robot"),
                                  ("%.1f min" % total_min, "explorer time"),
                                  ("%d" % len(MAPS), "maps saved on the PC")]):
    stat(s, 0.55 + i * 2.27, 1.35, 2.07, 1.35, big, small)
for i, (t, b) in enumerate([
        ("Bounded area: works", "7 of 9 enclosure runs finished and drove home; the last 6 runs had no failed goal"),
        ("Large open area: not yet", "82 % of goals aborted by Nav2 in the morning; no run got back to its start"),
        ("Two side findings", "battery check trips on voltage dips; new app timer matches the explorer within 12 s")]):
    y = 2.95 + i * 0.95
    circle_num(s, 0.7, y + 0.1, 0.55, str(i + 1), fill=BLUE if i != 1 else RED)
    text(s, 1.45, y, 8.0, 0.4, [t], size=17, bold=True, color=BLUE if i != 1 else RED, space=0)
    text(s, 1.45, y + 0.4, 8.0, 0.5, [b], size=14, color=GREY, space=0)
takeaway(s, 5.85, "No code changed during the day: the runs differ in where they ran and how they ended.")
notes(s, "Eighteen runs in about three and a half hours, 153 metres driven. The main result: in a bounded area the "
      "whole loop works, mapping until no frontier is left and returning home. In the large open area it does not yet.")

# 3 setup
s = add("Setup and What Was Measured", "Same software and parameters in every run")
card(s, 0.55, 1.35, 4.35, 2.15, "On the robot (Raspberry Pi 5)", [
    "Hector SLAM, 0.05 m cells, MS200 lidar 10 Hz",
    "Nav2: NavFn + Regulated Pure Pursuit, 0.10 m/s",
    "Frontier explorer: radius 0.15 m, min frontier 0.30 m, replan 3 s, no-progress 30 s, battery ≥ 7.0 V"],
     size=13)
card(s, 5.1, 1.35, 4.35, 2.15, "On the PC (robot04 mapper app)", [
    "Watches map, path, Nav2 plan and frontiers",
    "Starts the stack over ssh; Explore / Pause / Home",
    "Saves pgm + yaml + json; new mapping timer saved with the map"], size=13)
table(s, 0.55, 3.7, 8.9, [
    ["Measure", "Source", "Definition"],
    ["duration", "explorer log", "Explore pressed → done or operator stop"],
    ["distance", "explorer log", "sum of SLAM pose steps"],
    ["mapped area", "map", "known cells (free + occupied) × 0.05² m², also beyond walls"],
    ["goals", "explorer log", "reached / frontier seen on the way / failed (Nav2 aborted, timeout)"],
], [1.6, 1.6, 5.7], size=12, row_h=0.36)
takeaway(s, 5.85, "Data: 18 explorer logs, 17 robot maps, 8 PC maps, all in experiments/2026-10-20/data.")
notes(s, "Everything ran on the Pi; the PC only watched and saved maps. The explorer logs every goal and samples the "
      "pose, mapped area and battery every few seconds, which is where all the numbers in this deck come from.")

# 4 sessions
s = add("Five Sessions Through the Day", "How each group of runs ended")
cols = [("A", "09:32", "Large open area", RED), ("B", "10:09", "One long run", GREY),
        ("C", "10:53", "Battery low", RGBColor(0xE0, 0x7B, 0x00)), ("D", "11:49", "Small enclosure", BLUE),
        ("E", "12:38", "Enclosure, repeat", RGBColor(0x2E, 0x7D, 0x32))]
for i, (k, t, label, col) in enumerate(cols):
    x = 0.55 + i * 1.8
    se = SES[k]
    box(s, x, 1.35, 1.65, 4.2, fill=TINT)
    circle_num(s, x + 0.55, 1.5, 0.55, k, fill=col)
    text(s, x + 0.05, 2.15, 1.55, 0.35, [t], size=14, bold=True, color=INK, align=PP_ALIGN.CENTER, space=0)
    text(s, x + 0.05, 2.5, 1.55, 0.6, [label], size=13, color=col, bold=True, align=PP_ALIGN.CENTER, space=0)
    text(s, x + 0.1, 3.15, 1.45, 2.3, [
        [("%d" % se["n_runs"], {"bold": True}), (" runs", {})],
        [("%d" % se["n_completed"], {"bold": True}), (" back home", {})],
        [("%d / %d" % (se["goals_failed"], se["goals_sent"]), {"bold": True}), (" goals failed", {})],
        [("%.0f m" % se["distance_m"], {"bold": True}), (" driven", {})]], size=13, color=GREY, space=5)
takeaway(s, 5.85, "Failures fell from 82 % (A) to 29 % (D) to 0 % (E) as the area became smaller and closed.")
notes(s, "Session A was a large open area; B one long run there; C four runs that stopped at once on the battery rule; "
      "D and E a small walled enclosure, where the explorer finished on its own.")

# 5 all runs
s = add("Every Run", "Duration, distance and mapped area, coloured by outcome")
fit_picture(s, os.path.join(FIG, "runs_overview.png"), 0.45, 1.2, 5.9, 4.55)
for i, (t, b, col) in enumerate([
        ("Longest", "R05: 7.7 min, 58.6 m, 136 m²", INK),
        ("Completed", "%d runs, %.1f–%.1f min" % (len(completed), min(r["duration_s"] for r in completed) / 60,
                                                   max(r["duration_s"] for r in completed) / 60), INK),
        ("Cumulative", "A and C kept one SLAM map across runs, so their area adds up", GREY)]):
    box(s, 6.55, 1.35 + i * 1.45, 2.9, 1.3, fill=TINT)
    text(s, 6.65, 1.4 + i * 1.45, 2.7, 0.4, [t], size=15, bold=True, color=BLUE, space=0)
    text(s, 6.65, 1.8 + i * 1.45, 2.7, 0.8, [b], size=13, color=col, space=0)
takeaway(s, 5.85, "Green = explored to the last frontier and drove home without help.")
notes(s, "One bar per run. Red: could not drive back. Grey: stopped by the operator. Orange: battery low. Green: done.")

# 6 session A
s = add("Session A: Large Open Area", "Nav2 aborted 62 of 74 goals in R01 and R02")
fit_picture(s, os.path.join(MAPFIG, "explore_2026-10-20_09-35-26.png"), 0.45, 1.2, 5.4, 4.55)
r1, r2 = RUNS["R01"], RUNS["R02"]
stat(s, 6.0, 1.35, 1.65, 1.3, "%d / %d" % (r1["goals_failed"], r1["goals_sent"]), "R01 goals failed / sent")
stat(s, 7.8, 1.35, 1.65, 1.3, "%d / %d" % (r2["goals_failed"], r2["goals_sent"]), "R02 goals failed / sent")
text(s, 6.0, 2.85, 3.45, 1.4, [
    "Failed goals (×) sit at the far edge of the map and behind walls",
    "Neither run could drive back to its start",
    "Frontier search 80–150 ms per goal here (20–70 ms in the enclosure)"], size=13, color=INK, space=5)
box(s, 6.0, 4.35, 3.45, 1.35, fill=RTINT)
text(s, 6.1, 4.37, 3.25, 1.31, [[("Open question: ", {"bold": True}),
                                  ("why Nav2 aborts. Check the 0.45 m wall clearance in narrow passages and goals "
                                   "inside the inflated costmap.", {})]], size=12, color=RED,
     anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "The explorer kept choosing goals Nav2 could not plan to: 41 goals in 3 min in R01.")
notes(s, "The robot's own save from R01. Blue is the path, red crosses the goals Nav2 aborted. The cause is not "
      "known yet; the next test is to log the abort reason and the costmap at each failed goal.")

# 7 session B
s = add("Session B: The Longest Run", "R05, 10:09, saved as lab_2026-10-20_1008")
fit_picture(s, os.path.join(MAPFIG, "lab_2026-10-20_1008.png"), 0.4, 1.2, 5.6, 4.55)
r = RUNS["R05"]
for i, (big, small) in enumerate([("%.1f min" % (r["duration_s"] / 60), "explored"),
                                  ("%.1f m" % r["distance_m"], "driven"),
                                  ("%.0f m²" % r["explored_m2"], "mapped"),
                                  ("%d / %d" % (r["goals_reached"], r["goals_failed"]), "goals reached / failed")]):
    stat(s, 6.15 + (i % 2) * 1.7, 1.35 + (i // 2) * 1.5, 1.6, 1.35, big, small)
text(s, 6.15, 4.4, 3.3, 1.3, ["A corridor about 15 m long and the branch at its far end; stopped by the operator "
                              "before it finished"], size=13, color=GREY, space=0)
takeaway(s, 5.85, "In the same area as session A, one run reached 9 goals and drove 59 m.")
notes(s, "The longest run of the day: nearly 8 minutes and 59 metres, 136 square metres mapped. "
      "Only 2 of 16 goals failed. The operator stopped it before the end.")

# 8 session C
s = add("Session C: The Battery Rule Fired at Once", "Four runs at 10:53, each ended within 4 s")
fit_picture(s, os.path.join(FIG, "battery.png"), 0.45, 1.25, 5.6, 2.6)
table(s, 6.25, 1.35, 3.2, [["Run", "Battery", "Ran"]] + [
    [k, "%.2f V" % RUNS[k]["battery_v"][0], "%.0f s" % RUNS[k]["duration_s"]] for k in ("R06", "R07", "R08", "R09")],
      [0.9, 1.25, 1.05], size=12, row_h=0.4)
text(s, 0.55, 4.05, 5.5, 1.6, [
    "Explorer limit: battery_min_v = 7.0 V",
    "Logged samples 7.02–7.06 V, but the check uses the instantaneous voltage, which dips when the motors start",
    "R05 had ended at 7.07 V; by 11:49 the battery read 8.18 V"], size=13, color=INK, space=5)
box(s, 6.25, 3.55, 3.2, 2.1, fill=RTINT)
text(s, 6.35, 3.57, 3.0, 2.06, [[("Fix: ", {"bold": True}),
                                  ("filter the voltage (e.g. a 5 s mean) before comparing it with 7.0 V, and log "
                                   "the minimum voltage.", {})]], size=13, color=RED, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "A safety rule on a raw voltage stops the robot at the first load step.")
notes(s, "Each of these runs cancelled its first goal with 'battery low' and went home. The voltage in the log was "
      "just above the limit; the dip when the tracks start pushed the instantaneous value below it.")

# 9 session D
s = add("Session D: A Small Enclosure", "11:49 – 12:21, four of five runs finished on their own")
fit_picture(s, os.path.join(MAPFIG, "lab_2026-10-20_1148.png"), 0.3, 1.15, 4.75, 3.7)
fit_picture(s, os.path.join(MAPFIG, "lab_2026-10-20_1148_3.png"), 5.0, 1.15, 4.75, 3.7)
text(s, 0.55, 4.9, 8.9, 0.85, [
    [("R11 (left): ", {"bold": True, "color": BLUE}), ("%s; failed goals outside the walls. " % run_line(RUNS["R11"]), {}),
     ("R13 (right): ", {"bold": True, "color": BLUE}), ("%s." % run_line(RUNS["R13"]), {})]],
     size=12, color=INK, space=0)
takeaway(s, 5.85, "The lidar sees out of the enclosure; goals placed out there cannot be reached and fail.")
notes(s, "The robot drove only inside the walled enclosure about 2.5 m across; the lidar saw out into the room, so "
      "the map is larger than the area the robot could drive. 10 of 34 goals failed, all outside or against the walls.")

# 10 session E
s = add("Session E: Repeat Runs, No Failed Goals", "12:38 – 12:57, 31 goals sent, none failed")
fit_picture(s, os.path.join(MAPFIG, "lab_2026-10-20_1249_success2.png"), 0.3, 1.15, 4.75, 3.7)
fit_picture(s, os.path.join(MAPFIG, "lab_2026-10-20_1249_success3.png"), 5.0, 1.15, 4.75, 3.7)
e = [RUNS[k] for k in ("R16", "R17", "R18")]
text(s, 0.55, 4.9, 8.9, 0.85, [
    [("Completed runs R16–R18: ", {"bold": True, "color": BLUE}),
     ("%.1f–%.1f min, %.1f–%.1f m driven, mean %.2f m/s (cruise 0.10), %.0f–%.0f s to drive home after the last frontier."
      % (min(r["duration_s"] for r in e) / 60, max(r["duration_s"] for r in e) / 60,
         min(r["distance_m"] for r in e), max(r["distance_m"] for r in e), SES["E"]["completed_mean_speed"],
         min(r["return_s"] for r in e), max(r["return_s"] for r in e)), {})]], size=12, color=INK, space=0)
takeaway(s, 5.85, "R17 (left) reached all 8 of its goals; R18 (right) 7, and saw 1 more on the way.")
notes(s, "The last session: three of four runs finished, R15 was stopped by the operator. No goal failed. "
      "These two maps were also the first saved with the app's new timer.")

# 11 timing
s = add("How Long Mapping Takes", "Mapped area against time, and the new app timer")
fit_picture(s, os.path.join(FIG, "area_vs_time.png"), 0.45, 1.25, 5.6, 3.0)
text(s, 0.55, 4.35, 5.5, 1.4, [
    "Steep start: each goal opens a new view for a 360° lidar",
    "Then corners one at a time: R11 sat at 45–47 m² for more than 2 min",
    "Completed runs: %.1f–%.1f min" % (min(r["duration_s"] for r in completed) / 60,
                                       max(r["duration_s"] for r in completed) / 60)], size=13, color=INK, space=4)
tm = [m for m in MAPS if m["mapping_time_s"]]
table(s, 6.25, 1.35, 3.2, [["Map", "App timer", "Explorer"]] + [
    [m["run"], "%.0f s" % m["mapping_time_s"], "%.0f s" % m["explorer_elapsed_s"]] for m in tm],
      [0.9, 1.15, 1.15], size=12, row_h=0.4)
box(s, 6.25, 2.75, 3.2, 2.95, fill=TINT)
text(s, 6.35, 2.8, 3.0, 2.85, [
    [("Timer ", {"bold": True, "color": BLUE}), ("runs while SLAM poses arrive and is saved in the map's json.", {})],
    [("Reads 6–12 s longer: ", {"bold": True, "color": BLUE}),
     ("it also counts SLAM before Explore and the time until the map is saved.", {})]],
     size=13, color=INK, space=8)
takeaway(s, 5.85, "Use the explorer time to compare runs; the app timer records the whole session.")
notes(s, "Each completed run maps quickly at first and then slowly. The timer added to the app today agrees with the "
      "explorer's clock; the difference is the time before Explore and before saving.")

# 12 goals
s = add("Where the Goals Went", "Goal outcomes per run")
fit_picture(s, os.path.join(FIG, "goal_outcomes.png"), 0.45, 1.25, 9.1, 3.45)
table(s, 0.55, 4.8, 8.9, [["Session", "A", "B", "C", "D", "E"],
                          ["failed / sent"] + ["%d / %d" % (SES[k]["goals_failed"], SES[k]["goals_sent"]) for k in "ABCDE"]],
      [1.9, 1.4, 1.4, 1.4, 1.4, 1.4], size=12, row_h=0.4, bold_first=True)
takeaway(s, 5.85, "Orange: frontiers the lidar cleared before the robot got there, so the explorer moved on.")
notes(s, "Green goals were reached, orange disappeared on the way, red failed. The failures are almost all in the "
      "morning's open area.")

# 13 saved maps
s = add("The Saved Maps", "~/Desktop/robot04_maps, lab_2026-10-20_*")
rows = [["Map", "Run", "Extent (m)", "Known m²", "Occupied m²", "Path (m)", "Timer"]]
for m in MAPS:
    rows.append([m["name"].replace("lab_2026-10-20_", ""), m["run"], "%.1f × %.1f" % tuple(m["size_m"]),
                 "%.1f" % m["known_m2"], "%.1f" % m["occupied_m2"], "%.1f" % m["path_length_m"],
                 "%.0f s" % m["mapping_time_s"] if m["mapping_time_s"] else "–"])
table(s, 0.55, 1.35, 8.9, rows, [1.85, 0.75, 1.35, 1.2, 1.35, 1.2, 1.2], size=12, row_h=0.43)
takeaway(s, 5.85, "Every map is also plotted with metric axes, path and goals in figures/maps.")
notes(s, "Eight maps saved from the PC app. All are map_server pgm and yaml, so Nav2 can load them.")

# 14 next steps
s = add("Findings and Next Steps", "What to change before the next session")
items = [("Works in a bounded area", "7 of 9 enclosure runs finished and drove home; last 6 runs: 0 failed goals", BLUE),
         ("Open areas: Nav2 aborts", "log the abort reason and costmap per failed goal; try a smaller inflation", RED),
         ("Unreachable frontiers", "drop frontiers with no path in the global costmap before sending them", BLUE),
         ("Battery rule", "filter the voltage before the 7.0 V check; log the minimum", BLUE),
         ("Timing", "explorer time per run; app timer saved with every map from now on", BLUE)]
for i, (t, b, col) in enumerate(items):
    y = 1.3 + i * 0.88
    box(s, 0.55, y, 8.9, 0.76, fill=TINT if col == BLUE else RTINT)
    circle_num(s, 0.7, y + 0.13, 0.5, str(i + 1), fill=col)
    text(s, 1.35, y, 7.95, 0.76, [[(t + ": ", {"bold": True, "color": col}), (b, {})]], size=14,
         anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "Next session: the same enclosure test, then the open area with Nav2 abort logging.")
notes(s, "Five points: the loop works when the area is closed; the open area needs the Nav2 failures understood; "
      "unreachable frontiers should be filtered; the battery check needs filtering; and every map now carries its time.")

for old in orig[1:]:
    drop_slide(prs, old)
prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
