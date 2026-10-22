// Instant estimate: a live "conversion" over the customer's own point cloud while we measure the scan and the
// estimating agent plans the job, then a fixed price and the paywall, all on one screen.
//
//   mount(root, { id, fresh, uploading, files })  → { upload(pct, sent, total), uploaded(), uploadError(msg, retry) }
//
// The homepage mounts this as soon as "Get quote" is pressed (uploading: true) and feeds it upload progress;
// /quote/?id= mounts it on its own. Steps follow the real pipeline where there is one (upload, measuring, the
// agent's own narration) and play scripted detection steps on the real cloud in between.
// Data: /portal/api/estimate/:id (+ /preview, /poster, /scope) and /checkout/:id. See tools/portal/portal.js.
import { createCloudView, project } from "./cloud.js?v=4";

const $ = (s, r = document) => r.querySelector(s);
const esc = (t) => String(t == null ? "" : t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const num = (n) => Math.round(n).toLocaleString("en-US");
const usd = (n) => "$" + Math.round(n).toLocaleString("en-US");
const size = (b) => b >= 1e9 ? (b / 1e9).toFixed(1) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(0) + " MB" : Math.max(1, Math.round(b / 1e3)) + " KB";
const day = (ms) => new Date(ms).toLocaleDateString("en-US", { day: "numeric", month: "short" });
async function api(path, body) {
  const r = await fetch("/portal/api" + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "same-origin" } : { credentials: "same-origin" });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.ok) { const e = new Error(j.error || "Something went wrong."); e.status = r.status; throw e; }
  return j;
}

const OUT = { revit: "Revit", ifc: "IFC", step: "STEP", usd: "USD", glb: "GLB" };
const HOLD = {
  large: "Projects over $10,000 get a quick check from our team before payment. We'll confirm this price within a few hours.",
  low_confidence: "Your scan needs a quick look from our team before we can confirm the price. We'll be in touch within a few hours.",
  partial_area: "Tell us which part you need and we'll confirm the price within a few hours.",
  auto_estimate: "We'll confirm this price within a few hours.",
  confirm: "Larger projects get a second, detailed check of the measurements. Your final price will appear here in a few minutes; you can stay on this page.",
  damaged_file: "Part of your file was damaged, so we recovered what we could. We'll confirm the price, or ask for a fresh export, within a few hours.",
};
const DONE = ["quoted", "quote_review", "reviewing", "needs_info", "declined", "expired", "payment_processing", "paid", "accepted", "modelling", "delivered"];
const when = (ms) => new Date(ms).toLocaleString("en-US", { weekday: "long", day: "numeric", month: "long", hour: "numeric", minute: "2-digit" });
// the show: [label, heading, scene step, minimum ms]
const SHOW = [
  ["Reading points", "Reading your scan", 0, 2600],
  ["Aligning scan stations", "Aligning the scan", 1, 2400],
  ["Finding floors and levels", "Finding the levels", 2, 2900],
  ["Detecting walls, slabs and columns", "Detecting surfaces", 3, 3000],
  ["Tracing pipes, ducts and steel", "Tracing linear runs", 4, 3000],
  ["Separating objects", "Separating objects", 5, 2800],
  ["Planning the conversion", "Planning the work", 6, 3200],
  ["Preparing your quote", "Preparing your quote", 7, 1400],
];
const UPLOAD = ["Uploading your scan", "Uploading your scan", 0, 0];

// previous work under the paywall: the homepage's strongest scan → model examples
const WORK = [
  { title: "Process plant", sub: "Rotterdam · 4.3M LiDAR points · 89 objects, pipe network traced", href: "/lidarsample/?scene=rotterdam",
    model: "/home/media/rotterdam-model.webp", scan: "/home/media/rotterdam-scan.webp", alt: "Rotterdam process plant, reconstructed model", credit: "Captured with NavVis LiDAR" },
  { title: "Factory floor", sub: "9.6M LiDAR points · 394 objects", href: "/lidarsample/?scene=factory-floor",
    model: "/home/media/factory-model.webp", scan: "/home/media/factory-scan.webp", alt: "Factory floor, reconstructed model", credit: "Captured with NavVis LiDAR" },
  { title: "Medical warehouse", sub: "2.8M points · 1,575 objects", href: "/lidarsample/?scene=medical-warehouse",
    model: "/home/media/medical-model.webp", scan: "/home/media/medical-scan.webp", alt: "Medical supply warehouse, reconstructed model", credit: "Scan from Niantic Spatial" },
];

