import { createViewer } from './live.js?v=20261020-perf1';

const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const views = [
  [6, 'Workshop'], [8, 'Textile shelves'], [15, 'Workshop entrance'],
  [16, 'Warehouse loads'], [17, 'Cartons and wire cart'], [19, 'Cutting workbench'],
  [45, 'Ladder and storage'], [71, 'Workshop reverse'], [82, 'Passage'],
  [86, 'Sewing machines'], [93, 'Paper stock'], [96, 'Utility cart'], [98, 'Bags and cases'],
];
if (params.has('embed')) document.body.dataset.embedded = 'true';
let viewer, split = .5;
let current = views.some(([id]) => id === Number(params.get('view'))) ? Number(params.get('view')) : 17;
const startTour = !params.has('view') && !params.has('hold') && !matchMedia('(prefers-reduced-motion: reduce)').matches;
let tourOn = startTour;

for (const [id, label] of views) {
  const option = document.createElement('option');
  option.value = id;
  option.textContent = label;
  $('viewSelect').append(option);
}

function showTour(value) {
  tourOn = value;
  $('tourBtn').setAttribute('aria-pressed', String(value));
  $('tourLabel').textContent = value ? 'Guided tour' : 'Start tour';
}

function setSplit(value) {
  if (!Number.isFinite(value)) return;
  split = Math.max(0, Math.min(1, value));
  $('stage').style.setProperty('--split', `${split * 100}%`);
  $('divider').setAttribute('aria-valuenow', Math.round(split * 100));
  viewer?.setSplit(split);
  const labelWidth = innerWidth < 721 ? 120 : 250;
  $('tagLeft').style.opacity = Math.max(0, Math.min(1, (split * innerWidth - labelWidth) / 40));
  $('tagRight').style.opacity = Math.max(0, Math.min(1, ((1 - split) * innerWidth - labelWidth) / 40));
}

function selectView(id) {
  current = Number(id);
  viewer?.selectView(current);
  $('viewSelect').value = current;
  const url = new URL(location.href);
  url.searchParams.set('view', current);
  history.replaceState(null, '', url);
  if (parent !== window) parent.postMessage({ type: 'movingatoms:view', scene: 'linden-workshop', view: current }, location.origin);
}

$('viewSelect').addEventListener('change', event => {
  if (event.target.value) selectView(event.target.value);
});
$('tourBtn').addEventListener('click', () => viewer?.setTour(!tourOn));
$('aboutBtn').addEventListener('click', () => $('aboutDialog').showModal());
const divider = $('divider');
divider.addEventListener('pointerdown', event => {
  divider.setPointerCapture(event.pointerId);
  divider.classList.add('active');
  event.preventDefault();
});
divider.addEventListener('pointermove', event => {
  if (divider.hasPointerCapture(event.pointerId)) setSplit(event.clientX / $('stage').clientWidth);
});
for (const name of ['pointerup', 'pointercancel']) divider.addEventListener(name, () => divider.classList.remove('active'));
divider.addEventListener('keydown', event => {
  const step = event.shiftKey ? .1 : .02;
  const changes = { ArrowLeft: split - step, ArrowRight: split + step, Home: 0, End: 1 };
  if (!(event.key in changes)) return;
  event.preventDefault();
  setSplit(changes[event.key]);
});
addEventListener('resize', () => setSplit(split));
setSplit(params.has('split') ? Number(params.get('split')) : .5);
showTour(tourOn);

async function main() {
  try {
    viewer = await createViewer($('view'), $('stage'), text => {
      $('loadText').textContent = text;
      const percent = text.match(/(\d+)%/);
      if (percent) $('loadBar').style.width = percent[1] + '%';
    }, showTour);
    viewer.selectView(current);
    viewer.setSplit(split);
    viewer.setActive(true);
    viewer.setTour(startTour);
    $('viewSelect').value = current;
    $('pointCount').textContent = `${(viewer.state.pointCount / 1e6).toFixed(1)}M`;
    $('loader').classList.add('done');
    window.lindenLive = viewer;
  } catch (error) {
    console.error(error);
    $('loadText').textContent = 'The 3D scene could not load. View the matched reference images instead.';
    const fallback = document.createElement('a');
    fallback.className = 'pill';
    fallback.href = '/lidarsample2/gallery.html?mode=photos';
    fallback.target = '_top';
    fallback.textContent = 'Open matched views';
    $('loader').append(fallback);
  }
}
window.lindenSample = { selectView, setSplit, get state() { return { ready: Boolean(viewer), split, view: current, tourOn }; } };
main();
