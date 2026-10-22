(function () {
  "use strict";

  // Add future LiDAR scenes here. Change DEFAULT_SCENE when another scene should open first.
  var SCENES = [
    {
      id: "rotterdam",
      name: "Rotterdam",
      type: "Scene 01",
      url: "/rotterdam-scan/?embed=1&v=20261019-rotterdam-objects",
      page: "/lidarsample/",
      title: "Rotterdam LiDAR point cloud and reconstructed mesh"
    },
    {
      id: "factory-floor",
      name: "Factory Floor",
      type: "Scene 02",
      url: "/factory-floor-scan/?embed=1",
      page: "/lidarsample/",
      title: "Factory Floor LiDAR sample",
      revit: "/lidarsample/revit/Factory_Floor_Revit2027.zip?v=20261019-aligned-bim",
      revitSize: "806 MB"
    },
    {
      id: "linden-workshop",
      name: "Linden Workshop",
      type: "Scene 03",
      url: "/lidarsample2/viewer.html?embed=1&v=20261016-credit",
      page: "/lidarsample/",
      title: "Linden Workshop capture and reconstruction",
      revit: "/lidarsample/revit/Linden_Workshop_Revit2027.zip",
      revitSize: "245 MB"
    },
    {
      id: "medical-warehouse",
      name: "Medical Warehouse",
      type: "Scene 04",
      url: "/medical-warehouse-scan/?embed=1&v=20261016-credit",
      page: "/lidarsample/",
      title: "Medical Warehouse capture and reconstruction",
      revit: "/lidarsample/revit/Medical_Warehouse_Revit2027.zip",
      revitSize: "481 MB"
    }
  ];
  var DEFAULT_SCENE = "rotterdam";

  var frame = document.querySelector("[data-scene-frame]");
  var tabs = document.querySelector("[data-scene-tabs]");
  var count = document.querySelector("[data-scene-count]");
  var loading = document.querySelector("[data-loading]");
  var download = document.querySelector("[data-scene-download]");
  if (!frame || !tabs) return;
  var activeScene;

  function requestedScene() {
    var id = new URLSearchParams(location.search).get("scene");
    return SCENES.find(function (scene) { return scene.id === id; }) ||
      SCENES.find(function (scene) { return scene.id === DEFAULT_SCENE; }) || SCENES[0];
  }

  function setLoading(scene) {
    loading.classList.remove("is-hidden");
    loading.lastElementChild.textContent = "Entering " + scene.name;
  }

  // Switching scenes replaces the iframe element instead of changing its src. Changing src keeps
  // the old scene (its WebGL context, decoded models and pending downloads) alive until the next
  // one commits, so two heavy scenes overlap on the page's one thread. Removing the element ends
  // the old scene first; the next starts 60 ms later, and only the latest click wins.
  function mount(source) {
    var expected = source.split("?")[0];
    if (!frame.getAttribute("src")) { frame.setAttribute("src", source); watchFrame(frame, expected); return; }
    var old = frame, parent = old.parentNode, before = old.nextSibling;
    var next = old.cloneNode(false);
    next.removeAttribute("src");
    next.addEventListener("load", onFrameLoad);
    old.removeEventListener("load", onFrameLoad);
    old.setAttribute("src", "about:blank");
    old.remove();
    frame = next;
    setTimeout(function () {
      if (frame !== next) return;
      next.setAttribute("src", source);
      parent.insertBefore(next, before);
      watchFrame(next, expected);
    }, 60);
  }

  function select(scene, updateHistory) {
    document.body.dataset.scene = scene.id;
    setLoading(scene);
    var target = new URL(scene.url, location.origin);
    var options = new URLSearchParams(location.search);
    if (updateHistory && activeScene !== scene.id) options.delete("view");
    ["view", "hold", "points", "split", "mode", "paused"].forEach(function (name) {
      if (options.has(name)) target.searchParams.set(name, options.get(name));
    });
    var source = target.pathname + target.search;
    if (frame.getAttribute("src") !== source) mount(source);
    frame.title = scene.title;
    if (download) download.hidden = !scene.revit;
    if (download && scene.revit) {
      download.href = scene.revit;
      download.title = "Download the " + scene.name + " Revit 2027 model (.rvt, " + scene.revitSize + " zip)";
      download.querySelector("[data-download-size]").textContent = scene.revitSize;
    }
    document.title = scene.name + " · LiDAR Samples · Moving Atoms";
    tabs.querySelectorAll("[data-scene-id]").forEach(function (tab, index) {
      var active = tab.dataset.sceneId === scene.id;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
      tab.tabIndex = active ? 0 : -1;
      if (active) tab.scrollIntoView({ block: "nearest", inline: "nearest" });
      if (active && count) count.textContent = String(index + 1).padStart(2, "0") + " / " + String(SCENES.length).padStart(2, "0");
    });
    if (updateHistory) {
      var url = new URL(location.href);
      url.pathname = scene.page;
      if (scene.id === DEFAULT_SCENE) url.searchParams.delete("scene");
      else url.searchParams.set("scene", scene.id);
      if (activeScene !== scene.id) url.searchParams.delete("view");
      history.replaceState({ scene: scene.id }, "", url);
    }
    activeScene = scene.id;
  }

  tabs.innerHTML = "";
  SCENES.forEach(function (scene) {
    var button = document.createElement("button");
    button.className = "scene-tab";
    button.type = "button";
    button.role = "tab";
    button.dataset.sceneId = scene.id;
    button.innerHTML = '<span class="scene-type">' + scene.type + '</span><strong>' + scene.name + "</strong>";
    button.addEventListener("click", function () { select(scene, true); });
    tabs.appendChild(button);
  });

  tabs.addEventListener("keydown", function (event) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    var buttons = Array.from(tabs.querySelectorAll("[data-scene-id]"));
    var current = buttons.findIndex(function (button) { return button.getAttribute("aria-selected") === "true"; });
    var direction = event.key === "ArrowRight" ? 1 : -1;
    var next = buttons[(current + direction + buttons.length) % buttons.length];
    next.click();
    next.focus();
    event.preventDefault();
  });

  addEventListener("resize", function () {
    var active = tabs.querySelector('[aria-selected="true"]');
    if (active) active.scrollIntoView({ block: "nearest", inline: "nearest" });
  });

  // Hide the overlay as soon as the scene page is usable. The iframe "load" event alone is not enough:
  // it waits for every subresource inside the scene and in some browsers never reaches us for a freshly
  // inserted frame, which left "Entering …" on screen. The scene is same-origin, so we can also watch its
  // document directly, and a timeout guarantees the overlay never sticks.
  var watch = 0, giveUp = 0;
  function hideLoading() { clearInterval(watch); clearTimeout(giveUp); loading.classList.add("is-hidden"); }
  function onFrameLoad() { if (frame.getAttribute("src")) hideLoading(); }
  function watchFrame(target, expected) {
    clearInterval(watch); clearTimeout(giveUp);
    watch = setInterval(function () {
      if (frame !== target) return clearInterval(watch);
      try {
        var w = target.contentWindow, d = w && w.document;
        if (d && d.readyState !== "loading" && w.location.pathname === expected) hideLoading();
      } catch (e) { /* not yet navigated */ }
    }, 200);
    giveUp = setTimeout(hideLoading, 15000);
  }
  frame.addEventListener("load", onFrameLoad);
  addEventListener("message", function (event) {
    if (event.origin !== location.origin || event.source !== frame.contentWindow ||
        event.data?.type !== "movingatoms:view" || event.data.scene !== activeScene) return;
    var url = new URL(location.href);
    url.searchParams.set("view", event.data.view);
    history.replaceState({ scene: activeScene }, "", url);
  });
  select(requestedScene(), false);
})();