const TEMPLATE = `
<section class="qstage">
  <div class="viz">
    <canvas class="qcv" aria-label="Your point cloud" role="img"></canvas>
    <img class="viz-poster" alt="" hidden />
    <div class="viz-hud"><span class="hud-tag">Preview</span><span class="hud-n"></span></div>
    <ul class="viz-legend">
      <li data-k="planar"><i></i>Walls, floors &amp; slabs</li>
      <li data-k="linear"><i></i>Pipes, ducts &amp; steel</li>
      <li data-k="scatter"><i></i>Equipment &amp; objects</li>
    </ul>
    <div class="viz-levels" aria-hidden="true"></div>
  </div>
  <aside class="panel">
    <div class="prep">
      <p class="eyebrow">Preparing your estimate</p>
      <h1 class="prep-h">Reading your scan</h1>
      <div class="pbar"><i></i></div>
      <p class="pmeta"><span class="pfile"></span><span class="ptime">00:00</span></p>
      <ol class="steps8"></ol>
      <p class="pnote" hidden></p>
    </div>
    <div class="est" hidden>
      <div class="est-top">
        <p class="eyebrow est-eb">Your estimate</p>
        <h2 class="est-h"></h2>
        <dl class="facts"></dl>
        <p class="lbl">What we'll model</p>
        <ul class="summary"></ul>
        <p class="lbl">Files you get back <span>· all included</span></p>
        <div class="chips fmt"></div>
      </div>
      <div class="est-pay">
        <p class="hold" hidden></p>
        <div class="price"><span class="price-v"></span><span class="price-s"></span></div>
        <a class="btn btn-white pay" href="https://movingatoms.ai/app/">Continue in the new app</a>
        <p class="refund">Payments for new scans now happen in the app.</p>
        <p class="qfine"><a href="/contact" data-cal>Talk to us</a><span class="valid"></span></p>
      </div>
    </div>
    <div class="qstate" hidden>
      <p class="eyebrow qs-eb"></p>
      <h1 class="qs-h"></h1>
      <p class="qs-s"></p>
      <ul class="qs-list"></ul>
      <div class="qcta qs-cta"></div>
    </div>
  </aside>
</section>
<section class="qwork" aria-labelledby="qworkH">
  <div class="sec-head">
    <div><p class="eyebrow">Previous work</p><h2 id="qworkH">Scans we've already turned into models</h2></div>
    <p class="sec-side">Each image sweeps between the raw scan and the model we delivered. Hover to compare, or open it in the 3D viewer.</p>
  </div>
  <div class="grid">${WORK.map((w) => `
    <a class="card" href="${w.href}" target="_blank" rel="noopener" data-compare>
      <div class="media">
        <img class="m-model" src="${w.model}" alt="${w.alt}" loading="lazy" />
        <img class="m-scan" src="${w.scan}" alt="" loading="lazy" />
        <span class="tag tag-l">Scan</span><span class="tag tag-r">Model</span>
        <span class="credit">${w.credit}</span>
        <i class="wipe" aria-hidden="true"></i>
      </div>
      <div class="meta"><div><h3>${w.title}</h3><p>${w.sub}</p></div><span class="go" aria-hidden="true">↗</span></div>
    </a>`).join("")}
  </div>
</section>
<div class="mock" hidden>
  <div class="mock-card" role="dialog" aria-modal="true">
    <p class="eyebrow">Test checkout</p>
    <h2>Pay <span class="mock-amt"></span></h2>
    <p class="mock-s">Local preview: Stripe isn't connected, so no card is charged. In production this is the Stripe Checkout page.</p>
    <div class="mock-card-f"><span>4242 4242 4242 4242</span><span>12 / 34</span><span>123</span></div>
    <div class="qcta"><button type="button" class="btn btn-white mock-pay">Pay (test)</button><button type="button" class="btn btn-ghost mock-cancel">Cancel</button></div>
  </div>
</div>`;

