/* The Feverdream design site. Data comes from data.js (python3 design/tools/site.py); this file only draws it. */
(function () {
  'use strict';
  const FD = window.FD;
  const $ = (id) => document.getElementById(id);
  const el = (t, a, ...kids) => {
    const e = document.createElement(t);
    for (const k in a || {}) {
      const v = a[k];
      if (v === null || v === undefined) continue;
      if (k === 'class') e.className = v;
      else if (k === 'html') e.innerHTML = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
      else e.setAttribute(k, v);
    }
    for (const c of kids.flat()) if (c !== null && c !== undefined) e.append(c);
    return e;
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const TAGT = { M: 'Identical to Move', 'M+': 'A Move gesture carried further', New: 'New in Feverdream' };
  const tags = (s) => esc(s).replace(/\[(M\+|M|New)([^\]]*)\]/g, (m, a, b) =>
    `<span class="tag ${a === 'New' ? 'new' : a === 'M+' ? 'plus' : ''}" title="${TAGT[a]}">${a}</span>` +
    (b.replace(/^[;,:\s]+/, '') ? ` <span class="mute">${b.replace(/^[;,:\s]+/, '')}</span>` : ''));
  const md = (s) => (window.marked ? window.marked.parseInline(s) : esc(s));
  const RM = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  /* ------------------------------------------------------------ the one-bit screen */
  const cache = new Map();
  function bits(b64) {
    let p = cache.get(b64);
    if (!p) {
      const s = atob(b64);
      p = new Uint8Array(8192);
      for (let i = 0; i < 8192; i++) p[i] = (s.charCodeAt(i >> 3) >> (7 - (i & 7))) & 1;
      cache.set(b64, p);
    }
    return p;
  }
  function paint(cv, p) {
    const c = cv.getContext('2d');
    const im = c.createImageData(128, 64);
    const d = im.data;
    for (let i = 0; i < 8192; i++) {
      const o = i * 4;
      if (p[i]) { d[o] = 234; d[o + 1] = 246; d[o + 2] = 255; } else { d[o] = 6; d[o + 1] = 8; d[o + 2] = 10; }
      d[o + 3] = 255;
    }
    c.putImageData(im, 0, 0);
  }
  const players = [];
  function bind(cv, key) {
    const s = FD.screens[key];
    const fr = s.frames.map(bits);
    let rest = 0;
    s.ms.forEach((m, i) => { if (m > s.ms[rest]) rest = i; });
    paint(cv, fr[rest]);
    cv.setAttribute('aria-label', s.name);
    const at = players.findIndex((p) => p.cv === cv);
    if (at >= 0) players.splice(at, 1);
    if (fr.length > 1 && !RM) players.push({ cv, fr, ms: s.ms, i: rest, t: 0 });
  }
  function oled(key, cls) {
    const cv = el('canvas', { class: cls === undefined ? 'oled' : cls, width: 128, height: 64, role: 'img' });
    bind(cv, key);
    return cv;
  }
  const shot = (key) => {
    const s = FD.screens[key];
    return el('div', { class: 'sec', style: 'gap:8px' }, oled(key), el('h3', {}, s.name), el('p', { class: 'mute', style: 'font-size:13.5px' }, s.desc));
  };

  /* ------------------------------------------------------------ views */
  const VIEWS = ['map', 'move', 'chain', 'screens', 'grammar', 'steps', 'build', 'decisions', 'spec'];
  let specDone = false;
  function route() {
    let h = location.hash.slice(1);
    if (!VIEWS.includes(h)) h = 'map';
    VIEWS.forEach((v) => { $('v-' + v).hidden = v !== h; });
    document.querySelectorAll('#nav a').forEach((a) => {
      if (a.getAttribute('href') === '#' + h) { a.setAttribute('aria-current', 'page'); a.scrollIntoView({ block: 'nearest', inline: 'nearest' }); } else a.removeAttribute('aria-current');
    });
    if (h === 'spec' && !specDone) renderSpec('design');
    window.scrollTo(0, 0);
  }
  function go(v) { if (location.hash !== '#' + v) location.hash = v; route(); }
  window.addEventListener('hashchange', route);
  document.querySelectorAll('#nav a, .brand').forEach((a) => a.addEventListener('click', (e) => { e.preventDefault(); go(a.getAttribute('href').slice(1)); }));

  /* ------------------------------------------------------------ map */
  $('draft').textContent = FD.draft + ' · proposal for review';
  const N = (key, title, how, to) => ({ key, title, how, to });
  const E = (text, both) => ({ edge: text, both });
  function flow(id, items) {
    $(id).append(...items.map((it) => it.edge !== undefined
      ? el('div', { class: 'edge' + (it.both ? ' both' : '') }, it.edge)
      : el('button', { class: 'node', type: 'button', onclick: () => { if (it.to[0] === 'move') setLayout(it.to[1]); go(it.to[0]); } },
        oled(it.key), el('b', {}, it.title), el('span', {}, it.how))));
  }
  flow('flow-modes', [
    N('projects', 'Projects', '32 projects on the pads', ['screens']), E('Shift + Step 1 · Back', 1),
    N('note-device-view', 'Note Mode', 'play, sequence and edit one track', ['move', 0]), E('Note/Session, quick click', 1),
    N('session', 'Session Mode', 'columns are tracks, rows are scenes', ['move', 4])]);
  flow('flow-wheel', [
    N('note-device-view', 'The chain', 'home: the belt of devices', ['chain']), E('press: in · Back: out', 1),
    N('device-main', 'Main page', "where a device opens: its own world, eight key parameters", ['chain']), E('wheel turn', 1),
    N('param-page', 'Plain pages', 'eight pictograms a page: OSC A, FILTER…', ['chain']), E('touch an encoder'),
    N('param-touch', 'Touch view', 'name and value take the screen', ['screens']), E('wheel left of the main page, press'),
    N('preset-sheet', 'The name', 'Load, Save, Save As, Init, Revert', ['chain'])]);
  flow('flow-held', [
    N('step-held', 'A step held', 'the controls edit that step only', ['move', 1]),
    N('shift-map', 'Shift', 'Shift, or Note/Session held', ['move', 2]),
    N('hint-copy', 'A modifier held', 'Copy, Delete, Mute: a hint card', ['steps']),
    N('loop-pages', 'Loop Mode', 'Loop: the steps are pages', ['move', 3]),
    N('sampling', 'Sampling Mode', 'Sampling: pads take samples', ['move', 5]),
    N('map-row', 'The map row', 'track button again, inside a device', ['move', 9]),
    N('view-scope8', 'Views', 'track button again, at the chain', ['screens']),
    N('belt-pick', 'A picker belt', 'Shift + Step 8: pad layouts', ['chain']),
    N('chords', 'Chords layout', 'chord types, chord pads, roots', ['move', 7]),
    N('toast', 'A message', 'what just happened, for a second', ['screens'])]);

  const bar = (w, h, c) => el('i', { style: `width:${w}px;height:${h}px${c ? ';background:' + c : ''}` });
  const rung = (title, pic, text) => el('div', { class: 'panel rung' }, el('div', { class: 'pic' }, pic), el('h3', {}, title), el('p', {}, text));
  $('ladder').append(
    rung('Project', [...FD.track.map((c) => bar(12, 50, c)), bar(12, 34), bar(12, 34), bar(12, 50)],
      'Eight tracks in two banks, Send A, Send B and Master. Sixteen scenes across them.'),
    rung('Track', [26, 26, 18, 18, 14, 14, 34, 16, 16, 20].map((w, i) => bar(w, i === 6 ? 46 : 30, i === 6 ? FD.track[2] : null)),
      'A chain of devices with macros over it, and sixteen clips, four on the pads at a time.'),
    rung('Clip', Array.from({ length: 16 }, (_, i) => bar(16, 24, i < 4 ? FD.track[2] : null)),
      'Up to sixteen pages, any length from 1 to 256 steps, and its own rate: 1/64 to 4 bars, straight, dotted or triplet.'),
    rung('Page', Array.from({ length: 16 }, (_, i) => bar(8, [0, 4, 8, 10, 14].includes(i) ? 40 : 14, [0, 4, 8, 10, 14].includes(i) ? '#f4f6f8' : null)),
      'Sixteen steps on the step buttons. Left and Right turn the pages.'),
    rung('Step', [bar(60, 12, '#f4f6f8'), bar(40, 12, FD.track[2]), bar(26, 12, '#ff9000')],
      'Notes, parameter locks on any device in the chain, and its TRIG values: chance, condition, ratchet, micro timing, function.'));

  /* ------------------------------------------------------------ the Move */
  const SVG = 'http://www.w3.org/2000/svg';
  const sv = (t, a) => { const e = document.createElementNS(SVG, t); for (const k in a) e.setAttribute(k, a[k]); return e; };
  const CT = [];
  const circ = (id, name, cx, cy, r, label, kind) => CT.push({ id, name, c: [cx, cy, r], label, kind: kind || 'button' });
  for (let i = 0; i < 8; i++) circ('knob-' + (i + 1), 'Encoder ' + (i + 1), 227 + i * 85.2, 46, 19, String(i + 1), 'knob');
  for (let i = 0; i < 8; i++) circ('knobled-' + (i + 1), 'Encoder ' + (i + 1) + ' light', 227 + i * 85.2, 84, 5, '', 'led');
  circ('volume', 'Volume', 961, 53, 23, 'VOL', 'knob');
  circ('wheel', 'Jog wheel', 75, 172, 42, 'WHEEL', 'knob');
  circ('back', 'Back', 45, 269, 21, 'BACK');
  circ('menu', 'Note / Session', 104, 269, 21, 'NOTE');
  for (let i = 0; i < 4; i++) CT.push({ id: 'track-' + (i + 1), name: 'Track button ' + (i + 1), r: [134, 140 + i * 64.6 - 25, 24, 50, 12], kind: 'track' });
  for (let r = 0; r < 4; r++) for (let c = 0; c < 8; c++) CT.push({ id: `pad-${r + 1}-${c + 1}`, name: `Pad, row ${r + 1}, column ${c + 1}`, r: [191 + c * 85.3, 114 + r * 64.9, 72, 52, 3], kind: 'pad' });
  [['capture', 'Capture', 903, 139, 'CAPT'], ['sample', 'Sampling', 961, 139, 'SAMP'], ['loop', 'Loop', 903, 204, 'LOOP'], ['mute', 'Mute', 961, 204, 'MUTE'],
    ['delete', 'Delete', 903, 269, 'DEL'], ['copy', 'Copy', 961, 269, 'COPY'], ['undo', 'Undo', 903, 334, 'UNDO'], ['shift', 'Shift', 961, 334, 'SHIFT']]
    .forEach(([id, n, x, y, l]) => circ(id, n, x, y, 21, l));
  circ('play', 'Play', 48, 411, 22, '▶'); circ('record', 'Record', 104, 411, 22, '●');
  for (let i = 0; i < 16; i++) circ('step-' + (i + 1), 'Step ' + (i + 1), 206 + i * 42.67, 411, 15, String(i + 1), 'step');
  for (let i = 0; i < 16; i++) circ('stepicon-' + (i + 1), 'Icon under step ' + (i + 1), 206 + i * 42.67, 448, 9, FD.shift[i], 'icon');
  circ('left', 'Left', 895, 411, 15, '‹'); circ('right', 'Right', 970, 411, 15, '›');
  circ('up', 'Plus (octave up)', 933, 391, 15, '+'); circ('down', 'Minus (octave down)', 933, 431, 15, '−');
  CT.push({ id: 'power', name: 'Power (rear)', r: [760, -16, 34, 12, 4], kind: 'button' });

  let cur = 0, pinned = null;
  const parts = {};
  const lum = (hex) => { const n = parseInt(hex.slice(1), 16); return (0.3 * (n >> 16) + 0.59 * ((n >> 8) & 255) + 0.11 * (n & 255)) / 255; };
  function ledFill(v, kind) {
    if (typeof v === 'string') return v;
    if (typeof v === 'number' && v > 0) { const a = v > 1 ? v / 127 : v; const g = Math.round(46 + 200 * a); return `rgb(${g},${g},${g})`; }
    return kind === 'led' ? '#15171a' : '#2a2d32';
  }
  const brightOf = (v) => (typeof v === 'string' ? lum(v) : typeof v === 'number' ? (v > 1 ? v / 127 : v) : 0);
  let moveCanvas;
  (function buildMove() {
    const svg = sv('svg', { viewBox: '0 -20 1008 494', role: 'group', 'aria-label': 'Ableton Move top panel' });
    svg.append(sv('rect', { x: 1, y: 1, width: 1006, height: 468, rx: 20, style: 'fill:var(--dev);stroke:var(--dev-edge)', 'stroke-width': 2 }));
    svg.append(sv('rect', { x: 22, y: 27, width: 112, height: 58, rx: 2, style: 'fill:var(--oled);stroke:var(--dev-edge)' }));
    for (const c of CT) {
      const g = sv('g', { class: 'ctl', tabindex: 0, role: 'button', 'aria-label': c.name });
      const shape = c.c ? sv('circle', { cx: c.c[0], cy: c.c[1], r: c.c[2] }) : sv('rect', { x: c.r[0], y: c.r[1], width: c.r[2], height: c.r[3], rx: c.r[4] });
      shape.setAttribute('class', 'ring');
      shape.setAttribute('stroke', c.kind === 'icon' ? 'none' : '#3a3e44');
      shape.setAttribute('stroke-width', 1.2);
      g.append(shape);
      let text = null;
      if (c.label) {
        const big = c.label.length === 1;
        text = sv('text', { x: c.c[0], y: c.c[1] + (c.kind === 'icon' ? 2.5 : big ? 4.5 : 3), 'text-anchor': 'middle', 'font-size': c.kind === 'icon' ? 7 : big ? 13 : c.kind === 'step' ? 10 : 8.5,
          'font-family': 'IBM Plex Mono, ui-monospace, monospace', 'font-weight': 500, 'pointer-events': 'none' });
        text.textContent = c.label;
        g.append(text);
      }
      if (c.kind === 'knob' && c.id !== 'wheel') g.append(sv('line', { x1: c.c[0], y1: c.c[1] - c.c[2] + 3, x2: c.c[0], y2: c.c[1] - c.c[2] + 9, stroke: '#7b828a', 'stroke-width': 2, 'pointer-events': 'none' }));
      parts[c.id] = { shape, text, kind: c.kind };
      g.addEventListener('mouseenter', () => showInfo(c.id));
      g.addEventListener('mouseleave', () => showInfo(pinned));
      g.addEventListener('focus', () => showInfo(c.id));
      const pick = () => { pinned = pinned === c.id ? null : c.id; markSel(); showInfo(c.id); };
      g.addEventListener('click', pick);
      g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
      svg.append(g);
    }
    moveCanvas = el('canvas', { width: 128, height: 64, role: 'img' });
    $('surface').append(svg, moveCanvas);
    const short = ['Note Mode', 'Step held', 'Shift held', 'Loop Mode', 'Session Mode', 'Sampling', 'Keyboard layout', 'Chords layout', 'Progression layout', 'Map row'];
    $('states').append(...FD.layouts.map((L, i) => el('button', { class: 'btn', type: 'button', 'aria-pressed': 'false', onclick: () => setLayout(i) }, short[i] || L.name)));
    const LEG = [['#ffffff', 'selected, or a step with notes'], [FD.track[0], 'track colour: it exists'], ['#4a4a4a', 'available, empty'], ['#00e050', 'playing'],
      ['#ff2020', 'recording, automation'], ['#ff40a0', 'sampling'], ['#2060ff', 'solo'], ['#ff9000', "a held modifier's targets"]];
    $('legend').append(...LEG.map(([c, t]) => el('span', {}, el('i', { style: 'background:' + c }), t)));
  })();
  function markSel() { document.querySelectorAll('.ctl').forEach((g, i) => g.classList.toggle('sel', CT[i].id === pinned)); }
  function setLayout(i) {
    cur = i;
    const L = FD.layouts[i];
    for (const c of CT) {
      const p = parts[c.id];
      const v = (L.controls[c.id] || [null])[0];
      if (p.kind === 'icon') { p.shape.setAttribute('fill', 'transparent'); p.text.setAttribute('fill', brightOf(v) > 0 ? '#ffffff' : '#555b63'); continue; }
      const lit = p.kind === 'knob' ? '#24272b' : ledFill(v, p.kind);
      p.shape.setAttribute('fill', lit);
      if (p.text) p.text.setAttribute('fill', p.kind !== 'knob' && brightOf(v) > 0.5 ? '#14181d' : '#9aa1a9');
    }
    bind(moveCanvas, L.screen);
    bind($('move-big'), L.screen);
    document.querySelectorAll('#states .btn').forEach((b, k) => b.setAttribute('aria-pressed', k === i ? 'true' : 'false'));
    showInfo(pinned);
  }
  const FIELDS = [['function', 'What it is here'], ['click', 'Quick click'], ['doubleClick', 'Double click'], ['hold', 'Hold'], ['turn', 'Turn'],
    ['shiftTurn', 'Shift + turn'], ['touch', 'Touch'], ['shift', 'With Shift'], ['description', 'Also']];
  function showInfo(id) {
    const L = FD.layouts[cur], box = $('info');
    box.textContent = '';
    if (!id) {
      box.append(el('span', { class: 'lab' }, 'State'), el('h2', {}, L.name), el('p', { html: tags(L.desc) }),
        el('p', { class: 'mute', style: 'font-size:13px' }, 'Point at a control to read it. Click to keep it while you change state.'));
      return;
    }
    const c = CT.find((x) => x.id === id);
    const m = FD.metas[(L.controls[id] || [])[1]] || {};
    box.append(el('span', { class: 'lab' }, c.name + ' · ' + L.name), el('h2', {}, m.label || c.name));
    const dl = el('dl');
    for (const [k, label] of FIELDS) if (m[k]) dl.append(el('div', {}, el('dt', {}, label), el('dd', { html: tags(m[k]) })));
    if (!dl.children.length) dl.append(el('div', {}, el('dd', { class: 'mute' }, 'Nothing is written for this control in this state.')));
    box.append(dl);
  }

  /* ------------------------------------------------------------ drawing for the simulator */
  class Scr {
    constructor() { this.p = new Uint8Array(8192); }
    set(x, y, v = 1) { x = Math.round(x); y = Math.round(y); if (x >= 0 && x < 128 && y >= 0 && y < 64) this.p[y * 128 + x] = v; }
    fill(x, y, w, h, v = 1) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) this.set(x + i, y + j, v); }
    hl(x, y, w, v = 1) { this.fill(x, y, w, 1, v); }
    vl(x, y, h, v = 1) { this.fill(x, y, 1, h, v); }
    rect(x, y, w, h, v = 1) { this.hl(x, y, w, v); this.hl(x, y + h - 1, w, v); this.vl(x, y, h, v); this.vl(x + w - 1, y, h, v); }
    inv(x, y, w, h) { for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) if (i >= 0 && i < 128 && j >= 0 && j < 64) this.p[j * 128 + i] ^= 1; }
    line(x0, y0, x1, y1) { const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0)) || 1; for (let i = 0; i <= n; i++) this.set(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n); }
    poly(pts) { for (let i = 1; i < pts.length; i++) this.line(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]); }
    t(x, y, s, k = 1, v = 1) {
      for (const ch of s) {
        const g = FD.font[ch.charCodeAt(0) - 32] || FD.font[0];
        for (let c = 0; c < 5; c++) for (let r = 0; r < 8; r++) if (g[c] & (1 << r)) this.fill(x + c * k, y + r * k, k, k, v);
        x += 6 * k;
      }
      return x;
    }
    tc(xc, y, s, k = 1, v = 1) { return this.t(Math.round(xc - (s.length * 6 - 1) * k / 2), y, s, k, v); }
  }
  const ICON = {
    rack: (s, x, y) => { s.rect(x + 3, y + 2, 12, 14); s.rect(x + 6, y + 2, 6, 5); s.hl(x + 5, y + 10, 8); s.hl(x + 5, y + 12, 8); },
    macro: (s, x, y) => { for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) { s.rect(x + 1 + c * 6, y + 3 + r * 8, 5, 5); s.set(x + 3 + c * 6, y + 4 + r * 8); } },
    pads: (s, x, y) => { for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) ((r === 2 && c === 0) || (r === 1 && c === 2) ? s.fill(x + 2 + c * 5, y + 2 + r * 5, 4, 4) : s.rect(x + 2 + c * 5, y + 2 + r * 5, 4, 4)); },
    seq: (s, x, y) => { for (let r = 0; r < 2; r++) for (let c = 0; c < 4; c++) ((r + c) % 2 === 0 || (r === 1 && c === 2) ? s.fill(x + 1 + c * 4, y + 4 + r * 6, 3, 4) : s.rect(x + 1 + c * 4, y + 4 + r * 6, 3, 4)); },
    chord: (s, x, y) => { s.vl(x + 3, y + 3, 11); for (let i = 0; i < 3; i++) s.fill(x + 5, y + 3 + i * 4, 9 - i * 2, 3); },
    arp: (s, x, y) => { for (let i = 0; i < 4; i++) s.fill(x + 2 + i * 3, y + 12 - i * 3, 3, 3); },
    plus: (s, x, y) => { s.hl(x + 4, y + 8, 9); s.vl(x + 8, y + 4, 9); },
    synth: (s, x, y) => { s.poly([[x + 1, y + 13], [x + 7, y + 4], [x + 7, y + 13], [x + 13, y + 4], [x + 13, y + 13], [x + 16, y + 9]]); for (let i = 1; i < 17; i += 2) s.set(x + i, y + 15); },
    filter: (s, x, y) => { s.poly([[x + 1, y + 7], [x + 8, y + 7], [x + 10, y + 4], [x + 12, y + 7], [x + 16, y + 14]]); for (let i = 1; i < 17; i += 2) s.set(x + i, y + 15); },
    delay: (s, x, y) => { [12, 8, 5, 3].forEach((h, i) => s.fill(x + 2 + i * 4, y + 15 - h, 2, h)); },
    mix: (s, x, y) => { [9, 4, 11].forEach((k, i) => { const cx = x + 3 + i * 6; s.vl(cx, y + 2, 14); s.fill(cx - 2, y + k, 5, 3); }); },
  };
  function strip(s, n, curI, y, front) {
    const x0 = front ? 8 : 0;
    if (front) { if (curI < 0) s.fill(0, y - 1, 4, 3); else s.hl(1, y, 2); }
    const seg = Math.floor((128 - x0 - (n - 1) * 2) / n);
    for (let i = 0; i < n; i++) { const x = x0 + i * (seg + 2); s.hl(x, y, seg); if (i === curI) { s.hl(x, y - 1, seg); s.hl(x, y + 1, seg); } }
  }
  function listScreen(s, items, i) {
    if (items[i - 1]) s.t(4, 3, items[i - 1]);
    s.t(4, 17, items[i], 2); s.inv(0, 15, 122, 18);
    if (items[i + 1]) s.t(4, 38, items[i + 1]);
    s.vl(125, 2, 44); s.fill(124, 2 + Math.round(i * 36 / Math.max(1, items.length - 1)), 3, 8);
    strip(s, items.length, i, 58);
  }

  /* ------------------------------------------------------------ the chain simulator */
  const prm = (...n) => n.map((x, i) => (x ? { n: x, v: ((i * 37 + x.length * 13) % 80 + 10) / 100 } : null));
  const TRIG = ['MICRO', 'RATCH', 'CHANCE', 'COND', 'FUNC', 'AMOUNT', 'LENGTH', 'SLIDE'];
  const OSC = ['WAVE', 'SHAPE', 'OCTAVE', 'SEMI', 'FINE', 'UNISON', 'DETUNE', 'LEVEL'];
  const chain = [
    { zone: 'RACK', name: 'GLASS', full: 'Glass Keys', kind: 'the rack', ic: 'rack', rack: 1 },
    { zone: 'MACROS', name: 'MACROS', full: 'Macros', kind: 'macros', ic: 'macro', nofront: 1, pages: [{ name: 'BANK A', p: prm('BRIGHT', 'MOVE', 'SPACE', 'DIRT', 'ATTACK', 'TAIL', 'WIDTH', 'LEVEL') }, { name: 'BANK B', p: prm('WOBBLE', 'GRIT', 0, 0, 0, 0, 0, 0) }] },
    { zone: 'NOTES IN', name: 'PADS', full: 'Pads', kind: 'pad layout', ic: 'pads', preset: 'CHORDS', pages: [{ name: 'PADS', main: 1, p: prm('VOICING', 'PERFORM', 'AMOUNT', 'ROOTS', 'STYLE', 'BANK', 0, 0) }] },
    { zone: 'NOTES IN', name: 'SEQ', full: 'Sequencer', kind: 'sequencer', ic: 'seq', preset: 'STEP', pages: [{ name: 'ROLL', main: 1, p: prm(...TRIG) }, { name: 'TRIG', p: prm(...TRIG) }, { name: 'MORE', p: prm('VELOCITY', 'V RAMP', 0, 0, 0, 0, 0, 0) }, { name: 'CLIP', p: prm('RATE', 'FEEL', 'LENGTH', 'DIRECTION', 'SWING', 'TRANSPOSE', 0, 0) }] },
    { zone: 'MIDI FX', name: 'CHORD', full: 'Chord', kind: 'MIDI effect', ic: 'chord', preset: 'TRIADS', move: 1, pages: [{ name: 'CHORD', main: 1, p: prm('SHAPE', 'SPREAD', 'INVERT', 'STRUM', 0, 0, 0, 0) }] },
    { zone: 'MIDI FX', name: 'ARP', full: 'Arp', kind: 'MIDI effect', ic: 'arp', preset: 'UP 16', move: 1, pages: [{ name: 'ARP', main: 1, p: prm('RATE', 'GATE', 'STYLE', 'OCTAVES', 'STEPS', 'SWING', 0, 0) }] },
    { zone: 'MIDI FX', name: 'ADD', full: 'Add a MIDI effect', kind: 'empty place', ic: 'plus', plus: 1 },
    { zone: 'INSTRUMENT', name: 'DRIFT', full: 'Drift', kind: 'instrument', ic: 'synth', preset: 'DARK POLY', pages: [
      { name: 'DRIFT', main: 1, p: prm('CUTOFF', 'RESO', 'SHAPE A', 'SHAPE B', 'ATTACK', 'RELEASE', 'LFO RATE', 'LEVEL') },
      { name: 'OSC A', p: prm(...OSC) }, { name: 'OSC B', p: prm(...OSC) },
      { name: 'FILTER', p: prm('CUTOFF', 'RESO', 'TYPE', 'DRIVE', 'ENV AMT', 'KEY TRACK', 0, 'LEVEL') },
      { name: 'ENV', p: prm('ATTACK', 'DECAY', 'SUSTAIN', 'RELEASE', 0, 0, 0, 0) },
      { name: 'LFO', p: prm('RATE', 'SHAPE', 'SYNC', 'FADE', 0, 0, 0, 0) },
      { name: 'MIX', p: prm('OSC A', 'OSC B', 'NOISE', 'SUB', 0, 0, 'PAN', 'LEVEL') }] },
    { zone: 'AUDIO FX', name: 'FILTER', full: 'Filter', kind: 'audio effect', ic: 'filter', preset: 'LOW 24', move: 1, pages: [{ name: 'FILTER', main: 1, p: prm('CUTOFF', 'RESO', 'TYPE', 'DRIVE', 0, 0, 0, 0) }] },
    { zone: 'AUDIO FX', name: 'DELAY', full: 'Delay', kind: 'audio effect', ic: 'delay', preset: 'CANYON', move: 1, world: 'device-main', pages: [{ name: 'DELAY', main: 1, p: prm('TIME', 'FEEDBACK', 'FOG', 'WIDTH', 'WOW', 'DUCK', 0, 'MIX') }] },
    { zone: 'AUDIO FX', name: 'ADD', full: 'Add an audio effect', kind: 'empty place', ic: 'plus', plus: 1 },
    { zone: 'MIX', name: 'MIX', full: 'Mix', kind: 'the strip', ic: 'mix', nofront: 1, pages: [{ name: 'MIX', main: 1, p: prm('VOLUME', 'PAN', 'SEND A', 'SEND B', 'DRIVE', 'WIDTH', 'OUTPUT', 'INPUT') }] },
  ];
  const SHEET = ['LOAD', 'SAVE', 'SAVE AS', 'INIT', 'REVERT'];
  const S = { lvl: 'chain', i: 7, pg: 0, touch: -1, touchUntil: 0, shift: false, toast: null, toastUntil: 0, sheet: 0, list: 0, off: 0, flash: 0, owner: 'chain', note: '' };
  const dev = () => chain[S.i];
  const title = (t) => t.charAt(0) + t.slice(1).toLowerCase();
  function params() {
    if (S.lvl === 'chain') return chain.find((d) => d.ic === 'macro').pages[0].p;
    if (S.lvl === 'dev' && S.pg >= 0) return dev().pages[S.pg].p;
    return [null, null, null, null, null, null, null, null];
  }
  function toast(a, b) { S.toast = [a, b || '']; S.toastUntil = performance.now() + 1100; }
  function turn(d) {
    S.note = '';
    if (S.lvl === 'chain') {
      const j = S.i + d;
      if (S.shift) {
        const a = dev(), b = chain[j];
        if (a.move && b && b.move && b.zone === a.zone) { chain[S.i] = b; chain[j] = a; S.i = j; S.off = 18 * d; S.note = `${a.full} moved inside ${title(a.zone)}.`; } else S.note = a.move ? `${a.full} stays inside ${title(a.zone)}: a device moves only in its zone.` : `${a.full} cannot be moved.`;
      } else if (j >= 0 && j < chain.length) { S.i = j; S.off = 18 * d; }
    } else if (S.lvl === 'dev') {
      const pg = clamp(S.pg + d, dev().nofront ? 0 : -1, dev().pages.length - 1);
      if (pg !== S.pg) { S.pg = pg; if (pg >= 0) S.flash = performance.now() + 550; }
    } else if (S.lvl === 'sheet') S.sheet = clamp(S.sheet + d, 0, SHEET.length - 1);
    else if (S.lvl === 'list') S.list = clamp(S.list + d, 0, dev().pages.length - 1);
    S.touch = -1;
    syncSim();
  }
  function press() {
    S.note = '';
    const d = dev();
    if (S.lvl === 'chain') {
      if (d.plus) { toast('ADD', 'PICK A KIND'); S.note = 'A belt of the kinds of device that fit this place opens.'; } else if (d.rack) { S.lvl = 'sheet'; S.owner = 'chain'; S.sheet = 0; } else { S.lvl = 'dev'; S.pg = d.last === undefined ? 0 : d.last; S.flash = performance.now() + 550; }
    } else if (S.lvl === 'dev') {
      if (S.pg < 0) { S.lvl = 'sheet'; S.owner = 'dev'; S.sheet = 0; } else { S.lvl = 'list'; S.list = S.pg; }
    } else if (S.lvl === 'sheet') { toast(SHEET[S.sheet], S.owner === 'chain' ? 'GLASS' : d.preset); S.lvl = S.owner; } else if (S.lvl === 'list') { S.pg = S.list; S.lvl = 'dev'; S.flash = performance.now() + 550; }
    S.touch = -1;
    syncSim();
  }
  function back() {
    S.note = '';
    if (S.lvl === 'sheet') S.lvl = S.owner;
    else if (S.lvl === 'list') S.lvl = 'dev';
    else if (S.lvl === 'dev') { if (S.pg >= 0) dev().last = S.pg; S.lvl = 'chain'; } else S.note = 'Already home: the chain.';
    S.touch = -1;
    syncSim();
  }
  function say() {
    const d = dev();
    if (S.note) return S.note;
    const ps = params();
    if (S.touch >= 0 && ps[S.touch]) return `${title(ps[S.touch].n)}: ${Math.round(ps[S.touch].v * 100)}`;
    if (S.lvl === 'chain') return `Track 3. ${d.full}, ${d.kind}, ${S.i + 1} of ${chain.length}.` + (S.shift ? ' Shift: turn to move it.' : d.plus ? ' Press to add a device.' : ' Press to enter. The encoders are the macros.');
    if (S.lvl === 'sheet') return `${title(SHEET[S.sheet])}, ${S.sheet + 1} of ${SHEET.length}.`;
    if (S.lvl === 'list') return `${title(d.pages[S.list].name)}, ${S.list + 1} of ${d.pages.length}. Press to go there.`;
    if (S.pg < 0) return `${d.full}, preset ${title(d.preset)}. Press to load or save.`;
    const pg = d.pages[S.pg];
    if (pg.main) return `${d.full}, main page.` + (d.world ? ' A canyon and a ball: a sketch of a world.' : ' Its world is not designed yet.');
    const named = d.pages.filter((p) => !p.main);
    return `${d.full}, ${title(pg.name)}, page ${named.indexOf(pg) + 1} of ${named.length}.`;
  }
  function syncSim() {
    const belt = $('sim-belt');
    belt.textContent = '';
    let zone = null, rowEl = null;
    chain.forEach((d, i) => {
      if (d.zone !== zone) { zone = d.zone; rowEl = el('div'); belt.append(el('div', { class: 'zone' }, el('span', { class: 'lab' }, zone), rowEl)); }
      rowEl.append(el('span', { class: 'dv' + (i === S.i ? (S.lvl === 'chain' ? ' cur' : ' in') : '') }, d.plus ? '+' : d.name));
    });
    const d = dev(), pgs = $('sim-pgs');
    pgs.textContent = '';
    const inside = S.lvl !== 'chain' && d.pages;
    $('sim-pglab').textContent = inside ? `Pages of ${d.full}` : 'Pages: enter a device to see them';
    if (inside) {
      if (!d.nofront) pgs.append(el('span', { class: 'dv' + (S.pg < 0 ? ' cur' : '') }, '■ ' + d.preset));
      d.pages.forEach((p, i) => pgs.append(el('span', { class: 'dv' + (S.pg === i ? ' cur' : '') }, p.main ? p.name + ' · main' : p.name)));
    }
    const ps = params();
    document.querySelectorAll('#sim-knobs .knob').forEach((k, i) => {
      k.classList.toggle('on', !!ps[i]); k.classList.toggle('touch', S.touch === i);
      k.setAttribute('aria-label', 'Encoder ' + (i + 1) + (ps[i] ? ': ' + ps[i].n : ': no job here'));
    });
    $('k-s').setAttribute('aria-pressed', S.shift ? 'true' : 'false');
    $('sim-say').textContent = say();
  }
  function drawSim(now) {
    const s = new Scr(), d = dev(), ps = params();
    if (S.touch >= 0 && S.touchUntil && now > S.touchUntil) { S.touch = -1; S.touchUntil = 0; syncSim(); }
    if (S.toast && now < S.toastUntil) { s.tc(64, 14, S.toast[0], 2); s.tc(64, 36, S.toast[1], 2); return s.p; }
    if (S.touch >= 0 && ps[S.touch]) {
      const p = ps[S.touch];
      s.t(2, 2, p.n, 2); s.t(2, 22, String(Math.round(p.v * 100)), 4);
      for (let i = 0; i < 8; i++) { const x = 3 + i * 16; if (i === S.touch) s.fill(x, 57, 10, 5); else s.rect(x, 57, 10, 5); }
      return s.p;
    }
    if (S.lvl === 'chain') {
      const off = Math.round(S.off), last = chain.length - 1;
      chain.forEach((c, j) => { if (j === last) return; const x = 55 + (j - S.i) * 18 + off; if (x >= 0 && x + 17 <= 104) ICON[c.ic](s, x, 0); });
      if (off === 0 && S.i < last) s.inv(54, 0, 20, 18);
      s.hl(0, 18, 106);
      const ph = (((-S.i * 18 + off) % 6) + 6) % 6;
      for (let x = -6 + ph; x < 104; x += 6) if (x >= 0) s.hl(x, 20, 2);
      s.rect(106, 0, 22, 22); s.vl(106, 3, 14, 0); ICON.mix(s, 109, 2);
      if (S.i === last) s.inv(107, 1, 20, 20);
      s.fill(0, 24, 14, 17); s.t(2, 25, '3', 2, 0); s.t(18, 25, d.name, 2);
      strip(s, chain.length, S.i, 45);
      const pat = 'n...n..%n.k.c.n.', play = Math.floor(now / 240) % 16;
      for (let i = 0; i < 16; i++) { const x = i * 8, c = pat[i]; if (c === 'n') s.fill(x + 1, 54, 5, 5); else if (c === '.') s.set(x + 3, 56); else s.rect(x + 1, 54, 5, 5); if (i === play) s.inv(x, 53, 7, 7); }
      return s.p;
    }
    if (S.lvl === 'sheet') { listScreen(s, SHEET, S.sheet); return s.p; }
    if (S.lvl === 'list') { listScreen(s, d.pages.map((p) => p.name), S.list); return s.p; }
    if (S.pg < 0) { s.t(2, 2, d.name); s.tc(64, 22, d.preset, 2); strip(s, d.pages.length, -1, 58, true); return s.p; }
    const pg = d.pages[S.pg];
    if (now < S.flash) { s.tc(64, 24, pg.name, 2); return s.p; }
    if (pg.main && d.world) { const fr = FD.screens[d.world].frames; return bits(fr[RM ? 0 : Math.floor(now / 110) % fr.length]); }
    if (pg.main) {
      for (let x = 0; x < 128; x += 3) s.set(x, 50);
      pg.p.forEach((p, k) => { if (!p) return; const x = 8 + k * 16, h = Math.round(6 + p.v * 30 + (RM ? 0 : Math.sin(now / 320 + k * 1.3) * 2)); s.vl(x, 50 - h, h); s.rect(x - 3, 50 - h - 6, 7, 7); s.set(x - 1, 50 - h - 4); s.set(x + 1, 50 - h - 4); });
    } else {
      s.tc(64, 1, pg.name, 2);
      pg.p.forEach((p, k) => {
        const x = (k % 4) * 32, y = 22 + (k >> 2) * 16;
        if (!p) { s.set(x + 10, y + 5); s.set(x + 16, y + 5); s.set(x + 22, y + 5); return; }
        const wob = p.n === 'CUTOFF' && !RM ? Math.sin(now / 420) * 0.13 : 0;
        s.hl(x + 4, y + 5, 24); s.vl(x + 4 + Math.round(p.v * 22), y + 9, 2);
        s.fill(x + 3 + Math.round(clamp(p.v + wob, 0, 1) * 22), y + 1, 3, 9);
      });
    }
    strip(s, d.pages.length, S.pg, 58, !d.nofront);
    return s.p;
  }
  (function buildSim() {
    const kn = $('sim-knobs');
    for (let i = 0; i < 8; i++) {
      const k = el('button', { class: 'knob', type: 'button' });
      let y0 = null;
      const touch = () => { if (params()[i]) { S.touch = i; S.touchUntil = 0; S.note = ''; syncSim(); } };
      const nudge = (dv) => { const p = params()[i]; if (p) { p.v = clamp(p.v + dv, 0, 1); syncSim(); } };
      k.addEventListener('pointerdown', (e) => { k.setPointerCapture(e.pointerId); y0 = e.clientY; touch(); });
      k.addEventListener('pointermove', (e) => { if (y0 !== null) { nudge((y0 - e.clientY) / 160); y0 = e.clientY; } });
      const up = () => { y0 = null; if (S.touch === i) S.touchUntil = performance.now() + 900; };
      k.addEventListener('pointerup', up); k.addEventListener('pointercancel', up);
      k.addEventListener('keydown', (e) => { if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { e.preventDefault(); e.stopPropagation(); touch(); nudge(e.key === 'ArrowUp' ? 0.02 : -0.02); S.touchUntil = performance.now() + 900; } });
      kn.append(k);
    }
    $('k-l').onclick = () => turn(-1); $('k-r').onclick = () => turn(1); $('k-p').onclick = press; $('k-b').onclick = back;
    $('k-s').onclick = () => { S.shift = !S.shift; S.note = ''; syncSim(); };
    document.addEventListener('keydown', (e) => {
      if ($('v-chain').hidden || e.metaKey || e.ctrlKey || e.altKey) return;
      const onBtn = e.target.closest && e.target.closest('button, a, select, input');
      if (e.key === 'Shift' && !S.shift) { S.shift = true; syncSim(); } else if (e.key === 'ArrowLeft') { e.preventDefault(); turn(-1); } else if (e.key === 'ArrowRight') { e.preventDefault(); turn(1); } else if (e.key === 'Enter' && !onBtn) { e.preventDefault(); press(); } else if (e.key === 'Escape') back();
    });
    document.addEventListener('keyup', (e) => { if (e.key === 'Shift' && S.shift && !$('v-chain').hidden) { S.shift = false; syncSim(); } });
    $('belt-shots').append(shot('note-device-view'), shot('belt-session'), shot('belt-pick'));
    syncSim();
  })();

  /* ------------------------------------------------------------ screens */
  $('gallery').append(...Object.keys(FD.screens).map(shot));

  /* ------------------------------------------------------------ grammar */
  let pressFrame = null;
  (function pressDemo() {
    const b = $('press'), fillEl = $('tl').querySelector('i');
    let t0 = 0, isDown = false, held = false, dbl = false, holdT = null, clickT = null, lastUp = -1e9;
    const log = (t) => { const ul = $('plog'); ul.prepend(el('li', {}, t)); while (ul.children.length > 5) ul.lastChild.remove(); };
    function down() {
      if (isDown) return;
      const now = performance.now();
      isDown = true; held = false; t0 = now; b.classList.add('down');
      if (clickT && now - lastUp < 300) { clearTimeout(clickT); clickT = null; dbl = true; log('DOUBLE CLICK: it acts now, at the second press.'); return; }
      dbl = false;
      log('Pressed: the button lights. Nothing else shows yet.');
      holdT = setTimeout(() => { held = true; log('HOLD: it acts now, as the window ends. The release will do nothing.'); }, 300);
    }
    function up() {
      if (!isDown) return;
      isDown = false; clearTimeout(holdT); b.classList.remove('down');
      if (held) log('Released after a hold: nothing happens.');
      else if (!dbl) { lastUp = performance.now(); log('Released inside the window. Waiting 300 ms for a second press.'); clickT = setTimeout(() => { clickT = null; log('QUICK CLICK: it acts now. No second press came.'); }, 300); }
    }
    b.addEventListener('pointerdown', (e) => { b.setPointerCapture(e.pointerId); down(); });
    b.addEventListener('pointerup', up); b.addEventListener('pointercancel', up);
    b.addEventListener('keydown', (e) => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); down(); } });
    b.addEventListener('keyup', (e) => { if (e.key === ' ' || e.key === 'Enter') up(); });
    pressFrame = (now) => { if (isDown) fillEl.style.width = clamp((now - t0) / 6, 0, 100) + '%'; };
  })();

  (function bankDemo() {
    let bank = 0, row = 2, shift = false;
    const btns = [0, 1, 2, 3].map((r) => el('button', { type: 'button', onclick: () => { if (shift) bank = 1 - bank; row = r; draw(); } }));
    $('tb').append(...btns);
    $('tshift').onclick = () => { shift = !shift; draw(); };
    function draw() {
      const shown = shift ? 1 - bank : bank;
      btns.forEach((b, r) => { b.style.background = !shift && r === row ? '#ffffff' : FD.track[shown * 4 + r]; b.setAttribute('aria-label', 'Track ' + (shown * 4 + r + 1)); });
      $('tnum').textContent = bank * 4 + row + 1;
      $('tbank').textContent = 'BANK ' + 'AB'[bank] + (shift ? ' · the buttons show bank ' + 'AB'[1 - bank] : '');
      $('tshift').setAttribute('aria-pressed', shift ? 'true' : 'false');
    }
    draw();
  })();

  (function shiftMap() {
    const M = [
      ['Projects', 'M', 'Set Overview, as on Move: 32 projects on the pads.'],
      ['Setup', 'M+', 'Speech (Off, On, Jog) first, then Wi-Fi, Feverdream Manager, MIDI, brightness, about, Exit to Move.'],
      ['Workflow Settings', 'M+', 'Quantize, Step Grid (rate), Count-In, Autoload, Launch Quantize, Record Mode, Page Follow.'],
      ['Track Setup', 'New', 'The cylinder, read as the body of the track: type, name, colour, MIDI channel, voices, output. Ableton has not said what this icon is for.'],
      ['Tempo', 'M+', 'The wheel sets it, Shift for fine, a press confirms. Each further press of Step 5 is a tap of the tempo.'],
      ['Metronome', 'M', 'As on Move.'],
      ['Groove', 'M+', 'Encoders 1 to 8 set how much each track takes.'],
      ['Pad layout', 'M+', 'A belt of layouts. Melodic tracks: In Key, Chromatic, Keyboard, Chords, Progression. Kits: 16 Pitches, 16 Velocities. Then Perform on any track.'],
      ['Keys & Scales', 'M', 'As on Move.'],
      ['Full Velocity', 'M', 'As on Move.'],
      ['Repeat / Arp', 'M', "The track's first MIDI effect."],
      ['Bounce', 'New', 'Layers merging into one: render the selected clip, track or scene to audio, onto a pad or into an Audio Loops clip. Open: it could be a mixer page instead.'],
      ['Tools', 'New', "The star, as in Schwung and EvilGenius: transpose, shift, reverse, randomize, humanize, regrid, locks to automation."],
      ['New Clip', 'M', "Select the track's next empty slot."],
      ['Double Loop', 'M', 'As on Move.'],
      ['Quantize', 'M', 'As on Move.']];
    let sel = 3;
    const btns = M.map((m, i) => el('button', { type: 'button', class: m[1] === 'New' ? 'new' : '', 'aria-label': 'Step ' + (i + 1) + ': ' + m[0], onclick: () => { sel = i; draw(); }, onmouseenter: () => { sel = i; draw(); } }, String(i + 1)));
    $('shiftsteps').append(...btns);
    function draw() {
      btns.forEach((b, i) => b.classList.toggle('head', i === sel));
      const m = M[sel], box = $('shiftinfo');
      box.textContent = '';
      box.append(el('span', { class: 'lab' }, 'Shift + Step ' + (sel + 1)), el('h3', { style: 'margin:4px 0', html: esc(m[0]) + ' ' + tags('[' + m[1] + ']') }), el('p', { class: 'mute' }, m[2]));
    }
    draw();
    const LED = [['#ffffff', 'White', 'selected, or a step that holds notes'], [FD.track[0], 'Track colour', 'exists and belongs to this track'], ['#4a4a4a', 'Dim grey', 'available but empty'],
      ['#00e050', 'Green', 'playing, the playhead, queued to play'], ['#ff2020', 'Red', 'recording, automation'], ['#ff40a0', 'Pink', 'sampling: this pad can take a sample'],
      ['#2060ff', 'Blue', 'solo'], ['#ff9000', 'Amber', "new: a held modifier's valid targets, and nothing else"], [FD.track[2], 'Bright track colour on a step', 'new: locks but no note']];
    $('ledtable').append(...LED.map(([c, n, t]) => el('tr', {}, el('td', { class: 'legend' }, el('i', { style: 'background:' + c }), el('b', { style: 'color:var(--ink)' }, n)), el('td', {}, t))));
  })();

  /* ------------------------------------------------------------ sequencing */
  (function lengthDemo() {
    let pages = 4, last = 5;
    const RATES = [['1/64', 1 / 64], ['1/32', 1 / 32], ['1/16', 1 / 16], ['1/8', 1 / 8], ['1/4', 1 / 4], ['1/2', 1 / 2], ['1 bar', 1], ['2 bars', 2], ['4 bars', 4]];
    const pb = Array.from({ length: 16 }, (_, i) => el('button', { type: 'button', 'aria-label': (i + 1) + ' pages', onclick: () => { pages = i + 1; draw(); } }, String(i + 1)));
    const lb = Array.from({ length: 16 }, (_, i) => el('button', { type: 'button', 'aria-label': 'last page ends after ' + (i + 1) + ' steps', onclick: () => { last = i + 1; draw(); } }, String(i + 1)));
    $('pgsteps').append(...pb); $('lastpads').append(...lb);
    const rate = $('rate');
    RATES.forEach(([n], i) => rate.append(el('option', { value: i }, n)));
    rate.value = 2; rate.onchange = draw;
    function draw() {
      pb.forEach((b, i) => { b.className = i + 1 === pages ? 'head' : i < pages ? 'lit' : ''; });
      lb.forEach((b, i) => { b.className = i + 1 === last ? 'head' : i < last ? 'lit' : ''; });
      const full = pages - 1, steps = full * 16 + last;
      $('lenout').textContent = last === 16 ? `${pages} Page${pages > 1 ? 's' : ''}` : full === 0 ? `${last} Step${last > 1 ? 's' : ''}` : `${full} Page${full > 1 ? 's' : ''} + ${last}`;
      const bars = steps * RATES[rate.value][1];
      $('lensub').textContent = `${steps} steps. At ${RATES[rate.value][0]} a step, straight, that is ${+bars.toFixed(3)} bar${bars === 1 ? '' : 's'}. Another track at another rate runs against it.`;
    }
    draw();
  })();

  let fnFrame = () => {};
  (function fnDemo() {
    const F = {
      RESTART: "Back to the loop's start. Steps 10 to 16 never play.",
      REVERSE: 'The direction is set to backwards, and stays so.',
      FORWARD: 'The direction is set to forwards. Here the track starts out running backwards.',
      FLIP: 'The direction turns round each time the step plays.',
      RANDOM: 'The playhead jumps to a random step.',
      'RND FN': 'A random one of the other functions, each time.',
      LEAP: 'The playhead skips the amount of steps.',
      JUMP: 'The playhead goes to the step named by the amount.',
      REPEAT: 'The step plays again on the next few steps, as if copied there, skipping what is under them.' };
    const sel = $('fn'), amt = $('amt'), cells = Array.from({ length: 16 }, (_, i) => el('i', {}, String(i + 1)));
    Object.keys(F).forEach((k) => sel.append(el('option', {}, k)));
    $('fnsteps').append(...cells);
    let pos = 0, dir = 1, rep = 0, playing = false, acc = 0, lastT = 0;
    const mod = (n) => ((n % 16) + 16) % 16;
    function reset() { pos = sel.value === 'FORWARD' ? 15 : 0; dir = sel.value === 'FORWARD' ? -1 : 1; rep = 0; draw(); }
    function draw() {
      cells.forEach((c, i) => { c.className = i === pos ? 'head' : i === 8 ? 'fn' : ''; });
      if (rep > 0) cells[pos].className = 'lit';
      $('fntext').textContent = F[sel.value];
      $('amtv').textContent = amt.value;
      amt.disabled = !['LEAP', 'JUMP', 'REPEAT'].includes(sel.value);
    }
    function step() {
      const a = +amt.value;
      if (rep > 0) { rep--; pos = mod(pos + dir); return; }
      if (pos === 8) {
        let f = sel.value;
        if (f === 'RND FN') f = ['RESTART', 'REVERSE', 'FLIP', 'RANDOM', 'LEAP', 'JUMP'][Math.floor(Math.random() * 6)];
        if (f === 'RESTART') { pos = 0; return; }
        if (f === 'RANDOM') { pos = Math.floor(Math.random() * 16); return; }
        if (f === 'JUMP') { pos = mod(a - 1 === 8 ? 0 : a - 1); return; }
        if (f === 'REVERSE') dir = -1; else if (f === 'FORWARD') dir = 1; else if (f === 'FLIP') dir = -dir;
        else if (f === 'LEAP') { pos = mod(pos + dir * (a + 1)); return; } else if (f === 'REPEAT') rep = a;
      }
      pos = mod(pos + dir);
    }
    sel.onchange = reset; amt.oninput = draw;
    $('fnplay').onclick = () => { playing = !playing; $('fnplay').setAttribute('aria-pressed', playing ? 'true' : 'false'); $('fnplay').textContent = playing ? 'Stop' : 'Play'; lastT = 0; };
    fnFrame = (now) => { if (!playing || $('v-steps').hidden) return; if (!lastT) lastT = now; acc += now - lastT; lastT = now; if (acc > 230) { acc = 0; step(); draw(); } };
    reset();
  })();
  $('stepsrow').append(oled('note-device-view'));
  $('copyshot').append(oled('hint-copy'));

  /* ------------------------------------------------------------ decisions */
  $('open').append(...FD.open.map((o) => el('div', { class: 'card' }, el('span', { class: 'n' }, String(o.n)), el('h3', { html: md(o.title) }), el('p', { html: md(o.text) }))));
  $('decided').append(...FD.decided.map((d) => el('div', { class: 'card' }, el('span', { class: 'lab' }, d.date), el('h3', { html: md(d.title) }), el('p', { html: md(d.text) }))));

  /* ------------------------------------------------------------ the documents */
  function renderSpec(which) {
    specDone = true;
    const doc = $('doc'), toc = $('toc'), text = FD.docs[which];
    $('doc-design').setAttribute('aria-pressed', which === 'design' ? 'true' : 'false');
    $('doc-arch').setAttribute('aria-pressed', which === 'arch' ? 'true' : 'false');
    if (!window.marked) { doc.textContent = ''; doc.append(el('pre', {}, text)); return; }
    doc.innerHTML = window.marked.parse(text.replace(/!\[[^\]]*\]\(img\/([\w-]+)\.png\)/g, '<span data-oled="$1"></span>'));
    doc.querySelectorAll('[data-oled]').forEach((sp) => {
      const k = sp.getAttribute('data-oled');
      if (FD.screens[k]) sp.replaceWith(oled(k)); else sp.remove();
    });
    doc.querySelectorAll('table').forEach((t) => { const w = el('div', { class: 'tw' }); t.replaceWith(w); w.append(t); });
    toc.textContent = '';
    doc.querySelectorAll('h2').forEach((h) => toc.append(el('a', { tabindex: 0, role: 'link', onclick: () => h.scrollIntoView({ block: 'start' }), onkeydown: (e) => { if (e.key === 'Enter') h.scrollIntoView({ block: 'start' }); } }, h.textContent)));
    doc.querySelectorAll('h2').forEach((h) => { h.style.scrollMarginTop = '70px'; });
  }
  $('doc-design').onclick = () => renderSpec('design');
  $('doc-arch').onclick = () => renderSpec('arch');

  /* ------------------------------------------------------------ run */
  const simCv = $('sim-oled');
  let lastNow = 0;
  function frame(now) {
    const dt = Math.min(100, now - lastNow);
    lastNow = now;
    for (const p of players) {
      if (!p.cv.isConnected || p.cv.offsetParent === null) continue;
      p.t += dt;
      if (p.t >= p.ms[p.i]) { p.t = 0; p.i = (p.i + 1) % p.fr.length; paint(p.cv, p.fr[p.i]); }
    }
    if (!$('v-chain').hidden) {
      if (S.off) { S.off = RM ? 0 : S.off * Math.pow(0.0001, dt / 180); if (Math.abs(S.off) < 0.6) S.off = 0; }
      paint(simCv, drawSim(now));
    }
    if (pressFrame) pressFrame(now);
    fnFrame(now);
    requestAnimationFrame(frame);
  }
  setLayout(0);
  route();
  requestAnimationFrame(frame);
})();
