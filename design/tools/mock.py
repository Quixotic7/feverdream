#!/usr/bin/env python3
"""Feverdream mock-ups: the screens in docs/DESIGN.md and the Move Designer board.

    python3 design/tools/mock.py

writes docs/img/*.png (each 128 x 64 screen, four times size), docs/img/sheet.png (all of them) and
design/feverdream.movedesign.json (open it in Ableton Move Designer). Needs Pillow.

The screens are drawn in screens.py (with gfx.py), by hand, to show the screen rules. They are not the instrument's
renderer. This file is the board: the control layouts, their lights and their notes.
"""
import base64
import json
import os

from PIL import Image

from gfx import H, ROOT, W
from screens import ANIM, SCREENS

# Shift + step 1..16: a short label for the board's controls; the three whose printed icon is not in the Move manual
SHIFT = ["PRJ", "SET", "WRK", "TRK", "BPM", "MET", "GRV", "LAY", "KEY", "VEL", "ARP", "BNC", "TLS", "NEW", "DBL", "QNT"]
NEW_STEPS = (3, 11, 12)

# ------------------------------------------------------------------ the board
TRACK = ["#ff6a1a", "#ffb000", "#f5e400", "#b4f000", "#00e0b0", "#33c8ff", "#7a7cff", "#c060ff"]
WHITE, GREEN, RED, PINK, BLUE, AMBER, GREY = "#ffffff", "#00e050", "#ff2020", "#ff40a0", "#2060ff", "#ff9000", "#4a4a4a"
SCOPE = (["screen"] + ["knob-%d" % i for i in range(1, 9)] + ["knobled-%d" % i for i in range(1, 9)]
         + ["volume", "wheel", "back", "menu"] + ["track-%d" % i for i in range(1, 5)]
         + ["pad-%d-%d" % (r, c) for r in range(1, 5) for c in range(1, 9)]
         + ["capture", "sample", "loop", "mute", "delete", "copy", "undo", "shift", "play", "record"]
         + ["step-%d" % i for i in range(1, 17)]
         + ["stepicon-%d" % i for i in range(1, 17)]
         + ["left", "right", "up", "down", "power"])
SHIFT_NAMES = ["Projects", "Setup", "Workflow Settings", "Track Setup (new)", "Tempo", "Metronome", "Groove",
               "Pad layout (incl. Perform)", "Keys & Scales", "Full Velocity", "Repeat / Arp", "Mixer (new)", "Tools (new)",
               "New Clip", "Double Loop", "Quantize"]
OFF = "off"          # put(..., OFF): an RGB light switched off (None leaves it as it was)
_n = [0]


def uid():
    _n[0] += 1
    return "fd%010d" % _n[0]


def dim(c, k=0.25):
    return "#%02x%02x%02x" % tuple(int(int(c[i:i + 2], 16) * k) for i in (1, 3, 5))


def put(ctl, cid, led=None, **meta):
    e = ctl.setdefault(cid, {})
    if meta:
        e.setdefault("meta", {}).update(meta)
    if led == OFF:
        e["led"] = {"color": None}
    elif led is not None:
        e["led"] = {"color": led} if isinstance(led, str) else {"brightness": led}


