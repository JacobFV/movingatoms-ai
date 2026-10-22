/* Moving Atoms first-party event tracking (Umami). Cookieless; no personal data.
   Events: cta (button text + href), outbound (host + url), mailto, scroll (25/50/75/100),
   engine_chapter (data-engine card), contact_submit, video_play. */
(function () {
  var track = function (name, data) { try { if (window.umami && umami.track) umami.track(name, data || {}); } catch (e) {} };
  var host = location.host;
  var CTA = /book a demo|start on robotgym|open robotgym|let.s talk|explore the platform|explore environments|meet atom|create an account|start free|get in touch|contact us|view all articles|all demos|newsletter/i;

  // Clicks: CTAs, outbound links, mailto
  document.addEventListener("click", function (e) {
    var a = e.target && e.target.closest ? e.target.closest("a,button") : null;
    if (!a) return;
    var text = (a.textContent || "").replace(/\s+/g, " ").trim().slice(0, 60);
    var href = a.getAttribute && a.getAttribute("href") || "";
    var section = (a.closest("section,header,footer,nav") || {}).className || "";
    section = String(section).split(" ")[0].slice(0, 40);
    if (/^mailto:/i.test(href)) { track("mailto", { address: href.replace(/^mailto:/i, "").split("?")[0], text: text, section: section }); return; }
    if (/^https?:\/\//i.test(href)) { try { var u = new URL(href); if (u.host !== host) track("outbound", { host: u.host, url: u.href.slice(0, 120), text: text, section: section }); } catch (err) {} }
    if (CTA.test(text)) track("cta", { text: text, href: href.slice(0, 120), section: section, page: location.pathname });
    var card = a.closest && a.closest(".ma-eng-item"); if (card) track("engine_chapter", { chapter: (card.querySelector("strong") || {}).textContent || card.dataset.i });
  }, true);

  // Scroll depth (once per threshold per page)
  var marks = [25, 50, 75, 100], seen = {};
  var onScroll = function () {
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight; if (max <= 0) return;
    var p = Math.round((h.scrollTop || window.pageYOffset) / max * 100);
    marks.forEach(function (m) { if (p >= m && !seen[m]) { seen[m] = 1; track("scroll", { depth: m, page: location.pathname }); } });
  };
  addEventListener("scroll", onScroll, { passive: true }); addEventListener("load", onScroll);

  // Contact form (mailto composer) + product videos
  document.addEventListener("submit", function (e) { var f = e.target; if (f && f.id === "contact-form") track("contact_submit", { page: location.pathname }); }, true);
  document.addEventListener("play", function (e) { var v = e.target; if (v && v.tagName === "VIDEO") track("video_play", { src: (v.currentSrc || v.src || "").split("/").pop().slice(0, 60) }); }, true);

  // Time on page (sent when leaving; Umami batches on pagehide)
  var t0 = Date.now();
  addEventListener("pagehide", function () { track("leave", { seconds: Math.round((Date.now() - t0) / 1000), page: location.pathname }); });
})();
