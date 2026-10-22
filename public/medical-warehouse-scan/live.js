import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { warmUp } from "/shared/warmup.js?v=20261020-warm1";
import { createSceneEditor } from "/shared/scene-editor/editor.js?v=20261014-medical-r016";
import { createBakedLighting } from "./baked-lighting.js?v=20261014-medical-r016";
export async function createViewer(
  canvas,
  stage,
  status,
  onTourChange = () => {},
  onViewChange = () => {},
) {
  const holdTour = new URLSearchParams(location.search).has("hold");
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    powerPreference: "high-performance",
    preserveDrawingBuffer: true,
  });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.9;
  renderer.autoClear = false;
  const reference = new THREE.Scene(),
    model = new THREE.Scene();
  reference.background = new THREE.Color("#10131a");
  model.background = new THREE.Color("#171b22");
  const camera = new THREE.PerspectiveCamera(83.58, 1, 0.035, 120);
  camera.up.set(0, 0, 1);
  const progress = { cloud: 0, scene: 0 };
  function report() {
    status(
      `Loading captured points and authored scene · ${Math.round((progress.cloud + progress.scene) * 50)}%`,
    );
  }
  async function binary(path, key) {
    const response = await fetch(path);
    if (!response.ok) throw Error(`${path}: ${response.status}`);
    const total = Number(response.headers.get("Content-Length"));
    if (!total || !response.body) return response.arrayBuffer();
    const result = new Uint8Array(total),
      reader = response.body.getReader();
    let offset = 0;
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      result.set(value, offset);
      offset += value.length;
      progress[key] = offset / total;
      report();
    }
    if (offset !== total) throw Error("Incomplete scene download");
    return result.buffer;
  }
  const response = await fetch("assets/render-manifest.json?v=20261014-medical-r016");
  if (!response.ok) throw Error("Rendered scene manifest unavailable");
  const manifest = await response.json();
  const [cloudBuffer, sceneBuffer, meta, lighting] =
    await Promise.all([
      binary(manifest.capture, "cloud"),
      binary(manifest.scene, "scene"),
      fetch("assets/cameras.json").then((r) => {
        if (!r.ok) throw Error("Cameras unavailable");
        return r.json();
      }),
      createBakedLighting(renderer, model, manifest),
    ]);
  status("Preparing the synchronized 3D view…");
  const dv = new DataView(cloudBuffer),
    count = dv.getUint32(4, true);
  if (
    dv.getUint32(0, true) !== 0x4350414d ||
    cloudBuffer.byteLength !== 32 + count * 9
  )
    throw Error("Invalid captured point data");
  const pointBudget = Math.min(
    count,
    Math.max(
      100000,
      Number(new URLSearchParams(location.search).get("points")) ||
        (matchMedia("(pointer: coarse)").matches ? 1000000 : count),
    ),
  );
  const low = new Float32Array(cloudBuffer, 8, 3),
    high = new Float32Array(cloudBuffer, 20, 3),
    geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    "position",
    new THREE.BufferAttribute(
      new Uint16Array(cloudBuffer, 32, count * 3),
      3,
      true,
    ),
  );
  geometry.setAttribute(
    "color",
    new THREE.BufferAttribute(
      new Uint8Array(cloudBuffer, 32 + count * 6, count * 3),
      3,
      true,
    ),
  );
  geometry.setDrawRange(0, pointBudget);
  const cloudMaterial = new THREE.ShaderMaterial({
    uniforms: { uSize: { value: 0.026 }, uScale: { value: 1 } },
    vertexShader: `uniform float uSize,uScale;attribute vec3 color;varying vec3 vColor;void main(){vColor=color;vec4 mv=modelViewMatrix*vec4(position,1.);gl_Position=projectionMatrix*mv;gl_PointSize=clamp(uSize*uScale/max(.01,-mv.z),1.,16.);}`,
    fragmentShader: `varying vec3 vColor;void main(){vec2 p=gl_PointCoord-.5;if(dot(p,p)>.25)discard;gl_FragColor=vec4(vColor,1.);}`,
  });
  const cloud = new THREE.Points(geometry, cloudMaterial);
  cloud.position.fromArray(low);
  cloud.scale.set(high[0] - low[0], high[1] - low[1], high[2] - low[2]);
  cloud.frustumCulled = false;
  reference.add(cloud);
  const gltf = await new GLTFLoader()
    .setMeshoptDecoder(MeshoptDecoder)
    .parseAsync(sceneBuffer, "");
  gltf.scene.rotation.x = Math.PI / 2;
  gltf.scene.updateMatrixWorld(true);
  lighting.apply(gltf.scene);
  // Owned UV crops and material colors stay separate from cached illumination.
  const authoredMaterials = new Map();
  gltf.scene.traverse((object) => {
    if (!object.isMesh) return;
    const material = object.material;
    if (Array.isArray(material))
      throw Error("Unexpected multi-material display primitive");
    authoredMaterials.set(material.uuid, material);
  });
  const originalBounds = new THREE.Box3().setFromObject(gltf.scene),
    groups = new Map();
  let sourceMeshes = 0;
  // Copy, dequantize and transform every mesh in ~12 ms slices (one per frame) instead of one
  // multi-second pass, so the page keeps responding while the scene is prepared.
  const sourceList = [];
  gltf.scene.traverse((object) => { if (object.isMesh) sourceList.push(object); });
  let sliceStart = performance.now();
  for (const object of sourceList) {
    sourceMeshes++;
    const material = object.material;
    if (Array.isArray(material))
      throw Error("Unexpected multi-material display primitive");
    const copy = object.geometry.clone();
    for (const name of Object.keys(copy.attributes)) {
      const a = copy.attributes[name];
      if (
        a.isInterleavedBufferAttribute ||
        a.normalized ||
        !(a.array instanceof Float32Array)
      ) {
        const n = a.itemSize,
          f = new Float32Array(a.count * n),
          get = [a.getX, a.getY, a.getZ, a.getW];
        for (let i = 0; i < a.count; i++)
          for (let c = 0; c < n; c++) f[i * n + c] = get[c].call(a, i);
        copy.setAttribute(name, new THREE.BufferAttribute(f, n));
      }
    }
    copy.applyMatrix4(object.matrixWorld);
    const key =
      material.uuid +
      "|" +
      Object.keys(copy.attributes).sort().join(",") +
      "|" +
      Boolean(copy.index);
    if (!groups.has(key)) groups.set(key, { material, geometries: [] });
    groups.get(key).geometries.push(copy);
    if (performance.now() - sliceStart > 12) {
      await new Promise(requestAnimationFrame);
      sliceStart = performance.now();
    }
  }
  const display = new THREE.Group();
  let batch = 0;
  for (const { material, geometries } of groups.values()) {
    const merged = mergeGeometries(geometries, false);
    if (!merged) throw Error("Could not combine display geometry");
    const mesh = new THREE.Mesh(merged, material);
    mesh.name = "Display_" + material.name;
    display.add(mesh);
    for (const g of geometries) g.dispose();
    if (++batch % 60 === 0) {
      status(`Preparing 3D materials · ${batch} / ${groups.size}`);
      await new Promise(requestAnimationFrame);
    }
  }
  model.add(display);
  const bounds = new THREE.Box3().setFromObject(display);
  if (
    bounds.min.distanceTo(originalBounds.min) > 0.005 ||
    bounds.max.distanceTo(originalBounds.max) > 0.005
  )
    throw Error("Display geometry bounds changed");
  // Upload textures and compile shaders before the first frame, in slices and in parallel,
  // instead of freezing the page inside the first render.
  await warmUp(renderer, [reference, model], camera, { status });
  let drawnFrames = 0,
    tourOn = false,
    tourU = 0,
    active = false,
    dirty = true,
    split = 0.5,
    layout = "wipe",
    yaw = 0,
    pitch = 0,
    current = 42,
    lastTime = performance.now(),
    width = 0,
    height = 0;
  const keys = new Set(),
    eye = new THREE.Vector3(),
    quat = new THREE.Quaternion(),
    scale = new THREE.Vector3();
  const tourViews = meta.views.filter((v) =>
    [42, 49, 51, 58, 64, 68, 72, 85, 86].includes(v.timestamp),
  );
  const tourPoses = tourViews.map((v) => {
    const p = new THREE.Vector3(),
      q = new THREE.Quaternion(),
      s = new THREE.Vector3();
    new THREE.Matrix4().set(...v.camera_to_canonical.flat()).decompose(p, q, s);
    return { p, q };
  });
  function setTour(value) {
    tourOn = Boolean(value);
    keys.clear();
    if (tourOn) {
      let nearest = 0,
        dist = Infinity;
      for (let i = 0; i < tourPoses.length; i++) {
        const d = camera.position.distanceToSquared(tourPoses[i].p);
        if (d < dist) {
          dist = d;
          nearest = i;
        }
      }
      tourU = nearest / tourPoses.length;
    } else setLook();
    onTourChange(tourOn);
    if (tourOn) dirty = true;
  }
  function setLook() {
    const dir = new THREE.Vector3();
    camera.getWorldDirection(dir);
    yaw = Math.atan2(dir.y, dir.x);
    pitch = Math.asin(THREE.MathUtils.clamp(dir.z, -1, 1));
  }
  function orient() {
    camera.lookAt(
      camera.position
        .clone()
        .add(
          new THREE.Vector3(
            Math.cos(pitch) * Math.cos(yaw),
            Math.cos(pitch) * Math.sin(yaw),
            Math.sin(pitch),
          ),
        ),
    );
  }
  function selectView(id) {
    setTour(false);
    const view = meta.views.find((v) => v.timestamp === Number(id));
    if (!view) return;
    current = Number(id);
    const matrix = new THREE.Matrix4().set(...view.camera_to_canonical.flat());
    matrix.decompose(eye, quat, scale);
    camera.position.copy(eye);
    camera.quaternion.copy(quat);
    setIntrinsics(view);
    setLook();
    dirty = true;
  }
  function setIntrinsics(view) {
    const intrinsics = view.K || meta.K;
    const imageWidth = view.width || meta.width, imageHeight = view.height || meta.height;
    camera.fov = (2 * Math.atan(imageHeight / (2 * intrinsics[1][1])) * 180) / Math.PI;
    camera.setViewOffset(imageWidth, imageHeight, imageWidth / 2 - intrinsics[0][2], imageHeight / 2 - intrinsics[1][2], imageWidth, imageHeight);
  }
  let pointer = null;
  canvas.addEventListener("pointerdown", (e) => {
    if (!active) return;
    setTour(false);
    canvas.focus({ preventScroll: true });
    pointer = { id: e.pointerId, x: e.clientX, y: e.clientY };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!active || pointer?.id !== e.pointerId) return;
    yaw -= (e.clientX - pointer.x) * 0.004;
    pitch = THREE.MathUtils.clamp(
      pitch - (e.clientY - pointer.y) * 0.004,
      -1.49,
      1.49,
    );
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    orient();
    dirty = true;
  });
  const end = (e) => {
    if (pointer?.id === e.pointerId) pointer = null;
  };
  canvas.addEventListener("pointerup", end);
  canvas.addEventListener("pointercancel", end);
  canvas.addEventListener(
    "wheel",
    (e) => {
      if (!active) return;
      e.preventDefault();
      setTour(false);
      const d = new THREE.Vector3();
      camera.getWorldDirection(d);
      camera.position.addScaledVector(d, -e.deltaY * 0.003);
      dirty = true;
    },
    { passive: false },
  );
  const valid = [
    "w",
    "a",
    "s",
    "d",
    "q",
    "e",
    "arrowup",
    "arrowdown",
    "arrowleft",
    "arrowright",
  ];
  addEventListener("keydown", (e) => {
    if (
      !active ||
      document.querySelector("dialog[open]") ||
      e.target.closest?.('select,button,input,a,[role="slider"]')
    )
      return;
    const k = e.key.toLowerCase();
    if (valid.includes(k)) {
      setTour(false);
      keys.add(k);
      e.preventDefault();
    }
  });
  addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));
  addEventListener("blur", () => keys.clear());
  const observer = new ResizeObserver(() => (dirty = true));
  observer.observe(stage);
  const modeOptions = { renderer, camera, canvas, stage, comparisonScene: model,
    manifestUrl: '/medical-warehouse-scan/assets/editor-manifest.json?v=20261014-medical-r016',
    invalidate() { dirty = true; },
    onEnter() {
      const saved = { active, tourOn, tourU };
      setTour(false); active = false; keys.clear(); pointer = null;
      return saved;
    },
    onExit(saved) {
      active = saved.active; setTour(saved.tourOn); tourU = saved.tourU;
      dirty = true;
    },
  };
  const editor = createSceneEditor(modeOptions);
  window.sceneEditor = editor;
  function frame(now) {
    requestAnimationFrame(frame);
    const elapsed = (now - lastTime) / 1000;
    const dt = Math.min(elapsed, 0.05);
    lastTime = now;
    if (editor.active) { editor.frame(dt); return; }
    if (!active || document.hidden) return;
    if (tourOn && (!holdTour || dirty)) {
      // A slow render or resumed tab must not skip through stops continuously.
      // Leave a useful viewing interval after each expensive frame completes.
      if (!holdTour) tourU = (((tourU + Math.min(Math.max(elapsed, 0), 1) / 90) % 1) + 1) % 1;
      const n = Math.min(tourPoses.length, tourViews.length);
      if (!n) return;
      const i = Math.min(n - 1, Math.floor(tourU * n));
      // Hold each calibrated comparison view, then cut to the next stop.
      const changed = current !== tourViews[i].timestamp;
      if (changed) {
        current = tourViews[i].timestamp;
        onViewChange(current);
      }
      // Recorded stops hold a fixed camera. Redrawing the same large scene
      // every frame wastes GPU time and can delay the pause button.
      if (changed || dirty) {
        setIntrinsics(tourViews[i]);
        camera.position.copy(tourPoses[i].p);
        camera.quaternion.copy(tourPoses[i].q);
        dirty = true;
      }
    }
    if (keys.size) {
      const forward = new THREE.Vector3(Math.cos(yaw), Math.sin(yaw), 0),
        right = new THREE.Vector3(Math.sin(yaw), -Math.cos(yaw), 0),
        speed = dt * 2.2;
      if (keys.has("w") || keys.has("arrowup"))
        camera.position.addScaledVector(forward, speed);
      if (keys.has("s") || keys.has("arrowdown"))
        camera.position.addScaledVector(forward, -speed);
      if (keys.has("a") || keys.has("arrowleft"))
        camera.position.addScaledVector(right, -speed);
      if (keys.has("d") || keys.has("arrowright"))
        camera.position.addScaledVector(right, speed);
      if (keys.has("q")) camera.position.z -= speed;
      if (keys.has("e")) camera.position.z += speed;
      dirty = true;
    }
    if (!dirty) return;
    drawnFrames++;
    const w = stage.clientWidth,
      h = stage.clientHeight;
    if (!w || !h) return;
    if (w !== width || h !== height) {
      width = w;
      height = h;
      renderer.setSize(w, h, false);
    }
    camera.aspect = (layout === "side" ? w / 2 : w) / h;
    camera.updateProjectionMatrix();
    cloudMaterial.uniforms.uScale.value =
      (h * renderer.getPixelRatio()) /
      (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
    renderer.setScissorTest(true);
    const border = Math.round(layout === "side" ? w / 2 : w * split);
    renderer.setViewport(0, 0, layout === "side" ? w / 2 : w, h);
    renderer.setScissor(0, 0, border, h);
    if (border > 0) {
      renderer.clear();
      renderer.render(reference, camera);
    }
    renderer.setViewport(
      layout === "side" ? w / 2 : 0,
      0,
      layout === "side" ? w / 2 : w,
      h,
    );
    renderer.setScissor(border, 0, w - border, h);
    if (w - border > 0) {
      renderer.clear();
      renderer.render(model, camera);
    }
    renderer.setScissorTest(false);
    dirty = false;
  }
  requestAnimationFrame(frame);
  selectView(42);
  return {
    editor,
    selectView,
    setTour,
    setSplit(value) {
      split = value;
      dirty = true;
    },
    setLayout(value) {
      layout = value;
      dirty = true;
    },
    setActive(value) {
      active = value;
      keys.clear();
      dirty = true;
    },
    get state() {
      return {
        ready: true,
        active,
        tourOn,
        drawnFrames,
        lighting: "cycles-baked",
        lightCache: manifest.revision,
        view: current,
        pointCount: pointBudget,
        totalPointCount: count,
        assetCount: manifest.assetCount,
        revision: manifest.revision,
        workInProgress: Boolean(manifest.workInProgress),
        sourceMeshPrimitives: sourceMeshes,
        displayBatches: groups.size,
        materialCount: authoredMaterials.size,
        exposure: renderer.toneMappingExposure,
        split,
        layout,
        camera: camera.position.toArray(),
        quaternion: camera.quaternion.toArray(),
        bounds: { min: bounds.min.toArray(), max: bounds.max.toArray() },
        drawCalls: renderer.info.render.calls,
      };
    },
  };
}