def base_note(trk=2, steps="n...n..%n.k.c.n.", playstep=6):
    """Note Mode, bank A, a synth track selected: the controls every Note Mode layout starts from."""
    c = {}
    col = TRACK[trk]
    for i in range(4):
        put(c, "track-%d" % (i + 1), WHITE if i == trk else TRACK[i], label="Track %d" % (i + 1),
            function="Track %d (bank A). Its colour; white when selected; dim when muted; blue when soloed." % (i + 1),
            click="Select the track [M]. Already selected: at the chain, the next view (Chain, Scene, Scope, "
            "Scope 8, Tracks); inside a device, the map row (MOD, MACRO, off) [New]",
            hold="View it while held [M]. + Volume: its level [M]. + wheel: pan. "
            "+ encoders 1-4: Send A, Send B, drive, width",
            shift="Track %d: the same row in bank B, and the buttons switch to bank B [New]" % (i + 5),
            description="Mute + button: mute [M]. Shift + Mute + button: solo [M]. Copy / Delete + button: the track.")
    for r in range(1, 5):
        for k in range(1, 9):
            root = k in (1, 8)
            put(c, "pad-%d-%d" % (r, k), col if root else GREY,
                function="A note in the scale: In-Key, C major, a row an octave [M, 9.1]. Root notes in the track's "
                "colour.", click="Play the note; then a step button puts it on that step [M]",
                hold="With a step held: add or remove this note on the step [M]")
    for i, ch in enumerate(steps):
        led = GREEN if i == playstep else WHITE if ch in "ntLc%" else col if ch == "k" else dim(col)
        put(c, "step-%d" % (i + 1), led, label=str(i + 1),
            function="Step %d of the page shown. White: notes. Dim track colour: empty. Bright track colour: locks "
            "with no note. Green: the playhead [M + locks]." % (i + 1),
            click="Add the held pads' notes, or clear the step [M]",
            hold="The step card; Volume velocity, wheel length, Plus / Minus pitch, arrows nudge, encoders lock [M]. "
            "A later step: stretch the notes to it [RemoteFM1]. Wheel press: the TRIG page for this step [New]",
            shift=SHIFT_NAMES[i])
    for i in range(1, 17):
        put(c, "stepicon-%d" % i, 0, description="Dark: the step above is a step, a track, a page or a length "
            "(the owner's rule R6). Lit only when the step is a function.")
    names = ["Cutoff", "Bite", "Attack", "Release", "Drive", "Echo", "Space", "Level"]
    for i in range(8):
        put(c, "knob-%d" % (i + 1), label=names[i], function="At the chain: macro %d of the bank shown, a knob of "
            "the track's own that turns one or more parameters in its chain. Inside a device: value %d of its page "
            "[M]" % (i + 1, i + 1), turn="Change it; the value takes the screen, large",
            touch="Show the page: the macros, or the device's parameters [M]",
            shiftTurn="Fine steps [M]", hold="With a step held: lock this value on the step [M]. Record on: write "
            "automation [M]. Mute + touch: automation off / on [M]. Delete + touch: delete it [M]. Inside a "
            "device, touched + wheel press: the parameter's options (Map to Macro, Delete Automation, Reset)")
        put(c, "knobled-%d" % (i + 1), dim(WHITE, 0.4), description="Lit: the knob has a job (rule R4). Red: "
            "automated. Off: dead.")
    put(c, "knobled-5", RED, description="Red: this parameter has automation in the clip [M]")
    put(c, "volume", label="Volume", turn="Master level [M]", hold="Step held: velocity [M]. Track button held: track "
        "level [M]. Pad held: sample gain [M]")
    put(c, "wheel", label="Wheel", turn="At the chain: along the devices (MACROS, PADS, SEQ, MIDI effects, the "
        "instrument, audio effects, MIX) [M]. Inside a device: its parameter pages",
        click="At the chain: enter the device [New; Move opens the browser]; on a +: browse devices to add; on the "
        "rack's name at the front: its sheet (Load, Save, Save As, Init, Revert). Inside a device: on its front "
        "item, the same sheet for the device; on a page, the list of its pages", shift="The device's options: Replace, Bypass, Move, Copy, "
        "Delete, Save Preset [M]",
        shiftTurn="At the chain: move the device along its zone [New]", touch="Where you are, in large words: track, device, page. Speech on Jog: the touch says the screen as it is, then "
        "every word while the finger stays; let go: silent [RemoteFM1]",
        hold="Step held + turn: note length [M]; + press: TRIG page [New]. Mute + press: bypass [M]. Delete + "
        "press: remove. Copy + press: copy the device")
    put(c, "back", 0.4, label="Back", click="Up one level: out of a device to the chain [M]",
        hold="Home of this mode [M]")
    put(c, "menu", 0.4, label="Note / Session", click="Session Mode, on release [M]", hold="Left-hand Shift: all of "
        "Shift's meanings while held, for playing in the lap [New; Move previews the other mode here]",
        shift="")
    put(c, "play", GREEN, label="Play", click="Start / stop [M]", shift="Retrigger [M]")
    put(c, "record", dim(RED, 0.3), label="Record", click="Record notes and automation, after the count-in [M]")
    put(c, "capture", 0.4, label="Capture", click="Keep what was just played [M]; on a generator: write its notes "
        "into the clip [New]", shift="Clear what Capture holds [M]")
    put(c, "sample", 0.4, label="Sampling", click="Sampling Mode [M]", shift="Grab: the last bars played, onto a pad "
        "[New]")
    put(c, "loop", 0.4, label="Loop", click="Loop Mode: the steps are the clip's pages [M]",
        hold="+ wheel: length by a page [M]; + Shift + wheel: by a step")
    put(c, "mute", 0.4, label="Mute", click="Mute the selected track [M]", hold="Hint card. + track: mute [M]. "
        "+ pad: mute a kit pad [M]. + encoder: automation off / on [M]. + wheel press: bypass. + step: mute it [New]")
    put(c, "delete", 0.4, label="Delete", click="Nothing: a modifier only [RemoteFM1; Move deletes the clip]",
        hold="Its mark (scissors) at the press. + a step with notes: cut, crossed. + an empty step: the clipboard "
        "pasted. + any step right after a cut: pasted over it. + pad: that note out of the clip [M]. + encoder: its "
        "automation [M]. + Play: the clip cleared. + wheel press: the device. + track button: the track cleared",
        description="One clipboard with Copy; a paste never empties it. Back clears the marks.")
    put(c, "copy", 0.4, label="Copy", click="Nothing: a modifier only [RemoteFM1; Move duplicates the clip]",
        hold="Its mark (two sheets) at the press. + a step with notes: copied, dashed; several: a group. + an empty "
        "step: pasted. Let go after copying, then a step: pasted once [M]. + wheel press: the device. + track "
        "button: the track", description="Copy never overwrites a full step.")
    put(c, "undo", 0.4, label="Undo", click="Undo; a toast names what [M]", shift="Redo [M]",
        hold="The list of recent actions; the wheel picks how far back [Melodee]")
    put(c, "shift", 0.4, label="Shift", hold="The Shift map on the screen; printed icons light [M]; track buttons "
        "show bank B")
    put(c, "left", 0.4, label="Left", click="Previous page [M]", hold="Step held: nudge [M]", shift="First page")
    put(c, "right", 0.4, label="Right", click="Next page; past the last: a new page [M]", hold="Step held: nudge [M]",
        shift="Last page")
    put(c, "up", 0.4, label="Plus", click="Octave up [M]", hold="Step held: transpose [M]", shift="A scale degree up")
    put(c, "down", 0.4, label="Minus", click="Octave down [M]", hold="Step held: transpose [M]",
        shift="A scale degree down")
    put(c, "power", label="Power", click="A menu: Cancel, Exit to Move, Power off")
    put(c, "screen", function="At rest a picture and one large line; a touched knob or wheel takes the whole "
        "screen and says what it is, large. No small text.")
    return c


