# Feverdream: high-level architecture

Draft 6, 24 November 2026. Status: proposal for review. Nothing here is built yet. Read `DESIGN.md` first; this
document explains how that design is built.

## 1. What shapes it

| Constraint | Consequence |
|---|---|
| Runs instead of Move's software, as a standalone Schwung tool | one process owns the SPI link: audio out and in, pad and button MIDI, LEDs, screen. Proven in `evilgeniusmove/src/plat_move.c` |
| 44.1 kHz, blocks of 128 frames (2.9 ms), quad Cortex-A72, 2 GB | a real-time audio thread that never allocates, locks or touches disk |
| The UI must be designed and tried before the sound exists | the control layer and the screen run with no audio engine at all, on a desk |
| Every parameter is on an encoder, lockable per step, automatable, saved in presets, shown on the web, exported to Live | one description of a parameter, used by all of them |
| Synths and effects must later exist as Max for Live devices | DSP is portable C with no knowledge of Move, behind one module interface |
| A web interface and file manager | the project on disk is plain files in a documented format |
| Lots of animation | the screen is redrawn every frame from state; no page keeps its own pixels |
| A small screen: big type, one thing at a time, told on touch (`DESIGN.md` rule 8) | touch sensing on the encoders and the wheel is a first-class input; every parameter needs a name that fits one large line |
| Everything can be said (`DESIGN.md` rule 7): a screen reader from the first screen | words are the source. A view, popup, value or state change is defined as words; the screen and the voice are two renderings of them. No drawing code may show a state that has no words |

## 2. Layers

```
+--------------------------------------------------------------+
| plat/move      plat/sim (tests)      plat/web (WASM)         |  threads, SPI, files, time
+--------------------------------------------------------------+
| app            ties the layers together; owns the threads' handoff
+----------------+----------------+----------------------------+
| ctl            | ui             | web                        |
| input grammar, | screen, LEDs,  | manager server, remote     |
| modes, actions | faces, motion  | protocol                   |
+----------------+----------------+----------------------------+
| model          projects, tracks, clips, notes, locks, devices, undo
+----------------+---------------------------------------------+
| seq            | dsp                                         |
| clock, launch, | module host, instruments, effects, mixer    |
| sequencers     |                                             |
+----------------+---------------------------------------------+
```

Everything below `plat` is `core/`: C11, no operating system calls, no allocation on the audio path. The same core
builds three ways:

| Target | Is | Used for |
|---|---|---|
| `move` | static aarch64 binary, built in Docker | the instrument |
| `sim` | headless native binary driven by a script of presses and turns, writes screens and LED states | tests, as `evilgeniusmove/tests/*.txt` |
| `web` | WebAssembly with a drawing of the Move | trying the UI on a desk; the Remote page of the web interface |

The `web` target is the reason the UI can be built first. It is also not throwaway work: the page that simulates the
Move is the page that later mirrors a real one.

## 3. Threads

| Thread | Priority | Does | Must not |
|---|---|---|---|
| Audio | SCHED_FIFO, core 3 | one SPI transfer a block: read surface MIDI and input audio, advance the clock, run sequencers, render, write audio, LEDs and a slice of the screen | allocate, lock, log, touch files |
| Control | normal, every 2 ms | turn surface events into actions on the model; send parameter and note changes to audio | block on disk |
| Frame | normal, every 33 ms | build the screen and LED states from the model and the meters | change the model |
| Workers | low | load and save, stream samples, analyse waveforms, export | |
| Web | separate process | serve the manager, relay the remote protocol | touch the SPI device |

