/* Moving Atoms: "Book a Demo", "Book a call" and "Let's talk" open the team's Cal booking page in an overlay.
   The links keep their /contact href, so modified clicks (new tab) and visitors without
   JavaScript still reach the contact page. Add data-cal to any other link or button to give
   it the same behaviour. Only preventDefault is used, so the analytics click listener still
   records these CTAs. */
(function () {
  var CAL = "https://moving-atoms.cal.com/ahmad/30min?theme=dark";
  var TITLE = "Book a call with Moving Atoms";
  var TRIGGER = /^(book a demo|book a call|let's talk)(\W|$)/;
  var overlay = null, lastFocus = null, overflow = "";

  var CSS =
    ".ma-cal{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;padding:24px;background:rgba(5,5,7,.72);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);animation:ma-cal-in .18s ease-out}" +
    ".ma-cal *{box-sizing:border-box}" +
    ".ma-cal-box{display:flex;flex-direction:column;width:min(1000px,100%);height:min(780px,100%);overflow:hidden;border-radius:18px;background:#111113;border:1px solid rgba(255,255,255,.1);box-shadow:0 30px 90px rgba(0,0,0,.55)}" +
    ".ma-cal-head{display:flex;align-items:center;gap:16px;margin:0;padding:12px 12px 12px 20px;border-bottom:1px solid rgba(255,255,255,.08);color:#f4f4f5;font-size:14px;line-height:1.2}" +
    ".ma-cal-head strong{margin-right:auto;font-weight:600;letter-spacing:-.01em}" +
    ".ma-cal-new{color:rgba(255,255,255,.62);font-size:13px;text-decoration:none;white-space:nowrap}" +
    ".ma-cal-new:hover{color:#fff}" +
    ".ma-cal-x{display:grid;place-items:center;width:34px;height:34px;margin:0;padding:0;border:0;border-radius:10px;background:transparent;color:#f4f4f5;cursor:pointer}" +
    ".ma-cal-x:hover{background:rgba(255,255,255,.08)}" +
    ".ma-cal-x svg{width:16px;height:16px}" +
    ".ma-cal-body{position:relative;flex:1;background:#101010}" +
    ".ma-cal-body:before{content:'Loading calendar\\2026';position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.45);font-size:14px}" +
    ".ma-cal-frame{position:absolute;inset:0;display:block;width:100%;height:100%;border:0;background:transparent}" +
    "@keyframes ma-cal-in{from{opacity:0}}" +
    "@media (max-width:640px){.ma-cal{padding:0}.ma-cal-box{width:100%;height:100%;border:0;border-radius:0}.ma-cal-new{display:none}}" +
    "@media (prefers-reduced-motion:reduce){.ma-cal{animation:none}}";

  function label(el) {
    return (el.textContent || "").replace(/[‘’]/g, "'").replace(/\s+/g, " ").trim().toLowerCase();
  }

  function trigger(target) {
    var el = target && target.closest ? target.closest("a,button") : null;
    if (!el || el.closest(".ma-cal")) return null;
    return el.hasAttribute("data-cal") || TRIGGER.test(label(el)) ? el : null;
  }

  function onKey(e) {
    if (e.key === "Escape") {
      e.preventDefault();
      close();
    }
  }

  function close() {
    if (!overlay) return;
    overlay.parentNode.removeChild(overlay);
    overlay = null;
    document.documentElement.style.overflow = overflow;
    document.removeEventListener("keydown", onKey, true);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function open(from) {
    if (overlay) return;
    if (!document.getElementById("ma-cal-style")) {
      var style = document.createElement("style");
      style.id = "ma-cal-style";
      style.textContent = CSS;
      document.head.appendChild(style);
    }
    lastFocus = from;
    overlay = document.createElement("div");
    overlay.className = "ma-cal";
    overlay.setAttribute("data-lenis-prevent", "");
    overlay.innerHTML =
      '<div class="ma-cal-box" role="dialog" aria-modal="true" aria-label="' + TITLE + '">' +
      '<div class="ma-cal-head"><strong>' + TITLE + "</strong>" +
      '<a class="ma-cal-new" href="' + CAL + '" target="_blank" rel="noopener noreferrer">Open in a new tab ↗</a>' +
      '<button type="button" class="ma-cal-x" aria-label="Close">' +
      '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg>' +
      "</button></div>" +
      '<div class="ma-cal-body"><iframe class="ma-cal-frame" title="' + TITLE + '" src="' + CAL + '"></iframe></div>' +
      "</div>";
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay || (e.target.closest && e.target.closest(".ma-cal-x"))) close();
    });
    document.body.appendChild(overlay);
    overflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    document.addEventListener("keydown", onKey, true);
    overlay.querySelector(".ma-cal-x").focus();
  }

  document.addEventListener(
    "click",
    function (e) {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      var el = trigger(e.target);
      if (!el) return;
      e.preventDefault();
      open(el);
    },
    true
  );
})();