def lay_note():
    return base_note(), "Note Mode: Device View", (
        "Home. Track 3 (a synth) of bank A. Everything here is Move's Note Mode [8, 9] with a longer device row. "
        "[M] marks what is unchanged from Move.")


def lay_step():
    c = base_note(playstep=None)
    put(c, "step-5", WHITE, label="held")
    for i in (6, 7):
        put(c, "step-%d" % i, RED, description="Red while an encoder is touched: the range the lock covers [M]")
    notes = {(4, 1), (4, 3), (4, 5)}
    for (r, k) in notes:
        put(c, "pad-%d-%d" % (r, k), WHITE, description="White: a note on the held step [M, 11.9]")
    for i in range(1, 9):
        put(c, "knobled-%d" % i, AMBER if i not in (5, 6) else RED,
            description="Amber: can be locked. Red: locked on this step.")
    put(c, "wheel", description="Turn: note length. Press: the encoders become the TRIG page (micro, ratchet, "
        "chance, condition, function, amount, length, slide; RemoteFM1's order) until the step is let go.")
    return c, "Note Mode: a step held", (
        "Step 5 held. Move's gestures all work [11]; the screen shows the step card. Pads show the step's notes in "
        "white. Encoders lock the selected device's values on this step (Move's per-step automation [14.2.4]).")


def lay_shift():
    c = base_note()
    for i in range(1, 17):
        put(c, "stepicon-%d" % i, 1.0, label=SHIFT_NAMES[i - 1],
            description="Lit: with Shift held the step above is a function (rule R6).")
    for i in range(16):
        put(c, "step-%d" % (i + 1), label=SHIFT[i],
            click=SHIFT_NAMES[i], function="Shift + Step %d: %s" % (i + 1, SHIFT_NAMES[i]),
            description="Its icon is printed on the unit (%s) and lights on CC %d, but is not in the Move manual "
            "(Move Designer 4 and later draws it). Feverdream's own entry, chosen to match the picture."
            % ({3: "a cylinder", 11: "layers merging", 12: "a star"}.get(i), 16 + i) if i in NEW_STEPS else
            "Printed icon, meaning as on Move.")
    for i in range(4):
        put(c, "track-%d" % (i + 1), dim(TRACK[i + 4], 0.6), label="Track %d" % (i + 5),
            click="Select track %d and switch to bank B" % (i + 5))
    put(c, "shift", 1.0)
    put(c, "menu", 1.0, description="Held: the same Shift, under the left thumb. Use it when the target is under "
        "the right hand (encoders, pads, steps); use Shift when the target is under the left (wheel, Play, Back).")
    return c, "Shift held (or Note/Session held)", (
        "Two Shifts: Shift at the bottom right, and Note/Session held under the left thumb, so no combination needs "
        "the unit put down. All 16 printed icons light (CC 16-31), as on Move; icons 4, 12 and 13 need Move "
        "Designer's document version 4 to be drawn. The steps themselves do not change. The screen "
        "names all sixteen. The track buttons show bank B.")


