import * as THREE from 'three';
import { loadWorld, previewScene, addWorldLight, sceneModes } from '../scene-runtime/world.js?v=20261011-chest1';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Both scene adapters use this editor. Its camera and transforms are temporary;
// comparison geometry and the native authored masters are never modified.
export function createSceneEditor({ renderer, camera: comparisonCamera, canvas, stage,
  comparisonScene, manifestUrl, loadObjects = loadWorld, onEnter, onExit, invalidate }) {
  const entry = document.getElementById('objectBtn');
  // Older cached entry HTML must keep its comparison working during rollout.
  if (!entry) return { active: false, frame() {} };
  const scene = previewScene(comparisonScene);
  scene.backgroundRotation.copy(comparisonScene.backgroundRotation);
  scene.backgroundIntensity = comparisonScene.backgroundIntensity;
  const modes = sceneModes(renderer);
  modes.register('objects', exit);
  const camera = comparisonCamera.clone();
  const assets = new Map(), raycaster = new THREE.Raycaster();
  const selectionBox = new THREE.Box3Helper(new THREE.Box3(), 0xc1ff00);
  selectionBox.material.depthTest = false;
  selectionBox.material.transparent = true;
  selectionBox.material.opacity = .9;
  selectionBox.renderOrder = 1000;
  selectionBox.visible = false;
  scene.add(selectionBox);
  let active = false, loading = false, ready = false, requested = false;
  let selected = null, loadPromise = null, dirty = true, savedRenderer, adapterState;
  let controls = null, orbit = null, dragBefore = null, gesture = null;
  let history = [], cursor = 0, drawnFrames = 0, error = null;
  const keys = new Set(), bindings = new AbortController();
  const panel = document.createElement('aside');
  panel.className = 'object-editor';
  panel.hidden = true;
  panel.setAttribute('aria-label', 'Object selection');
  panel.innerHTML = `
    <div class="editor-status" role="status" aria-live="polite">Select an object</div>
    <p class="editor-note">Temporary changes · return to reset</p>
    <details class="editor-browser" open>
      <summary>Objects <span class="editor-count"></span></summary>
      <label class="editor-search-label">Find an object<input type="search" class="editor-search" placeholder="Search objects" autocomplete="off"></label>
      <select class="editor-list" size="7" aria-label="Scene objects"></select>
    </details>
    <div class="editor-selection" hidden>
      <strong class="editor-name"></strong>
      <div class="editor-position">${['X', 'Y', 'Z'].map(axis => `<label>${axis}<input type="number" step="0.01" data-axis="${axis.toLowerCase()}" aria-label="${axis} position in metres"></label>`).join('')}</div>
      <div class="editor-options"><button type="button" data-action="focus">Focus object</button><label><input type="checkbox" class="editor-snap"> Snap 10 cm</label></div>
    </div>`;
  const toolbar = document.createElement('div');
  toolbar.className = 'editor-toolbar';
  toolbar.hidden = true;
  toolbar.innerHTML = `<button type="button" class="pill" data-action="back">← Back to comparison</button><button type="button" class="pill" data-action="undo" disabled>Undo</button><button type="button" class="pill" data-action="redo" disabled>Redo</button><button type="button" class="pill" data-action="reset">Reset scene</button>`;
  const hint = document.createElement('p');
  hint.className = 'editor-help';
  hint.hidden = true;
  hint.textContent = 'Click to select · drag arrows to move · drag background to look · scroll to zoom';
  stage.append(panel, toolbar, hint);
  const $ = name => panel.querySelector('.editor-' + name);
  const caption = stage.querySelector('.title p');
  const comparisonCaption = caption?.textContent;
  entry.disabled = false;

  function redraw(shadows = false) {
    dirty = true;
    if (shadows) renderer.shadowMap.needsUpdate = true;
    if (selected) {
      selected.root.updateWorldMatrix(true, true);
      selectionBox.box.setFromObject(selected.root);
      selected.bounds.copy(selectionBox.box);
      const position = selected.root.getWorldPosition(new THREE.Vector3());
      for (const input of panel.querySelectorAll('[data-axis]'))
        if (document.activeElement !== input) input.value = position[input.dataset.axis].toFixed(3);
    }
    invalidate();
  }
  function updateHistoryButtons() {
    toolbar.querySelector('[data-action="undo"]').disabled = cursor === 0;
    toolbar.querySelector('[data-action="redo"]').disabled = cursor === history.length;
  }
  function record(asset, before) {
    asset.root.updateMatrix();
    const after = asset.root.matrix.clone();
    if (before.equals(after)) return;
    history.splice(cursor);
    history.push({ id: asset.id, before: before.clone(), after });
    cursor = history.length;
    updateHistoryButtons();
    redraw(true);
  }
  function restoreMatrix(asset, matrix) {
    matrix.decompose(asset.root.position, asset.root.quaternion, asset.root.scale);
    asset.root.updateMatrix();
    asset.root.updateWorldMatrix(true, true);
    asset.bounds.setFromObject(asset.root);
  }
  function select(id) {
    if (!active || !ready) return false;
    if (dragBefore) cancelGesture();
    const asset = assets.get(id);
    selected = asset || null;
    selectionBox.visible = Boolean(asset);
    $('selection').hidden = !asset;
    if (asset) {
      controls.attach(asset.root);
      $('name').textContent = asset.name;
      $('status').textContent = 'Selected object';
      $('list').value = id;
      if (matchMedia('(max-width: 720px)').matches) $('browser').open = false;
    } else {
      controls.detach();
      $('list').value = '';
      $('status').textContent = 'Select an object';
    }
    redraw();
    return Boolean(asset);
  }
  function pick(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    raycaster.near = camera.near;
    raycaster.far = camera.far;
    raycaster.setFromCamera(new THREE.Vector2(
      (clientX - rect.left) / rect.width * 2 - 1,
      -(clientY - rect.top) / rect.height * 2 + 1), camera);
    scene.updateMatrixWorld(true);
    const candidates = [];
    for (const asset of assets.values()) {
      if (raycaster.ray.intersectsBox(asset.bounds)) candidates.push(...asset.meshes);
    }
    const hit = raycaster.intersectObjects(candidates, false)[0];
    return hit ? select(hit.object.userData.editorOwner) : select(null);
  }
  function populateList() {
    const query = $('search').value.trim().toLowerCase();
    const list = $('list');
    list.replaceChildren();
    for (const asset of assets.values()) {
      if (query && !`${asset.name} ${asset.id}`.toLowerCase().includes(query)) continue;
      const option = document.createElement('option');
      option.value = asset.id;
      option.textContent = asset.name;
      list.append(option);
    }
    list.value = selected?.id || '';
    $('count').textContent = `${list.options.length} / ${assets.size}`;
  }
  function makeControls() {
    if (controls) return;
    controls = new TransformControls(camera, canvas);
    controls.setMode('translate');
    controls.setSpace('world');
    controls.setSize(matchMedia('(pointer: coarse)').matches ? 1.15 : .85);
    scene.add(controls.getHelper());
    controls.enabled = false;
    orbit = new OrbitControls(camera, canvas);
    orbit.enabled = false;
    orbit.enableDamping = false;
    orbit.minDistance = .12;
    orbit.maxDistance = 90;
    orbit.addEventListener('change', () => redraw());
    controls.addEventListener('dragging-changed', event => {
      orbit.enabled = active && !event.value;
      if (gesture && event.value) gesture.transform = true;
      if (event.value && selected) { selected.root.updateMatrix(); dragBefore = selected.root.matrix.clone(); }
      if (!event.value && dragBefore && selected) { record(selected, dragBefore); dragBefore = null; }
    });
    controls.addEventListener('objectChange', () => redraw(true));
    controls.addEventListener('change', () => redraw());
  }
  async function load() {
    const world = await loadObjects(manifestUrl, renderer, event => {
      if (!requested) return;
      $('status').textContent = event.lengthComputable && event.total
        ? `Loading objects · ${Math.round(event.loaded / event.total * 100)}%`
        : `Loading objects · ${(event.loaded / 1048576).toFixed(0)} MB`;
    });
    for (const [id, asset] of world.assets) assets.set(id, asset);
    // Already-baked object-preserving displays can share their GPU geometry and
    // materials. Only their cloned transforms belong to this editing session.
    if (world.baked) scene.add(world.root);
    else addWorldLight(scene, world.root, world.manifest);
    ready = true;
    populateList();
  }
  async function enter() {
    if (requested) return;
    modes.enter('objects');
    requested = true;
    active = true;
    loading = !ready;
    error = null;
    adapterState = onEnter();
    makeControls();
    camera.copy(comparisonCamera);
    savedRenderer = { shadow: renderer.shadowMap.enabled, autoUpdate: renderer.shadowMap.autoUpdate,
      type: renderer.shadowMap.type, autoClear: renderer.autoClear, pixelRatio: renderer.getPixelRatio() };
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.shadowMap.autoUpdate = false;
    renderer.autoClear = true;
    renderer.setPixelRatio(Math.min(devicePixelRatio, matchMedia('(pointer: coarse)').matches ? 1 : 1.5));
    document.body.dataset.editor = 'true';
    if (caption) caption.textContent = 'Select an object to move it. Changes reset when you return.';
    panel.hidden = toolbar.hidden = hint.hidden = false;
    $('status').textContent = ready ? 'Select an object' : 'Loading editable objects…';
    if (matchMedia('(max-width: 720px)').matches) $('browser').open = false;
    orbit.target.copy(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(3).add(camera.position));
    orbit.update();
    // OrbitControls normalizes its spherical representation on update. Keep
    // the initial shared view bit-for-bit identical to the comparison camera.
    camera.copy(comparisonCamera);
    orbit.enabled = controls.enabled = ready;
    redraw(true);
    try {
      loadPromise ||= load();
      await loadPromise;
      if (!requested) return;
      loading = false;
      orbit.enabled = controls.enabled = true;
      $('status').textContent = 'Select an object';
      redraw(true);
      canvas.focus({ preventScroll: true });
    } catch (failure) {
      error = failure.message;
      loading = false;
      loadPromise = null;
      $('status').textContent = 'Objects could not load. Return to comparison and try again.';
      console.error(failure);
    }
  }
  function cancelGesture() {
    const interrupted = Boolean(dragBefore);
    if (dragBefore && selected) restoreMatrix(selected, dragBefore);
    dragBefore = null;
    if (controls?.dragging) controls.dragging = false;
    if (controls) controls.axis = null;
    if (gesture && canvas.hasPointerCapture(gesture.id)) canvas.releasePointerCapture(gesture.id);
    gesture = null;
    keys.clear();
    if (interrupted) redraw(true);
  }
  function reset() {
    cancelGesture();
    for (const asset of assets.values()) {
      restoreMatrix(asset, asset.original);
    }
    history = []; cursor = 0;
    updateHistoryButtons();
    redraw(true);
  }
  function exit() {
    if (!requested) return;
    reset();
    controls.detach();
    controls.enabled = orbit.enabled = false;
    selected = null;
    selectionBox.visible = false;
    $('selection').hidden = true;
    requested = active = false;
    modes.leave('objects');
    gesture = null; keys.clear();
    panel.hidden = toolbar.hidden = hint.hidden = true;
    delete document.body.dataset.editor;
    if (caption) caption.textContent = comparisonCaption;
    renderer.shadowMap.enabled = savedRenderer.shadow;
    renderer.shadowMap.autoUpdate = savedRenderer.autoUpdate;
    renderer.shadowMap.type = savedRenderer.type;
    renderer.autoClear = savedRenderer.autoClear;
    renderer.setPixelRatio(savedRenderer.pixelRatio);
    onExit(adapterState);
    invalidate();
    entry.focus({ preventScroll: true });
  }
  function undo() {
    if (dragBefore) cancelGesture();
    if (!cursor) return;
    const change = history[--cursor];
    restoreMatrix(assets.get(change.id), change.before); select(change.id);
    updateHistoryButtons(); redraw(true);
  }
  function redo() {
    if (dragBefore) cancelGesture();
    if (cursor === history.length) return;
    const change = history[cursor++];
    restoreMatrix(assets.get(change.id), change.after); select(change.id);
    updateHistoryButtons(); redraw(true);
  }
  function setPosition(id, values) {
    const asset = assets.get(id);
    if (!active || !asset || !values.every(Number.isFinite)) return false;
    if (dragBefore) cancelGesture();
    asset.root.updateMatrix();
    const before = asset.root.matrix.clone();
    const local = asset.root.parent.worldToLocal(new THREE.Vector3(...values));
    asset.root.position.copy(local);
    asset.root.updateWorldMatrix(true, true);
    asset.bounds.setFromObject(asset.root);
    record(asset, before); redraw(true);
    return true;
  }
  function focus() {
    if (!selected) return;
    const bounds = new THREE.Box3().setFromObject(selected.root), center = bounds.getCenter(new THREE.Vector3());
    const distance = Math.max(.7, bounds.getSize(new THREE.Vector3()).length() * .9);
    const direction = camera.position.clone().sub(orbit.target).normalize();
    camera.position.copy(center).addScaledVector(direction, distance);
    orbit.target.copy(center); orbit.update(); redraw();
  }
  const actions = { back: exit, reset, undo, redo, focus };
  for (const element of [panel, toolbar]) element.addEventListener('click', event => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (action) actions[action]();
  });
  $('search').addEventListener('input', populateList);
  $('list').addEventListener('change', event => select(event.target.value));
  $('snap').addEventListener('change', event => controls.setTranslationSnap(event.target.checked ? .1 : null));
  for (const input of panel.querySelectorAll('[data-axis]')) input.addEventListener('change', () => {
    if (!selected) return;
    const position = selected.root.getWorldPosition(new THREE.Vector3());
    const value = Number(input.value);
    if (input.value.trim() && Number.isFinite(value)) {
      position[input.dataset.axis] = value;
      setPosition(selected.id, position.toArray());
    } else input.value = position[input.dataset.axis].toFixed(3);
    redraw();
  });
  entry.addEventListener('click', enter);
  canvas.addEventListener('pointerdown', event => {
    if (!active || !ready) return;
    canvas.focus({ preventScroll: true });
    gesture = { id: event.pointerId, x: event.clientX, y: event.clientY, transform: Boolean(controls.axis) };
  }, { capture: true, signal: bindings.signal });
  canvas.addEventListener('pointerup', event => {
    if (!active || gesture?.id !== event.pointerId) return;
    const tap = !gesture.transform && Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) < 5;
    gesture = null;
    if (tap) pick(event.clientX, event.clientY);
  }, { signal: bindings.signal });
  canvas.addEventListener('pointercancel', () => {
    if (!active) return;
    cancelGesture();
    orbit.enabled = ready; keys.clear(); redraw(true);
  }, { capture: true, signal: bindings.signal });
  canvas.addEventListener('webglcontextrestored', () => redraw(true), { signal: bindings.signal });
  addEventListener('keydown', event => {
    if (!active || event.target.closest?.('input,select,button,a,summary')) return;
    const key = event.key.toLowerCase();
    if ((event.ctrlKey || event.metaKey) && key === 'z') {
      event.preventDefault(); event.shiftKey ? redo() : undo(); return;
    }
    if (key === 'escape') { select(null); event.preventDefault(); return; }
    if (['w', 'a', 's', 'd', 'q', 'e', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
      keys.add(key); event.preventDefault();
    }
  }, { signal: bindings.signal });
  addEventListener('keyup', event => keys.delete(event.key.toLowerCase()), { signal: bindings.signal });
  addEventListener('blur', () => keys.clear(), { signal: bindings.signal });
  addEventListener('popstate', exit, { signal: bindings.signal });
  addEventListener('pagehide', exit, { signal: bindings.signal });

  // Download the editable objects before Object selection is clicked, so it opens without a
  // long wait. Standalone desktop pages warm up a few seconds after the comparison view is
  // ready. Inside the /lidarsample switcher (embedded) visitors hop between scenes, and a
  // background download plus parse would compete with the next scene, so there it only starts
  // when the visitor reaches for the button. Phones load on demand to save data and memory.
  const warm = () => {
    if (loadPromise) return;
    loadPromise = load();
    loadPromise.catch(() => { if (!requested) loadPromise = null; });
  };
  if (!matchMedia('(pointer: coarse)').matches && !navigator.connection?.saveData) {
    if (document.body.dataset.embedded === 'true') entry?.addEventListener('pointerenter', warm, { once: true, signal: bindings.signal });
    else setTimeout(warm, 3000);
  }
  entry?.addEventListener('focus', warm, { once: true, signal: bindings.signal });

  return {
    enter, exit, select, setPosition, undo, redo, reset,
    get active() { return active; },
    frame(dt) {
      if (!active || document.hidden) return;
      const width = stage.clientWidth, height = stage.clientHeight;
      if (!width || !height) return;
      if (canvas.clientWidth !== width || renderer.getSize(new THREE.Vector2()).x !== width || camera.aspect !== width / height) {
        renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix(); redraw();
      }
      if (keys.size && !controls.dragging) {
        const forward = camera.getWorldDirection(new THREE.Vector3()); forward.z = 0; forward.normalize();
        const right = forward.clone().cross(camera.up).normalize(), move = new THREE.Vector3();
        if (keys.has('w') || keys.has('arrowup')) move.add(forward);
        if (keys.has('s') || keys.has('arrowdown')) move.sub(forward);
        if (keys.has('d') || keys.has('arrowright')) move.add(right);
        if (keys.has('a') || keys.has('arrowleft')) move.sub(right);
        if (keys.has('e')) move.z += 1;
        if (keys.has('q')) move.z -= 1;
        move.multiplyScalar(dt * 2.2); camera.position.add(move); orbit.target.add(move); orbit.update(); redraw();
      }
      if (!dirty) return;
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, width, height);
      renderer.clear(); renderer.render(scene, camera);
      drawnFrames++; dirty = false;
    },
    get state() {
      return { active, loading, ready, error, assetCount: assets.size, selected: selected?.id || null,
        drawnFrames, undoCount: cursor, redoCount: history.length - cursor,
        camera: camera.position.toArray(), quaternion: camera.quaternion.toArray(),
        fov: camera.fov, aspect: camera.aspect,
        assets: [...assets.values()].map(asset => ({ id: asset.id, name: asset.name,
          position: asset.root.getWorldPosition(new THREE.Vector3()).toArray(),
          componentCount: asset.meshes.length, moved: !asset.root.matrix.equals(asset.original) })) };
    },
  };
}
