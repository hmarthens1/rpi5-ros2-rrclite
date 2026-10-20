#!/usr/bin/env python3
"""Builds robot04_autonomous_mapping.pptx in the style of the MSE 804 seminar deck.

The seminar deck is the base: its title slide is kept (SFU picture, white bar) and the
header bar, page number and lab footers of a content slide are copied onto every new
slide; the body of each slide is drawn here in the same palette (blue 0000CC, red CC0633,
ink 1A1A1A, grey 55555F, card ECECFA) and Times New Roman.

  python3 build_deck.py            (reads ../data/run_summary.json, ../paper/figures/*.png)
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
BASE = os.path.expanduser("~/Desktop/Seminar MSE804 2026/presentation/MSE804_Hakizimana_Seminar.pptx")
FIG = os.path.join(HERE, "..", "paper", "figures")
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "robot04_autonomous_mapping.pptx")

BLUE = RGBColor(0x00, 0x00, 0xCC)
RED = RGBColor(0xCC, 0x06, 0x33)
INK = RGBColor(0x1A, 0x1A, 0x1A)
GREY = RGBColor(0x55, 0x55, 0x5F)
TINT = RGBColor(0xEC, 0xEC, 0xFA)
RTINT = RGBColor(0xFB, 0xE9, 0xED)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Times New Roman"
KEEP = ("TextBox 2", "Title 1", "TextBox 13", "TextBox 14")     # header bar, page no., footers

R = json.load(open(os.path.join(DATA, "run_summary.json")))
SIM = json.load(open(os.path.join(DATA, "sim_explore.json")))["final"]


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

# 1 title
for sh in title_slide.shapes:
    if sh.name == "Title 1":
        runs_text(sh.text_frame.paragraphs[0], "A Low-Cost Robot that Maps a Home on Its Own")
    elif sh.name == "Date Placeholder 3":
        ps = sh.text_frame.paragraphs
        runs_text(ps[-1], "Hector SLAM, Nav2 and frontier exploration on a Raspberry Pi 5 · robot04 (MentorPi T1), October 2026")
    elif sh.name == "TextBox 3":
        authors(sh.text_frame.paragraphs[2], ["Marthens HAKIZIMANA", "Amir TAGHAVIPOUR"])
notes(title_slide, "~20 s. This is about turning a small educational robot into one that maps a home by itself: "
      "it decides where to go, avoids obstacles, and comes back with a map. Everything runs on a Raspberry Pi 5; "
      "my laptop only watches.")

slides = []


def add(title, sub):
    global n
    n += 1
    s = new_content_slide(prs, content_template)
    header(s, n, title, sub)
    slides.append(s)
    return s


# 2 why
s = add("Why Let the Robot Drive Itself?", "Motivation & goal")
for i, (t, b) in enumerate([
        ("A map comes first", "Localisation, path planning and inspection all start from a map of the space"),
        ("Driving is the slow part", "With a lidar the mapping is solved; steering slowly through every room is not"),
        ("Low-cost hardware", "Can a low-cost tracked robot with an entry-level lidar do it, with everything on board?")]):
    y = 1.4 + i * 1.45
    circle_num(s, 0.7, y + 0.05, 0.6, str(i + 1))
    text(s, 1.5, y, 7.9, 0.45, [t], size=20, bold=True, color=BLUE, space=0)
    text(s, 1.5, y + 0.47, 7.9, 0.8, [b], size=16, space=0)
takeaway(s, 5.85, "Goal: press Explore, walk away, come back to a finished map of the house.")
notes(s, "~40 s. Mapping with a 2D lidar is a solved problem; what costs time is the operator driving slowly "
      "through every room. Frontier exploration automates that. The question was whether a cheap robot can do it "
      "with all the computation on board.")

# 3 robot
s = add("robot04: What We Started With", "Hiwonder MentorPi T1, rebuilt on ROS 2 Jazzy")
cam = os.path.join(FIG, "camera_view.jpg")
if os.path.exists(cam):
    fit_picture(s, cam, 0.55, 1.35, 4.3, 2.7)
    text(s, 0.55, 4.08, 4.3, 0.35, ["What the robot sees: its RGB camera, 10 fps on the PC"], size=10, italic=True, color=GREY)
rows = [("Computer", "Raspberry Pi 5, 8 GB · Ubuntu 24.04 · ROS 2 Jazzy"),
        ("Drive", "2 tracks, JGB37-520 motors, STM32 speed loop · 0.15 m/s top"),
        ("Lidar", "Oradar MS200 · 360° · 10 Hz · own ROS 2 driver"),
        ("Camera", "Deptrum Aurora 930 RGB-D · watched from the PC"),
        ("Operator", "Laptop, ROS 2 Humble, same Wi-Fi · Cyclone DDS")]
for i, (k, v) in enumerate(rows):
    y = 1.35 + i * 0.6
    box(s, 5.1, y, 1.25, 0.52, fill=BLUE)
    text(s, 5.1, y, 1.25, 0.52, [k], size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
    box(s, 6.45, y, 3.0, 0.52, fill=TINT)
    text(s, 6.52, y, 2.9, 0.52, [v], size=11, anchor=MSO_ANCHOR.MIDDLE, space=0)
box(s, 0.55, 4.6, 8.9, 1.1, fill=RTINT)
text(s, 0.75, 4.62, 8.5, 1.05, [[("Written for this work: ", {"bold": True, "color": RED}),
                                ("lidar driver (47-byte packets, CRC-8, 450 rays), velocity adapter, frontier explorer, "
                                 "Nav2 configuration, the PC mapper app, and a lidar-only calibration test.", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "Standard ROS 2 parts where they exist; small, testable glue where they don't.")
notes(s, "~40 s. The robot: Pi 5, tracks, a 360 degree lidar and a depth camera. There was no ROS 2 driver for "
      "the lidar, so I wrote one. The rest is standard ROS 2: Hector SLAM and Nav2, plus glue I wrote.")

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


def eq(slide, x, y, w, h, lines, size=15):
    """Equation card: monospace-free, centred maths lines on a white card with a blue rule."""
    box(slide, x, y, w, h, fill=WHITE, line=BLUE)
    text(slide, x + 0.1, y + 0.05, w - 0.2, h - 0.1, lines, size=size, color=INK, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, space=4)


# 4 related work
s = add("Which SLAM, Which Navigation, Which Exploration?", "Related work and the choices made")
table(s, 0.55, 1.35, 8.9, [
    ["Component", "Options considered", "Chosen", "Why"],
    ["2D SLAM", "GMapping (RBPF), Cartographer, SLAM Toolbox, Hector", "Hector SLAM",
     "needs no odometry (tracks skid); ≈ 3 % of a Pi core"],
    ["Navigation", "Nav2: DWB, MPPI, Regulated Pure Pursuit", "Nav2 + RPP",
     "slow diff-drive robot, few parameters, built-in collision check"],
    ["Planner", "NavFn, Smac 2D/Hybrid, Theta*", "NavFn (A*)",
     "cheap, allow_unknown for goals at the map's edge"],
    ["Exploration", "explore_lite, RRT exploration, information gain", "own greedy frontier",
     "every decision logged; blacklist + return home; Jazzy native"],
    ["Placement", "SLAM on PC, robot as sensor  vs.  all on robot", "all on robot",
     "Wi-Fi drop must not break the control loop"],
], [1.35, 3.0, 1.55, 3.0], size=11, row_h=0.62, bold_first=True)
text(s, 0.55, 5.2, 8.9, 0.5, ["Kohlbrecher 2011 (Hector) · Grisetti 2007 (GMapping) · Hess 2016 (Cartographer) · Macenski 2020/2023 (Nav2, RPP) · "
                              "Yamauchi 1997 (frontiers) · Umari 2017 (RRT exploration)"], size=10, italic=True, color=GREY)
takeaway(s, 5.85, "Mature parts for SLAM and navigation; the explorer is the only planning logic written here.")
notes(s, "~45 s. For SLAM I chose Hector because it needs no odometry, and the tracks skid. For navigation Nav2 with "
      "Regulated Pure Pursuit, which suits a slow differential robot. The explorer is my own greedy frontier explorer, "
      "because I wanted every decision logged and a clean return home.")

# 5 architecture
s = add("Every Loop on the Robot, the PC Only Watches", "System architecture: nodes, rates and where they run")
cols = [("Drivers", "robot-fleet-node.service", ["ms200_node  /scan 10 Hz", "robot_node  odom 20 Hz,", "  cmd_vel, 0.25 m stop", "camera_bridge  JPEG 10 Hz"]),
        ("SLAM", "robot-explore.service", ["hector_mapping", "/map 1 Hz, 5 cm, 1024²", "TF map → robot04/odom"]),
        ("Navigation", "robot-explore.service", ["planner 1 Hz (NavFn)", "controller 8 Hz (RPP)", "local costmap 10 Hz", "BT navigator, smoother 20 Hz"]),
        ("Explorer", "robot-explore.service", ["search every 3 s", "NavigateToPose action", "/explore/state 1 Hz", "JSONL run log"])]
for i, (t, sub, body) in enumerate(cols):
    x = 0.55 + i * 2.28
    box(s, x, 1.35, 2.06, 1.95, fill=TINT)
    text(s, x + 0.1, 1.4, 1.9, 0.4, [t], size=16, bold=True, color=BLUE, space=0)
    text(s, x + 0.1, 1.74, 1.9, 0.3, [sub], size=9, italic=True, color=GREY, space=0)
    text(s, x + 0.1, 2.02, 1.9, 1.25, body, size=10.5, color=INK, space=1)
    arrow(s, x + 1.03, 3.32, x + 1.03, 3.62, color=BLUE)
box(s, 0.55, 3.65, 8.9, 0.55, fill=BLUE, shape=MSO_SHAPE.RECTANGLE)
text(s, 0.55, 3.65, 8.9, 0.55, ["Raspberry Pi 5 · ROS 2 Jazzy · Cyclone DDS · domain 17 · ≈ 1.5 of 4 cores"],
     size=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
arrow(s, 5.0, 4.22, 5.0, 4.52, color=RED)
box(s, 0.55, 4.55, 5.2, 1.15, fill=WHITE, line=RED)
text(s, 0.7, 4.58, 5.0, 1.1, [[("Operator PC: Humble, Wi-Fi", {"bold": True, "color": RED, "size": 15})],
                              "subscribes /map, /plan, /slam_out_pose, JPEG, /explore/state · publishes "
                              "/explore/control and teleop cmd_vel · starts the stack with ssh systemctl --user"],
     size=11, color=GREY, space=2)
box(s, 6.0, 4.55, 3.45, 1.15, fill=TINT)
text(s, 6.1, 4.58, 3.3, 1.1, [[("Rule: ", {"bold": True}), ("a Wi-Fi drop costs the view, never the control loop", {})]],
     size=14, color=BLUE, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "Hector on the PC worked for teleop mapping (≈ 20 KB/s, +6 ms); for autonomy it moved on board.")
notes(s, "~60 s. Two systemd services on the Pi: drivers at boot, and the exploration stack on demand, which the PC "
      "starts over ssh. Every control loop runs on the Pi. The laptop subscribes to the map, plan, camera and "
      "explorer state, and only publishes start, pause and home.")

# 6 lidar driver + TF
s = add("A Lidar Driver and a Frame Tree", "ms200_node (written for this work) and the TF chain")
table(s, 0.55, 1.35, 4.5, [
    ["Bytes", "Field (MS200, LD06 layout)"],
    ["0–1", "header 0x54 0x2C"],
    ["2–3", "rotation speed, °/s"],
    ["4–5", "start angle, 0.01°"],
    ["6–41", "12 × (range mm u16, intensity u8)"],
    ["42–43", "end angle, 0.01°"],
    ["44–45", "time stamp, ms"],
    ["46", "CRC-8, polynomial 0x4D"],
], [0.8, 3.7], size=11, row_h=0.36)
text(s, 0.55, 4.35, 4.5, 1.4, [
    "230 400 baud · angle of point k interpolated start → end",
    "revolution ends when the angle wraps → 450 rays (0.8°), nearest return per ray, invalid = inf",
    "device angles clockwise → negated (ROS: counter-clockwise) · drop < 0.10 m (own frame)"],
    size=11, color=GREY, space=3)
text(s, 5.35, 1.35, 4.1, 0.4, ["TF tree"], size=16, bold=True, color=BLUE, space=0)
frames = [("map", None), ("robot04/odom", "hector_mapping, at scan time"),
          ("robot04/base_footprint", "robot_node, encoders, 20 Hz"), ("robot04/laser", "static: z = 0.12 m")]
for i, (f_, by) in enumerate(frames):
    y = 1.8 + i * 0.95
    box(s, 5.35, y, 2.3, 0.5, fill=BLUE)
    text(s, 5.35, y, 2.3, 0.5, [f_], size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
    if i < len(frames) - 1:
        arrow(s, 6.5, y + 0.5, 6.5, y + 0.95)
        text(s, 6.65, y + 0.52, 2.8, 0.4, [frames[i + 1][1]], size=10, italic=True, color=GREY, space=0)
text(s, 5.35, 5.6 - 0.15, 4.1, 0.3, ["udev: /dev/lidar matched by USB ID and port (voice module is a CH340 too)"], size=9.5, color=GREY)
takeaway(s, 5.85, "Lidar yaw checked against the camera: 0° is the front, angles counter-clockwise.")
notes(s, "~45 s. No ROS 2 Jazzy driver existed, so I parsed the 47-byte packets myself, checked the CRC, and binned "
      "each revolution into 450 rays. The TF chain: Hector publishes map to odom, the motor node odom to base, and the "
      "laser is a static frame 12 cm up.")

# 7 hector
s = add("Hector SLAM: Scan Matching Without Odometry", "Kohlbrecher et al. 2011, ROS 2 port, running on the Pi")
eq(s, 0.55, 1.35, 8.9, 1.25, [
    "ξ* = argmin_ξ  Σᵢ [ 1 − M( Sᵢ(ξ) ) ]²",
    [("ξ = (x, y, ψ) robot pose · Sᵢ(ξ) = scan end point i in the map · M = occupancy, bilinearly interpolated", {"size": 11, "color": GREY})]], size=19)
eq(s, 0.55, 2.75, 8.9, 1.05, [
    "Δξ = H⁻¹ Σᵢ [ ∇M(Sᵢ(ξ)) ∂Sᵢ/∂ξ ]ᵀ [ 1 − M(Sᵢ(ξ)) ],   H = Σᵢ [∇M ∂Sᵢ/∂ξ]ᵀ[∇M ∂Sᵢ/∂ξ]",
    [("Gauss–Newton step; coarse map level first, then fine (2 levels) to avoid local minima", {"size": 11, "color": GREY})]], size=14)
table(s, 0.55, 3.95, 8.9, [
    ["Map", "Updates", "Scan window", "Occupancy update", "Frames", "Cost on the Pi"],
    ["5 cm, 1024² (51 m), 2 levels", "every 0.2 m / 0.06 rad", "0.12–8 m", "free 0.4 · occupied 0.9",
     "map → robot04/odom", "≈ 3 % of a core"],
], [1.8, 1.45, 1.05, 1.6, 1.6, 1.4], size=10.5, row_h=0.55)
box(s, 0.55, 5.1, 8.9, 0.62, fill=RTINT)
text(s, 0.7, 5.1, 8.6, 0.62, ["No loop closure: Hector's map is only as good as each match. It holds at ≤ 0.6 rad/s turning; "
                              "it fails if the robot's motion is not what the controller believes (slide 15)."],
     size=12, color=RED, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "Odometry-free SLAM suits tracks: the map is the only reference the pose needs.")
notes(s, "~60 s. Hector finds the pose that puts every scan point on an occupied cell, by Gauss-Newton on a "
      "bilinearly interpolated map, coarse to fine. No odometry is used, which is why it suits a tracked robot. "
      "It has no loop closure, so a bad match stays in the map.")

# 8 Nav2 configuration
s = add("Nav2 on a Raspberry Pi: The Configuration", "config/nav2.yaml (servers started directly, no bringup)")
table(s, 0.55, 1.35, 5.3, [
    ["Server", "Plugin / key parameters"],
    ["planner_server", "NavFn, A*, allow_unknown, tolerance 0.3 m"],
    ["controller_server", "RPP, 8 Hz, 0.10 m/s, lookahead 0.25–0.6 m"],
    ["  goal checker", "0.20 m, any heading"],
    ["  progress checker", "0.10 m in 20 s"],
    ["local costmap", "odom frame, 3 × 3 m rolling, 10 Hz, inflation 0.40"],
    ["global costmap", "map frame, static (/map) + scan, inflation 0.45"],
    ["behavior_server", "spin, backup, wait"],
    ["velocity_smoother", "20 Hz, ≤ 0.12 m/s, ≤ 0.8 rad/s, open loop"],
    ["bt_navigator", "navigate_to_pose w/ replanning + recovery"],
], [1.6, 3.7], size=10, row_h=0.4)
text(s, 6.1, 1.35, 3.35, 0.4, ["Regulated Pure Pursuit"], size=16, bold=True, color=BLUE, space=0)
eq(s, 6.1, 1.8, 3.35, 1.25, ["κ = 2 y_L / L²", "ω = v κ"], size=17)
text(s, 6.1, 3.1, 3.35, 2.6, [
    "L: lookahead distance, y_L: lateral offset of the carrot",
    "v reduced on tight curves (r < 0.5 m) and near obstacles (costmap cost)",
    "rotate in place first when heading error > 0.6 rad, at 0.6 rad/s",
    "collision check of the arc up to the carrot, 1.5 s ahead",
    "robot = circle r = 0.15 m"], size=11, color=GREY, space=4)
takeaway(s, 5.85, "TF tolerance 1.0 s: Hector stamps map → odom with the scan time, 0.1–0.2 s old.")
notes(s, "~60 s. The servers I start, with their key parameters. Pure pursuit steers toward a carrot on the path: "
      "curvature two y over L squared. It slows down on tight curves and near obstacles and rotates in place for big "
      "heading errors. The transform tolerance had to go to one second because Hector's TF is stamped with the scan time.")

# 9 obstacle avoidance
s = add("Obstacle Avoidance in Three Layers", "Each layer works even if the one above fails")
layers = [("Layer 1  Global planner (1 Hz)", "NavFn on Hector's map + live scan; inflation 0.45 m keeps paths off walls; replans around new obstacles"),
          ("Layer 2  Local controller (8 Hz)", "3 × 3 m costmap from the latest scan (raytrace clears, marks to 3.5 m); RPP stops if its arc collides within 1.5 s"),
          ("Layer 3  Motor node (20 Hz)", "independent of Nav2: refuses or stops motion toward anything closer than 0.25 m in ±25° of travel; stops 0.5 s after the last command")]
for i, (t, b) in enumerate(layers):
    y = 1.35 + i * 1.12
    box(s, 0.55, y, 5.6, 0.92, fill=TINT)
    text(s, 0.7, y + 0.02, 5.35, 0.9, [[(t, {"bold": True, "size": 14})], b], size=11, color=BLUE, space=1)
    if i < 2:
        arrow(s, 3.35, y + 0.93, 3.35, y + 1.11)
box(s, 0.55, 4.75, 5.6, 0.95, fill=RTINT)
text(s, 0.7, 4.75, 5.35, 0.95, ["Blind spots: one plane at 12 cm. Stairs, cables, chair-leg crossbars and table tops are invisible "
                                "to all three layers."], size=12, color=RED, bold=True, anchor=MSO_ANCHOR.MIDDLE, space=0)
text(s, 6.45, 1.35, 3.0, 0.4, ["Operator override"], size=16, bold=True, color=BLUE, space=0)
text(s, 6.45, 1.8, 3.0, 3.9, [
    "Any drive key, button, Space or STOP sends pause first",
    "pause → explorer cancels the Nav2 goal, adapter is muted",
    "teleop cmd_vel then owns the motors",
    "Explore resumes from the same map",
    "One run: zero interventions"], size=12, color=INK, space=6)
takeaway(s, 5.85, "The last layer does not trust the first two.")
notes(s, "~45 s. Three layers: planner, controller, and the motor node, which checks the lidar itself and stops "
      "below 25 cm whatever Nav2 asks. The operator can always take over: any key pauses the explorer first.")

# 10 velocity adapter
s = add("From m/s to Track Commands", "cmd_vel_adapter and the kinematic calibration")
eq(s, 0.55, 1.35, 4.6, 1.6, ["f = v / v_max         t = ω b / (2 v_max)",
                             "ℓ = f − t          r = f + t",
                             [("v_max = 0.153 m/s · b = 0.105 m (effective) · |ℓ|, |r| ≥ 0.12 if ≠ 0", {"size": 11, "color": GREY})]], size=15)
text(s, 0.55, 3.1, 4.6, 2.6, [
    "robot_node takes fractions −1…1 of max speed, not m/s",
    "tracks do not move below ≈ 0.1 of max: each non-zero track raised to 0.12",
    "both scaled down together if one saturates: curvature kept",
    "muted until Explore, and on pause/stop"], size=12, color=GREY, space=5)
table(s, 5.4, 1.35, 4.05, [
    ["Command", "Measured", "Model"],
    ["fwd 0.15, 2 s", "0.017 m/s", "0.023 (ramp)"],
    ["fwd 0.30, 2 s", "0.047 m/s", "0.046 m/s"],
    ["fwd 0.60, 2 s", "0.091 m/s", "0.092 m/s"],
    ["turn 0.10", "0.05 rad/s", "deadband"],
    ["turn 0.25, 1.5 s", "43° (scan)", "47° (encoders)"],
    ["turn 0.40, 1.5 s", "82° (scan)", "85° (encoders)"],
], [1.45, 1.3, 1.3], size=11, row_h=0.42)
text(s, 5.4, 4.4, 4.05, 1.3, ["Linear: encoders; rotation: lidar scan alignment. Scan / encoder yaw = 0.954 → b = 0.10 / 0.954 = 0.105 m, "
                              "far below the 0.17 m between track centres: tracks skid when turning in place."],
     size=11, italic=True, color=GREY, space=0)
takeaway(s, 5.85, "A two-line adapter, but every constant in it was measured on the floor.")
notes(s, "~45 s. Nav2 speaks metres per second; the motor node speaks fractions. The adapter converts, compensates "
      "the deadband, and keeps the curvature when one track saturates. Speeds measured on carpet match the model.")

# 11 explorer algorithm
s = add("Where to Go Next: The Frontier Search", "explorer.py + frontiers.py, every 3 s on the Pi")
steps = ["Classify: free p ≤ 25, occupied p ≥ 65, unknown −1; crop to the known area",
         "Clearance c = EDT(¬occupied) · res;  traversable = free ∧ c ≥ 0.15 m",
         "Dijkstra (8-connected) from the robot's cell → geodesic distance d",
         "Frontier = free cell with an unknown 4-neighbour; 8-connected clusters ≥ 0.30 m",
         "Goal of a cluster: reachable cell within 0.35 m, nearest its centroid",
         "Score = d − 0.5 · min(L, 1.5 m);  lowest wins"]
for i, t in enumerate(steps):
    y = 1.32 + i * 0.62
    circle_num(s, 0.55, y + 0.06, 0.42, str(i + 1))
    text(s, 1.07, y, 4.3, 0.6, [t], size=11.5, anchor=MSO_ANCHOR.MIDDLE, space=0)
table(s, 5.6, 1.35, 3.85, [
    ["Search on the Pi", ""],
    ["mean / max", "%s / %s ms" % (fmt(R.get("search_ms_mean"), 0), fmt(R.get("search_ms_max"), 0))],
    ["candidates per search", fmt(R.get("candidates_mean"), 1)],
    ["map cells searched", "known area + 20 cells"],
], [2.05, 1.8], size=11, row_h=0.42)
box(s, 5.6, 3.25, 3.85, 1.85, fill=RTINT)
text(s, 5.7, 3.28, 3.65, 1.8, [[("Why the cap on L: ", {"bold": True, "color": RED})],
                               "the ragged edge of a long scan merged into one 38.9 m \"frontier\"; uncapped, its bonus "
                               "outweighed every distance and the robot chased it."], size=12, space=3)
takeaway(s, 5.85, "Nearest-frontier greedy (Yamauchi 1997) with a capped size bonus.")
notes(s, "~60 s. The search: classify cells, distance transform for clearance, Dijkstra for the real path distance, "
      "frontier clusters, a goal on the reachable side of each, then the score. The size bonus is capped: on the first "
      "run one 39 metre ragged edge dominated everything.")

# 12 explorer state machine
s = add("Goals, Failures and Going Home", "The explorer's state machine")
states = [("idle", 0.55), ("exploring", 2.45), ("returning", 4.35), ("done", 6.25)]
for name, x in states:
    box(s, x, 1.4, 1.5, 0.6, fill=BLUE)
    text(s, x, 1.4, 1.5, 0.6, [name], size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
for (n1, x1), (n2, x2), lbl in zip(states, states[1:], ("Explore", "no frontier ×3", "start reached")):
    arrow(s, x1 + 1.52, 1.7, x2 - 0.02, 1.7)
    text(s, x1 + 1.3, 2.02, 0.85, 0.3, [lbl], size=9, italic=True, color=GREY, align=PP_ALIGN.CENTER, space=0)
box(s, 8.0, 1.4, 1.45, 0.6, fill=RTINT)
text(s, 8.0, 1.4, 1.45, 0.6, ["paused"], size=13, bold=True, color=RED, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space=0)
text(s, 7.85, 2.02, 1.75, 0.3, ["from any, by the operator"], size=9, italic=True, color=GREY, align=PP_ALIGN.CENTER, space=0)
table(s, 0.55, 2.5, 8.9, [
    ["A goal ends when …", "Then", "In the run"],
    ["Nav2 reports success", "blacklist goal + its frontier (pockets under furniture never clear)", "%d" % R.get("frontiers_reached", 0)],
    ["its frontier is seen on the way (no frontier within 0.6 m of it)", "cancel, take the next", "%d" % R.get("frontiers_seen_on_the_way", 0)],
    ["Nav2 aborts, or < 0.15 m / 0.5 rad progress in 30 s", "blacklist (0.4 m radius)", "0"],
    ["timeout 40 s + 2.5 · d / 0.05 m/s", "blacklist", "%d" % R.get("goals_failed", 0)],
    ["battery < 7.0 V or 45 min", "return home", "–"],
], [4.0, 3.7, 1.2], size=11, row_h=0.45)
text(s, 0.55, 5.3, 8.9, 0.45, ["Every event and a 5 s sample (area, frontiers, battery) → ~/explore_logs/<time>.jsonl; the results slides are computed from it."],
     size=11, italic=True, color=GREY)
takeaway(s, 5.85, "Without blacklisting reached goals, the robot re-sent one goal 39 times in two minutes.")
notes(s, "~45 s. Goals end four ways. Reached goals are blacklisted too, because a frontier that is still there when "
      "you stand next to it is a pocket the lidar can't see into. When three searches find nothing, the robot drives home "
      "and saves the map. Everything is logged.")

# 13 simulation
s = add("Checking the Explorer Before the Robot", "tools/sim_explore.py: synthetic apartment, ray-cast lidar")
fit_picture(s, os.path.join(FIG, "sim_explore.png"), 0.45, 1.3, 9.1, 3.2)
stat(s, 0.55, 4.55, 2.1, 1.2, "%d %%" % round(100 * SIM["coverage"]), "of %.0f m² free space mapped" % SIM["free_area_m2"])
stat(s, 2.8, 4.55, 2.1, 1.2, "%.1f m" % SIM["distance_m"], "driven")
stat(s, 5.05, 4.55, 2.1, 1.2, "%d" % SIM["goals"], "frontier goals")
stat(s, 7.3, 4.55, 2.15, 1.2, "%.0f ms" % SIM["mean_search_ms"], "per search (laptop)")
takeaway(s, 5.85, "No SLAM error, no controller: tests goal choice and termination only.")
notes(s, "~30 s. Before the robot, the explorer ran on a synthetic 10 by 7 metre apartment with a ray-cast lidar. "
      "It mapped all free space in 22 metres. This checks the goal choice and the stopping rule, not SLAM or control.")

# 14 distributed + middleware
s = add("Distributing the Load: Measured, Not Assumed", "CPU on the Pi 5 while exploring · network · middleware")
table(s, 0.55, 1.35, 4.3, [
    ["Process (Pi 5)", "% of a core"],
    ["aurora930 camera driver", "26"], ["explorer (Python)", "21"], ["robot_node (Python)", "17"],
    ["camera_bridge (JPEG)", "9"], ["bt_navigator", "9"], ["planner_server", "7"], ["controller_server", "6"],
    ["ms200_node", "5"], ["behaviour, smoother, lifecycle", "11"], ["hector_mapping", "3"],
    ["total (of 400), 52 °C, no throttle", "≈ 150"],
], [3.1, 1.2], size=10, row_h=0.32)
text(s, 5.1, 1.35, 4.35, 0.4, ["Placement"], size=16, bold=True, color=BLUE, space=0)
text(s, 5.1, 1.75, 4.35, 1.6, [
    "Scan over Wi-Fi: ≈ 2 KB × 10 Hz = 20 KB/s, +6 ms latency",
    "Control loop on board: a drop > 0.5 s would otherwise stop the robot (cmd_vel timeout)",
    "Movable to the PC if needed: explorer + global planner (not time-critical)"], size=11, color=INK, space=4)
text(s, 5.1, 3.45, 4.35, 0.4, ["Middleware"], size=16, bold=True, color=BLUE, space=0)
text(s, 5.1, 3.85, 4.35, 1.9, [
    "PC Cyclone, robot Fast DDS → camera frames lost after driver restart (shared memory), explorer state garbled on the PC",
    "Fix: Cyclone on both (service drop-in rmw.conf)",
    "Humble ↔ Jazzy NavigateToPose differ: action stays on the Pi"], size=11, color=INK, space=4)
takeaway(s, 5.85, "The Pi has headroom: the 0.1 m/s tracks, not the CPU, set the pace.")
notes(s, "~45 s. I measured before moving anything: about one and a half cores of four. The camera is the biggest "
      "load. Mixing DDS vendors caused two unrelated bugs; using Cyclone everywhere fixed both.")

# 15 calibration
s = add("The Bug the Wheels Could Not See", "Inverted motor signs, found with the lidar only")
text(s, 0.55, 1.3, 8.9, 0.6, ["Commanded left turn, 20 s: encoder odometry +383°, Hector −678°. Mirrored lidar, or a robot turning "
                              "the wrong way?"], size=14, space=0)
eq(s, 0.55, 1.95, 4.4, 1.35, ["k* = argmin_k median_i | A_i − B_{i+k} |",
                              "Δψ = 0.8° · k*",
                              [("A, B: range vectors (450 rays) before/after; valid rays only", {"size": 10, "color": GREY})]], size=14)
table(s, 5.15, 1.95, 4.3, [
    ["Command (1.5 s)", "Scan", "Encoders"],
    ["before: turn +0.25", "−51.2°", "+28.5°"],
    ["before: turn −0.25", "+44.8°", "−28.8°"],
    ["after: turn +0.25", "+43.2°", "+46.8°"],
    ["after: turn −0.25", "−47.2°", "−50.3°"],
    ["after: turn +0.40", "+81.6°", "+85.3°"],
    ["after: turn −0.40", "−86.4°", "−88.5°"],
], [1.9, 1.2, 1.2], size=11, row_h=0.33)
box(s, 0.55, 4.45, 8.9, 1.25, fill=TINT)
text(s, 0.75, 4.47, 8.5, 1.2, [[("Diagnosis: ", {"bold": True, "color": BLUE}),
                                ("both motor signs inverted since set-up: \"forward\" drove toward the rear (range ahead grew 0.37 m), "
                                 "\"left\" turned right. The odometry used the same signs, so it always agreed with the command. ", {}),
                                ("Fix: ", {"bold": True, "color": BLUE}),
                                ("left_sign −1, right_sign +1, track width 0.105 m; confirmed by camera frames.", {})]],
     size=12, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "Check motion with a sensor that does not share the motors' conventions.")
notes(s, "~60 s. The key finding. The wheels and SLAM disagreed in sign. Aligning two scans by circular shift gives "
      "the true rotation without trusting either; the lidar's angle convention had been checked with the camera. "
      "Both motor signs were inverted, and the odometry, using the same signs, could never notice.")

# 16 bring-up timeline
s = add("Bring-Up: Seven Faults Before a Clean Map", "Symptom, cause and fix, in the order they were found")
table(s, 0.55, 1.35, 8.9, [
    ["Symptom", "Cause", "Fix"],
    ["camera black after a driver restart", "Fast DDS shared memory: old subscriber never rematched", "Cyclone DDS on the robot"],
    ["explorer \"waiting for Nav2\"", "relative action name in /robot04 namespace", "/navigate_to_pose"],
    ["explorer crashed on first failure", "keyword clash in the event logger", "rename + guarded callbacks + respawn"],
    ["goals aborted: \"unable to transform\"", "Hector TF stamped with scan time (0.1–0.2 s old)", "transform tolerance 1.0 s"],
    ["controller at 5–6 Hz", "local costmap 5 Hz < controller 8 Hz", "local costmap 10 Hz"],
    ["walls drawn twice, map smeared", "both motor signs inverted, track width 0.17", "signs −1/+1, b = 0.105 m"],
    ["one goal sent 39 times", "reached frontier that never clears", "blacklist reached goals"],
], [2.7, 3.45, 2.75], size=10.5, row_h=0.52)
takeaway(s, 5.85, "None of the seven was in an algorithm; all were at an interface.")
notes(s, "~45 s. Seven faults, in order. Middleware, namespaces, a logger bug, timestamps, rates, motor signs and "
      "frontier pockets. None was in Hector, Nav2 or the frontier idea; all were at the joins.")

# 17 operator app
s = add("Watching and Steering from the PC", "robot04 mapper (PyQt5, ROS 2 Humble)")
fit_picture(s, os.path.join(FIG, "mapper_app.png"), 0.45, 1.25, 9.1, 3.95)
text(s, 0.55, 5.22, 8.9, 0.55, ["Left: camera (10 fps JPEG) and hold-to-drive teleop. Right: live map, SLAM path (blue), Nav2 plan (green), "
                                "goal (magenta), frontiers (cyan), start (yellow); Explore / Pause / Return home; save as map_server pgm + yaml."],
     size=10.5, italic=True, color=GREY, space=0)
takeaway(s, 5.85, "The app never commands the robot while it explores, unless the operator takes over.")
notes(s, "~30 s. The operator app at the end of the run: camera on the left, the map and the robot's path on the "
      "right, the explorer's state below. It starts the stack over ssh and can pause, take over or send the robot home.")

# 18 results map
s = add("The Result: The Home, Mapped Unattended", "One autonomous run, robot04 on its own")
mapfig = os.path.join(FIG, "run_map.png")
if os.path.exists(mapfig):
    fit_picture(s, mapfig, 0.45, 1.25, 5.1, 4.5)
cards = [("%s m²" % fmt(R.get("explored_m2_final"), 0), "mapped"),
         ("%s min" % fmt(R.get("duration_min"), 1), "unattended"),
         ("%s m" % fmt(R.get("path_length_m"), 0), "driven"),
         ("%d / %d" % (R.get("frontiers_reached", 0) + R.get("frontiers_seen_on_the_way", 0), R.get("goals_sent", 0)),
          "goals done / sent; %d failed" % R.get("goals_failed", 0))]
for i, (big, small) in enumerate(cards):
    stat(s, 5.75 + (i % 2) * 1.88, 1.35 + (i // 2) * 1.5, 1.75, 1.35, big, small)
box(s, 5.75, 4.4, 3.65, 1.3, fill=RTINT)
text(s, 5.85, 4.42, 3.45, 1.26, [R.get("end_note", "")], size=12, color=RED, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, R.get("takeaway", ""))
notes(s, R.get("notes_map", ""))

# 19 results numbers
s = add("The Run in Numbers", "From the explorer's log and the saved map")
prog = os.path.join(FIG, "run_progress.png")
if os.path.exists(prog):
    fit_picture(s, prog, 0.45, 1.25, 5.3, 2.3)
mean_v = R["path_length_m"] / (60 * R["duration_min"])
table(s, 5.95, 1.35, 3.5, [
    ["Metric", "Value"],
    ["duration", "%s min" % fmt(R["duration_min"], 1)],
    ["mapped (known cells)", "%s m²" % fmt(R["explored_m2_final"], 1)],
    ["free / occupied", "%s / %s m²" % (fmt(R["map_free_m2"], 1), fmt(R["map_occupied_m2"], 1))],
    ["map extent", "%s × %s m" % (fmt(R["map_size_m"][0], 1), fmt(R["map_size_m"][1], 1))],
    ["path (SLAM, 5 cm steps)", "%s m" % fmt(R["path_length_m"], 1)],
    ["mean speed", "%s m/s" % fmt(mean_v, 3)],
    ["mapping rate", "%s m²/min" % fmt(R.get("area_rate_m2_per_min"), 1)],
    ["goals sent / failed", "%d / %d" % (R["goals_sent"], R["goals_failed"])],
    ["search mean / max", "%s / %s ms" % (fmt(R["search_ms_mean"], 0), fmt(R["search_ms_max"], 0))],
    ["battery", "%s → %s V" % (fmt(R["battery_v"][0], 2), fmt(R["battery_v"][1], 2))],
    ["interventions", "%d" % R["operator_pauses"]],
], [1.9, 1.6], size=10, row_h=0.34)
text(s, 0.55, 3.65, 5.2, 2.1, [
    "Area: fast for 2 min (each goal opens a room to a 360° lidar), then corners one at a time",
    "Open frontiers peak ≈ 4.5 min, zero at 11.6 min → drive home",
    "Mean speed ≈ cruise 0.10 m/s: time spent driving, not recovering",
    "1 failure: goal behind a wall, reachable only through unknown space; dropped at its 156 s timeout"],
    size=11, color=INK, space=4)
takeaway(s, 5.85, "Greedy exploration's usual shape: quick coverage, then a long tail of corners.")
notes(s, R.get("notes_progress", ""))

# 20 lessons
s = add("What Bringing It Up Taught Us", "Lessons & limitations")
lessons = [("Conventions", "Odometry agreed with wrong motor signs; only the lidar disagreed"),
           ("Rates", "Controller faster than its costmap → it waits; looked like CPU load"),
           ("Time stamps", "SLAM pose carries the scan time: raise TF tolerance"),
           ("Namespaces", "Explorer looked for /robot04/navigate_to_pose; Nav2 was at /"),
           ("Pockets", "Reached frontiers that never clear (under furniture) → blacklist"),
           ("Middleware", "Same DDS on every machine fixed two unrelated faults")]
for i, (t, b) in enumerate(lessons):
    x = 0.55 + (i % 2) * 4.5
    y = 1.35 + (i // 2) * 1.1
    box(s, x, y, 4.35, 0.95, fill=TINT)
    text(s, x + 0.1, y + 0.03, 4.15, 0.9, [[(t + ": ", {"bold": True, "color": BLUE}), (b, {})]], size=13,
         anchor=MSO_ANCHOR.MIDDLE, space=0)
box(s, 0.55, 4.7, 8.9, 1.0, fill=RTINT)
text(s, 0.75, 4.72, 8.5, 0.96, [[("Limits: ", {"bold": True, "color": RED}),
                                 ("a 2D lidar at 12 cm cannot see stairs, cables or table tops; Hector has no loop closure. "
                                  "Next: depth-camera cliff and 3D obstacle check, information-gain frontiers.", {})]],
     size=13, anchor=MSO_ANCHOR.MIDDLE, space=0)
takeaway(s, 5.85, "The algorithms worked as published; the time went into the interfaces.")
notes(s, "~45 s. None of the problems were in the algorithms. They were in conventions, rates, timestamps, names "
      "and middleware. Limits: the lidar sees one plane, so stairs and cables are invisible to it.")

# 21 remember
s = add("What to Remember", "Summary")
box(s, 0.55, 1.35, 8.9, 1.5, fill=BLUE)
text(s, 0.85, 1.35, 8.3, 1.5, ["A low-cost robot maps a home by itself with standard ROS 2 parts, provided each part is "
                               "configured for the next and the motion is checked against the lidar."],
     size=21, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, space=0)
for i, (t, b) in enumerate([("On board", "SLAM, Nav2 and the explorer on a Pi 5; the PC only watches"),
                            ("Safe by layers", "planner, controller, and a motor node that refuses to hit things"),
                            ("Reproducible", "code, configuration, run logs and this analysis on GitHub")]):
    x = 0.55 + i * 3.05
    box(s, x, 3.15, 2.8, 2.0, fill=TINT)
    circle_num(s, x + 0.2, 3.35, 0.5, str(i + 1))
    text(s, x + 0.8, 3.35, 1.95, 0.5, [t], size=17, bold=True, color=BLUE, anchor=MSO_ANCHOR.MIDDLE, space=0)
    text(s, x + 0.2, 3.95, 2.45, 1.15, [b], size=13, space=0)
text(s, 0.55, 5.4, 8.9, 0.6, ["Thank you! Questions?"], size=26, bold=True, color=RED, align=PP_ALIGN.CENTER)
text(s, 0.55, 6.0, 8.9, 0.4, ["github.com/hmarthens1/rpi5-robot-board · ros2/mentorpi_nav · pc/robot04-mapper"],
     size=11, color=GREY, align=PP_ALIGN.CENTER)
notes(s, "~30 s. Three things: everything runs on the robot, obstacle avoidance is layered down to the motor node, "
      "and it is all on GitHub with the run logs. Thank you.")

# drop the seminar's own content slides (keep its title slide, now rewritten)
for old in orig[1:]:
    drop_slide(prs, old)
prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