def lay_loop():
    c = base_note()
    col = TRACK[2]
    for i in range(16):
        led = WHITE if i == 1 else GREEN if i == 2 else col if i < 4 else dim(GREY, 0.5)
        put(c, "step-%d" % (i + 1), led, label="P%d" % (i + 1),
            function="Page %d. White: shown. Track colour: in the loop. Dim: outside. Green: playing [M]." % (i + 1),
            click="Show the page [M]", doubleClick="Loop this page alone [M]",
            hold="+ another page: the loop from one to the other [M]. + wheel / Volume / Plus / Minus / arrows: "
            "length, velocity, pitch, nudge of all its notes [M]")
    last = 5                                             # the last page ends after 5 steps
    for r in range(1, 5):
        for k in range(1, 9):
            n = (r - 3) * 8 + k                          # rows 3 and 4: steps 1-8 and 9-16 of the last page
            if r == 2:
                sp = ["1/16X", "1/8X", "1/4X", "1/2X", "3/4X", "1X", "3/2X", "2X"][k - 1]
                put(c, "pad-%d-%d" % (r, k), WHITE if sp == "1X" else BLUE, label=sp,
                    function="The clip's speed [New, the owner's]. Blue; the current one white. 1X is a 16th note "
                    "a step, 2X a 32nd, 1/16X a bar.", click="Set the speed to %s" % sp, hold="")
            elif r == 1 and k >= 7:
                fl = ["Straight", "Triplet"][k - 7]
                put(c, "pad-%d-%d" % (r, k), WHITE if k == 7 else BLUE, label=fl,
                    function="The clip's feel [New, the owner's]. Blue; the current one white. Triplet uses three "
                    "steps of every four: the fourth of each group is dark and dead.",
                    click="Set the feel to %s" % fl.lower(), hold="")
            elif r < 3:
                put(c, "pad-%d-%d" % (r, k), OFF, label="", function="Dark and dead in Loop Mode (rule R3: the "
                    "layer uses some pads, so it takes them all).", click="", hold="")
            else:
                led = WHITE if n == last else col if n < last else dim(GREY, 0.5)
                put(c, "pad-%d-%d" % (r, k), led, label=str(n), function="The last page's length [RemoteFM1]. "
                    "Lit up to the length, the length itself white. No pad plays in Loop Mode.",
                    click="End the last page after %d step%s" % (n, "" if n == 1 else "s"), hold="")
    put(c, "loop", 1.0, click="Leave Loop Mode (it was latched by a quick click)",
        hold="Loop Mode while held; let go unused, it does not latch")
    put(c, "wheel", turn="The loop's length, a step a click [RemoteFM1; Move's wheel moves a bar]",
        shiftTurn="A page a click", click="", hold="", description="A page held + turn: the length of all its notes.")
    put(c, "left", click="The page shown, no wrap [M]", hold="", shift="")
    put(c, "right", click="The next page; past the last: a ghost page (+), real when its key is pressed [M]",
        hold="", shift="")
    put(c, "back", click="Leave Loop Mode", hold="+ Left: the first page. + Loop: the loop back to the whole clip")
    return c, "Loop Mode: pages", (
        "Loop, quick click: latched. The steps are the clip's pages, up to 16, as Move's bars [12.1] with "
        "RemoteFM1's page edit: the wheel is the length, and the two lower pad rows set where the last page ends. "
        "Here 4 pages, the last ending after 5 steps: 53 steps.")


def lay_keyboard():
    c = base_note()
    col = TRACK[2]
    white = ["C", "D", "E", "F", "G", "A", "B", "C"]
    black = [None, "C#", "D#", None, "F#", "G#", "A#", None]
    for pair, octave in ((0, 4), (1, 3)):                # rows 1-2: the upper octave; rows 3-4: the lower
        for k in range(8):
            b, w = black[k], white[k]
            oc = octave + (1 if k == 7 else 0)
            if b:
                put(c, "pad-%d-%d" % (pair * 2 + 1, k + 1), dim(WHITE, 0.25), label="%s%d" % (b, octave),
                    function="A black key. Dim; brighter when it is in the scale.", click="Play %s%d" % (b, octave))
            else:
                put(c, "pad-%d-%d" % (pair * 2 + 1, k + 1), OFF, label="", function="Not a key: dark and dead "
                    "(rule R1).", click="", hold="")
            put(c, "pad-%d-%d" % (pair * 2 + 2, k + 1), col if w == "C" else "#9a9a9a", label="%s%d" % (w, oc),
                function="A white key. Every C in the track colour; the others light grey, brighter in the scale.",
                click="Play %s%d" % (w, oc))
    put(c, "step-8", description="Shift + this step: the next pad layout (In Key, Chromatic, Keyboard, Chords, "
        "Progression, Perform).")
    put(c, "up", click="Both octaves up an octave [M]; the popup names the range and a white row sweeps the pads")
    put(c, "down", click="Both octaves down an octave [M]")
    return c, "Note Mode: Keyboard layout", (
        "Shift + Step 8 (Layout) on a melodic track: a piano. Two rows an octave, white keys below, black keys "
        "above and between them; two octaves, each starting on C at the left, whatever the key.")


