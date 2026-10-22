/* Moving Atoms homepage, v2.
 *
 * 1. The hero composer is a real uploader: the same resumable browser -> R2 multipart flow as /upload
 *    (create, sign, PUT parts, list, complete, finish on /upload/api). Drop files on the box or anywhere
 *    on the page. On localhost the part PUTs go through the dev server (/__r2put), because the R2 bucket's
 *    CORS rule only admits movingatoms.ai.
 * 2. Example cards: hover to wipe from the raw scan to the model. Touch screens get a slow automatic sweep.
 */
(function () {
  "use strict";

  // ── uploader ─────────────────────────────────────────────────────────────
  var API = "/upload/api";
  var LOCAL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  var CONCURRENCY = 4, PART_RETRIES = 6, SIGN_BATCH = 100;
  var LS_PREFIX = "ma_up_", LS_TTL = 7 * 864e5;   // 7 days, matching the bucket's abort-incomplete rule
  // Mirrors ALLOWED_EXT in the upload API, so a bad file is caught before any request.
  var ALLOWED = (".e57 .las .laz .pts .ptx .pcd .ply .xyz .rcp .rcs .pod .zfs .fls .lcc .lgsx .rdbx .bpf " +
    ".obj .fbx .glb .gltf .stl .usd .usda .usdc .usdz .dae .3ds .x3d .3mf .blend .abc .drc " +
    ".ifc .rvt .rfa .step .stp .iges .igs .dwg .dxf .skp .3dm " +
    ".zip .7z .rar .tar .gz .tgz .bz2 .xz .zst " +
    ".mp4 .mov .webm .mkv .avi .insv .360 .jpg .jpeg .png .tif .tiff .exr .heic .webp .pdf .csv .json .txt").split(" ");

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var form = $("#up"), fileInput = $("#file"), drop = $("#drop"), filesUl = $("#files"),
      who = $("#who"), auth = $("#auth"), send = $("#send"), status = $("#status"),
      msg = $("#msg"), sendLabel = $("#sendLabel"), done = $("#done");
  if (!form) return;

  var items = [], running = false, submissionId = null;

  // ── the platform hand-off (movingatoms.ai/app, CONTRACTS §19) ─────────────────────────────────────
  // When it is on, sign-in is the app's emailed code and "Get quote" turns this page into the visitor's project at
  // /app/p/<id> in place: /app/onboard.js creates the project with the scope picked here, starts the upload into it and
  // mounts the app over the page (Back shows the page again, the upload still running). HANDOFF_LIVE turns it on for
  // everyone (since 2026-10-22); ?app=0 turns it off in this browser (the old portal flow), ?app=1 back on.
  var HANDOFF_LIVE = true;
  var HANDOFF = (function () {
    try {
      var q = new URLSearchParams(location.search).get("app");
      if (q === "1" || q === "0") localStorage.setItem("ma_app_handoff", q);
      var v = localStorage.getItem("ma_app_handoff");
      return v === "1" || (HANDOFF_LIVE && v !== "0");
    } catch (e) { return HANDOFF_LIVE; }
  })();
  var obLoad = null, handedOff = null;
  function onboard() {
    return obLoad || (obLoad = import("/app/onboard.js").catch(function (e) {
      obLoad = null; console.error(e);
      throw new Error("We couldn't reach Moving Atoms. Check your connection and try again.");
    }));
  }
  function appShown() { return document.documentElement.classList.contains("ma-app-on"); }

  function uuid() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0; return (c === "x" ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
  function fmt(b) {
    if (b >= 1e9) return (b / 1e9).toFixed(2) + " GB";
    if (b >= 1e6) return (b / 1e6).toFixed(1) + " MB";
    if (b >= 1e3) return (b / 1e3).toFixed(0) + " KB";
    return b + " B";
  }
  function ext(name) { var i = name.lastIndexOf("."); return i < 0 ? "" : name.slice(i).toLowerCase(); }
  function fp(f) { return [f.name, f.size, f.lastModified].join("|"); }
  function lsGet(f) {
    try {
      var r = JSON.parse(localStorage.getItem(LS_PREFIX + fp(f)) || "null");
      if (r && Date.now() - r.ts < LS_TTL) return r;
    } catch (e) {}
    return null;
  }
  function lsSet(f, rec) { try { rec.ts = Date.now(); localStorage.setItem(LS_PREFIX + fp(f), JSON.stringify(rec)); } catch (e) {} }
  function lsDel(f) { try { localStorage.removeItem(LS_PREFIX + fp(f)); } catch (e) {} }

  async function call(path, body) {
    var r = await fetch(API + path, body === undefined ? undefined : {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body)
    });
    var j = await r.json().catch(function () { return {}; });
    if (!r.ok || j.ok !== true) {
      var error = new Error(j.error || ("request failed (" + r.status + ")"));
      error.status = r.status; throw error;
    }
    return j;
  }
  function listPath(key, uploadId, sid) {
    return "/list?key=" + encodeURIComponent(key) + "&uploadId=" + encodeURIComponent(uploadId) +
      "&submissionId=" + encodeURIComponent(sid);
  }

  // file list
  function addFiles(list) {
    if (running || form.classList.contains("is-done")) return;
    var rejected = [];
    Array.prototype.forEach.call(list, function (f) {
      if (ALLOWED.indexOf(ext(f.name)) < 0) { rejected.push(f.name); return; }
      if (items.some(function (it) { return fp(it.file) === fp(f); })) return;
      var li = document.createElement("li");
      li.className = "file";
      li.innerHTML = '<span class="file-ico"></span><span class="file-name"></span><span class="file-size"></span>' +
        '<button type="button" class="file-x" aria-label="Remove">&times;</button><span class="file-bar"><i></i></span>';
      $(".file-ico", li).textContent = (ext(f.name).slice(1) || "file").slice(0, 4);
      $(".file-name", li).textContent = f.name;
      $(".file-size", li).textContent = fmt(f.size);
      var it = { file: f, el: li, bar: $(".file-bar i", li), uploaded: 0, total: f.size, done: false };
      $(".file-x", li).addEventListener("click", function (e) {
        e.stopPropagation();
        if (running) return;
        items = items.filter(function (x) { return x !== it; });
        li.remove(); refresh();
      });
      items.push(it);
      filesUl.insertBefore(li, $(".add-more", filesUl));
    });
    note(rejected.length ? "We can't take " + rejected.join(", ") + ". Zip it, or send point clouds, meshes, CAD or archives." : "");
    if (items.length && !$(".add-more", filesUl)) {
      var more = document.createElement("li");
      more.className = "add-more";
      more.innerHTML = '<button type="button">Add more files</button>';
      more.firstChild.addEventListener("click", function (e) { e.stopPropagation(); fileInput.click(); });
      filesUl.appendChild(more);
    }
    refresh();
  }

  function totals() {
    var tot = 0, up = 0;
    items.forEach(function (it) { tot += it.total; up += it.done ? it.total : it.uploaded; });
    return { tot: tot, up: up };
  }
  function refresh() {
    var t = totals();
    form.classList.toggle("has-files", items.length > 0);
    form.classList.toggle("running", running);
    form.classList.toggle("handing", running && HANDOFF);
    if (!items.length) { $(".add-more", filesUl) && $(".add-more", filesUl).remove(); }
    send.disabled = running || (!items.length && !handedOff);
    Array.prototype.forEach.call(who.querySelectorAll("input, select"), function (el) { el.disabled = running; });
    items.forEach(function (it) { $(".file-x", it.el).disabled = running || !!handedOff; });
    var pct = t.tot ? t.up / t.tot : 0;
    if (quoteCtl && running) quoteCtl.upload(pct, t.up, t.tot);
    send.style.setProperty("--p", (pct * 100).toFixed(1) + "%");
    sendLabel.textContent = running ? (HANDOFF ? "Opening your project…" : "Uploading " + Math.floor(pct * 100) + "%") : handedOff ? "Back to your project" : "Start model";
    status.textContent = !items.length ? "" : handedOff ? "Uploading into your project" : running && HANDOFF ? "" : running
      ? "Uploading " + Math.floor(pct * 100) + "% · " + fmt(t.up) + " of " + fmt(t.tot)
      : items.length + " file" + (items.length > 1 ? "s" : "") + " · " + fmt(t.tot);
  }
  function setBar(it) { it.bar.style.width = (it.total ? Math.min(100, it.uploaded / it.total * 100) : 100).toFixed(1) + "%"; }
  function note(t) { msg.textContent = t; }
  function markDone(it, sid) { it.done = true; it.uploaded = it.total; it._sub = sid; setBar(it); it.el.classList.add("is-done"); return sid; }

  // one part, straight to R2 (or through the dev server on localhost). Some company networks block the storage
  // domain: if direct parts fail before any has succeeded, or nothing moves for 45 s, parts are relayed through
  // movingatoms.ai instead (/upload/api/part), which those networks allow since they load the site.
  var viaProxy = false, directOk = false, directFails = 0, lastErr = "", lastProgressAt = 0, partsDone = 0, liveXhrs = [];
  function switchToProxy(why) {
    if (viaProxy) return;
    viaProxy = true; lastErr = why || lastErr; report();
    liveXhrs.slice().forEach(function (x) { x.abort(); });   // their retries go through the relay
  }
  function putPart(url, blob, onChunk, relayUrl) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest(), last = 0, relayed = viaProxy || !url;
      var done = function () { liveXhrs = liveXhrs.filter(function (x) { return x !== xhr; }); };
      xhr.open("PUT", relayed ? relayUrl : (LOCAL ? "/__r2put?u=" + encodeURIComponent(url) : url), true);
      xhr.upload.onprogress = function (e) { if (e.lengthComputable) { lastProgressAt = Date.now(); onChunk(e.loaded - last); last = e.loaded; } };
      xhr.onload = function () {
        done();
        if (xhr.status >= 200 && xhr.status < 300) { if (!relayed) directOk = true; partsDone++; lastProgressAt = Date.now(); onChunk(blob.size - last); resolve(); }
        else {
          lastErr = (relayed ? "relay" : "storage") + " HTTP " + xhr.status;
          if (!relayed && !directOk && ++directFails >= 2) switchToProxy(lastErr);
          reject(new Error("part HTTP " + xhr.status));
        }
      };
      xhr.onerror = function () {
        done(); lastErr = relayed ? "relay network error" : "network error reaching storage";
        if (!relayed && !directOk && ++directFails >= 2) switchToProxy(lastErr);
        reject(new Error("network error"));
      };
      xhr.onabort = function () { done(); reject(new Error("aborted")); };
      liveXhrs.push(xhr); xhr.send(blob);
    });
  }
  // the browser is our only view of an upload in flight: report it every 10 s (the team is told if it's in trouble)
  var reportT = 0;
  function report() {
    if (!submissionId) return;
    var t = totals();
    fetch("/portal/api/upload-progress", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
      body: JSON.stringify({ submissionId: submissionId, sent: t.up, total: t.tot, mode: viaProxy ? "proxy" : "direct", parts: partsDone, error: lastErr || null }) }).catch(function () {});
  }
  function watch(on) {
    clearInterval(reportT);
    if (!on) return report();
    lastProgressAt = Date.now();
    reportT = setInterval(function () {
      report();
      if (!viaProxy && !directOk && Date.now() - lastProgressAt > 45000) switchToProxy("no upload progress to storage for 45 s");
    }, 10000);
  }

  async function uploadFile(it, submitter) {
    var f = it.file, rec = lsGet(f), partSize, key, uploadId, mySub;
    it.uploaded = 0; it.el.classList.remove("is-err"); setBar(it); refresh();

    // resume an existing multipart upload if the server still has it
    if (rec) {
      try {
        var resumed = await call(listPath(rec.key, rec.uploadId, rec.submissionId));
        if (resumed.complete) {
          if (resumed.size !== f.size) throw new Error("stored file size does not match");
          lsSet(f, rec);
          return markDone(it, rec.submissionId);
        }
        key = rec.key; uploadId = rec.uploadId; partSize = rec.partSize; mySub = rec.submissionId;
      } catch (e) {
        if (e.status !== 404) throw e;   // a temporary outage must not discard resumable work
        lsDel(f); rec = null;
      }
    }
    if (!rec) {
      var c = await call("/create", {
        submissionId: submissionId, submitter: submitter, scope: submitter.scope,
        file: { name: f.name, size: f.size, type: f.type || "application/octet-stream" }
      });
      key = c.key; uploadId = c.uploadId; partSize = c.partSize; mySub = c.submissionId;
      lsSet(f, { key: key, uploadId: uploadId, partSize: partSize, submissionId: mySub });
    }

    var total = Math.max(1, Math.ceil(f.size / partSize));
    var have = {};
    ((await call(listPath(key, uploadId, mySub))).parts || []).forEach(function (p) { have[p.PartNumber] = p.Size; });
    var pending = [];
    for (var n = 1; n <= total; n++) {
      var expected = n < total ? partSize : f.size - partSize * (total - 1);
      if (have[n] === expected) it.uploaded += expected; else pending.push(n);
    }
    setBar(it);

    var urlCache = {}, signing = null;
    async function urlFor(n) {
      if (urlCache[n]) return urlCache[n];
      if (signing) { await signing; return urlFor(n); }
      var batch = [];
      for (var i = 0; i < pending.length && batch.length < SIGN_BATCH; i++) if (!urlCache[pending[i]]) batch.push(pending[i]);
      if (batch.indexOf(n) < 0) batch.unshift(n);
      signing = call("/sign", { key: key, uploadId: uploadId, parts: batch }).then(function (s) {
        Object.keys(s.urls).forEach(function (k) { urlCache[k] = s.urls[k]; });
      });
      try { await signing; } finally { signing = null; }
      if (!urlCache[n]) throw new Error("no upload URL returned for part " + n);
      return urlCache[n];
    }
    function relayUrl(n) {
      return "/upload/api/part?submissionId=" + encodeURIComponent(mySub) + "&key=" + encodeURIComponent(key) +
        "&uploadId=" + encodeURIComponent(uploadId) + "&partNumber=" + n;
    }
    async function runPart(n) {
      var start = (n - 1) * partSize, blob = f.slice(start, Math.min(f.size, start + partSize));
      for (var attempt = 0; attempt <= PART_RETRIES; attempt++) {
        var sent = 0;
        try {
          var url = viaProxy ? null : await urlFor(n);
          await putPart(url, blob, function (d) { sent += d; it.uploaded += d; setBar(it); refresh(); }, relayUrl(n));
          return;
        } catch (e) {
          it.uploaded = Math.max(0, it.uploaded - sent); setBar(it); refresh();   // failed bytes don't count
          delete urlCache[n];                                                    // maybe expired: re-sign
          if (attempt === PART_RETRIES) throw new Error("part " + n + ": " + e.message);
          await new Promise(function (r) { setTimeout(r, Math.min(15000, 800 * Math.pow(2, attempt))); });
        }
      }
    }
    var queue = pending.slice();
    async function worker() { while (queue.length) await runPart(queue.shift()); }
    var workers = [];
    for (var w = 0; w < Math.min(CONCURRENCY, queue.length); w++) workers.push(worker());
    await Promise.all(workers);

    // authoritative part list straight from R2, then complete
    var parts = (await call(listPath(key, uploadId, mySub))).parts || [];
    parts.sort(function (a, b) { return a.PartNumber - b.PartNumber; });
    if (parts.length !== total || parts.some(function (p, i) {
      return p.PartNumber !== i + 1 || p.Size !== Math.min(partSize, f.size - i * partSize);
    })) throw new Error("some parts did not arrive. Press upload again to resume");
    await call("/complete", {
      submissionId: mySub, key: key, uploadId: uploadId, file: { name: f.name, size: f.size },
      parts: parts.map(function (p) { return { PartNumber: p.PartNumber, ETag: p.ETag }; })
    });
    return markDone(it, mySub);
  }

  // the old portal's submission (?app=0 only): the scope at its old defaults (the app asks for it in the project now)
  function readForm() {
    var w = whoValues();
    return {
      // the server stamps the email from the signed-in session
      name: (me && me.name) || w.name, email: (me && me.email) || "", company: (me && me.company) || w.company,
      scanner: "", siteType: "", website: form.elements.website.value || "",
      notes: w.role ? "Role: " + w.role : "",
      scope: { lod: 350, outputs: ["revit"] }
    };
  }
  function whoValues() {
    var el = form.elements;
    return { email: el.email.value.trim(), name: el.name.value.trim(), company: el.company.value.trim(), role: el.role.value };
  }

  async function run() {
    if (running) return;
    if (handedOff) return backToProject();
    if (!items.length) return fileInput.click();
    if (form.elements.website.value) return;
    if (!me) await whoami();
    if (!me) return askCode();
    auth.hidden = true;
    if (HANDOFF) return handoff();
    var sub = readForm();
    submissionId = submissionId || uuid();
    var quotable = items.some(function (it) { return canQuote(it.file.name); });
    if (quotable) await enterQuote(submissionId);
    running = true; note(""); refresh(); watch(true);
    var subs = {}, failed = false;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (it.done) { subs[it._sub] = 1; continue; }
      try { subs[await uploadFile(it, sub)] = 1; }
      catch (e) {
        failed = true; it.el.classList.add("is-err");
        if (e.status === 401) { me = null; running = false; refresh(); watch(false); setAccount(); return askCode(); }
        note("“" + it.file.name + "”: " + e.message + ". Press upload again and it will resume.");
        if (quoteCtl) quoteCtl.uploadError("“" + it.file.name + "” didn't finish uploading: " + e.message + ".", run);
      }
      refresh();
    }
    try {
      for (var k in subs) if (k && k !== "undefined") await call("/finish", { submissionId: k });
    } catch (e) {
      failed = true;
      note("Your files arrived, but confirming the submission failed: " + e.message + ". Press upload again to retry.");
      if (quoteCtl) quoteCtl.uploadError("Your files arrived, but confirming them failed: " + e.message + ".", run);
    }
    running = false; refresh(); watch(false);
    if (failed) return;
    if (quoteCtl) {
      items.forEach(function (it) { lsDel(it.file); });
      var real = Object.keys(subs).filter(function (k) { return k && k !== "undefined"; })[0];
      if (real && real !== submissionId) { location.href = "/quote/?new=1&id=" + encodeURIComponent(real); return; }   // resumed an older upload
      return quoteCtl.uploaded();
    }
    var t = totals(), first = Object.keys(subs)[0] || "";
    items.forEach(function (it) { lsDel(it.file); });
    $("#doneSub").textContent = "We received " + items.length + " file" + (items.length > 1 ? "s" : "") + " (" + fmt(t.tot) +
      (quotable ? "). Preparing your estimate…" : "). We'll review them and email you.");
    form.classList.add("is-done"); done.hidden = false;
    setTimeout(function () { location.href = quotable ? "/quote/?new=1&id=" + encodeURIComponent(first) : "/dashboard/?new=" + encodeURIComponent(first); }, 1400);
  }

  // the hand-off: the project, its upload and the app over this page (the estimate and the paywall are in the app)
  async function handoff() {
    running = true; note(""); refresh();
    try {
      var ob = await onboard();
      var r = await ob.handoff({ files: items.map(function (it) { return it.file; }) });
      handedOff = r.projectId;
    } catch (e) {
      running = false; refresh();
      if (e && e.status === 401) { me = null; setAccount(); return askCode(); }
      return note((e && e.message) || "Something went wrong. Try again.");
    }
    running = false; refresh();
  }
  function backToProject() { onboard().then(function (ob) { return ob.show(); }).catch(function () { location.href = "/app/p/" + handedOff; }); }
  // Back from the project: the box says where the files went, and its button goes back to them
  addEventListener("movingatoms:app", function (e) {
    if (!e.detail || e.detail.shown) return;
    form.classList.add("is-done"); done.hidden = false;
    $(".done-title", done).textContent = "Your project is open";
    $("#doneSub").textContent = "Your upload and your estimate carry on while you look around.";
    $("#again").textContent = "Back to your project";
  });

  // formats the estimator prices automatically (tools/estimator/worker.py KIND); archives are opened and checked there.
  // Anything else (CAD, scanner-native, video, a lone .rcp) skips the estimate: dashboard, and we follow up by email.
  var QUOTABLE = (".las .laz .ply .e57 .xyz .pts .txt .csv .pcd .ptx .rcs .glb .gltf .obj .stl .fbx .dae .3ds .x3d .3mf " +
    ".usd .usda .usdc .usdz .zip .7z .rar .tar .gz .tgz .bz2 .xz .zst").split(" ");
  function canQuote(name) { return QUOTABLE.indexOf(ext(name)) >= 0; }

  // ── hand-off: "Get quote" turns the page into the live estimate while the files upload ─────
  // (quote/quote.js; the upload keeps running here and feeds it progress; the URL becomes /quote/?id=…)
  var quoteCtl = null;
  async function enterQuote(id) {
    if (quoteCtl) return quoteCtl;
    try {
      if (!document.querySelector('link[href^="/quote/quote.css"]')) {
        var l = document.createElement("link"); l.rel = "stylesheet"; l.href = "/quote/quote.css?v=7"; document.head.appendChild(l);
      }
      var m = await import("/quote/quote.js?v=16");
      var root = document.createElement("main"); root.className = "qwrap qhome"; root.id = "qroot";
      $(".nav").after(root);
      document.body.classList.add("quoting");
      document.documentElement.style.setProperty("--ann-h", "0px");
      scrollTo(0, 0);
      history.pushState({ quote: id }, "", "/quote/?new=1&id=" + encodeURIComponent(id));
      addEventListener("popstate", function () { location.reload(); });
      quoteCtl = m.mount(root, { id: id, fresh: true, uploading: true,
        files: items.map(function (it) { return { name: it.file.name, size: it.file.size }; }) });
    } catch (e) { console.error(e); quoteCtl = null; }   // fall back to uploading on the homepage
    return quoteCtl;
  }

  // ── account: email + one-time code, then the upload continues ─────────────
  var me = null, authEmail = "";
  async function whoami() {
    if (HANDOFF) {
      try {
        var s = await fetch("/app/api/auth/session?probe=1", { credentials: "same-origin", cache: "no-store" });
        me = s.ok ? (await s.json()).user : null;
      } catch (e) { me = null; }
      setAccount();
      return me;
    }
    try {
      var r = await fetch("/portal/api/me", { credentials: "same-origin" });
      me = r.ok ? (await r.json()).user : null;
    } catch (e) { me = null; }
    setAccount();
    return me;
  }
  function setAccount() {
    var a = $("#navAcct");
    signedClass();
    if (HANDOFF) {
      a.textContent = me ? "Projects" : "Sign in";
      a.href = me ? "/app/" : "/app/sign-in";
      $("#fine").innerHTML = me
        ? "Signed in as " + esc(me.email) + " · <a href=\"/app/\">Your projects</a>"
        : "Private and resumable. Files go straight to our storage and never become public.";
      return;
    }
    a.textContent = me ? "Dashboard" : "Sign in";
    $("#fine").innerHTML = me
      ? "Signed in as " + esc(me.email) + " · <a href=\"/dashboard/\">Your scans</a>"
      : "Private and resumable. Files go straight to our storage and never become public.";
  }
  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  // signed in already: the who row hides and Upload goes straight to the hand-off
  function signedClass() { form.classList.toggle("signed", !!me); }
  // the code panel takes the who row's place until the code is in (or they go back to fix the email)
  function showCode(email) {
    who.hidden = true; auth.hidden = false; form.classList.add("coding");
    $("#authS").textContent = "Sign in as " + email + ", or choose a password (8+ characters) to create your account. There's no password reset.";
    form.elements.code.value = "";
    setTimeout(function () { form.elements.code.focus(); }, 30);
  }
  function hideCode() { auth.hidden = true; who.hidden = false; form.classList.remove("coding"); $("#authDev").hidden = true; }
  async function post(url, body) {
    var r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin", body: JSON.stringify(body) });
    var j = await r.json().catch(function () { return {}; });
    if (!r.ok || !j.ok) throw new Error(j.error || "Something went wrong. Try again.");
    return j;
  }
  // Upload, signed out: work email, name and role are needed (company when they have one), then the code goes out
  async function askCode() {
    var w = whoValues(), el = form.elements, bad = [];
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(w.email)) bad.push([el.email, "Enter your work email."]);
    if (!w.name) bad.push([el.name, "Add your name."]);
    if (!w.role) bad.push([el.role, "Pick your role."]);
    Array.prototype.forEach.call(who.querySelectorAll("input, select"), function (x) { x.classList.remove("bad"); });
    if (bad.length) {
      bad.forEach(function (b) { b[0].classList.add("bad"); });
      bad[0][0].focus();
      return note(bad[0][1]);
    }
    note("");
    authEmail = w.email;
    showCode(w.email);
  }
  async function verify() {
    var input = form.elements.code, code = input.value;
    if (!code) { input.classList.add("bad"); input.focus(); return; }
    var b = $("#authVerify"), w = whoValues(); b.disabled = true; note("");
    try {
      var r = await fetch("/app/api/auth/password", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, password: code, name: w.name, company: w.company, role: w.role, mode: "auto" }) });
      var j = await r.json().catch(function () { return {}; });
      if (!r.ok) throw new Error(j.message || "Something went wrong. Try again.");
      me = j.user; setAccount();
      hideCode();
      b.disabled = false;
      return run();
    } catch (e) { input.classList.add("bad"); note(e.message); }
    b.disabled = false;
  }
  $("#authVerify").addEventListener("click", verify);
  $("#authBack").addEventListener("click", function () { hideCode(); note(""); form.elements.email.focus(); });
  Array.prototype.forEach.call(who.querySelectorAll("input"), function (el) {
    el.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); run(); } });
  });
  form.elements.role.addEventListener("change", function () { this.classList.toggle("empty", !this.value); });
  form.elements.role.classList.add("empty");
  form.elements.code.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); verify(); } });
  form.elements.code.addEventListener("input", function () {
    this.classList.remove("bad");

  });
  who.addEventListener("input", function (e) { e.target.classList && e.target.classList.remove("bad"); if (!$(".bad", who)) note(""); });
  who.addEventListener("change", function (e) { e.target.classList && e.target.classList.remove("bad"); });
  whoami();

  function reset() {
    items = []; submissionId = null; filesUl.innerHTML = "";
    form.classList.remove("is-done"); done.hidden = true; note(""); refresh();
  }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (e) { document.documentElement.classList.toggle("composer-in-view", e[0].isIntersecting); })
      .observe(form);
  }
  drop.addEventListener("click", function () { if (!items.length) fileInput.click(); });
  drop.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fileInput.click(); } });
  fileInput.addEventListener("change", function () { addFiles(fileInput.files); fileInput.value = ""; });
  form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
  $("#again").addEventListener("click", function () { if (handedOff) return backToProject(); reset(); });
  addEventListener("beforeunload", function (e) { if (running) { e.preventDefault(); e.returnValue = ""; } });

  // drop anywhere on the page
  var depth = 0;
  function hasFiles(e) { return e.dataTransfer && Array.prototype.indexOf.call(e.dataTransfer.types || [], "Files") >= 0; }
  addEventListener("dragenter", function (e) { if (!hasFiles(e) || appShown()) return; e.preventDefault(); depth++; document.body.classList.add("dragging"); });
  addEventListener("dragleave", function (e) { if (!hasFiles(e) || appShown()) return; if (--depth <= 0) { depth = 0; document.body.classList.remove("dragging"); form.classList.remove("over"); } });
  addEventListener("dragover", function (e) {
    if (!hasFiles(e) || appShown()) return;
    e.preventDefault(); e.dataTransfer.dropEffect = "copy";
    form.classList.toggle("over", form.contains(e.target));
  });
  addEventListener("drop", function (e) {
    if (!hasFiles(e) || appShown()) return;
    e.preventDefault(); depth = 0;
    document.body.classList.remove("dragging"); form.classList.remove("over");
    if (handedOff) return backToProject();   // more files go into the project, from there
    var onBox = form.contains(e.target);
    addFiles(e.dataTransfer.files);
    if (!onBox) form.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  Array.prototype.forEach.call(document.querySelectorAll("[data-focus-upload]"), function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      form.scrollIntoView({ behavior: "smooth", block: "center" });
      setTimeout(function () { drop.focus({ preventScroll: true }); }, 500);
    });
  });

  // how it works: draw the Revit window over its fallback image (revit.js; the image stays if it is missing)
  Array.prototype.forEach.call(document.querySelectorAll("[data-revit]"), function (el) {
    if (window.revitWindow) el.innerHTML = window.revitWindow({ compact: true, img: "/home/media/rotterdam-model.webp", sel: { x: 74, y: 64, w: 25, h: 32 } });
  });

  // ── page details ─────────────────────────────────────────────────────────
  // announcement bar: dismissed once, stays dismissed for this announcement
  var ann = $("#announce"), ANN_KEY = "ma_announce_pmarca";
  if (ann) {
    try { if (localStorage.getItem(ANN_KEY)) ann.hidden = true; } catch (e) {}
    // the bar stays pinned while scrolling, and the nav sits right under it
    var annH = function () { document.documentElement.style.setProperty("--ann-h", (ann.hidden ? 0 : ann.offsetHeight) + "px"); };
    annH(); addEventListener("resize", annH);
    $("#announceX").addEventListener("click", function () { ann.hidden = true; annH(); try { localStorage.setItem(ANN_KEY, "1"); } catch (e) {} });
  }
  // newsletter
  var news = $("#news");
  if (news) news.addEventListener("submit", async function (e) {
    e.preventDefault();
    var m = $("#newsMsg"), email = news.elements.email.value.trim();
    m.className = "bf-news-msg";
    if (news.elements.website.value) return;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { m.className += " err"; m.textContent = "Enter a valid work email."; return; }
    try {
      var r = await fetch("/portal/api/newsletter", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: email }) });
      var j = await r.json().catch(function () { return {}; });
      if (!r.ok || !j.ok) throw new Error(j.error || "Something went wrong. Try again.");
      news.elements.email.value = ""; m.textContent = "You're subscribed. Thanks.";
    } catch (err) { m.className += " err"; m.textContent = err.message; }
  });

  // the marquee loops by sliding half its width, so it holds two copies of the logo list
  var track = $(".marquee-track");
  if (track) track.innerHTML += track.innerHTML;

  var nav = $(".nav");
  function onScroll() { nav.classList.toggle("scrolled", scrollY > 8); }
  addEventListener("scroll", onScroll, { passive: true }); onScroll();

  var touch = matchMedia("(hover: none)").matches;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  // scan -> model wipe
  Array.prototype.forEach.call(document.querySelectorAll("[data-compare]"), function (card) {
    var media = $(".media", card);
    function at(clientX) {
      var r = media.getBoundingClientRect();
      media.style.setProperty("--x", Math.max(0, Math.min(100, (clientX - r.left) / r.width * 100)).toFixed(2) + "%");
    }
    media.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") { at(e.clientX); card.classList.add("comparing"); } });
    media.addEventListener("pointermove", function (e) { if (e.pointerType === "mouse") at(e.clientX); });
    media.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") card.classList.remove("comparing"); });
  });

  // randomized variants
  Array.prototype.forEach.call(document.querySelectorAll("[data-cycle]"), function (card) {
    var timer = null, n = 1, num = $("[data-n]", card);
    function tick() { card.classList.toggle("alt"); n = n % 24 + 1; num.textContent = (n < 10 ? "0" : "") + n; }
    card.startCycle = function () { if (!timer) { tick(); timer = setInterval(tick, 1400); } };
    card.stopCycle = function () { clearInterval(timer); timer = null; };
    card.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") card.startCycle(); });
    card.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") card.stopCycle(); });
  });

  // touch: sweep the wipe slowly and cycle variants while a card is on screen
  if (touch && !reduce && "IntersectionObserver" in window) {
    var visible = new Set();
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        var c = e.target;
        if (e.isIntersecting) { visible.add(c); c.classList.add("comparing"); c.startCycle && c.startCycle(); }
        else { visible.delete(c); c.classList.remove("comparing"); c.stopCycle && c.stopCycle(); }
      });
    }, { threshold: .6 });
    Array.prototype.forEach.call(document.querySelectorAll("[data-compare],[data-cycle]"), function (c) { io.observe(c); });
    (function loop(t) {
      visible.forEach(function (c) {
        if (c.hasAttribute("data-compare")) $(".media", c).style.setProperty("--x", (50 + 38 * Math.sin(t / 1400)).toFixed(2) + "%");
      });
      requestAnimationFrame(loop);
    })(0);
  }

  // films: plays only while the stage is on screen, crossfades between two <video>s, advances on end
  (function () {
    var stage = $("#stage"), reel = $("#reel");
    if (!stage || !reel) return;
    var vids = stage.querySelectorAll(".stage-v"), pp = $("#stagePP");
    var items = Array.prototype.slice.call(reel.querySelectorAll("li"));
    var small = matchMedia("(max-width: 900px)").matches;
    var cur = 0, front = 0, inView = false, paused = reduce;
    function src(i) { var k = $("button", items[i]).dataset.film; return "/home/films/" + k + (small ? "-960" : "") + ".mp4"; }
    var CREDITS = {
      niantic: 'Scan from <a href="https://www.nianticspatial.com/" target="_blank" rel="noopener">Niantic Spatial</a>, converted by Moving Atoms',
      navvis: 'Captured with <a href="https://www.navvis.com/" target="_blank" rel="noopener">NavVis</a> LiDAR, converted by Moving Atoms'
    };
    var creditEl = $("#stageCredit");
    function credit(i) { creditEl.innerHTML = CREDITS[$("button", items[i]).dataset.credit] || ""; }
    function poster(i) { return "/home/films/" + $("button", items[i]).dataset.film + ".webp"; }
    function mark() {
      items.forEach(function (li, i) {
        li.classList.toggle("on", i === cur); li.classList.toggle("done", i < cur);
        if (i !== cur) $(".reel-p b", li).style.width = "";
      });
    }
    function show(i) {
      cur = (i + items.length) % items.length;
      var next = vids[1 - front], prev = vids[front];
      next.poster = poster(cur);
      next.src = src(cur);
      next.currentTime = 0;
      next.classList.add("is-on"); prev.classList.remove("is-on");
      setTimeout(function () { prev.pause(); }, 900);
      front = 1 - front;
      mark(); sync(); credit(cur);
      if (small) { var li = items[cur]; reel.scrollTo({ left: li.offsetLeft - reel.offsetLeft, behavior: "smooth" }); }
    }
    function sync() {
      var v = vids[front];
      stage.classList.toggle("paused", paused);
      pp.setAttribute("aria-label", paused ? "Play" : "Pause");
      if (inView && !paused) { if (!v.src) v.src = src(cur); v.play().catch(function () {}); }
      else v.pause();
    }
    Array.prototype.forEach.call(vids, function (v) {
      v.addEventListener("ended", function () { if (v === vids[front]) show(cur + 1); });
    });
    (function tick() {
      var v = vids[front];
      if (v.duration) $(".reel-p b", items[cur]).style.width = (v.currentTime / v.duration * 100).toFixed(2) + "%";
      requestAnimationFrame(tick);
    })();
    items.forEach(function (li, i) {
      $("button", li).addEventListener("click", function () { paused = false; if (i !== cur) show(i); else sync(); });
    });
    pp.addEventListener("click", function () { paused = !paused; sync(); });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { inView = es[0].isIntersecting; sync(); }, { threshold: .35 }).observe(stage);
    } else { inView = true; }
    mark(); sync(); credit(cur);
  })();

  // section entrances
  if (!reduce && "IntersectionObserver" in window) {
    var els = document.querySelectorAll(".sec-head, .card, .dl-step, .cta");
    var ro = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); ro.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    Array.prototype.forEach.call(els, function (el, i) {
      el.classList.add("reveal");
      if (el.classList.contains("card")) el.style.transitionDelay = (i % 3) * 70 + "ms";
      ro.observe(el);
    });
  }
})();