export function mount(root, { id, fresh = false, uploading = false, files = [], mockpay = null, checkout = null, sessionId = null } = {}) {
  root.innerHTML = TEMPLATE;
  const q = (s) => $(s, root);
  const steps = (uploading ? [UPLOAD] : []).concat(SHOW);
  const t0 = performance.now();
  let view = null, k = 0, kStart = t0, quoteReady = false, shown = false, previewOn = false, uploaded = !uploading, upPct = 0;
  let upText = "", stopped = false, scope = null, pollT = 0, lastStatus = "";

  // ── scene ────────────────────────────────────────────────────────────────
  const levelsBox = q(".viz-levels");
  let levelEls = [], levelsFor = null;
  const scene = createCloudView(q(".qcv"), {
    drive(now) {
      if (shown) return { i: 7, p: 1, final: true, dim: previewOn !== true };
      const s = steps[k], p = Math.min(1, (now - kStart) / Math.max(1, s[3]));
      if (s === UPLOAD) return { i: 0, p: Math.max(0.05, upPct), dim: true };
      if (s[2] === 0) return { i: previewOn ? 0 : 1, p: previewOn ? p : 0.15, dim: !previewOn };
      return { i: s[2], p: s[2] === 6 ? (now - kStart) / 6000 : p };
    },
    onFrame({ mvp, w, h, cloud, reveal, morph, st }) {
      if (levelsFor !== cloud) {
        levelsFor = cloud; levelsBox.innerHTML = "";
        levelEls = cloud.levels.map((z, i) => { const s = document.createElement("span"); s.textContent = "L" + (i + 1) + "  +" + (z - cloud.levels[0]).toFixed(1) + " m"; levelsBox.appendChild(s); return s; });
      }
      const on = st.i === 2 && !st.final && morph > 0.9;
      levelsBox.classList.toggle("on", on);
      if (on) {
        const hx = cloud.ext[0] / 2, hy = cloud.ext[1] / 2;
        let best = null;
        for (const c of [[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]]) { const s = project(mvp, [c[0], c[1], 0]); if (!best || s[0] > best.s[0]) best = { c, s }; }
        cloud.levels.forEach((z, i) => { const s = project(mvp, [best.c[0], best.c[1], z]); if (levelEls[i]) { levelEls[i].style.left = Math.min(w - 96, (s[0] * 0.5 + 0.5) * w) + "px"; levelEls[i].style.top = (0.5 - s[1] * 0.5) * h + "px"; } });
      }
      const n = Math.round((cloud.n - cloud.outN) * reveal), tot = view && view.features && view.features.points_total;
      q(".hud-n").textContent = num(n) + " pts" + (tot && previewOn ? " of " + num(tot) : "");
    },
  });
  if (scene.ok) { scene.setPlaceholder(); requestAnimationFrame(() => q(".qcv").classList.add("on")); }
  q(".hud-tag").textContent = uploading ? "Uploading" : "Sample geometry";

  async function loadPreview() {
    if (previewOn || !scene.ok) return;
    previewOn = "loading";
    try {
      const r = await fetch("/portal/api/estimate/" + encodeURIComponent(id) + "/preview", { credentials: "same-origin" });
      if (!r.ok) { previewOn = false; return; }
      scene.loadMAPV(await r.arrayBuffer(), true); scene.resetTint();
      previewOn = true; q(".hud-tag").textContent = "A sample of your scan";
      if (shown) Array.from(q(".viz-legend").children).forEach((li) => li.classList.add("on"));
    } catch (e) { console.error(e); previewOn = false; }
  }
  function showPoster() {
    const img = q(".viz-poster");
    if (!img.hidden) return;
    img.src = "/portal/api/estimate/" + encodeURIComponent(id) + "/poster"; img.hidden = false;
    const rcp = ((view && view.files) || files).some((f) => /\.rcp$/i.test(f.name));
    q(".qcv").classList.remove("on"); q(".hud-tag").textContent = rcp ? "Your ReCap project" : "Your video"; q(".viz-legend").hidden = true;
  }

  // ── steps panel ────────────────────────────────────────────────────────────
  const list = q(".steps8");
  list.innerHTML = steps.map((s) => `<li><span class="s-dot"></span><span class="s-l">${esc(s[0])}</span><span class="s-log"></span></li>`).join("");
  const lastLog = {};
  function logs(s, p) {
    const v = view || {}, f = v.features || {}, fl = (v.files || files || []).slice().sort((a, b) => b.size - a.size), big = fl[0];
    if (s === UPLOAD) return [upText || "Starting the upload"];
    switch (s[2]) {
      case 0: {
        const st = v.stage;
        if (!previewOn) return [st === "downloading" ? "Fetching your scan" + (big ? " · " + size(big.size) : "")
          : st === "unpacking" ? "Unpacking the archive" : st === "measuring" ? "Measuring " + (v.stageFile || (big ? big.name : "your scan"))
          : st === "preview" ? "Building the preview" : big ? "Opening " + big.name + " · " + size(big.size) : "Opening your upload"];
        return [f.points_total ? num(f.points_total) + " points indexed" : "Points indexed"];
      }
      case 1: return ["Matching overlap between scan positions", "Refining registration", "Scan positions locked"];
      case 2: { const c = scene.cloud, n = c && previewOn ? c.levels.length : 0;
        return ["Building a height histogram", n ? n + " horizontal slab" + (n > 1 ? "s" : "") + " found" : "Locating floor slabs", f.height_m ? f.height_m + " m floor to roof" : "Measuring storey heights"]; }
      case 3: return ["Fitting planes to surfaces", "Classifying walls, slabs and columns", f.share ? Math.round(f.share.planar * 100) + "% of the scan is surfaces" : "Surfaces classified"];
      case 4: return ["Following linear runs", f.linear_m_est ? "≈ " + num(f.linear_m_est) + " m of runs traced" : "Tracing pipes, ducts and steel", "Linear runs grouped"];
      case 5: return ["Clustering the remaining points", f.objects_est ? "≈ " + num(f.objects_est) + " objects separated" : "Separating equipment and furniture", "Objects separated"];
      case 6: { const notes = (v.agentNotes || []).map((x) => x.t).filter(Boolean); return notes.length ? notes.slice(-2) : ["Starting our estimating agent"]; }
      default: return ["Pricing the conversion", "Almost there"];
    }
  }
  function paintSteps(now) {
    const s = steps[k], p = Math.min(1, (now - kStart) / Math.max(1, s[3]));
    list.querySelectorAll("li").forEach((li, i) => {
      const cls = i < k || (shown && i === k) ? "ok" : i === k ? "now" : "";
      let html = "";
      if (i <= k) {
        const lines = logs(steps[i], i < k ? 1 : p);
        if (steps[i][2] === 6 && steps[i] !== UPLOAD) {
          const show = i < k ? lines.slice(-1) : lines;      // the agent's last few lines, newest last
          html = show.map((t, j) => `<span class="${j < show.length - 1 ? "old" : ""}">${esc(t)}</span>`).join("");
        } else {
          const idx = i < k ? lines.length - 1 : Math.min(lines.length - 1, Math.floor(p * lines.length));
          html = esc(lines[idx]);
        }
        if (cls === "now") html += '<i class="caret"></i>';
      }
      const key = cls + html;
      if (lastLog[i] !== key) { lastLog[i] = key; li.className = cls; $(".s-log", li).innerHTML = html; }
    });
    q(".prep-h").textContent = s[1];
    const prog = s === UPLOAD ? upPct * 0.35 : (uploading ? 0.35 : 0) + (k - (uploading ? 1 : 0) + p) / SHOW.length * (uploading ? 0.65 : 1);
    q(".pbar i").style.width = Math.min(quoteReady ? 100 : 96, prog * 100).toFixed(1) + "%";
    const sec = Math.floor((now - t0) / 1000);
    q(".ptime").textContent = String(Math.floor(sec / 60)).padStart(2, "0") + ":" + String(sec % 60).padStart(2, "0");
    const lg = q(".viz-legend").children, si = s[2];
    lg[0].classList.toggle("on", previewOn === true && si >= 3); lg[1].classList.toggle("on", previewOn === true && si >= 4); lg[2].classList.toggle("on", previewOn === true && si >= 5);
    const note = q(".pnote");
    if (s === steps.find((x) => x[2] === 0 && x !== UPLOAD) && !previewOn && now - kStart > 40000) {
      note.hidden = false; note.textContent = "Large scans take a few minutes to read. You can leave this page: your quote will be on your dashboard.";
    } else if (s[2] === 6 && now - kStart > 90000) {
      note.hidden = false; note.textContent = "Our agent is measuring the building in detail. This takes a few minutes on large scans; your quote will also be on your dashboard.";
    } else note.hidden = true;
  }
  // can the show leave step k?
  function canLeave(now) {
    const s = steps[k], v = view || {};
    if (now - kStart < (quoteReady && s[2] < 6 ? s[3] / 2.2 : s[3])) return false;
    if (s === UPLOAD) return uploaded;
    if (s[2] === 0) return previewOn === true || (quoteReady && previewOn !== "loading");
    if (s[2] === 6) return quoteReady;
    return true;
  }
  function tick(now) {
    if (stopped) return;
    requestAnimationFrame(tick);
    if (shown) return;
    if (canLeave(now)) {
      if (k === steps.length - 1) { finishShow(); return; }
      k++; kStart = now;
    }
    paintSteps(now);
  }

  // ── result ─────────────────────────────────────────────────────────────────
  function finishShow() {
    if (shown) return; shown = true;
    paintSteps(performance.now());
    root.querySelector(".viz").classList.add("is-done");
    if (previewOn === true) { q(".hud-tag").textContent = "A sample of your scan"; Array.from(q(".viz-legend").children).forEach((li) => li.classList.add("on")); }
    else if (q(".viz-poster").hidden) { q(".hud-tag").textContent = "No scan geometry yet"; q(".viz-legend").hidden = true; }
    setTimeout(() => { q(".prep").hidden = true; render(); }, 380);
  }
  function stateOnly(eb, h, s, cta, items = []) {
    q(".prep").hidden = true; q(".est").hidden = true; const box = q(".qstate"); box.hidden = false;
    q(".qs-eb").textContent = eb; q(".qs-h").textContent = h; q(".qs-s").textContent = s; q(".qs-cta").innerHTML = cta;
    q(".qs-list").innerHTML = items.map((x) => `<li><b>${esc(x.name)}</b>${esc(x.message)}</li>`).join("");
  }
  function render() {
    const v = view, st = v.status;
    if ((st === "quoted" || st === "quote_review") && v.quote) return renderQuote();
    if (st === "needs_info" || st === "declined") {
      return stateOnly("Your upload", "We need a hand with this one", (v.skipped || []).length ? "Here's what we found in your upload:" : v.message || "We couldn't measure this upload automatically.",
        '<a class="btn btn-white" href="/#up">Upload another file</a><a class="btn btn-ghost" href="/contact" data-cal>Talk to us</a>', v.skipped || []);
    }
    if (st === "expired") {
      stateOnly("Your estimate", "This quote has expired", "Quotes are valid for 14 days. Talk to us and we'll refresh it.", '<a class="btn btn-white" href="/contact" data-cal>Talk to us</a>');
      return;
    }
    if (["paid", "modelling", "accepted", "delivered"].includes(st)) {
      const pm = v.payment || {};
      const links = [pm.receipt_url ? `<a href="${esc(pm.receipt_url)}" target="_blank" rel="noopener">Receipt</a>` : "",
        pm.invoice_url ? `<a href="${esc(pm.invoice_url)}" target="_blank" rel="noopener">Invoice</a>` : ""].filter(Boolean).join(" · ");
      stateOnly("Paid" + (pm.amount_usd ? " · " + usd(pm.amount_usd) : ""), st === "delivered" ? "Your model is ready" : "Payment received",
        st === "delivered" ? "Download it from your dashboard." : "Thank you. Modelling has started" + (pm.due ? ", and your model will be delivered by " + when(pm.due) + "." : ". Your model will be delivered within 48 hours."),
        `<a class="btn btn-white" href="/dashboard/?paid=${encodeURIComponent(id)}">Follow it on your dashboard</a>`);
      q(".qstate").classList.add("is-paid");
      if (links) q(".qs-list").innerHTML = `<li class="qs-links">${links}<span>A confirmation email is on its way.</span></li>`;
      return;
    }
    if (st === "payment_processing") {
      return stateOnly("Payment processing", "Your payment is on its way", v.message || "Bank transfers take 1–4 working days. We start the moment it clears and email you when we do.",
        '<a class="btn btn-white" href="/dashboard/">Go to dashboard</a>');
    }
    stateOnly("Your upload", "Still measuring", "This is taking longer than usual. Your quote will appear on your dashboard.", '<a class="btn btn-white" href="/dashboard/">Go to dashboard</a>');
  }
  function renderQuote() {
    const v = view, qt = v.quote, f = v.features || {};
    q(".qstate").hidden = true; q(".est").hidden = false;
    q(".est-h").textContent = qt.class_label || f.class_label || "Your building";
    const pts = f.points_total ? (f.points_total >= 1e6 ? (f.points_total / 1e6).toFixed(1) + "M" : num(f.points_total)) : "–";
    const area = qt.area_sqft >= 100000 ? Math.round(qt.area_sqft / 1000) + "k" : num(qt.area_sqft);
    q(".facts").innerHTML = [["Floor area", area + "<small> sq ft</small>"], ["Levels", esc(qt.levels || f.floors || "–")],
      ["Detail", "LOD " + esc(qt.display_lod || qt.scope.lod)], ["Points", pts]].map((x) => `<div><dt>${x[0]}</dt><dd>${x[1]}</dd></div>`).join("");
    const sum = qt.summary && qt.summary.length ? qt.summary : [
      "Walls, floors, roofs, doors and windows", "Columns, beams and slabs", "Visible pipes, ducts and major equipment"];
    q(".summary").innerHTML = sum.map((t) => `<li>${esc(t)}</li>`).join("");
    scope = scope || (v.outputs || ["revit"]).slice();
    q(".fmt").innerHTML = v.options.outputs.map((o) => `<button type="button" data-v="${o}" aria-pressed="${scope.includes(o)}">${esc(OUT[o] || o)}</button>`).join("");
    paintPrice();
  }
  function paintPrice() {
    const v = view, qt = v.quote, held = qt.held;
    q(".price-v").textContent = usd(qt.price_usd);
    const confirming = held && qt.hold_reason === "confirm";
    q(".price-s").textContent = confirming ? "estimate · confirming now" : held ? "estimated" : "fixed price · 48 h delivery · 1 revision round";
    const reasons = (qt.hold_reason || "").split(",").filter(Boolean);
    const hold = q(".hold"); hold.hidden = !held; hold.textContent = reasons.map((r) => HOLD[r]).filter(Boolean)[0] || "We'll confirm this price within a few hours.";
    // payments moved to the app (movingatoms.ai/app, 2026-10-22): the button is a link there, nothing is paid here
    q(".valid").textContent = "";
    if (checkout === "cancel" && !held) { const h = q(".hold"); h.hidden = false; h.textContent = "Checkout closed. Nothing was charged, and your quote is still here when you're ready."; }
    if (checkout === "unavailable") { const h = q(".hold"); h.hidden = false; h.textContent = "That payment link can't be used for this quote any more. Use the button below, or talk to us."; }
    q(".est-eb").textContent = held ? "Your estimate · being confirmed" : "Your estimate";
  }
  q(".fmt").addEventListener("click", async (e) => {
    const b = e.target.closest("button"); if (!b || !scope) return;
    const o = b.dataset.v, on = scope.includes(o);
    if (on && scope.length === 1) return;
    scope = on ? scope.filter((x) => x !== o) : scope.concat(o);
    b.setAttribute("aria-pressed", String(!on));
    try { view = { ...view, ...(await api("/estimate/" + encodeURIComponent(id) + "/scope", { scope: { outputs: scope } })) }; } catch (err) { console.error(err); }
  });
  function openMock() {
    const m = q(".mock"); m.hidden = false;
    q(".mock-amt").textContent = view && view.quote ? usd(view.quote.price_usd) : "";
    q(".mock-cancel").onclick = () => { m.hidden = true; history.replaceState(null, "", "/quote/?id=" + encodeURIComponent(id)); };
    q(".mock-pay").onclick = async function () {
      this.disabled = true; this.textContent = "Processing…";
      try { await api("/dev/mockpay/" + encodeURIComponent(mockpay), {}); location.href = "/dashboard/?paid=" + encodeURIComponent(id); }
      catch (e) { this.textContent = e.message; }
    };
  }

  // ── polling ────────────────────────────────────────────────────────────────
  async function poll() {
    clearTimeout(pollT);
    if (stopped) return;
    try {
      view = await api("/estimate/" + encodeURIComponent(id));
    } catch (e) {
      if (e.status === 401) return stateOnly("Your estimate", "Sign in to see your estimate", "Use the email you uploaded with.", '<a class="btn btn-white" href="/dashboard/">Sign in</a>');
      if (e.status === 404 && !uploaded) { pollT = setTimeout(poll, 3000); return; }
      if (e.status === 404) return stateOnly("Your estimate", "We couldn't find this upload", "It may belong to a different account.", '<a class="btn btn-white" href="/dashboard/">Go to dashboard</a>');
      pollT = setTimeout(poll, 5000); return;
    }
    if (view.status === "uploading" && !uploading) {
      return stateOnly("Your upload", "This upload didn't finish", "Upload the files again from the homepage: new uploads now open as a project in the Moving Atoms app.", '<a class="btn btn-white" href="/#up">Upload again</a>');
    }
    if (["reviewing", "needs_info", "declined"].includes(view.status)) {
      if (!uploaded) { pollT = setTimeout(poll, 3000); return; }
      return location.replace("/dashboard/?new=" + encodeURIComponent(id));   // we follow up by email
    }
    if (view.preview) loadPreview();
    if (view.poster) showPoster();
    if (DONE.includes(view.status)) {
      if (!quoteReady) {
        quoteReady = true;
        if (!fresh && !uploading && !shown) { k = steps.length - 1; finishShow(); }   // revisiting: skip the show
        if (mockpay) openMock();
      }
      if (["needs_info", "declined"].includes(view.status) && !shown) { k = steps.length - 1; finishShow(); }
      // re-render on any change (e.g. the thorough check turns "confirming" into a payable price)
      const sig = view.status + "|" + (view.quote ? view.quote.price_usd + view.quote.hold_reason : "");
      if (shown && lastStatus && sig !== lastStatus) render();
      lastStatus = sig;
      const confirming = view.status === "quote_review" && view.quote && view.quote.hold_reason === "confirm";
      if (["quote_review", "paid", "accepted", "modelling", "payment_processing"].includes(view.status)) pollT = setTimeout(poll, confirming ? 5000 : 15000);
      return;
    }
    pollT = setTimeout(poll, view.stage === "agent" ? 1500 : 2500);
  }

  // back from Stripe Checkout: the server verifies the payment with Stripe (never trusts the URL)
  async function confirmReturn() {
    k = steps.length - 1; shown = true; root.querySelector(".viz").classList.add("is-done");
    q(".prep").hidden = true;
    stateOnly("Payment", "Confirming your payment…", "Checking with Stripe. This takes a moment.", "");
    for (let attempt = 0; attempt < 5; attempt++) {     // Stripe redirects after the charge, so "paid" is normally immediate
      try {
        const r = await api("/checkout/" + encodeURIComponent(id) + "/confirm", { session_id: sessionId });
        view = r; if (r.preview) loadPreview(); if (r.poster) showPoster();
        if (r.checkout === "paid" || r.checkout === "processing" || ["paid", "payment_processing", "modelling", "delivered"].includes(r.status)) {
          history.replaceState(null, "", "/quote/?id=" + encodeURIComponent(id)); return render();
        }
        if (r.checkout === "mismatch" || r.checkout === "duplicate") {
          return stateOnly("Payment", "We've received your payment", "We're checking one detail before we start, and we'll email you within a few hours.", '<a class="btn btn-white" href="/dashboard/">Go to dashboard</a>');
        }
      } catch (e) { if (e.status === 401) return stateOnly("Payment", "Sign in to see your payment", "Use the email you paid with.", '<a class="btn btn-white" href="/dashboard/">Sign in</a>'); }
      await new Promise((res) => setTimeout(res, 800 + attempt * 500));
    }
    history.replaceState(null, "", "/quote/?id=" + encodeURIComponent(id));
    view = await api("/estimate/" + encodeURIComponent(id)).catch(() => view);
    if (view && view.quote && view.status === "quoted") { renderQuote(); const h = q(".hold"); h.hidden = false; h.textContent = "We haven't received a payment yet. If you were charged, it will show here within a few minutes."; return; }
    render();
  }

  // previous work: each card sweeps scan ↔ model on its own while on screen; the pointer takes over on hover
  const cards = Array.from(root.querySelectorAll(".qwork [data-compare]")), live = new Set(), held = new Set();
  cards.forEach((card, i) => {
    const media = $(".media", card); card.classList.add("comparing"); card.dataset.phase = i * 1.3;
    media.addEventListener("pointermove", (e) => { if (e.pointerType !== "mouse") return; held.add(card);
      const r = media.getBoundingClientRect(); media.style.setProperty("--x", Math.max(0, Math.min(100, (e.clientX - r.left) / r.width * 100)).toFixed(2) + "%"); });
    media.addEventListener("pointerleave", () => held.delete(card));
  });
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting ? live.add(e.target) : live.delete(e.target)), { threshold: 0.2 });
    cards.forEach((c) => io.observe(c));
  } else cards.forEach((c) => live.add(c));
  (function sweep(t) {
    if (stopped) return;
    live.forEach((c) => { if (!held.has(c)) $(".media", c).style.setProperty("--x", (50 + 42 * Math.sin(t / 1600 + Number(c.dataset.phase))).toFixed(2) + "%"); });
    requestAnimationFrame(sweep);
  })(0);

  requestAnimationFrame(tick);
  if (checkout === "success" && sessionId) { quoteReady = true; confirmReturn(); }
  else if (uploaded) poll();
  return {
    upload(pct, sent, total) { upPct = pct; upText = "Uploading " + Math.floor(pct * 100) + "% · " + size(sent) + " of " + size(total); },
    uploaded() { uploaded = true; upPct = 1; upText = "Upload complete"; q(".hud-tag").textContent = "Reading"; poll(); },
    uploadError(msg, retry) {
      upText = msg;
      const note = q(".pnote"); note.hidden = false; note.innerHTML = esc(msg) + ' <button type="button" class="linkish">Try again</button>';
      note.querySelector("button").onclick = () => { note.hidden = true; retry && retry(); };
    },
    destroy() { stopped = true; clearTimeout(pollT); scene.destroy && scene.destroy(); },
  };
}

// standalone page: /quote/?id=…
const auto = document.getElementById("qroot");
if (auto && auto.dataset.auto !== undefined) {
  const params = new URLSearchParams(location.search), id = params.get("id");
  if (!id) auto.innerHTML = '<div class="qstate"><p class="eyebrow">Your estimate</p><h1>No upload selected</h1><div class="qcta"><a class="btn btn-white" href="/dashboard/">Go to dashboard</a></div></div>';
  else {
    const checkout = params.get("checkout");
    if (checkout === "success" && params.get("session_id")) {     // payments now return to the dashboard
      location.replace("/dashboard/?paid=" + encodeURIComponent(id) + "&session_id=" + encodeURIComponent(params.get("session_id")));
    }
    mount(auto, { id, fresh: params.has("new") && !checkout, mockpay: params.get("mockpay"), checkout, sessionId: params.get("session_id") });
    if (checkout === "cancel" || checkout === "unavailable") history.replaceState(null, "", "/quote/?id=" + encodeURIComponent(id));
  }
}