def lay_map():
    c = base_note()
    ENV, LFO, OTHER = "#e8c000", "#00c8e0", "#7a7a7a"
    keys = [("ENV 1", ENV, 0.35), ("ENV 2", ENV, 0.35), ("ENV 3", ENV, 0.15), ("LFO 1", LFO, 1.0),
            ("LFO 2", LFO, 0.35), ("LFO 3", LFO, 0.15), ("VEL", OTHER, 0.6), ("PRES", OTHER, 0.3)]
    for k, (name, colr, lvl) in enumerate(keys):
        put(c, "pad-1-%d" % (k + 1), dim(colr, lvl), label=name,
            function="Map row, MOD side: the synth's source %s. Dim: at rest. Dimmer: moves nothing yet. Full: held."
            % name, click="Go to this source's own page",
            hold="+ an encoder turned: this source now moves that parameter, the turn its depth. + the wheel: the "
            "synth's pages. + Delete + an encoder touched: the routing removed",
            description="The selected track's button again: the MACRO side (the eight macros as keys), then off.")
    reach = {1: LFO, 2: AMBER, 3: AMBER, 4: OFF, 5: AMBER, 6: LFO, 7: AMBER, 8: AMBER}
    names = ["Cutoff", "Resonance", "Env amount", "Type", "Drive", "LFO amount", "Rate", "Mix"]
    for i in range(1, 9):
        put(c, "knob-%d" % i, label=names[i - 1], function="FILTER page, value %d. With a source key held: turning "
            "sets that source's depth on this parameter and leaves the parameter's own value alone." % i)
        put(c, "knobled-%d" % i, reach[i], description="While a source key is held: the source's colour where it "
            "already moves this parameter, amber where it could, dark where the parameter cannot be modulated.")
    put(c, "track-3", WHITE, description="Clicked again inside a device: the map row on (MOD), its MACRO side, off.")
    put(c, "wheel", description="With a source key held the wheel still turns the synth's pages, so one hold can "
        "put a source on parameters on several pages.")
    return c, "Inside a device: the map row", (
        "Inside the synth, on its FILTER page, with the map row on (MOD side). The top row of pads is the synth's "
        "sources; LFO 1 is held and the Cutoff encoder is turning, so LFO 1 now moves Cutoff by +40. The three "
        "rows under it still play. After Serum; EvilGenius on the Move maps the same way.")


def lay_progression():
    c = base_note()
    col = TRACK[2]
    white = [("C", "Cmaj7"), ("D", "Dm7"), ("E", "Em7"), ("F", "Fmaj7"), ("G", "G7"), ("A", "Am7"), ("B", "Bm7b5"),
             ("C", "Cmaj7")]
    black = [None, ("C#", "C#dim"), ("D#", "Ebmaj7"), None, ("F#", "D7/F#"), ("G#", "E7/G#"), ("A#", "Bb9"), None]
    for pair, octave in ((0, 4), (1, 3)):                # rows 1-2: the upper octave; rows 3-4: the lower
        for k in range(8):
            b, (w, wch) = black[k], white[k]
            oc = octave + (1 if k == 7 else 0)
            empty_black = b and pair == 0 and k in (2, 5)   # the upper octave uses fewer accents in this pack
            if b and not empty_black:
                put(c, "pad-%d-%d" % (pair * 2 + 1, k + 1), dim(WHITE, 0.25), label=b[1],
                    function="The chord stored on %s%d: an accent, on a black key as its pack has it." % (b[0], octave),
                    click="Play %s" % b[1], hold="Step held + this pad: the step gets the chord",
                    description="Delete + pad: clear the chord. Copy + pad, then a key: copy it.")
            else:
                put(c, "pad-%d-%d" % (pair * 2 + 1, k + 1), OFF, label="", function="No chord on this key (or not "
                    "a key): dark and silent.", click="", hold="")
            sounding = pair == 1 and w == "E"
            put(c, "pad-%d-%d" % (pair * 2 + 2, k + 1), WHITE if sounding else col if w == "C" else "#9a9a9a",
                label=wch, function="The chord stored on %s%d: a main chord, on a white key as its pack has it. "
                "Every C in the track colour." % (w, oc), click="Play %s" % wch,
                hold="Step held + this pad: the step gets the chord",
                description="Delete + pad: clear the chord. Copy + pad, then a key: copy it.")
    labels = ["Prog", "Voicing", "Perform", "Amount", "Velocity", "Humanize", "Transpose", ""]
    for i in range(8):
        put(c, "knob-%d" % (i + 1), label=labels[i], function=("PADS page, value %d (inside PADS)." % (i + 1))
            if labels[i] else "No job in this layout: dark and dead (rules R3, R4).")
        put(c, "knobled-%d" % (i + 1), dim(WHITE, 0.4) if labels[i] else OFF)
    put(c, "up", click="The two octaves up an octave along the progression's keys [M]; the popup names the range")
    put(c, "down", click="The two octaves down an octave")
    return c, "Note Mode: Progression layout", (
        "A Ripchord-style progression on the two-octave Keyboard layout: every key plays the chord stored on it. "
        "Each chord stays on the key its pack put it on, so the main chords are on the white keys and the accents "
        "on the black keys. Here Em7 sounds. The encoders are the PADS page.")


