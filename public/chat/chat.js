/* Moving Atoms site chat: a bottom-right launcher and panel on every page (nginx injects this script), talking to
   /portal/api/chat/* (tools/portal/chat.js). Shadow DOM keeps the look identical on every page whatever its CSS.
   The conversation follows the visitor across pages (token in localStorage); the team answers from /inbox/. */
(function () {
  "use strict";
  if (window.__maChat) return; window.__maChat = 1;
  var P = location.pathname;
  if (/^\/(inbox|lidarsample|lidarsample2|rotterdam|david|faisal|jazeera|avetics|_|quote\/all)/.test(P) || /-scan\/?$/.test(P)) return;

  var API = "/portal/api/chat", KEY = "ma_chat_token", SEEN = "ma_chat_seen";
  var token = null; try { token = localStorage.getItem(KEY); } catch (e) {}
  var INTRO = "Hi, we're Ahmad and Shehryar. Ask us anything about your scan, pricing, formats or turnaround and we'll reply right here.";
  var QUOTE = /^\/quote\/?$/.test(P), QID = new URLSearchParams(location.search).get("id") || "";
  var QUOTE_INTRO = "Hi, we're Ahmad and Shehryar. We're here while your estimate comes together. Ask us anything about scope, LOD, formats or turnaround, or tell us what you need modelled.";
  var quoteNudge = false, msgs = [], lastId = 0, open = false, email = null, teamOnline = false, pollT = 0, unread = 0, sending = false;

  var host = document.createElement("div");
  host.id = "ma-chat"; host.style.cssText = "position:fixed;z-index:2147483000;right:0;bottom:0;width:0;height:0";
  var root = host.attachShadow({ mode: "open" });
  root.innerHTML = '<style>' +
    ':host{all:initial}' +
    '*{box-sizing:border-box;font-family:"General Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif;-webkit-font-smoothing:antialiased}' +
    '.mono{font-family:"Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}' +
    '.launch{position:fixed;right:22px;bottom:var(--b,22px);width:56px;height:56px;border-radius:999px;border:1px solid rgba(255,255,255,.18);background:#000;color:#fff;display:grid;place-items:center;cursor:pointer;' +
      'box-shadow:0 18px 50px -12px rgba(0,0,0,.8),0 0 0 6px rgba(255,255,255,.04);transition:transform .35s cubic-bezier(.2,.7,.2,1),border-color .25s,box-shadow .25s}' +
    '.launch:hover{transform:translateY(-2px);border-color:rgba(255,255,255,.4);box-shadow:0 22px 60px -12px rgba(0,0,0,.9),0 0 0 7px rgba(255,255,255,.06)}' +
    '.launch svg{position:absolute;transition:opacity .25s,transform .35s cubic-bezier(.2,.7,.2,1)}' +
    '.launch .i-x{opacity:0;transform:rotate(-45deg) scale(.6)}' +
    '.is-open .launch .i-chat{opacity:0;transform:rotate(45deg) scale(.6)} .is-open .launch .i-x{opacity:1;transform:none}' +
    '.badge{position:absolute;top:-3px;right:-3px;min-width:20px;height:20px;padding:0 6px;border-radius:999px;background:#fff;color:#000;font:600 11px/20px "Plex Mono",monospace;text-align:center;box-shadow:0 0 0 3px #000}' +
    '.badge[hidden]{display:none}' +
    '.nudge{position:fixed;right:88px;bottom:calc(var(--b,22px) + 8px);max-width:260px;padding:12px 14px 12px 14px;border-radius:16px 16px 4px 16px;background:#0b0b0b;border:1px solid rgba(255,255,255,.14);color:rgba(255,255,255,.86);font-size:13.5px;line-height:1.4;' +
      'box-shadow:0 20px 60px -20px rgba(0,0,0,.9);cursor:pointer;animation:rise .5s cubic-bezier(.2,.7,.2,1) both}' +
    '.nudge b{display:block;color:#fff;font-weight:500;margin-bottom:2px}.nudge[hidden]{display:none}' +
    '.nudge .nx{position:absolute;top:-8px;left:-8px;width:20px;height:20px;border-radius:999px;border:1px solid rgba(255,255,255,.18);background:#000;color:rgba(255,255,255,.7);font-size:12px;line-height:18px;text-align:center;cursor:pointer}' +
    '.panel{position:fixed;right:22px;bottom:calc(var(--b,22px) + 68px);width:380px;height:min(580px,calc(100vh - var(--b,22px) - 100px));display:flex;flex-direction:column;border-radius:22px;overflow:hidden;' +
      'background:linear-gradient(180deg,#0d0d0d,#060606);border:1px solid rgba(255,255,255,.14);box-shadow:0 40px 120px -30px rgba(0,0,0,.95),0 0 0 1px rgba(0,0,0,.6);' +
      'opacity:0;transform:translateY(14px) scale(.98);transform-origin:bottom right;pointer-events:none;transition:opacity .28s cubic-bezier(.2,.7,.2,1),transform .35s cubic-bezier(.2,.7,.2,1)}' +
    '.is-open .panel{opacity:1;transform:none;pointer-events:auto}' +
    '.head{display:flex;align-items:center;gap:12px;padding:16px 16px 14px;border-bottom:1px solid rgba(255,255,255,.08);background:radial-gradient(120% 140% at 0 0,rgba(255,255,255,.07),transparent 60%)}' +
    '.avs{display:flex}.av{width:34px;height:34px;border-radius:999px;display:grid;place-items:center;background:#fff;color:#000;font:600 13px/1 "General Sans",sans-serif;box-shadow:0 0 0 2px #0b0b0b}' +
    '.av+.av{margin-left:-10px;background:#2a2a2a;color:#fff}' +
    '.ht{flex:1;min-width:0}.ht b{display:block;color:#fff;font-size:15px;font-weight:500;letter-spacing:-.01em}' +
    '.st{display:flex;align-items:center;gap:6px;margin-top:3px;font-size:12px;color:rgba(255,255,255,.55)}.st i{width:6px;height:6px;border-radius:999px;background:rgba(255,255,255,.4)}' +
    '.st.on i{background:#7dffb0;box-shadow:0 0 8px #7dffb0}' +
    '.x{width:30px;height:30px;border:0;border-radius:9px;background:none;color:rgba(255,255,255,.55);font-size:20px;cursor:pointer}.x:hover{color:#fff;background:rgba(255,255,255,.06)}' +
    '.list{flex:1;overflow:auto;padding:16px 14px 6px;scrollbar-width:thin;scrollbar-color:#333 transparent}' +
    '.m{display:flex;flex-direction:column;max-width:84%;margin:0 0 10px}.m.new{animation:rise .3s cubic-bezier(.2,.7,.2,1) both}' +
    '.m.me{margin-left:auto;align-items:flex-end}' +
    '.who{margin:0 0 4px 2px;font:11px/1 "Plex Mono",monospace;letter-spacing:.04em;color:rgba(255,255,255,.45)}' +
    '.b{padding:10px 13px;border-radius:16px 16px 16px 5px;background:#1a1a1a;border:1px solid rgba(255,255,255,.07);color:rgba(255,255,255,.9);font-size:14px;line-height:1.45;white-space:pre-wrap;word-wrap:break-word}' +
    '.me .b{border-radius:16px 16px 5px 16px;background:#fff;color:#000;border-color:#fff}' +
    '.t{margin:4px 3px 0;font:10.5px/1 "Plex Mono",monospace;color:rgba(255,255,255,.3)}' +
    '.card{margin:4px 0 12px;padding:12px;border:1px solid rgba(255,255,255,.12);border-radius:14px;background:rgba(255,255,255,.03);font-size:13px;color:rgba(255,255,255,.75)}' +
    '.card form{display:flex;gap:6px;margin-top:8px}.card input{flex:1;min-width:0;height:36px;padding:0 12px;border-radius:999px;border:1px solid rgba(255,255,255,.18);background:#050505;color:#fff;font-size:13px;outline:0}' +
    '.card input:focus{border-color:rgba(255,255,255,.45)}.card button{height:36px;padding:0 14px;border:0;border-radius:999px;background:#fff;color:#000;font-weight:500;font-size:13px;cursor:pointer}' +
    '.card[hidden]{display:none}' +
    '.comp{display:flex;align-items:flex-end;gap:8px;margin:8px 12px 12px;padding:6px 6px 6px 14px;border:1px solid rgba(255,255,255,.14);border-radius:18px;background:#050505;transition:border-color .2s}' +
    '.comp:focus-within{border-color:rgba(255,255,255,.4)}' +
    '.comp textarea{flex:1;min-height:22px;max-height:120px;margin:6px 0;border:0;background:none;color:#fff;font-size:14px;line-height:1.45;resize:none;outline:0}' +
    '.comp textarea::placeholder{color:rgba(255,255,255,.38)}' +
    '.send{flex:none;width:34px;height:34px;border:0;border-radius:999px;background:#fff;color:#000;display:grid;place-items:center;cursor:pointer;transition:opacity .2s,transform .2s}' +
    '.send:disabled{opacity:.3;cursor:default}.send:not(:disabled):hover{transform:scale(1.05)}' +
    '.foot{display:flex;justify-content:space-between;padding:0 16px 12px;font-size:11.5px;color:rgba(255,255,255,.35)}.foot a{color:rgba(255,255,255,.6);text-decoration:none}.foot a:hover{color:#fff}' +
    '.err{margin:0 14px 6px;font-size:12px;color:#ff9a9a}.err:empty{display:none}' +
    '.hp{position:absolute;left:-9999px}' +
    '@keyframes rise{from{opacity:0;transform:translateY(8px)}}' +
    '@media (max-width:560px){.panel{right:8px;left:8px;width:auto;bottom:calc(var(--b,16px) + 66px);height:min(560px,calc(100vh - 110px))}.launch{right:16px}.nudge{right:80px}}' +
    '</style>' +
    '<div class="wrap">' +
    '<div class="nudge" hidden><span class="nx" aria-label="Dismiss">×</span><b>Questions about your scan?</b>Chat with the founders. We usually reply within minutes.</div>' +
    '<section class="panel" role="dialog" aria-label="Chat with Moving Atoms">' +
      '<div class="head"><div class="avs"><span class="av">A</span><span class="av">S</span></div>' +
        '<div class="ht"><b>Moving Atoms</b><span class="st"><i></i><span class="stt">Usually replies within minutes</span></span></div>' +
        '<button class="x" aria-label="Close">×</button></div>' +
      '<div class="list" aria-live="polite"></div>' +
      '<div class="card" hidden><b style="color:#fff;font-weight:500">Where should we reply if you step away?</b>' +
        '<form><input type="email" placeholder="Work email" aria-label="Your email" required /><button type="submit">Save</button></form></div>' +
      '<p class="err"></p>' +
      '<form class="comp"><input class="hp" name="website" tabindex="-1" autocomplete="off" />' +
        '<textarea rows="1" placeholder="Ask about pricing, formats, turnaround…" aria-label="Message"></textarea>' +
        '<button class="send" type="submit" aria-label="Send" disabled><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg></button></form>' +
      '<div class="foot"><span class="mono">Replies from the founders</span><a href="/contact">Book a call ↗</a></div>' +
    '</section>' +
    '<button class="launch" aria-label="Chat with us">' +
      '<svg class="i-chat" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-8.5 8.3 8.7 8.7 0 0 1-3.9-.9L3 21l1.9-5.1a8.1 8.1 0 0 1-.9-3.7A8.4 8.4 0 0 1 12.5 3.9 8.4 8.4 0 0 1 21 11.5z"/></svg>' +
      '<svg class="i-x" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>' +
      '<span class="badge" hidden>0</span></button>' +
    '</div>';
  var $ = function (s) { return root.querySelector(s); };
  var wrap = $(".wrap"), list = $(".list"), ta = $("textarea"), send = $(".send"), card = $(".card"), err = $(".err"), badge = $(".badge"), nudge = $(".nudge");

  // keep clear of the quote page's pinned pay bar on phones
  function offset() { host.style.setProperty("--b", innerWidth < 980 && /^\/quote\//.test(P) ? "104px" : (innerWidth < 560 ? "16px" : "22px")); wrap.style.setProperty("--b", host.style.getPropertyValue("--b")); }
  offset(); addEventListener("resize", offset);

  function esc(t) { return String(t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function hhmm(ms) { return new Date(ms).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }); }
  var drawn = null, drawnSig = "";
  function render() {
    var sig = msgs.map(function (m) { return m.id; }).join(",");
    if (sig !== drawnSig || !drawn) {
      var first = !drawn, seen = drawn || {}; drawn = {};
      var intro = '<div class="m' + (first ? " new" : "") + '"><span class="who">MOVING ATOMS</span><div class="b">' + esc(QUOTE ? QUOTE_INTRO : INTRO) + "</div></div>";
      list.innerHTML = intro + msgs.map(function (m) {
        var me = m.sender === "visitor", key = me && m.id % 1 ? "tmp" : m.id; drawn[key] = 1;
        return '<div class="m' + (me ? " me" : "") + (seen[key] || (me && seen.tmp) ? "" : " new") + '">' + (me ? "" : '<span class="who">' + esc((m.author || "Moving Atoms").toUpperCase()) + "</span>") +
          '<div class="b">' + esc(m.body) + '</div><span class="t">' + hhmm(m.created) + "</span></div>";
      }).join("");
      drawnSig = sig; list.scrollTop = list.scrollHeight;
    }
    card.hidden = !(token && !email && msgs.some(function (m) { return m.sender === "visitor"; }));
    var st = $(".st"); st.classList.toggle("on", teamOnline); $(".stt").textContent = teamOnline ? "Online now" : "Usually replies within minutes";
  }
  function setUnread() {
    var seen = 0; try { seen = Number(localStorage.getItem(SEEN)) || 0; } catch (e) {}
    unread = open ? 0 : msgs.filter(function (m) { return m.sender === "team" && m.id > seen; }).length;
    if (!open && quoteNudge && !unread) unread = 1;
    badge.hidden = !unread; badge.textContent = unread;
    if (open && lastId) try { localStorage.setItem(SEEN, String(lastId)); } catch (e) {}
  }
  function merge(arr) {
    var known = {}; msgs.forEach(function (m) { known[m.id] = 1; });
    arr.forEach(function (m) { if (!known[m.id]) msgs.push(m); });
    msgs.sort(function (a, b) { return a.id - b.id; });
    if (msgs.length) lastId = msgs[msgs.length - 1].id;
  }
  async function poll() {
    clearTimeout(pollT);
    try {
      var r = await fetch(API + "/poll?token=" + encodeURIComponent(token || "") + "&after=" + lastId, { credentials: "same-origin" });
      var j = await r.json();
      if (j.ok) {
        var before = msgs.length; merge(j.messages || []); teamOnline = !!j.team_online; if (j.email) email = j.email;
        if (msgs.length !== before || open) render();
        setUnread();
      }
    } catch (e) {}
    if (token || open) pollT = setTimeout(poll, open ? 3000 : 25000);
  }
  async function submit(e) {
    e.preventDefault();
    var text = ta.value.trim(); if (!text || sending) return;
    sending = true; send.disabled = true; err.textContent = "";
    var tmp = { id: lastId + 0.5, sender: "visitor", body: text, created: Date.now() }; msgs.push(tmp); render();
    ta.value = ""; grow();
    try {
      var r = await fetch(API + "/send", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
        body: JSON.stringify({ token: token, body: text, page: location.pathname + location.search, after: lastId, website: $(".hp").value }) });
      var j = await r.json();
      msgs = msgs.filter(function (m) { return m !== tmp; });
      if (!j.ok) { err.textContent = j.error || "Couldn't send. Try again."; ta.value = text; }
      else { if (j.token) { token = j.token; try { localStorage.setItem(KEY, token); } catch (x) {} } merge(j.messages || []); }
    } catch (x) { msgs = msgs.filter(function (m) { return m !== tmp; }); err.textContent = "Couldn't send. Check your connection."; ta.value = text; }
    sending = false; send.disabled = !ta.value.trim(); render(); setUnread(); poll();
  }
  function grow() { ta.style.height = "auto"; ta.style.height = Math.min(120, ta.scrollHeight) + "px"; send.disabled = !ta.value.trim(); }
  function toggle(on) {
    open = on === undefined ? !open : on;
    wrap.classList.toggle("is-open", open); nudge.hidden = true;
    if (open && quoteNudge) { quoteNudge = false; try { localStorage.setItem("ma_chat_q", QID); } catch (e) {} }
    try { sessionStorage.setItem("ma_chat_nudged", "1"); } catch (e) {}
    if (open) { render(); setUnread(); setTimeout(function () { ta.focus(); }, 250); poll(); }
  }
  $(".launch").addEventListener("click", function () { toggle(); });
  $(".x").addEventListener("click", function () { toggle(false); });
  nudge.addEventListener("click", function (e) { if (e.target.classList.contains("nx")) { e.stopPropagation(); nudge.hidden = true;
      if (quoteNudge) { quoteNudge = false; setUnread(); try { localStorage.setItem("ma_chat_q", QID); } catch (x) {} } try { sessionStorage.setItem("ma_chat_nudged", "1"); } catch (x) {} return; } toggle(true); });
  $(".comp").addEventListener("submit", submit);
  ta.addEventListener("input", grow);
  ta.addEventListener("keydown", function (e) { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $(".comp").requestSubmit(); } });
  card.querySelector("form").addEventListener("submit", async function (e) {
    e.preventDefault(); var v = this.querySelector("input").value.trim();
    try {
      var r = await fetch(API + "/email", { method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin", body: JSON.stringify({ token: token, email: v }) });
      var j = await r.json(); if (j.ok) { email = v; render(); } else err.textContent = j.error || "Add a valid email.";
    } catch (x) {}
  });
  addEventListener("keydown", function (e) { if (e.key === "Escape" && open) toggle(false); });

  function mount() {
    document.body.appendChild(host);
    if (token) poll();
    // a gentle nudge once per visit, after a while on the page (not on the dashboard or the quote page while preparing)
    var nudged = false; try { nudged = !!sessionStorage.getItem("ma_chat_nudged"); } catch (e) {}
    // the estimating page: a notification on the bubble (once per quote) saying we're around while it prices
    var qDone = ""; try { qDone = localStorage.getItem("ma_chat_q") || ""; } catch (e) {}
    if (QUOTE && QID && qDone !== QID) {
      setTimeout(function () {
        if (open) return;
        quoteNudge = true;
        nudge.innerHTML = '<span class="nx" aria-label="Dismiss">×</span><b>We\'re here while you wait</b>Questions about your estimate? Ahmad and Shehryar reply in minutes.';
        nudge.hidden = false; setUnread();
        setTimeout(function () { nudge.hidden = true; }, 12000);   // the badge stays; the text never sits over the pay button for long
      }, 3500);
      return;
    }
    if (!nudged && !/^\/(dashboard|contact|quote)/.test(P)) setTimeout(function () { if (!open && !token) nudge.hidden = false; }, 25000);
  }
  if (document.body) mount(); else document.addEventListener("DOMContentLoaded", mount);
})();
