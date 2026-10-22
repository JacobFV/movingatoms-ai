import * as THREE from 'three';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';

// Camera-independent Cycles radiance, stored separately from the authored albedo.
// Camera movement samples this cache; no ray tracer, shadow map or room-light bake runs here.
export async function createBakedLighting(renderer, scene, manifest) {
  const loader = new EXRLoader().setDataType(THREE.HalfFloatType);
  const textures = await Promise.all(manifest.reflections.map(url => loader.loadAsync(url)));
  const generator = new THREE.PMREMGenerator(renderer);
  const probes = textures.map(texture => {
    texture.mapping = THREE.EquirectangularReflectionMapping;
    const target = generator.fromEquirectangular(texture);
    texture.dispose();
    return target;
  });
  generator.dispose();
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.shadowMap.enabled = false;
  scene.environment = probes[0].texture;
  const materials = new Map();

  // linear: corrected presentation models store irradiance linearly; the original bake stored sqrt(radiance/16).
  function shade(material, linear = false) {
    material.onBeforeCompile = shader => {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nattribute vec3 lindenIrradiance;\nvarying vec3 vLindenGI;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvLindenGI = lindenIrradiance;');
      shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vLindenGI;');
      shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_maps>',
        THREE.ShaderChunk.lights_fragment_maps.replace('iblIrradiance += getIBLIrradiance( geometryNormal );',
          linear ? 'iblIrradiance += vLindenGI * PI;' : 'iblIrradiance += vLindenGI * vLindenGI * 16.0 * PI;'));
    };
    material.customProgramCacheKey = () => (linear ? 'linden-presentation-linear-v1' : 'linden-cycles-baked-v1');
    material.needsUpdate = true;
  }

  return {
    apply(root) {
      root.updateMatrixWorld(true);
      let count = 0;
      root.traverse(object => {
        if (!object.isMesh) return;
        const g = object.geometry;
        const baked = g.getAttribute('_linden_irradiance') || g.getAttribute('_LINDEN_IRRADIANCE');
        const presented = g.getAttribute('_presentation_irradiance') || g.getAttribute('_PRESENTATION_IRRADIANCE');
        // Corrected models reuse one mesh across several objects, so a geometry may already be converted.
        const gi = baked || presented || g.getAttribute('lindenIrradiance');
        if (!gi) throw new Error(`Baked lighting missing for ${object.name}`);
        const linear = baked ? false : presented ? true : Boolean(g.userData.lindenLinear);
        g.userData.lindenLinear = linear;
        g.setAttribute('lindenIrradiance', gi);
        for (const name of ['_linden_irradiance', '_LINDEN_IRRADIANCE', '_presentation_irradiance', '_PRESENTATION_IRRADIANCE']) g.deleteAttribute(name);
        object.castShadow = false;
        object.receiveShadow = false;
        const center = new THREE.Box3().setFromObject(object).getCenter(new THREE.Vector3());
        const probeIndex = center.x > -1 ? 1 : 0;
        const sources = Array.isArray(object.material) ? object.material : [object.material];
        const shaded = sources.map(source => {
          const key = `${source.uuid}:${probeIndex}:${linear}`;
          if (!materials.has(key)) {
            const material = source.clone();
            material.envMap = probes[probeIndex].texture;
            material.envMapIntensity = 1;
            material.envMapRotation.set(Math.PI / 2, 0, Math.PI / 2);
            if (material.map) material.map.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
            shade(material, linear);
            materials.set(key, material);
          }
          return materials.get(key);
        });
        object.material = Array.isArray(object.material) ? shaded : shaded[0];
        count++;
      });
      return count;
    },
    dispose() {
      for (const target of probes) target.dispose();
      for (const material of materials.values()) material.dispose();
    },
  };
}