def lay_chords():
    c = base_note()
    col = TRACK[2]
    VIOLET, ORANGE, TEAL = "#c43aff", "#ff7800", "#13abbf"
    types = ["DIM", "MIN", "MAJ", "SUS"]
    exts = ["6", "m7", "M7", "9"]
    adds = {"DIM": "3 and 6", "MIN": "3 and 7", "MAJ": "4 and 7", "SUS": "5 and 7", "6": "9", "m7": "10", "M7": "11",
            "9": "14"}
    for k in range(4):
        for r, names, colr, kind in ((1, types, VIOLET, "Chord type"), (2, exts, ORANGE, "Extension")):
            n = names[k]
            on = n in ("MIN", "m7")
            put(c, "pad-%d-%d" % (r, k + 1), colr if on else dim(colr, 0.3), label=n,
                function="%s: adds %s semitones above the root. Dim: idle. Full: down or locked." % (kind, adds[n]),
                click="", hold="Held with a root: that chord. Extensions stack; the last type pressed counts",
                shift="Lock: the chord keys that are down stay on")
        for r in (1, 2):
            n = (r - 1) * 4 + k + 1
            full = n in (1, 2, 3, 5)
            put(c, "pad-%d-%d" % (r, k + 5), TEAL if full else OFF, label="Chord %d" % n,
                function="Chord pad %d of the bank (8 banks). Teal: holds a chord. Dark: empty." % n,
                click="Play its chord, with the voicing it was saved with",
                hold="", description="A chord held + this pad: saved here (a white flash). Delete + pad: cleared. "
                "Copy + pad, then an empty one: copied. A step held + pad: the step gets the chord.")
    white = ["C", "D", "E", "F", "G", "A", "B", "C"]
    black = [None, "C#", "D#", None, "F#", "G#", "A#", None]
    for k in range(8):
        b, w = black[k], white[k]
        if b:
            put(c, "pad-3-%d" % (k + 1), dim(WHITE, 0.25), label=b + "3", function="Root, a black key.",
                click="Play the held chord on %s; with no chord key, the single note" % b)
        else:
            put(c, "pad-3-%d" % (k + 1), OFF, label="", function="Not a key: dark and dead.", click="", hold="")
        sounding = w == "D"
        put(c, "pad-4-%d" % (k + 1), WHITE if sounding else col if w == "C" else "#9a9a9a",
            label="%s%d" % (w, 4 if k == 7 else 3), function="Root, a white key (ROOTS: Keys). With ROOTS: Scale the "
            "two rows are the key's degrees and a root alone plays the chord that belongs on it.",
            click="Play the held chord on %s; with no chord key, the single note" % w)
    labels = ["Voicing", "Perform", "Amount", "Roots", "Style", "Ext", "6th", "Bank"]
    for i in range(8):
        put(c, "knob-%d" % (i + 1), label=labels[i], function="PADS page, value %d (PADS selected with the wheel)."
            % (i + 1))
        put(c, "knobled-%d" % (i + 1), dim(WHITE, 0.4), description="Lit: the knob has a job (rule R4).")
    put(c, "knobled-5", dim(WHITE, 0.4))
    return c, "Note Mode: Chords layout", (
        "ChoralRoot's Move layout as a pad layout. Top left: chord types (violet) and extensions (orange); here MIN "
        "and m7 are held. Top right: eight chord pads (teal). Below: the roots, one octave of the Keyboard layout; "
        "D is down, so D minor seven sounds. The encoders are the PADS page.")


def lay_session():
    c = base_note()
    clips = {0: (0, 1, 2), 1: (0, 1, 2), 2: (0, 2, 3), 3: (1, 2), 4: (2,), 5: (0, 2, 3), 6: (), 7: (1, 2)}
    playing = {0: 2, 1: 2, 2: 2, 3: 2, 5: 2, 7: 1}
    queued = {2: 3, 5: 3}
    muted, selected = 6, 2
    for r in range(4):
        for k in range(8):
            led = OFF
            if r in clips[k]:
                led = WHITE if playing.get(k) == r else GREEN if queued.get(k) == r else TRACK[k]
            put(c, "pad-%d-%d" % (r + 1, k + 1), led, label="T%d S%d" % (k + 1, r + 1),
                function="Track %d (the column), scene %d (the row). Track colour: a clip. Pulsing white: the "
                "track's selected, playing clip. Pulsing green: queued. Pulsing track colour: about to stop [M]."
                % (k + 1, r + 1),
                click="Launch; at the next bar when running. An empty slot: select it and stop the track [M]",
                hold="", shift="Select the clip without launching it [M, 18.8]",
                description="Copy + pad, then pad [M]. Delete + pad [M]. Slide along a row: the scene.")
    for k in range(8):
        sel = WHITE if k == selected else dim(TRACK[k], 0.3) if k == muted else TRACK[k]
        put(c, "step-%d" % (2 * k + 1), sel, label="T%d" % (k + 1),
            function="Track %d [M, 18.7]. Its colour; white: selected; dim: muted; blue: soloed." % (k + 1),
            click="Select the track", doubleClick="Open it in Note Mode", hold="+ Volume: its level [M, 18.1]",
            shift=SHIFT_NAMES[2 * k], description="Mute + this step: mute. Shift + Mute + this step: solo.")
        put(c, "step-%d" % (2 * k + 2), dim(WHITE, 0.4) if k in playing else OFF, label="Stop",
            function="Stop track %d [M, 18.7]. Lit while it has a clip playing." % (k + 1),
            click="Stop its clip at the launch quantize", hold="", shift=SHIFT_NAMES[2 * k + 1])
    for r in range(4):
        led = GREEN if r == 2 else dim(WHITE, 0.5)
        put(c, "track-%d" % (r + 1), led, label="Scene %d" % (r + 1),
            function="The scene beside it [New]. Dim white: has clips. Green: playing. Off: empty.",
            click="Launch the scene on all 8 tracks; an empty scene stops every clip", hold="", shift="",
            doubleClick="Stop every clip at the launch quantize [New]",
            description="Copy + button, then a button: copy the scene. Delete + button, twice: delete it "
            "[M, 18.8]. In Note Mode these buttons are the tracks.")
    for i in range(8):
        put(c, "knob-%d" % (i + 1), label="Track %d" % (i + 1), function="Track %d, the column below: its level "
            "(wheel on LEVEL), pan, Send A or Send B [New]" % (i + 1), turn="Set it", touch="Name the track", hold="")
        put(c, "knobled-%d" % (i + 1), TRACK[i])
    put(c, "wheel", turn="What the encoders are: LEVEL, PAN, SEND A, SEND B; then the bus devices: A FX 1, A FX 2, "
        "B FX 1, B FX 2, MASTER FX, OUT [M: where Move has its main effects]", click="Browser for a bus device")
    put(c, "up", click="The scenes shown, one up [M, 18.7]", hold="", shift="Four up")
    put(c, "down", click="The scenes shown, one down [M, 18.7]", hold="", shift="Four down")
    put(c, "left", click="Select the previous track", hold="", shift="")
    put(c, "right", click="Select the next track", hold="", shift="")
    put(c, "menu", 1.0, click="Note Mode on the selected track [M]", shift="")
    put(c, "mute", hold="Hint card. + a track's odd step: mute. With Shift: solo")
    put(c, "copy", click="Nothing: a modifier only", hold="+ a clip: copied, dashed while it waits. + an empty "
        "slot: pasted. + another clip while one waits: replaced. + track button, then one: a scene")
    put(c, "delete", click="Nothing: a modifier only", hold="+ a clip: deleted at the press, crossed until Delete "
        "is let go; Undo brings it back. Never pastes a clip. + track button: the scene")
    return c, "Session Mode", (
        "Columns are tracks, rows are scenes: Live's, Push's and Move's Control Live layout [18.7, 18.8]. A track's "
        "encoder, clips and two steps (select, stop) are in one column. The track buttons launch the scenes beside "
        "them.")


