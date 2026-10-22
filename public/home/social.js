/* "What people are saying": real posts and comments, drawn to look like the native LinkedIn / X cards.
   Every entry is copied verbatim from its source and links back to it. To add an X post, push an entry like
   { type: "x", name, handle, avatar, verified, when, text, url, replies, reposts, likes, views }.
   Avatars are stored locally in v2/media/social/. */
(function () {
  "use strict";
  var POSTS = [
  {
    "type": "x",
    "name": "Moving Atoms (YC S26)",
    "handle": "MovingAtomsLab",
    "avatar": "/home/media/social/movingatomslab.webp",
    "when": "Oct 16",
    "text": "Moving Atoms (YC S26): Scan to Sim is here.\n\nSend us a LiDAR or SLAM scan of your factory floor, warehouse or yard, from any scanner. Upload multi-gigabyte scans straight from your browser (up to 200 GB per file). Within 48 hours you get back a simulation-ready digital twin of…",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "replies": 23,
    "reposts": 59,
    "likes": 674,
    "views": 86983,
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Max the VC 👨‍🚀",
    "handle": "mreiffy",
    "when": "Oct 17",
    "text": "We should chat :)",
    "url": "https://x.com/MovingAtomsLab/status/2111378871090135182",
    "avatar": "/home/media/social/x/mreiffy.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Mauricio Iglesias",
    "handle": "MauriAIglesias",
    "when": "Oct 18",
    "text": "Would love to meet! Have many customers in my area that would be interested in this.",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/mauriaiglesias.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Teo Rizvanovic",
    "handle": "teorizvanovic",
    "when": "Oct 18",
    "text": "This is cracked we would use this",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/teorizvanovic.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Zard",
    "handle": "zardthecreator",
    "when": "Oct 19",
    "text": "flagging where hidden geometry was inferred rather than measured is the detail that makes sim engineers trust it",
    "url": "https://x.com/MovingAtomsLab/status/2111378871090135182",
    "avatar": "/home/media/social/x/zardthecreator.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Pranav",
    "handle": "bpranav6",
    "when": "Oct 17",
    "text": "Amazing!! How to get in touch? And how are these priced and available formats? \n\nWe have the scans ready to go!!",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/bpranav6.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "spiro el khoury",
    "handle": "spirokhoury_",
    "when": "Oct 17",
    "text": "fully functioning digital twins in 48H?\nThat's super cool!\n\nI am sure mining giants would be keen for that.",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/spirokhoury_.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Ankita Shrivastava",
    "handle": "ankita080393",
    "when": "Oct 17",
    "text": "Scan straight to USD/IFC removes the ugliest step in simulation pipelines. How clean is the segmentation on a cluttered room? Curious where the model starts inventing objects.",
    "url": "https://x.com/MovingAtomsLab/status/2111378871090135182",
    "avatar": "/home/media/social/x/ankita080393.webp",
    "row": 0
  },
  {
    "type": "x-reply",
    "name": "Yashas Salankimatt",
    "handle": "YSalankimatt",
    "when": "Oct 18",
    "text": "This is super sick. Is there a certain spec of scan that it requires and what’s the roadmap to make it so that iPhone quality roomscale scans/splats can be reconstructed to sim?",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/ysalankimatt.webp",
    "row": 0
  },
  {
    "type": "li-comment",
    "name": "Alejandro Martin Barreiro",
    "avatar": "",
    "text": "The leap here isn't the scan, it's that every object comes back separated and measured rather than as a dense cloud nobody can actually use. On the delivery and asset side a point cloud is a photograph, an editable IFC model is something you can question and keep honest across the whole lifecycle, and the gap between those two is where most scan-to-BIM value quietly leaks away. \n\nThe part I'd want to stress test is how it holds up on a messy, cluttered real site versus a clean demo space, because that's where these things usually meet reality. Promising direction though.",
    "reactions": 1,
    "when": "1w",
    "profile": "https://au.linkedin.com/in/amartinbarreiroarchitect",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Alex Hilger",
    "handle": "swagdawgalex",
    "when": "Oct 15",
    "text": "Very cool! I’d love to meet",
    "url": "https://x.com/MovingAtomsLab/status/2110579918224666778",
    "avatar": "/home/media/social/x/swagdawgalex.webp",
    "row": 1
  },
  {
    "type": "li-comment",
    "name": "RealMan Robotics",
    "avatar": "/home/media/social/realman-robotics.webp",
    "text": "Very useful direction for robotics deployment. How accurate are the resulting models for downstream tasks like collision checking, reachability analysis, and robot simulation — not just visualization?",
    "reactions": 2,
    "when": "1w",
    "profile": "https://jp.linkedin.com/company/realmanrobotics",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Sekardeavion Ventures",
    "handle": "sekardea",
    "when": "Oct 18",
    "text": "Scan-to-sim could make it much easier to bring real industrial spaces into simulation. Turning an ordinary LiDAR or SLAM scan into a useful digital environment is a compelling workflow.",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/sekardea.webp",
    "row": 1
  },
  {
    "type": "li-comment",
    "name": "Eduardo Andreu",
    "avatar": "/home/media/social/eduardo-andreu.webp",
    "text": "Appreciate it is not your business model, but in construction, firms pay quite a bit for Scan to BIM services: either as surveys for new construction projects, or as a 'digital twin' for facilities & management teams.\n\nSurveyors currently do this doing a point cloud survey, and manually (yes...) modelling to a required level of detail in their brief.\n\nWould love to cover the story in my newsletter if you guys fancy a chat! https://aecfieldnotes.ai",
    "reactions": 6,
    "when": "1w",
    "profile": "https://uk.linkedin.com/in/eduardoandreu",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Awesome ESP（必回关版）",
    "handle": "suchagreatthing",
    "when": "Oct 17",
    "text": "89 labeled objects makes the scan much more usable.",
    "url": "https://x.com/MovingAtomsLab/status/2111378871090135182",
    "avatar": "/home/media/social/x/suchagreatthing.webp",
    "row": 1
  },
  {
    "type": "li-comment",
    "name": "Guillermo R.",
    "avatar": "",
    "text": "Separating and measuring every object from a raw scan in 48 hours is the ambitious part; ScanNet (Dai et al. 2017) showed why semantic completion from noisy LiDAR is hard. Emitting STEP and IFC keeps the model inspectable downstream.",
    "reactions": 1,
    "when": "1w",
    "profile": "https://es.linkedin.com/in/grfone",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Leif Adamec Rydenfalk",
    "handle": "adamecrydenfalk",
    "when": "Oct 17",
    "text": "scan to sim per site is the piece everyone skips. we are coming from the other end, every factory on one map as a twin first, then down to the floor. your scans are exactly the zoom level we are missing",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/adamecrydenfalk.webp",
    "row": 1
  },
  {
    "type": "li-comment",
    "name": "Siddhant Kale",
    "avatar": "/home/media/social/siddhant-kale.webp",
    "text": "Looks pretty cool. Wondering if you tackled any applications/case studies with cable/harness/rope object scenarios.",
    "reactions": 1,
    "when": "1w",
    "profile": "https://www.linkedin.com/in/siddhant-kale",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Rui Zhou",
    "handle": "zhourui9813",
    "when": "Oct 19",
    "text": "This is really cool! Curious how accurate the physical properties like mass, friction and articulation can get?",
    "url": "https://x.com/MovingAtomsLab/status/2111224248555712997",
    "avatar": "/home/media/social/x/zhourui9813.webp",
    "row": 1
  },
  {
    "type": "li-comment",
    "name": "Dylan Tobin",
    "avatar": "",
    "text": "This is cool! 48 hours is a bit of a bottleneck though. Would love to see this method sped up! 👏👏",
    "reactions": 1,
    "when": "1w",
    "profile": "https://www.linkedin.com/in/dylan-tobin313",
    "url": "https://www.linkedin.com/feed/update/urn:li:activity:7514548602183200768/",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Kimi Nguyen",
    "handle": "kimindiehacker",
    "when": "Oct 17",
    "text": "outputting files like USD and IFC makes integration into workflows smoother",
    "url": "https://x.com/MovingAtomsLab/status/2111378871090135182",
    "avatar": "/home/media/social/x/kimindiehacker.webp",
    "row": 1
  },
  {
    "type": "x-reply",
    "name": "Adam Barta",
    "handle": "AdamBartas",
    "when": "Oct 15",
    "text": "Super impressive visualization",
    "url": "https://x.com/MovingAtomsLab/status/2110579918224666778",
    "avatar": "/home/media/social/x/adambartas.webp",
    "row": 1
  }
];

  function esc(t) { return String(t == null ? "" : t).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function n(v) { return v >= 1e6 ? (v / 1e6).toFixed(1).replace(/\.0$/, "") + "M" : v >= 1e4 ? Math.round(v / 1e3) + "K" : v >= 1e3 ? (v / 1e3).toFixed(1).replace(/\.0$/, "") + "K" : String(v); }
  function para(t) { return esc(t).replace(/\n{2,}/g, "<br><br>").replace(/\n/g, "<br>"); }
  var GHOST = '<svg viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" fill="#38434f"/><circle cx="20" cy="15.5" r="7" fill="#9aa5b1"/><path d="M6 38c1.6-7.6 7.3-11.5 14-11.5S32.4 30.4 34 38z" fill="#9aa5b1"/></svg>';
  function av(p, cls) {
    if (p.avatar) return '<img class="' + cls + '" src="' + esc(p.avatar) + '" alt="" loading="lazy" width="40" height="40">';
    if (p.initials) return '<span class="' + cls + ' av-i">' + esc(p.initials) + "</span>";
    return '<span class="' + cls + ' av-g">' + GHOST + "</span>";
  }
  var IN = '<svg class="net-in" viewBox="0 0 24 24" aria-label="LinkedIn"><rect width="24" height="24" rx="4" fill="#0a66c2"/><path fill="#fff" d="M7.1 9.6h2.6V18H7.1zM8.4 5.6a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zM11.3 9.6h2.5v1.2c.4-.7 1.2-1.4 2.6-1.4 2.7 0 3.2 1.8 3.2 4.1V18h-2.6v-4c0-1 0-2.2-1.3-2.2s-1.6 1-1.6 2.1V18h-2.6z"/></svg>';
  var X = '<svg class="net-x" viewBox="0 0 24 24" aria-label="X"><path fill="currentColor" d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.66l-5.21-6.82-5.97 6.82H1.68l7.73-8.84L1.25 2.25h6.83l4.71 6.23zm-1.16 17.52h1.83L7.08 4.13H5.12z"/></svg>';
  var LIKE = '<span class="rx-i rx-like" aria-hidden="true"><svg viewBox="0 0 16 16"><path fill="#fff" d="M12.6 6.3H9.9l.4-2.2c.1-.8-.4-1.5-1.2-1.6L8.6 2.4 5.8 6.1v6.6h5.6c.6 0 1.1-.4 1.2-1l.9-4.1c.2-.7-.3-1.3-.9-1.3zM3 6.4h1.8v6.3H3z"/></svg></span>';
  function ico(d) { return '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="' + d + '"/></svg>'; }
  var I_REPLY = ico("M1.75 10c0-4.42 3.58-8 8-8h4.37c4.48 0 8.13 3.64 8.13 8.13 0 2.96-1.6 5.68-4.19 7.11l-8.06 4.46V18.1h-.07c-4.49.1-8.18-3.51-8.18-8.1zm8-6c-3.32 0-6 2.69-6 6 0 3.37 2.77 6.08 6.14 6.01l.35-.01h1.76v2.3l5.09-2.81c1.95-1.08 3.16-3.13 3.16-5.36 0-3.39-2.74-6.13-6.13-6.13z");
  var I_RT = ico("M4.5 3.88l4.43 4.14-1.37 1.46L5.5 7.55V16c0 1.1.9 2 2 2H13v2H7.5c-2.21 0-4-1.79-4-4V7.55L1.44 9.48.07 8.02zM16.5 6H11V4h5.5c2.21 0 4 1.79 4 4v8.45l2.06-1.93 1.37 1.46-4.43 4.14-4.43-4.14 1.37-1.46 2.06 1.93V8c0-1.1-.9-2-2-2z");
  var I_LIKE = ico("M16.7 5.5c-1.11-.03-2.4.49-3.48 2.03l-.82 1.15-.82-1.16c-1.08-1.53-2.37-2.04-3.48-2.02-1.11.03-2.17.6-2.84 1.62-.66 1.02-.83 2.35-.27 3.84.55 1.47 1.88 3.15 4.27 4.9.84.62 1.83 1.27 3.14 2.02 1.31-.75 2.3-1.4 3.14-2.02 2.39-1.75 3.72-3.43 4.27-4.9.56-1.49.39-2.82-.27-3.84-.67-1.02-1.73-1.6-2.84-1.62z");
  var I_VIEWS = ico("M8.75 21V3h2v18zM18 21V8.5h2V21zM4 21l.004-10h2L6 21zm9.248 0v-7h2v7z");

  function liComment(p) {
    return '<a class="post li" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
      '<header>' + av(p, "av") + '<span class="who"><b>' + esc(p.name) + '</b><small>Commented on the Scan to Model launch</small></span>' +
        '<span class="when">' + esc(p.when) + "</span>" + IN + "</header>" +
      '<p class="body clamp">' + para(p.text) + "</p>" +
      '<footer class="li-foot"><span class="rx">' + LIKE + (p.reactions || "") + '</span><span class="li-acts">Like <i>·</i> Reply</span></footer></a>';
  }
  function liPost(p) {
    return '<a class="post li li-main" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
      '<header>' + av({ initials: "AS" }, "av") + '<span class="who"><b>' + esc(p.name) + "</b><small>" + esc(p.sub) + "</small><small>" + esc(p.when) + ' · <span aria-label="Public">🌐</span></small></span>' + IN + "</header>" +
      '<p class="body clamp4">' + para(p.text) + "</p>" +
      (p.media ? '<span class="media"><img src="' + esc(p.media) + '" alt="" loading="lazy"><i class="play" aria-hidden="true"></i></span>' : "") +
      '<footer class="li-stats"><span class="rx">' + LIKE + n(p.reactions) + "</span><span>" + p.comments + " comments</span></footer>" +
      '<span class="li-bar"><span>Like</span><span>Comment</span><span>Repost</span><span>Send</span></span></a>';
  }
  function xPost(p) {
    return '<a class="post x" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
      "<header>" + av(p, "av") + '<span class="who"><b>' + esc(p.name) + (p.verified ? ' <svg class="tick" viewBox="0 0 22 22" aria-label="Verified"><path fill="#1d9bf0" d="M20.4 11c0-1.4-.8-2.6-2-3.2.4-1.3.2-2.7-.8-3.6-.9-1-2.3-1.2-3.6-.8C13.4 2.2 12.2 1.4 10.8 1.4S8.2 2.2 7.6 3.4c-1.3-.4-2.7-.2-3.6.8-1 .9-1.2 2.3-.8 3.6C2 8.4 1.2 9.6 1.2 11s.8 2.6 2 3.2c-.4 1.3-.2 2.7.8 3.6.9 1 2.3 1.2 3.6.8.6 1.2 1.8 2 3.2 2s2.6-.8 3.2-2c1.3.4 2.7.2 3.6-.8 1-.9 1.2-2.3.8-3.6 1.2-.6 2-1.8 2-3.2z"/><path fill="#fff" d="m9.5 15.3-3.4-3.4 1.3-1.3 2.1 2.1 5-5 1.3 1.3z"/></svg>' : "") +
        "</b><small>@" + esc(p.handle) + " · " + esc(p.when) + "</small></span>" + X + "</header>" +
      '<p class="body clamp">' + para(p.text) + "</p>" +
      '<footer class="x-foot"><span>' + I_REPLY + n(p.replies || 0) + "</span><span>" + I_RT + n(p.reposts || 0) + "</span><span>" + I_LIKE + n(p.likes || 0) + "</span><span>" + I_VIEWS + n(p.views || 0) + "</span></footer></a>";
  }
  function xReply(p) {
    return '<a class="post x" href="' + esc(p.url) + '" target="_blank" rel="noopener">' +
      "<header>" + av(p, "av") + '<span class="who"><b>' + esc(p.name) + "</b><small>@" + esc(p.handle) + " · " + esc(p.when) + "</small></span>" + X + "</header>" +
      '<p class="x-to">Replying to <span>@MovingAtomsLab</span></p>' +
      '<p class="body clamp">' + para(p.text) + "</p>" +
      '<footer class="x-foot"><span>' + I_REPLY + "</span><span>" + I_RT + "</span><span>" + I_LIKE + "</span><span>" + I_VIEWS + "</span></footer></a>";
  }
  var draw = { "li-comment": liComment, "li-post": liPost, x: xPost, "x-reply": xReply };

  var tracks = document.querySelectorAll(".wall-track");
  if (!tracks.length) return;
  // spread the posts across the rows so neighbours differ, then loop each row seamlessly
  var rows = Array.prototype.map.call(tracks, function () { return []; });
  POSTS.forEach(function (p, i) { rows[(p.row != null ? p.row : i) % rows.length].push(p); });
  Array.prototype.forEach.call(tracks, function (t, r) {
    var one = rows[r].map(function (p) { return "<li>" + draw[p.type](p) + "</li>"; }).join("");
    t.innerHTML = one;
    while (t.scrollWidth < innerWidth * 1.2 && t.children.length < 30) t.innerHTML += one;
    t.innerHTML += t.innerHTML;
    Array.prototype.forEach.call(t.children, function (li, i) {
      if (i >= t.children.length / 2) { li.setAttribute("aria-hidden", "true"); li.firstChild.tabIndex = -1; }
    });
  });
})();
