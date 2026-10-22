import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";

// Geometry/textures are shared; transforms and canonical poses belong to each mode.
const resources = new Map();
export function loadModel(url, progress) {
  if (!resources.has(url)) {
    const promise = new GLTFLoader()
      .setMeshoptDecoder(MeshoptDecoder)
      .loadAsync(url, progress)
      .catch((error) => {
        resources.delete(url);
        throw error;
      });
    resources.set(url, promise);
  }
  return resources.get(url).then((gltf) => gltf.scene.clone(true));
}
export function previewScene(comparison) {
  const scene = new THREE.Scene();
  scene.background = comparison.background.clone();
  scene.environment = comparison.environment;
  scene.environmentIntensity = 0.55;
  scene.environmentRotation.set(Math.PI / 2, 0, Math.PI / 2);
  return scene;
}
export async function loadWorld(manifestUrl, renderer, progress) {
  const response = await fetch(manifestUrl);
  if (!response.ok) throw Error("Object inventory could not load");
  const manifest = await response.json();
  const root = await loadModel(
    new URL(manifest.scene, new URL(manifestUrl, location.href)).href,
    progress,
  );
  root.rotation.x = Math.PI / 2;
  root.updateMatrixWorld(true);
  const assets = new Map(),
    receiversOnly = new Set(manifest.shadowReceiversOnly || []);
  root.traverse((node) => {
    if (!node.userData.assetRoot) return;
    const { assetId: id } = node.userData,
      name = manifest.names?.[id] || node.userData.assetName;
    if (!id || !name || assets.has(id)) throw Error("Invalid object ownership");
    node.updateMatrix();
    const asset = {
      id,
      name,
      root: node,
      original: node.matrix.clone(),
      meshes: [],
      bounds: new THREE.Box3().setFromObject(node),
    };
    node.traverse((mesh) => {
      if (!mesh.isMesh) return;
      mesh.userData.editorOwner = id;
      mesh.castShadow = !receiversOnly.has(id);
      mesh.receiveShadow = true;
      for (const material of Array.isArray(mesh.material)
        ? mesh.material
        : [mesh.material])
        if (material.map)
          material.map.anisotropy = Math.min(
            8,
            renderer.capabilities.getMaxAnisotropy(),
          );
      asset.meshes.push(mesh);
    });
    if (!asset.meshes.length) throw Error("Empty article: " + id);
    assets.set(id, asset);
  });
  if (assets.size !== manifest.assetCount)
    throw Error("Object count does not match the validated export");
  return { root, assets, manifest };
}
export function addWorldLight(scene, root, manifest) {
  const bounds = new THREE.Box3().setFromObject(root),
    center = bounds.getCenter(new THREE.Vector3());
  const span = Math.max(
    bounds.max.x - bounds.min.x,
    bounds.max.y - bounds.min.y,
  );
  const light = new THREE.DirectionalLight(
    0xfff3dd,
    manifest.directIntensity || 0.9,
  );
  light.position.copy(center).add(new THREE.Vector3(-3, -4, span));
  light.target.position.copy(center);
  light.castShadow = true;
  light.shadow.mapSize.setScalar(
    matchMedia("(pointer: coarse)").matches ? 1024 : 2048,
  );
  Object.assign(light.shadow.camera, {
    left: -span / 2,
    right: span / 2,
    top: span / 2,
    bottom: -span / 2,
    near: 0.1,
    far: span * 3,
  });
  light.shadow.normalBias = 0.012;
  light.shadow.bias = -0.00005;
  scene.add(root, light, light.target);
  return light;
}

// One renderer, one input owner. A transition exits/restores the previous mode
// before its successor captures renderer and comparison state.
const coordinators = new WeakMap();
export function sceneModes(renderer) {
  if (coordinators.has(renderer)) return coordinators.get(renderer);
  const exits = new Map();
  let current = "compare";
  const buttons = {
    compare: document.getElementById("compareBtn"),
    objects: document.getElementById("objectBtn"),
    robot: document.getElementById("robotBtn"),
  };
  function update() {
    for (const [name, button] of Object.entries(buttons))
      if (button) button.setAttribute("aria-pressed", String(current === name));
  }
  const api = {
    register(name, exit) {
      exits.set(name, exit);
    },
    enter(name) {
      if (current !== name) exits.get(current)?.();
      current = name;
      update();
    },
    leave(name) {
      if (current === name) {
        current = "compare";
        update();
      }
    },
    get current() {
      return current;
    },
  };
  buttons.compare?.addEventListener("click", () => api.enter("compare"));
  coordinators.set(renderer, api);
  update();
  return api;
}