def lay_sampling():
    c = base_note(trk=0, steps="n...n...n...n...")
    col = TRACK[0]
    for r in range(1, 5):
        for k in range(1, 9):
            if k <= 4:
                led = RED if (r, k) == (3, 2) else col if (r, k) in ((4, 1), (4, 2), (4, 3), (3, 1)) else PINK
                put(c, "pad-%d-%d" % (r, k), led, function="Kit pad. Pink: can take a sample. Track colour: holds "
                    "one. Pulsing red: recording [M, 15].", click="Start recording here; again, or another pad, to "
                    "stop [M]. Another pad while recording: the same take continues there [M, 15.7]",
                    hold="Record while held [M]")
            else:
                put(c, "pad-%d-%d" % (r, k), OFF, function="16 Pitches when on [M]", click="", hold="")
    put(c, "sample", 1.0, click="Leave Sampling Mode [M]")
    put(c, "wheel", turn="Source, gain, monitor [M]; then threshold, bar sync [New]", click="Change the selected "
        "entry [M]", touch="Show the source [M]")
    put(c, "knob-1", label="Start", function="After a recording: the trim card. Start [M, as Slicing]")
    put(c, "knob-2", label="End", function="After a recording: end")
    return c, "Sampling Mode", (
        "Sampling pressed on a Sample Kit track. As Move [15], plus more sources, threshold, bar sync, the trim "
        "card after each take, and Grab (Shift + Sampling).")


LAYOUTS = [(lay_note, "note-device-view"), (lay_step, "step-held"), (lay_shift, "shift-map"), (lay_loop, "loop-pages"),
           (lay_session, "session"), (lay_sampling, "sampling"), (lay_keyboard, "note-device-view"),
           (lay_chords, "chords"), (lay_progression, "chords"), (lay_map, "map-row")]


