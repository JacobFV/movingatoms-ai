// Point-cloud scene for the instant estimate (quote page, homepage hand-off, local gallery). Plain WebGL 1.
//
//   const view = createCloudView(canvas, { drive, onFrame })
//   view.loadMAPV(arrayBuffer, animate)   the customer's preview (tools/estimator/worker.py write_preview)
//   drive(now, dt) → { i, p, final, dim }  called every frame: the show step (0-7), its progress, the calm end state
//   onFrame({ mvp, w, h, cloud, view })   after drawing, for HTML overlays (level labels, counters)
//
// Steps: 0 reading (points appear), 1 aligning (jitter settles), 2 levels (slabs glow, outlines), 3 surfaces,
// 4 linear runs, 5 objects (each swept in by a moving plane, boxes around object clusters), 6 measuring (slow
// plane passes over the coloured cloud), 7 preparing. Points: 0 planar, 1 linear, 2 scattered.

const VS = `
attribute vec3 a_pos; attribute vec3 a_from; attribute float a_lab; attribute float a_rnd;
uniform mat4 u_mvp; uniform float u_morph, u_time, u_reveal, u_jitter, u_sweep, u_sweepOn, u_size, u_levelGlow, u_alpha;
uniform vec2 u_planar, u_linear, u_scatter; uniform float u_levels[6]; uniform float u_nLevels;
varying vec3 v_col; varying float v_a;
void main() {
  vec3 p = mix(a_from, a_pos, u_morph);
  p += vec3(sin(a_rnd * 91.0 + u_time * 1.7), cos(a_rnd * 57.0 + u_time * 1.3), sin(a_rnd * 33.0 - u_time)) * u_jitter * (0.4 + a_rnd);
  gl_Position = u_mvp * vec4(p, 1.0);
  float isP = 1.0 - step(0.5, a_lab), isL = step(0.5, a_lab) * (1.0 - step(1.5, a_lab)), isS = step(1.5, a_lab);
  float behind = step(p.x, u_sweep);
  float kP = isP * max(u_planar.x, u_planar.y * behind), kL = isL * max(u_linear.x, u_linear.y * behind), kS = isS * max(u_scatter.x, u_scatter.y * behind);
  vec3 c = vec3(0.72); float a = 0.55;
  c = mix(c, vec3(1.0), kP); a += kP * 0.3;
  float flow = 0.55 + 0.45 * sin((p.x + p.y + p.z) * 1.3 - u_time * 3.2);
  c = mix(c, vec3(0.50, 0.82, 1.0) * (0.8 + 0.4 * flow), kL); a += kL * 0.5;
  c = mix(c, vec3(1.0, 0.69, 0.36), kS); a += kS * 0.4;
  float g = 0.0;
  for (int i = 0; i < 6; i++) { if (float(i) < u_nLevels) g = max(g, exp(-abs(p.z - u_levels[i]) * 7.0)); }
  g *= u_levelGlow * (0.35 + 0.65 * isP); c = mix(c, vec3(1.0), g); a += g * 0.45;
  float sw = exp(-abs(p.x - u_sweep) * 2.2) * u_sweepOn; c += vec3(sw * 0.7); a += sw * 0.5;
  v_col = c; v_a = clamp(a, 0.0, 1.0) * step(a_rnd, u_reveal) * u_alpha;
  gl_PointSize = clamp(u_size * (1.0 + sw * 0.9) / gl_Position.w, 1.0, 7.0);
}`;
const FS = `precision mediump float; varying vec3 v_col; varying float v_a;
void main() { vec2 d = gl_PointCoord - 0.5; float r = dot(d, d); if (r > 0.25) discard;
  float f = smoothstep(0.25, 0.02, r) * v_a; gl_FragColor = vec4(v_col * f, f); }`;
const LVS = "attribute vec3 a_p; uniform mat4 u_mvp; void main() { gl_Position = u_mvp * vec4(a_p, 1.0); }";
const LFS = "precision mediump float; uniform vec4 u_c; void main() { gl_FragColor = vec4(u_c.rgb * u_c.a, u_c.a); }";

