const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
if (params.has('embed')) document.body.dataset.embedded = 'true';
const state = window.__rotterdamSample = { ready: false, mode: 'matched', errors: [], split: .5 };
let live, opening = false, tour, views = [], current = 0;

function stopTour() {
  clearInterval(tour); tour = null;
  $('tourBtn').setAttribute('aria-pressed', 'false');
  $('tourLabel').textContent = 'Start tour';
}
function setSplit(value) {
  const split = Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : .5;
  state.split = split;
  $('stage').style.setProperty('--split', `${split * 100}%`);
  $('divider').setAttribute('aria-valuenow', String(Math.round(split * 100)));
  $('divider').setAttribute('aria-valuetext', `${Math.round(split * 100)}% point cloud, ${Math.round((1 - split) * 100)}% mesh`);
  const width = $('stage').clientWidth, threshold = width < 721 ? 135 : 240;
  $('tagLeft').style.opacity = split * width > threshold ? '1' : '0';
  $('tagRight').style.opacity = (1 - split) * width > threshold ? '1' : '0';
  live?.setSplit(split);
}
const divider = $('divider');
divider.addEventListener('pointerdown', e => {
  if (e.button !== 0) return;
  divider.setPointerCapture(e.pointerId); divider.classList.add('active'); e.preventDefault();
});
divider.addEventListener('pointermove', e => {
  if (!divider.hasPointerCapture(e.pointerId)) return;
  const r = $('stage').getBoundingClientRect(); setSplit((e.clientX - r.left) / r.width);
});
for (const event of ['pointerup', 'pointercancel', 'lostpointercapture']) divider.addEventListener(event, () => divider.classList.remove('active'));
divider.addEventListener('keydown', e => {
  const step = e.shiftKey ? .1 : .02;
  if (e.key === 'ArrowLeft') setSplit(state.split - step);
  else if (e.key === 'ArrowRight') setSplit(state.split + step);
  else if (e.key === 'Home') setSplit(0);
  else if (e.key === 'End') setSplit(1);
  else return;
  e.preventDefault();
});

function selectView(index, share = true) {
  current = (index + views.length) % views.length;
  const view = views[current]; state.view = view.id;
  $('viewSelect').value = view.id;
  $('modelPreview').src = view.model; $('cloudPreview').src = view.points;
  live?.preset(view.camera);
  if (share) {
    const url = new URL(location.href); url.searchParams.set('view', view.id);
    history.replaceState(null, '', url);
    if (parent !== window) parent.postMessage({ type: 'movingatoms:view', scene: 'rotterdam', view: view.id }, location.origin);
  }
}
$('viewSelect').addEventListener('change', e => { stopTour(); selectView(views.findIndex(v => v.id === e.target.value)); });
$('tourBtn').addEventListener('click', () => {
  if (tour) return stopTour();
  $('tourBtn').setAttribute('aria-pressed', 'true'); $('tourLabel').textContent = 'Pause tour';
  tour = setInterval(() => selectView(current + 1), 9000);
});
document.addEventListener('visibilitychange', () => { if (document.hidden) stopTour(); });
$('aboutBtn').addEventListener('click', () => { stopTour(); $('aboutDialog').showModal(); });
new ResizeObserver(() => { live?.resize(); setSplit(state.split); }).observe($('stage'));
$('view').addEventListener('webglcontextlost', e => {
  e.preventDefault(); live?.exitObjects(); $('sceneModes').hidden = true; stopTour(); state.mode = 'matched'; state.errors.push('WebGL context lost');
  $('view').hidden = true; $('preview').hidden = false; $('modeStatus').hidden = false;
  $('loadText').textContent = '3D paused by this device. Matched views remain available; reload to retry.';
});

async function openLive() {
  if (live || opening) return;
  opening = true; stopTour(); $('liveBtn').hidden = true;
  $('loadText').textContent = 'Loading point cloud and mesh…';
  try {
    const { default: create } = await import('./scene.js?v=20261019-rotterdam-objects');
    live = await create({ canvas: $('view'), camera: views[current].camera,
      progress: (title, detail) => { $('loadText').textContent = detail ? `${title} · ${detail}` : title; }, onMove: stopTour });
    live.preset(views[current].camera); live.setSplit(state.split);
    $('view').hidden = false; live.resize(); $('preview').hidden = true;
    $('modeStatus').hidden = true; $('sceneModes').hidden = false; state.mode = 'live'; state.live = live.state;
    $('hint').textContent = 'Drag to orbit · scroll to zoom · WASD to move · Q / E for height';
  } catch (error) {
    state.errors.push(String(error)); state.mode = 'matched';
    $('view').hidden = true; $('preview').hidden = false;
    $('loadText').textContent = '3D could not load on this device. Explore the matched views, or reload to retry.';
  } finally { opening = false; }
}
$('liveBtn').addEventListener('click', openLive);

try {
  const response = await fetch('./views.json');
  if (!response.ok) throw new Error('Viewpoints could not be loaded');
  const data = await response.json(); views = data.views;
  for (const view of views) { const option = document.createElement('option'); option.value = view.id; option.textContent = view.label; $('viewSelect').append(option); }
  const requested = views.findIndex(v => v.id === params.get('view'));
  selectView(requested >= 0 ? requested : data.defaultView, false);
  setSplit(params.has('split') ? Number(params.get('split')) : .5);
  state.ready = true; $('loadText').textContent = 'Matched views';
  const lightweight = matchMedia('(pointer: coarse)').matches || innerWidth < 721 || navigator.connection?.saveData;
  if (params.get('mode') === 'matched' || (lightweight && params.get('mode') !== 'live')) $('liveBtn').hidden = false;
  else await openLive();
} catch (error) {
  state.errors.push(String(error)); $('loadText').textContent = 'The scene could not load. Please refresh to try again.';
}