def frame(s, ms=400):
    full = base64.b64encode(b"\xff" * (W * H // 8)).decode()
    return {"id": uid(), "duration": ms, "image": s.b64(),
            "layers": [{"id": uid(), "type": "raster", "name": "Screen", "visible": True, "x": 0, "y": 0,
                        "data": s.b64(), "alpha": full}]}


def frames_for(key, shots):
    if key in ANIM:
        return [frame(s, ms) for s, ms in ANIM[key]]
    return [frame(shots[key], 600)]


def board(shots):
    items = []
    LW, LH, GAP = 1048, 616, 112
    rows = [("1 · Note Mode: Move's, with a chain of devices", LAYOUTS[:3]),
            ("2 · Pages, Session, Sampling", LAYOUTS[3:6]),
            ("3 · Pad layouts", LAYOUTS[6:9]),
            ("4 · Inside a device", LAYOUTS[9:])]
    for ri, (title, lays) in enumerate(rows):
        y = ri * 1000
        items.append({"type": "group", "id": uid(), "x": -60, "y": y - 80, "w": 3 * (LW + GAP) + 8, "h": 900,
                      "title": title, "color": "#6c8cff" if ri == 0 else "#3ccf91"})
        for i, (fn, key) in enumerate(lays):
            ctl, name, desc = fn()
            fr = frames_for(key, shots)
            items.append({"type": "layout", "id": uid(), "x": i * (LW + GAP), "y": y, "w": LW, "h": LH, "name": name,
                          "description": desc, "scope": list(SCOPE), "controls": ctl, "screen": fr[0]["image"],
                          "screenFrames": fr})
            items.append({"type": "note", "id": uid(), "x": i * (LW + GAP), "y": y + LH + 30, "w": LW, "h": 130,
                          "text": name.upper() + ". " + desc, "color": "#f2f2f2"})
    y = 4000
    items.append({"type": "group", "id": uid(), "x": -60, "y": y - 80, "w": 3 * (LW + GAP) + 8, "h": 1000,
                  "title": "5 · Screen rules: pictures at rest, one thing full screen, big type, told on touch",
                  "color": "#d36cff"})
    extra = ["belt-pick", "belt-session","param-page", "param-touch", "wheel-touch", "hint-copy", "toast", "browser", "preset-sheet",
             "projects", "device-main", "view-scene", "view-scope", "view-scope8", "view-tracks"]
    names = {k: (n, d) for k, n, _, d in SCREENS}
    for i, k in enumerate(extra):
        fr = frames_for(k, shots)
        items.append({"type": "screen", "id": uid(), "x": i * 620, "y": y, "w": 560, "h": 340, "name": names[k][0],
                      "description": names[k][1], "screen": fr[0]["image"], "screenFrames": fr})
    rules = ("FEVERDREAM, DRAFT 1. See docs/DESIGN.md.\n\n"
             "1. Move first: every gesture in the Move manual does the same here. [M] in a control's notes marks it.\n"
             "2. New things use Move's three shapes: select then turn; hold a thing then turn; modifier plus target.\n"
             "3. The picture says where you are, a touch says what a control does, a message what just happened.\n"
             "4. A held modifier shows a hint card and lights its targets amber.\n"
             "6. Two hands, never three: Note/Session held is a second Shift under the left thumb.\n"
             "7. Everything can be said: a screen reader from the first screen (Schwung's voice). Speech: Off, On, "
             "or Jog (only while the wheel is touched). Every view, popup, value and change has words.\n"
             "PRESSES: quick click = released inside the 300 ms hold window; hold = still down when it ends; "
             "double click. A button with a hold feature shows nothing before the hold and does its quick click "
             "on release.\n"
             "5. No hidden modes: a lit button and a symbol in the screen's corner for every state.\n"
             "8. Big, simple, told on touch: the screen is small, so nothing depends on small text. Three sizes of "
             "type, three lines at most.\n\n"
             "LED colours keep Move's meanings: white selected / notes, track colour exists, green playing, red "
             "recording and automation, pink sampling, blue solo. Amber is new: a modifier's targets.")
    items.append({"type": "note", "id": uid(), "x": 0, "y": y + 400, "w": 1180, "h": 380, "text": rules,
                  "color": "#ffe58a"})
    tracks = ("EIGHT TRACKS, FOUR BUTTONS. Bank A = tracks 1-4, bank B = 5-8. Shift + a track button: the same row "
              "in the other bank. The track's number is boxed on the screen. Colours run warm (A) to cool (B).\n\n"
              "DEVICES, AS IN LIVE: RACK | MACROS | PADS · SEQ · MIDI effects · INSTRUMENT · audio effects · MIX. "
              "SAVE AND LOAD: a rack's or a device's name stands at its front; a press on it opens one sheet "
              "(Load, Save, Save As, Init, Revert). The wheel "
              "walks the chain, a press enters a device, Back leaves; Shift + wheel moves a device inside its zone; "
              "at the chain the encoders are the track's macros (banks of 8). Every device: 8 values a page, a "
              "face, presets, locks.\n\n"
              "SENDS AND MASTER are chains too, in Session Mode on the wheel, where Move has its main effects.\n\n"
              "SESSION: columns are tracks, rows are scenes (decided 23 Nov 2026). All 8 tracks on the pads; the "
              "track buttons launch scenes; two steps under each column select and stop the track.")
    items.append({"type": "note", "id": uid(), "x": 1240, "y": y + 400, "w": 1180, "h": 380, "text": tracks,
                  "color": "#a9d8ff"})
    return {"format": "ableton-move-designer", "version": 4, "name": "Feverdream", "items": items}


def main():
    img = os.path.join(ROOT, "docs", "img")
    os.makedirs(img, exist_ok=True)
    shots = {}
    for key, _name, fn, _desc in SCREENS:
        shots[key] = fn()
        shots[key].image().save(os.path.join(img, key + ".png"))
    keys = list(shots)
    cols = 3
    tw, th = W * 4 + 16, H * 4 + 16
    sheet = Image.new("RGB", (cols * tw + 8, ((len(keys) + cols - 1) // cols) * th + 8), (40, 40, 44))
    for i, k in enumerate(keys):
        sheet.paste(shots[k].image(), (4 + (i % cols) * tw, 4 + (i // cols) * th))
    sheet.save(os.path.join(img, "sheet.png"))
    with open(os.path.join(ROOT, "design", "feverdream.movedesign.json"), "w") as f:
        json.dump(board(shots), f, indent=1)
    print("wrote %d screens, the sheet and the board" % len(keys))


if __name__ == "__main__":
    main()