export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ── clouds ───────────────────────────────────────────────────────────────────
// A cloud: { n, pos Float32Array (centred metres, Z up), lab Uint8Array, ext, levels, boxes, rnd, radius, outN }
export function placeholder() {
  // a generic two-storey building, shown until the customer's own preview arrives
  const pts = [], labs = [], W = 34, D = 20, H = 7.4, rnd = mulberry(11);
  const add = (x, y, z, l) => { pts.push(x - W / 2, y - D / 2, z - H / 2); labs.push(l); };
  let i;
  for (i = 0; i < 9000; i++) { const lv = [0, 3.6, H][i % 3]; add(rnd() * W, rnd() * D, lv + (rnd() - .5) * .04, 0); }
  for (i = 0; i < 9000; i++) {
    const side = i % 4, t = rnd(), z = rnd() * H;
    if (side === 0) add(t * W, 0, z, 0); else if (side === 1) add(t * W, D, z, 0); else if (side === 2) add(0, t * D, z, 0); else add(W, t * D, z, 0);
  }
  for (i = 0; i < 2600; i++) add([11, 23][i % 2] + (rnd() - .5) * .1, rnd() * D * .7, rnd() * 3.6, 0);
  for (i = 0; i < 2400; i++) add(4 + 6.5 * (i % 5) + (rnd() - .5) * .3, [6, 14][(i >> 3) % 2] + (rnd() - .5) * .3, rnd() * H, 1);
  for (i = 0; i < 4200; i++) { const run = i % 6, along = rnd(); add(along * W, 3 + (run % 3) * 6.5 + Math.sin(along * 9) * .05, (run < 3 ? 3.2 : 6.9) + (rnd() - .5) * .08, 1); }
  for (i = 0; i < 5200; i++) { const k = i % 18; add(2 + (k * 7.3) % (W - 4) + rnd() * 1.6, 2 + (k * 4.1) % (D - 4) + rnd() * 1.1, (k % 2 ? 0 : 3.6) + rnd() * (0.6 + (k % 3) * .4), 2); }
  return finish({ n: labs.length, pos: new Float32Array(pts), lab: new Uint8Array(labs), ext: [W, D, H], sample: true });
}

export function parseMAPV(buf) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, false) !== 0x4D415056) throw new Error("not a MAPV preview");
  const n = dv.getUint32(4, true), ext = [dv.getFloat32(8, true), dv.getFloat32(12, true), dv.getFloat32(16, true)];
  const q = new Uint16Array(buf.slice(20, 20 + n * 6)), lab = new Uint8Array(buf.slice(20 + n * 6, 20 + n * 7)), pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) pos[i * 3 + k] = (q[i * 3 + k] / 65535 - 0.5) * ext[k];
  return finish({ n, pos, lab, ext });
}