Audio and control talk through two lock-free queues: commands down (note on, set parameter, swap a loaded device,
launch a clip) and reports up (meters, playheads, voices, what just triggered, and the two things the screen's
live pictures need: section 7's live values and scope taps). The audio thread owns a *playable
copy* of the project: flat arrays it can read without following pointers the control thread might change. Edits reach
it as commands. Large things, such as a newly loaded sample or kit, are prepared by a worker and handed over as one
pointer swap; the old one is returned for freeing on the next report.

This differs from EvilGenius, which shares one model under a mutex. A mutex was acceptable for one SID engine; with
eight tracks of samplers it would put disk and allocation one mistake away from the audio thread.

The web server is a second process so that a browser upload or a crash in it cannot glitch the audio. The file
manager works on the files directly. The remote and the live pages talk to the host over a local socket.

## 4. The parameter schema

The centre of the design. Every device, including the sequencer and the mix strip, describes itself with a table:

```c
typedef struct {
    uint16_t    id;          /* stable for ever: saved in projects, locks, presets, exports */
    const char *name;        /* "Filter Frequency" */
    const char *label;       /* "CUTOFF": at most ten characters, one large line of the screen */
    uint8_t     kind;        /* continuous, stepped, toggle, choice */
    float       min, max, def;
    uint8_t     curve;       /* linear, exponential, decibel, bipolar */
    uint8_t     unit;        /* none, Hz, ms, dB, %, semitones, steps, sync division */
    uint8_t     picto;       /* which pictogram draws it */
    uint16_t    flags;       /* lockable, automatable, modulatable, per-voice, smoothed */
    const char *const *choices;
} fd_param;
```

Beside its parameters a device lists its **pages**. A page is a name of at most ten characters (`FILTER`), which
is one large line of the screen, the words to say, and up to eight parameter ids, one an encoder. A parameter can
be on more than one page. That is what the **main page** is (`DESIGN.md` 6.1): the device's first page, holding
the ids of its eight key parameters, each of which is also on a page further in, and drawn by the device's theme
instead of as pictograms. Pages are presentation only: nothing is saved by page or encoder, only by parameter id,
so a device's pages can be regrouped later without touching projects or presets.

A device that has modulation lists its **sources** the same way (an id, a name, a kind: envelope, LFO, other) and
a fixed number of **matrix slots**. A slot holds a source id, a target parameter id and a depth. The depth of each
slot is itself a parameter, so it can be locked, automated and saved with no special case; the source and target
of a slot are plain state. The map row (`DESIGN.md` 6.7) is nothing more than an editor for these slots: hold source
plus turn encoder finds or takes a slot for that pair and sets its depth. Only parameters flagged modulatable can
be targets. The modulation itself runs inside the module, per voice where the source is per voice; the host never
modulates a parameter from outside.

From this one table come:

- the screen: the pictogram at rest, and the name, value and unit that take the screen when the encoder is touched
- encoder behaviour (range, curve, fine steps with Shift, detents for choices)
- parameter locks and automation (which are the same thing: a value for a parameter id at a time in a clip)
- presets and projects on disk
- the web interface's device panels
- the Max for Live device's parameters and the Live export's automation

A parameter added to a device appears in all of these with no further code. A device never draws its own parameter
page. It may supply a *face* (section 7) for character.

## 5. The project model

```
project
  tempo, groove, key, scale, launch quantize
  track[8]            type, name, colour, rate, chain, macros
    chain[]           an ordered list of devices. Each: an instance id, a zone (notes in, MIDI effect, instrument,
                      audio effect, mix), a module id, its parameter values, bypass
    macro[4][8]       name, pictogram, and a list of targets: device instance id, parameter id, low, high
                      (a device's own modulation routings are part of that device's state, not listed here)
    chord pad[8][8]   the Chords layout's memories: notes and voicing
    clip[16]
      sequencer state, rate, feel, length in steps, direction
      note[]          position, pitch, velocity, length, and its trig values as locks
      lock[]          position, target (a device instance id and parameter id, or a macro), value, shape
      audio           for Audio Loops: file, warp markers
  bus[3]              send A, send B, master: each a chain of audio effects
  scene[16]           name, tempo, follow action
  pool                samples the project uses
```

**A device is addressed by its instance id, never by its place in the chain.** Locks, automation, macro targets
and the focus record all name a device by an id given when it is added and kept until it is removed. Moving a
device along the chain therefore changes one list and nothing else: every lock and macro still points at it.
Removing a device leaves its locks and macro targets in the undo journal with it, so Undo brings back the device
and everything that pointed at it together. The audio thread is handed a new chain as one pointer swap (section 3);
a reorder never rebuilds a device or cuts its tail.

**Macros are resolved on the control side.** A macro's value is turned into its targets' parameter values before
they are sent to the audio thread, so the audio thread knows only parameters. A locked or automated macro is
resolved at the step by the sequencer the same way.

**Notes are events, not cells.** A note has a position in *steps* with a fraction, so micro timing, unquantized
recording, nudging by a hundredth of a step and several notes on one step all work as they do on Move. A step button
shows the notes whose position rounds to it. Conditions, chance and repeats belong to the note. Locks are events on
the same timeline and need no note.

**Positions are in steps; the clip's rate says how long a step is.** That gives per-clip rates and dotted and triplet
feels for free: the sequencer multiplies. Regrid is a tool that rescales positions and changes the rate together.

**Undo** is a journal of reversible edits on the model, grouped by gesture, with a name for the toast. It covers
loading and deleting, as Move's does.

**On disk** a project is a folder: `project.json`, the samples it recorded, and references to library samples.
Presets are single JSON files, of two kinds with one shape (`DESIGN.md` 6.8). A **device preset** is a module id,
the module's version, and its state: parameter values by parameter id, matrix slots, sample references. A **rack
preset** is a track type, an ordered list of device presets with their zones, the macros with their targets, and
the mix strip; inside a rack file a macro's target names a device by its place in the list, and instance ids are
given afresh when it is loaded. Saving and loading are two actions that take "the thing in focus", so the same code
serves a rack, a device, a bus chain and a kit pad, and the sheet is one component. A parameter id missing from a
file takes its default and an unknown one is ignored, so presets survive a device gaining or losing parameters.
A preset can be exported with its samples inside it as one archive. Each saved thing remembers the file it came
from and whether it has changed since, for Save, Revert and the changed mark.

When a rack is loaded over a track that has clips, each lock is carried across by rule: a lock on a macro stays
(macros are addressed by bank and place); a lock on a device parameter is re-pointed at the device of the same
module in the same position of the same zone, if there is one; any other is kept in the clip marked dormant, plays
nothing, and wakes if a matching device returns. The whole load is one entry in the undo journal. Writes go to a temporary name and are renamed into place, and the project is saved as
Move saves a Set: as you work, on leaving it and on shutdown. Plain files are what make the web file manager, backup
and Live export simple. A progression is one small JSON file too: a name and a list of chords, each with the MIDI note of the
key it sits on and up to eight notes. Ripchord's `.rpc` (XML) is read and written by the web interface, so the unit
itself never parses XML. `ChoralRootFM1/web/fm1prog.js` is the reference for the parser and for cutting a chord to
eight notes; unlike it, a chord keeps its trigger note instead of being counted from the lowest one
(`DESIGN.md` 6.5). Layout under `/data/UserData/feverdream/`: `projects/`, `samples/`, `recordings/`, `progressions/`, `racks/`, `devices/`,
`sequencers/`.

## 6. The control layer

`ctl` is the part that makes the instrument feel like Move, so it is built as a small engine and a table, not as a
switch statement per mode.

- **Gesture recogniser.** Turns raw surface events into the gestures of `DESIGN.md` 1.1: quick click, hold, double
  click, plus turn, touch, and which controls were already held. A held step plus a turned encoder arrives as one
  gesture with both. It is the only code that looks at press and release times. It enforces the two rules for every
  button with a hold feature: nothing is emitted that could show anything before the hold, and a quick click is
  emitted on release. Whether a button has a hold feature in the current state is read from the binding table, so
  the rule cannot be forgotten for one button.
- **One hold window.** `fd_input.hold_ms` (300) and `fd_input.double_ms` (300) live in one record in `ctl`. Nothing
  else holds a copy or a literal: the frame thread reads the record to time hint cards, the simulator and the test
  scripts read it to know how long a hold is, and the remote protocol sends it to the browser on connecting so the
  clickable Move behaves the same. Being a value and not a constant, it can become a Setup entry later.
- **Binding table.** For each mode and state, rows of *gesture, action, hint text, LED rule*. The hint text is also what is said when the modifier is held. The Shift map, the hint
  cards, the amber target lights and the Move Designer board are all read from this table, so what the screen says a
  control does and what it does cannot drift apart. The board in `design/` is generated from the same rows once the
  code exists; until then it is written by hand to match `DESIGN.md`.
- **Actions.** Named, undoable operations on the model: `note.toggle`, `clip.launch`, `param.lock`, `device.load`.
  The surface, the test scripts and the web remote all call the same actions.
- **Focus.** One record of where the player is: mode, track, bank, clip, page, device slot, parameter page, held
  things, and what is touched. The rest view, the touch views and the wheel's "where am I" are drawn from it. Parameters are always addressed through it, which is why locks work on every
  device without each one knowing about locks.

## 7. Screen and LEDs

The frame thread draws from scratch every 33 ms into a 128 x 64 one-bit buffer. Nothing is retained between frames
except the state of animations.

- **Primitives**: lines, boxes, circles, arcs, dither fills, bitmaps, three fonts. No general vector renderer; at this
  size hand-placed pixels look better and cost nothing.
- **Layout**: `DESIGN.md` 3.1. A place has one rest view (a picture, one large line, the strip, the steps row) and
  the touch views replace it while a control is touched and for a second after. The renderer offers three text
  sizes and no others, and refuses a fourth line of text, so the rules cannot be broken by one page. Views are
  functions of the focus record and the model.
- **Words** (`DESIGN.md` 3.4). Every page is two functions of the same state: `draw`, and `words`, which describes
  the page whole in a sentence or two. Every toast, popup and value is built as a small record of label, value and
  unit, from which both its pixels and its spoken form are made; there is no way to put up a toast without one.
  State changes that have no popup (a mute, a step, a clip queued) are named by the action that made them: an
  action's definition includes its words, beside its undo. A parameter's words come from its schema entry (name,
  value text, unit spoken in full), so a device added later speaks with no further work. The build fails if a page
  has no `words`, an action has none, or a parameter's unit has no spoken form.
- **A device's page and its touch view**: generated from the parameter schema.
- **Pictograms**: one small draw function per `picto` kind, taking two normalised values: the one set by hand and
  the one the sound is using now. Envelope, cutoff, wave shape, spread, time, level, pan, mix, pitch, density and so
  on; about thirty cover everything.
- **Live values** (`DESIGN.md` rule 9). The audio thread publishes, once a block, the value in force for each
  parameter of the page the screen is showing: the eight of the open device, or the eight macros at the chain. That
  is at most eight numbers a block into a lock-free slot the frame thread reads; the control thread tells the audio
  thread which eight when the focus changes. The module computes them, since only it knows its modulation, and
  for a per-voice parameter it reports the newest voice. A pictogram draws the live value against the set one. A
  touch view draws the set value as its number, from the model, and never from this slot.
- **Scope taps.** Each track, each bus and the master keeps a short ring of its output, and a tap can be moved to
  the output of any one device for the scope inside a device. The frame thread copies what it needs each frame:
  one track at full width for Scope, eight at a quarter of that for Scope 8. To hold a note still the scope starts
  each picture at a rising zero crossing, using the newest voice's pitch to choose how much to show.
- **Themes** (`DESIGN.md` 6.1): every device has one draw function for its world, used for its main page, for its
  icon in the chain (a small emblem drawn by the same function) and, for an instrument, for the Scene view. It is
  given the same things wherever it is drawn and nothing else: the set and live values of the eight key parameters,
  the notes just triggered (pitch, velocity, pad), the signal's level and a few envelope followers, the transport
  phase and the frame's real time. A theme keeps its own small state (where the fish is) and moves it with springs
  stepped by real time, as h1 does, so it looks the same at any frame rate. A theme draws only: it cannot change
  the project, and with Reduce Motion it is given no time. A theme is written with its device and lives beside
  the device's DSP, but compiles into `ui`, never into the audio thread. A device whose theme is not drawn yet
  shows its key parameters as pictograms, so a device can be built before its world is.
- **The belt** (`DESIGN.md` 3.5) is one component: a list of boxes (an emblem, a name, words), the chosen index
  and a sprung offset. The chain, the pad layouts, track types, device kinds and tools all draw through it, so
  its motion and its speech are written once.
- **Views** are which rest picture a track has: chain, scene, scope, scope 8, tracks. It is one field of the focus
  record, kept per track.
- **Motion**: a small tween system: named values with a target, a duration and an ease, advanced every frame. Toasts,
  touch views, slides and LED pulses use it. Tempo-locked motion reads the transport phase.
- **LEDs**: computed the same way: a function from focus, model and transport to a colour per control, then diffed
  against what was last sent so only changes go down the wire.

Icons and faces are drawn in Ableton Move Designer or Aseprite and converted to C arrays by a tool, so the art in the
board and the art on the unit are the same pixels.

## 8. Sequencing

- **Clock** on the audio thread, in samples, with tempo, groove and the launch quantize. External clock and Link are
  inputs to it later.
- **Launcher**: per track, the playing clip, the queued clip and when it starts. Scenes are launches on eight tracks.
- **Sequencer devices** produce note and lock events for the block ahead. *Step* reads the clip's notes and applies
  chance, conditions, repeats and functions. Generators compute notes from their parameters. All of them write to the
  same event stream, so MIDI FX, instruments and Capture do not care which sequencer made a note.
- **MIDI FX** transform that stream in order.
- **Scripted sequencers** run a small embedded language (Lua is the candidate) on the control side, never on the
  audio thread. A script fills the next bar of events ahead of time; the audio thread plays what it was given. A slow
  or broken script can make a sequencer fall silent but cannot glitch the audio. Scripts declare parameters with the
  same schema, so they get encoders, pages, locks and presets like built-in devices.

## 9. Audio

```
track 1-8:  sound -> fx 1 -> fx 2 -> mix (level, pan) --+--> master fx -> limiter -> out
                                     |        |         |
                                   send A   send B      |
                                     v        v         |
                          bus A: fx 1 -> fx 2 ----------+
                          bus B: fx 1 -> fx 2 ----------+
track output may instead feed an FX Bus track's input
input (mic, line, USB-C) -> sampler, FX Bus input, monitor
resample taps: master, any track, either send -> sampler, and the Grab ring buffer
```

- **Module interface.** A device is a descriptor (its parameter table, voice count, flags) and a few functions:
  create in a given block of memory, set a parameter, note on and off, process a block. No module allocates, reads a
  file or knows what a track is. That is what lets the same source build as a Max external later.
- **Per-track rendering** into separate buffers, then buses, then master. Tracks do not depend on each other except
  through FX Bus routing, so they can later be spread over the other three cores if one is not enough. Start on one
  core and measure.
- **Samples**: short ones in memory, long loops and recordings streamed by a worker. Audio Loops need a time stretch;
  a simple granular one first.
- **Float inside, 16-bit at the SPI edge**, as the link carries.
- **Grab**: a ring buffer of the last eight bars of the master, always running.

Engine choices for the first synth, kit voices and effects are deliberately not made here. They are separate design
work and do not change this structure.

## 10. Web, the voice, export

- **Manager**: a static single-page app served from the unit, a small HTTP server for files, and a WebSocket for the
  live pages. The remote protocol carries the action names from section 6 one way and screen frames, LED states and
  model changes the other.
- **The voice** (`DESIGN.md` 3.4). The core emits `say` records: a kind (view, value, change, modifier) and the
  words. A small speech gate applies the Speech setting: Off drops them, On passes them, Jog passes them only while
  the wheel is touched and, at the touch, asks the current page for its `words`. What passes goes to the platform:
  - on the Move, Schwung's screen reader. RemoteFM1 has already solved this for a standalone tool:
    `remoteFM14Move/src/announce.c` starts Schwung's `schwung-tts` as a child, hands it text through Schwung's
    shared memory contract and mixes its audio in on the audio thread without a lock. Feverdream reuses that, and
    reads the system's screen reader setting for the default.
  - in the browser target, the browser's own speech, so the spoken interface can be tried and tested on a desk.
  - in the test simulator, a log. The test scripts assert the words of every step as they assert the screens, as
    RemoteFM1's `move_speech` tests do.
  The voice is mixed after the master and is never recorded by resampling, Grab or Bounce.
- **Export to Live**: a Live Set is gzipped XML. From the model: one track per track, clips into session slots with
  notes, velocity and chance (Live has note probability), automation from locks. Three stages:
  1. MIDI clips plus rendered stems as audio clips. Always sounds right; nothing to install.
  2. Sample-based tracks as Live's own Simpler and Drum Rack, which is what Move itself does.
  3. Synths and effects as Max for Live devices built from the same DSP modules, with parameters matched by id.
  Conditions and step functions have no Live equivalent and are written out as the notes they produce over a number
  of cycles.

## 11. Repository layout

```
core/      model/ seq/ dsp/ ctl/ ui/ app/     portable C, built for all three targets
plat/      move/ sim/ web/
web/       manager (browser app) and server
assets/    fonts, pictograms, faces: sources and generated C
tools/     asset conversion, Live export, test helpers
tests/     surface scripts and expected screens
design/    the Move Designer board, mock-up generator
docs/      DESIGN.md, ARCHITECTURE.md
m4l/       later
```

## 12. Order of work

Each stage ends with something that can be played with and judged.

| Stage | Builds | Ends with |
|---|---|---|
| 0 | this design, the board, mock-ups | agreement on the open decisions in `DESIGN.md` 14 |
| 1 | `ctl`, `ui`, `model`, the `web` and `sim` targets. No sound | the whole navigation clickable in a browser, and spoken by it: modes, banks, device row, hint cards, Shift map, toasts, motion, the three Speech modes |
| 2 | `plat/move`, clock, Step sequencer, one synth, Sample Kit, mixer, two effects, save and load | a four-bar beat made on the unit, the Move way |
| 3 | the rest of Move: record, capture, automation, Loop Mode, browser, presets, sampling | parity: a Move owner misses nothing |
| 4 | 8 tracks and banks, 16 pages, rates, the note page, locks on every device, sends and master | the "whole lot more" core |
| 5 | Feverdream Manager: files, then Remote | projects and samples managed from a browser |
| 6 | MIDI FX, generators, MIDI tracks, FX Bus, Audio Loops, Perform, Grab, Bounce | all seven track types |
| 7 | scripted sequencers, Live export, Max for Live devices | |

Stage 1 comes before any audio on purpose. The risk in this project is not whether a sampler can be written. It is
whether eight tracks, seven track types and a dozen new features can stay as clear as Move. That is cheapest to find
out with no engine underneath.

## 13. Open technical questions

1. Whether one core carries eight tracks with inserts. Measured in stage 2; the per-track structure allows more
   cores if not.
2. The scripting language and how far ahead a script must compute.
3. Time stretch quality for Audio Loops against CPU.
4. Whether Schwung's speech program can be told to stop a sentence at once. Jog mode needs silence the moment the
   finger leaves the wheel, and a fast player needs a new word to cut off the old one.
5. USB-C audio, Wi-Fi setup and Link while Move's software is stopped: what the system still provides and what
   Feverdream must do itself.
6. Licence for the repository. EvilGenius is MPL-2.0.
