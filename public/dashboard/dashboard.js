/* Customer dashboard: signs in with an emailed code, then lists the customer's scans with their progress.
   Data comes from /portal/api (tools/portal/portal.js) and refreshes every 20 seconds. */
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var STEPS = ["Uploaded", "Quote", "Paid", "Modelling", "Delivered"];
  // status → [steps finished, step in progress (-1: none), pill label, pill style]
  var STATUS = {
    uploading: [0, 0, "Uploading", "wait"],
    received: [1, 1, "Measuring", "live"],
    analysing: [1, 1, "Preparing quote", "live"],
    quote_review: [1, 1, "Confirming quote", "wait"],
    quoted: [2, 2, "Quote ready", "alert"],
    expired: [1, 1, "Quote expired", "off"],
    reviewing: [1, 1, "In review", "live"],
    needs_info: [1, 1, "In review", "wait"],
    declined: [1, -1, "Declined", "off"],
    payment_processing: [2, 2, "Payment processing", "wait"],
    paid: [3, 3, "Paid", "live"],
    accepted: [3, 3, "Starting", "live"],
    modelling: [3, 3, "Modelling", "live"],
    delivered: [5, -1, "Delivered", "done"]
  };
  var STEP_OF = { received: 0, quoted: 1, quote_review: 1, needs_info: 1, declined: 1, payment_processing: 2, paid: 2, accepted: 2, modelling: 3, delivered: 4 };
  var QUOTE_LINK = ["analysing", "received", "quoted", "quote_review", "expired", "payment_processing"];
  var params = new URLSearchParams(location.search), paidId = params.get("paid"), sessionId = params.get("session_id"),
      fresh = params.get("new") || paidId, user = null, email = "", timer = 0, open = {}, paidHint = "";

  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fmt(b) {
    if (b >= 1e9) return (b / 1e9).toFixed(2) + " GB";
    if (b >= 1e6) return (b / 1e6).toFixed(1) + " MB";
    if (b >= 1e3) return (b / 1e3).toFixed(0) + " KB";
    return b + " B";
  }
  function when(ms) {
    var d = new Date(ms), diff = (Date.now() - ms) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return Math.floor(diff / 60) + " min ago";
    if (diff < 86400) return Math.floor(diff / 3600) + " h ago";
    return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
  }
  function ext(n) { var i = n.lastIndexOf("."); return i < 0 ? "file" : n.slice(i + 1).slice(0, 4); }
  async function api(path, body) {
    var r = await fetch("/portal/api" + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), credentials: "same-origin" } : { credentials: "same-origin" });
    var j = await r.json().catch(function () { return {}; });
    if (!r.ok || !j.ok) { var e = new Error(j.error || "Something went wrong."); e.status = r.status; throw e; }
    return j;
  }

  // ── sign in ────────────────────────────────────────────────────────────────
  var gate = $("#gate"), board = $("#board"), msg = $("#gateMsg");
  function showGate() {
    // sign-in is email + password on the app's sign-in page now; it comes back here afterwards
    location.replace("/app/sign-in?next=" + encodeURIComponent(location.pathname + location.search));
    return;
    gate.hidden = false; board.hidden = true; $("#acct").hidden = true;
    setTimeout(function () { $("#gateEmail").elements.email.focus(); }, 50);
  }
  $("#gateEmail").addEventListener("submit", async function (e) {
    e.preventDefault();
    email = this.elements.email.value.trim();
    msg.className = "gate-msg"; msg.textContent = "";
    try {
      var j = await api("/auth/start", { email: email });
      $("#gateS").textContent = "We sent a 6-digit code to " + email + ".";
      this.hidden = true; $("#gateCode").hidden = false;
      if (j.devCode) msg.innerHTML = "Local preview, no email sent. Your code is <b>" + j.devCode + "</b>";
      $("#gateCode").elements.code.focus();
    } catch (err) { msg.className = "gate-msg err"; msg.textContent = err.message; }
  });
  $("#gateCode").addEventListener("submit", async function (e) {
    e.preventDefault();
    try {
      await api("/auth/verify", { email: email, code: this.elements.code.value });
      msg.textContent = ""; load();
    } catch (err) { msg.className = "gate-msg err"; msg.textContent = err.message; }
  });
  $("#gateCode").elements.code.addEventListener("input", function () {
    this.value = this.value.replace(/\D/g, "").slice(0, 6);
    if (this.value.length === 6) $("#gateCode").requestSubmit();
  });

  // account menu
  var menu = $("#acctMenu"), btn = $("#acctBtn");
  btn.addEventListener("click", function () { menu.hidden = !menu.hidden; btn.setAttribute("aria-expanded", String(!menu.hidden)); });
  document.addEventListener("click", function (e) { if (!e.target.closest(".acct")) menu.hidden = true; });
  $("#signOut").addEventListener("click", async function () {
    await api("/auth/logout", {}).catch(function () {});
    clearInterval(timer); location.href = "/";
  });
  $("#toastX").addEventListener("click", function () { $("#toast").hidden = true; history.replaceState(null, "", location.pathname); });

  // ── board ──────────────────────────────────────────────────────────────────
  function title(s) {
    var first = s.files[0] ? s.files[0].name.replace(/\.[^.]+$/, "") : "Scan";
    return first + (s.files.length > 1 ? " + " + (s.files.length - 1) + " more" : "");
  }
  function parseNotes(n) {
    var out = { needs: [], lod: "", text: [] };
    String(n || "").split("\n").forEach(function (line) {
      var m;
      if ((m = /^Needs back: (.+)$/.exec(line))) out.needs = m[1].split(/,\s*/);
      else if ((m = /^Level of development: (LOD \d+)$/.exec(line))) out.lod = m[1];
      else if (line.trim()) out.text.push(line);
    });
    out.text = out.text.join("\n");
    return out;
  }
  function stepTimes(s) {
    var t = [s.finished || s.created, null, null, null, null];
    (s.history || []).forEach(function (h) { var i = STEP_OF[h.status]; if (i > 0) t[i] = h.at; });
    return t;
  }
  function card(s) {
    var st = STATUS[s.status] || STATUS.received, doneN = st[0], now = st[1], n = parseNotes(s.notes), times = stepTimes(s);
    var size = s.files.reduce(function (a, f) { return a + (f.size || 0); }, 0);
    var stepsHtml = STEPS.map(function (label, i) {
      var cls = i < doneN ? "ok" : (i === now ? "now" : "");
      return '<li class="' + cls + '"><span class="dot"></span><span class="st-l">' + label + '</span><span class="st-t">' +
        (times[i] && (i < doneN || i === now) ? esc(when(times[i])) : "&nbsp;") + "</span></li>";
    }).join("");
    var fillSteps = Math.max(doneN - 1, now, 0);
    var li = document.createElement("li");
    li.className = "sub" + (s.id === fresh ? " is-new" : "") + (open[s.id] ? " open" : "");
    li.dataset.id = s.id;
    li.innerHTML =
      '<div class="sub-top"><div>' +
        '<h3 class="sub-title">' + esc(title(s)) + "</h3>" +
        '<p class="sub-meta"><span>' + esc(when(s.finished || s.created)) + "</span><span>" + s.files.length + " file" + (s.files.length === 1 ? "" : "s") + " · " + fmt(size) + "</span>" +
          // the LOD the customer picked (prices use the 350 minimum internally)
          (s.lodRequested ? '<span class="chip">LOD ' + esc(s.lodRequested) + "</span>" : n.lod ? '<span class="chip">' + esc(n.lod) + "</span>" : "") +
          n.needs.map(function (x) { return '<span class="chip">' + esc(x) + "</span>"; }).join("") + "</p>" +
      '</div><span class="pill ' + st[3] + '"><i></i>' + st[2] + "</span></div>" +
      '<ol class="steps5" aria-label="Progress"><i class="fill" style="width:calc(' + fillSteps + ' * 20%)"></i>' + stepsHtml + "</ol>" +
      (s.message ? '<p class="sub-msg"><b>From the team</b>' + esc(s.message) + "</p>" : "") +
      '<div class="sub-foot"><span class="sub-id">' + esc(s.id.slice(0, 8)) +
        (s.payment && s.payment.receipt_url ? ' · <a class="rcpt" href="' + esc(s.payment.receipt_url) + '" target="_blank" rel="noopener">Receipt</a>' : "") + "</span>" +
        (s.deliveryUrl ? '<a class="btn btn-white" href="' + esc(s.deliveryUrl) + '">Download delivery</a>' :
        QUOTE_LINK.indexOf(s.status) >= 0 ? '<a class="btn ' + (s.status === "quoted" ? "btn-white" : "btn-ghost") + ' qlink" href="/quote/?id=' + encodeURIComponent(s.id) + '">' +
          (s.quote && s.status !== "needs_info" ? (s.status === "quoted" ? "Pay " : "Quote ") + "$" + Number(s.quote.price_usd).toLocaleString("en-US") : s.status === "needs_info" ? "See what's needed" : "View progress") + "</a>" :
        '<button type="button" class="more" aria-expanded="' + !!open[s.id] + '">Details <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg></button>') +
      "</div>" +
      '<div class="sub-details"><div><div class="inner"><ul class="flist">' +
        s.files.map(function (f) {
          return '<li><span class="file-ico">' + esc(ext(f.name)) + '</span><span class="fn">' + esc(f.name) + '</span><span class="fs">' + fmt(f.size) +
            '</span><span class="fk">' + (f.status === "uploaded" ? "✓ Received" : "Uploading") + "</span></li>";
        }).join("") + "</ul>" +
        (n.text ? '<p class="notes">' + esc(n.text) + "</p>" : "") +
      "</div></div></div>";
    var more = $(".more", li);
    if (more) more.addEventListener("click", function () {
      open[s.id] = !open[s.id]; li.classList.toggle("open", open[s.id]); more.setAttribute("aria-expanded", String(open[s.id]));
    });
    return li;
  }
  function render(data) {
    user = data.user;
    var name = user.name && user.name !== user.email ? user.name.split(" ")[0] : "";
    $("#hello").textContent = name ? "Welcome back, " + name : user.email;
    $("#acctAv").textContent = (user.name || user.email).trim().slice(0, 1).toUpperCase();
    $("#acctEmail").textContent = user.email;
    $("#acct").hidden = false;
    var subs = data.submissions;
    var active = subs.filter(function (s) { return ["received", "analysing", "quoted", "quote_review", "paid", "reviewing", "accepted", "modelling", "needs_info"].indexOf(s.status) >= 0; }).length;
    var delivered = subs.filter(function (s) { return s.status === "delivered"; }).length;
    var bytes = subs.reduce(function (a, s) { return a + s.files.reduce(function (b, f) { return b + (f.size || 0); }, 0); }, 0);
    $("#stats").innerHTML = "<div><dt>In progress</dt><dd>" + active + "</dd></div><div><dt>Delivered</dt><dd>" + delivered +
      "</dd></div><div><dt>Uploaded</dt><dd>" + fmt(bytes) + "</dd></div>";
    var list = $("#subs"); list.innerHTML = "";
    subs.forEach(function (s, i) { var c = card(s); c.style.animationDelay = i * 60 + "ms"; list.appendChild(c); });
    $("#empty").hidden = subs.length > 0;
    $("#toast").hidden = !fresh || !subs.some(function (s) { return s.id === fresh; });
    if (paidId) $("#toast").hidden = true;          // the payment card at the top says it
  }
  // ── back from Stripe: confirm the payment with the checkout session (signed in or not) ─────────
  function when2(ms) { return new Date(ms).toLocaleString(undefined, { weekday: "long", day: "numeric", month: "long", hour: "numeric", minute: "2-digit" }); }
  async function confirmPayment() {
    var card = $("#paidCard"); card.hidden = false; card.className = "paidcard busy";
    for (var i = 0; i < 12; i++) {
      var r = null;
      try { r = await api("/checkout/session", { session_id: sessionId }); } catch (e) {}
      if (r && (r.state === "paid" || r.state === "processing" || r.state === "duplicate" || r.state === "mismatch")) {
        card.className = "paidcard " + (r.state === "paid" ? "ok" : "wait");
        var amt = "$" + Number(r.amount_usd).toLocaleString("en-US");
        if (r.state === "paid") {
          $("#pcEb").textContent = "Paid · " + amt;
          $("#pcH").textContent = "Payment received. Thank you.";
          $("#pcS").textContent = "We've started on " + (r.label ? "your " + r.label.toLowerCase() : "your model") +
            (r.due ? ". It will be delivered by " + when2(r.due) + ", with one round of revisions included." : ". It will be delivered within 48 hours.") +
            " A confirmation email is on its way.";
        } else if (r.state === "processing") {
          $("#pcEb").textContent = "Payment processing · " + amt;
          $("#pcH").textContent = "Your payment is on its way.";
          $("#pcS").textContent = "Bank payments take 1–4 working days. We start the moment it clears and email you.";
        } else {
          $("#pcEb").textContent = "Payment · " + amt;
          $("#pcH").textContent = "We've received your payment.";
          $("#pcS").textContent = "We're checking one detail before we start, and we'll email you within a few hours.";
        }
        $("#pcL").innerHTML = [r.receipt_url ? '<a href="' + esc(r.receipt_url) + '" target="_blank" rel="noopener">Receipt</a>' : "",
          r.invoice_url ? '<a href="' + esc(r.invoice_url) + '" target="_blank" rel="noopener">Invoice</a>' : ""].filter(Boolean).join("");
        if (!r.owner && r.email_hint) {
          paidHint = r.email_hint;
          $("#pcL").innerHTML += '<span>This job is in the account for <b>' + esc(r.email_hint) + "</b>. Sign in with that email to follow it.</span>";
          $("#gateS").textContent = "Sign in as " + r.email_hint + " to follow your model.";
        }
        history.replaceState(null, "", location.pathname + (paidId ? "?paid=" + encodeURIComponent(paidId) : ""));
        return;
      }
      await new Promise(function (res) { setTimeout(res, 1200); });
    }
    card.className = "paidcard wait";
    $("#pcH").textContent = "We're confirming your payment.";
    $("#pcS").textContent = "Stripe hasn't told us yet. It will show here within a few minutes, and we'll email you. If you were charged, nothing else is needed.";
  }
  if (sessionId) confirmPayment();

  async function load() {
    try {
      var data = await api("/submissions");
      gate.hidden = true; board.hidden = false;
      render(data);
      clearInterval(timer);
      timer = setInterval(function () { api("/submissions").then(render).catch(function (e) { if (e.status === 401) showGate(); }); }, 20000);
    } catch (e) { if (e.status === 401) showGate(); }
  }
  load();
})();