function finish(c) {
  // frame on the 2nd-98th percentile box: scans (splats especially) carry stray floaters far from the building
  let i, k;
  const lo = [], hi = [], stride = Math.max(1, Math.floor(c.n / 6000));
  for (k = 0; k < 3; k++) {
    const v = []; for (i = 0; i < c.n; i += stride) v.push(c.pos[i * 3 + k]);
    v.sort((a, b) => a - b);
    const a0 = v[Math.floor(v.length * .02)], a1 = v[Math.floor(v.length * .98)], pad = 0.04 * (a1 - a0);
    lo.push(a0 - pad); hi.push(a1 + pad);
  }
  const ctr = [0, 1, 2].map((j) => (lo[j] + hi[j]) / 2);
  c.ext = [0, 1, 2].map((j) => Math.max(0.5, hi[j] - lo[j]));
  c.out = new Uint8Array(c.n);
  for (i = 0; i < c.n; i++) for (k = 0; k < 3; k++) { const q = (c.pos[i * 3 + k] -= ctr[k]); if (Math.abs(q) > c.ext[k] * 0.62) c.out[i] = 1; }
  // floor levels: peaks in the height histogram of surface points
  const bin = 0.2, nb = Math.max(1, Math.ceil(c.ext[2] / bin)), h = new Float32Array(nb);
  for (i = 0; i < c.n; i++) if (c.lab[i] === 0 && !c.out[i]) h[Math.min(nb - 1, Math.max(0, Math.floor((c.pos[i * 3 + 2] + c.ext[2] / 2) / bin)))]++;
  const sorted = Array.from(h).sort((a, b) => a - b), med = sorted[nb >> 1] || 1, peaks = [];
  for (i = 0; i < nb; i++) if (h[i] > 2.2 * med && h[i] >= (h[i - 1] || 0) && h[i] >= (h[i + 1] || 0)) peaks.push([h[i], i]);
  peaks.sort((a, b) => b[0] - a[0]);
  const lv = [];
  for (const p of peaks) { const z = (p[1] + .5) * bin - c.ext[2] / 2; if (lv.length < 6 && lv.every((q) => Math.abs(q - z) > 2.4)) lv.push(z); }
  c.levels = lv.sort((a, b) => a - b);
  // object boxes: the densest 3D cells of scattered points, tightened to their points (5th-95th percentile)
  const cell = Math.max(1.2, Math.max(c.ext[0], c.ext[1]) / 36), cells = {};
  for (i = 0; i < c.n; i++) if (c.lab[i] === 2 && !c.out[i]) {
    const key = Math.floor(c.pos[i * 3] / cell) + "," + Math.floor(c.pos[i * 3 + 1] / cell) + "," + Math.floor(c.pos[i * 3 + 2] / cell);
    (cells[key] || (cells[key] = [])).push(i);
  }
  const minPts = Math.max(10, c.n / 2500);
  c.boxes = Object.values(cells).filter((ix) => ix.length >= minPts).sort((a, b) => b.length - a.length).slice(0, 16).map((ix) => {
    const blo = [], bhi = [];
    for (let j = 0; j < 3; j++) { const v = ix.map((m) => c.pos[m * 3 + j]).sort((a, b) => a - b); blo.push(v[Math.floor(v.length * .05)]); bhi.push(v[Math.floor(v.length * .95)]); }
    return { lo: blo, hi: bhi };
  });
  c.rnd = new Float32Array(c.n); const r = mulberry(c.n);
  for (i = 0; i < c.n; i++) c.rnd[i] = c.out[i] ? 2 : r();   // > 1: never revealed
  c.radius = 0.5 * Math.hypot(c.ext[0], c.ext[1], c.ext[2]);
  c.outN = c.out.reduce((a, b) => a + b, 0);
  return c;
}

// ── matrices ─────────────────────────────────────────────────────────────────
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
function persp(f, a, n, fa) { const t = 1 / Math.tan(f / 2); return [t / a, 0, 0, 0, 0, t, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, 2 * fa * n / (n - fa), 0]; }
function look(e, c, u) {
  const z = norm([e[0] - c[0], e[1] - c[1], e[2] - c[2]]), x = norm(cross(u, z)), y = cross(z, x);
  return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, e), -dot(y, e), -dot(z, e), 1];
}
function mul(a, b) { const o = new Array(16); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k * 4 + j] * b[i * 4 + k]; o[i * 4 + j] = s; } return o; }
export function project(m, p) {
  const x = m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12], y = m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13], w = m[3] * p[0] + m[7] * p[1] + m[11] * p[2] + m[15];
  return [x / w, y / w];
}

// ── the view ─────────────────────────────────────────────────────────────────
export function createCloudView(canvas, { drive, onFrame, spin = 0.13 } = {}) {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const gl = canvas.getContext("webgl", { antialias: true, alpha: true, premultipliedAlpha: true });
  const view = { ok: !!gl, cloud: null, yaw: 0.7 + Math.random() * 0.6, running: true };
  if (!gl) return Object.assign(view, { loadMAPV() {}, setPlaceholder() {}, destroy() {} });

  function program(vs, fs) {
    const sh = (t, src) => { const s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; };
    const p = gl.createProgram(); gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p);
    const u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) { const nm = gl.getActiveUniform(p, i).name.replace("[0]", ""); u[nm] = gl.getUniformLocation(p, nm); }
    return { p, u };
  }
  const P = program(VS, FS), L = program(LVS, LFS), bufs = {};
  let ghost = null, morph = 1, morphAt = 0, lineVerts = { levels: 0, boxes: 0 }, raf = 0, lastT = performance.now();
  const S = { reveal: 0, jitter: 0.6, planar: [0, 0], linear: [0, 0], scatter: [0, 0], sweep: -1e3, sweepOn: 0, levelGlow: 0, lineLv: 0, lineBox: 0, pitch: 0.62, zoom: 1.25, alpha: 1 };
  const T = JSON.parse(JSON.stringify(S));

  function upload(target, from) {
    const buf = (name, data) => { if (!bufs[name]) bufs[name] = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, bufs[name]); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); };
    const fromPos = new Float32Array(target.n * 3);
    for (let i = 0; i < target.n; i++) { const j = (i * 7919) % from.n; fromPos[i * 3] = from.pos[j * 3]; fromPos[i * 3 + 1] = from.pos[j * 3 + 1]; fromPos[i * 3 + 2] = from.pos[j * 3 + 2]; }
    buf("pos", target.pos); buf("from", fromPos); buf("lab", new Float32Array(target.lab)); buf("rnd", target.rnd);
    const v = [], hx = target.ext[0] / 2, hy = target.ext[1] / 2;
    target.levels.forEach((z) => v.push(-hx, -hy, z, hx, -hy, z, hx, -hy, z, hx, hy, z, hx, hy, z, -hx, hy, z, -hx, hy, z, -hx, -hy, z));
    target.boxes.forEach((b) => {
      const [x0, y0, z0] = b.lo, [x1, y1, z1] = b.hi;
      const c8 = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
      [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].forEach((e) => v.push(...c8[e[0]], ...c8[e[1]]));
    });
    buf("lines", new Float32Array(v.length ? v : [0, 0, 0, 0, 0, 0]));
    lineVerts = { levels: target.levels.length * 8, boxes: target.boxes.length * 24 };
    view.cloud = target;
  }
  view.setCloud = (c, animate) => {
    const from = view.cloud || c;
    upload(c, from);
    morph = animate && from !== c ? 0 : 1; morphAt = performance.now(); ghost = from; view.drawn = false;
    if (morph === 1) ghost = null;
  };
  view.setPlaceholder = () => view.setCloud(placeholder(), false);
  view.loadMAPV = (buf, animate = true) => { const c = parseMAPV(buf); view.setCloud(c, animate); return c; };
  view.resetTint = () => { S.planar = [0, 0]; S.linear = [0, 0]; S.scatter = [0, 0]; };

  function targets(i, p, final) {
    const hx = view.cloud ? view.cloud.ext[0] / 2 + 1 : 20;
    T.sweepOn = 0; T.levelGlow = i === 2 ? 1 : i > 2 && !final ? 0.18 : 0;
    T.lineLv = i === 2 ? 0.55 : i > 2 && i < 6 ? 0.12 : 0.06;
    T.lineBox = i === 5 ? 0.7 : i > 5 ? 0.22 : 0;
    T.reveal = i === 0 ? ease(p * 1.1) : 1;
    T.jitter = i === 0 ? 0.6 : i === 1 ? 0.6 * (1 - ease(p * 1.2)) : 0;
    T.pitch = i === 2 ? 0.16 : i === 4 ? 0.85 : 0.6;
    T.zoom = i === 0 ? 1.25 : i === 4 ? 0.98 : i === 5 ? 1.0 : 1.08;
    T.planar = [i > 3 ? 1 : 0, i === 3 ? 1 : 0];
    T.linear = [i > 4 ? 1 : 0, i === 4 ? 1 : 0];
    T.scatter = [i > 5 ? 1 : 0, i === 5 ? 1 : 0];
    if (i >= 3 && i <= 5) { T.sweepOn = Math.sin(Math.PI * Math.min(1, p)); T.sweep = lerp(-hx, hx, ease(p)); }
    if (i === 6) { const q = (p * 0.6) % 1; T.sweepOn = 0.55 * Math.sin(Math.PI * q); T.sweep = lerp(-hx, hx, q); }
    if (final) { T.planar = [1, 0]; T.linear = [1, 0]; T.scatter = [1, 0]; T.lineBox = 0.1; T.lineLv = 0.05; T.pitch = 0.55; T.zoom = 1.06; T.levelGlow = 0; T.sweepOn = 0; }
  }

  function frame(now) {
    raf = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (now - lastT) / 1000); lastT = now;
    if (!view.cloud || (!view.running && view.drawn)) return;   // paused views still draw their first frame
    const st = (drive && drive(now, dt)) || { i: 7, p: 1, final: true };
    targets(st.i, st.p, st.final);
    const k = 1 - Math.exp(-dt * 3.2);
    for (const key of ["reveal", "jitter", "sweepOn", "levelGlow", "lineLv", "lineBox", "pitch", "zoom"]) S[key] = lerp(S[key], T[key], key === "reveal" ? 1 : k);
    S.sweep = T.sweep; S.alpha = lerp(S.alpha, st.dim ? 0.45 : 1, k);
    for (const key of ["planar", "linear", "scatter"]) { S[key][0] = lerp(S[key][0], T[key][0], k); S[key][1] = lerp(S[key][1], T[key][1], k * 2); }
    draw(now, dt, st); view.drawn = true;
  }

  function draw(now, dt, st) {
    const cloud = view.cloud, dpr = Math.min(2, devicePixelRatio || 1), w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    morph = morph < 1 ? ease((now - morphAt) / 1800) : 1;
    const radius = ghost && morph < 1 ? lerp(ghost.radius, cloud.radius, morph) : cloud.radius;
    if (!reduce) view.yaw += dt * (st.final ? spin * 0.55 : spin);
    const fov = 0.62, aspect = w / h, fit = radius / Math.sin(fov / 2) / Math.min(1, aspect * 0.95);
    const dist = fit * S.zoom * 0.92;
    const eye = [Math.cos(view.yaw) * Math.cos(S.pitch) * dist, Math.sin(view.yaw) * Math.cos(S.pitch) * dist, Math.sin(S.pitch) * dist];
    const mvp = mul(persp(fov, aspect, dist * 0.05, dist * 4), look(eye, [0, 0, 0], [0, 0, 1]));
    gl.useProgram(P.p);
    const attr = (name, bname, n) => { const loc = gl.getAttribLocation(P.p, name); gl.bindBuffer(gl.ARRAY_BUFFER, bufs[bname]); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, 0, 0); return loc; };
    const locs = [attr("a_pos", "pos", 3), attr("a_from", "from", 3), attr("a_lab", "lab", 1), attr("a_rnd", "rnd", 1)];
    const u = P.u;
    gl.uniformMatrix4fv(u.u_mvp, false, mvp);
    gl.uniform1f(u.u_morph, morph); gl.uniform1f(u.u_time, now / 1000); gl.uniform1f(u.u_reveal, S.reveal); gl.uniform1f(u.u_jitter, S.jitter);
    gl.uniform1f(u.u_sweep, S.sweep); gl.uniform1f(u.u_sweepOn, S.sweepOn); gl.uniform1f(u.u_levelGlow, S.levelGlow);
    // ~2 px points for a full 40k preview, a little larger for sparse clouds and small canvases
    gl.uniform1f(u.u_size, dpr * dist * (cloud.n > 30000 ? 2.1 : 2.6) * (w < 600 ? 0.85 : 1));
    gl.uniform1f(u.u_alpha, 0.9 * S.alpha);
    gl.uniform2f(u.u_planar, S.planar[0], S.planar[1]); gl.uniform2f(u.u_linear, S.linear[0], S.linear[1]); gl.uniform2f(u.u_scatter, S.scatter[0], S.scatter[1]);
    gl.uniform1fv(u.u_levels, new Float32Array(cloud.levels.concat([0, 0, 0, 0, 0, 0]).slice(0, 6))); gl.uniform1f(u.u_nLevels, cloud.levels.length);
    gl.drawArrays(gl.POINTS, 0, cloud.n);
    locs.forEach((l) => gl.disableVertexAttribArray(l));
    gl.useProgram(L.p);
    const la = gl.getAttribLocation(L.p, "a_p"); gl.bindBuffer(gl.ARRAY_BUFFER, bufs.lines); gl.enableVertexAttribArray(la); gl.vertexAttribPointer(la, 3, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(L.u.u_mvp, false, mvp);
    if (lineVerts.levels && S.lineLv > 0.01) { gl.uniform4f(L.u.u_c, 1, 1, 1, S.lineLv * morph * S.alpha); gl.drawArrays(gl.LINES, 0, lineVerts.levels); }
    if (lineVerts.boxes && S.lineBox > 0.01) {
      const shown = st.i === 5 && !st.final ? Math.ceil(cloud.boxes.length * Math.min(1, st.p / 0.7)) : cloud.boxes.length;
      gl.uniform4f(L.u.u_c, 1, 0.75, 0.45, S.lineBox * morph * S.alpha); gl.drawArrays(gl.LINES, lineVerts.levels, shown * 24);
    }
    gl.disableVertexAttribArray(la);
    onFrame && onFrame({ mvp, w, h, cloud, reveal: S.reveal, morph, st });
  }

  raf = requestAnimationFrame(frame);
  view.destroy = () => { cancelAnimationFrame(raf); const ext = gl.getExtension("WEBGL_lose_context"); ext && ext.loseContext(); };
  return view;
}
