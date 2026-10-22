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

  function shade(material) {
    material.onBeforeCompile = shader => {
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nattribute vec3 medicalIrradiance;\nvarying vec3 vMedicalGI;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvMedicalGI = medicalIrradiance;');
      shader.fragmentShader = shader.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vMedicalGI;');
      shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_maps>',
        THREE.ShaderChunk.lights_fragment_maps.replace('iblIrradiance += getIBLIrradiance( geometryNormal );',
          'iblIrradiance += vMedicalGI * vMedicalGI * 16.0 * PI;'));
    };
    material.customProgramCacheKey = () => 'medical-cycles-baked-v1';
    material.needsUpdate = true;
  }

  return {
    apply(root) {
      root.updateMatrixWorld(true);
      let count = 0;
      root.traverse(object => {
        if (!object.isMesh) return;
        const gi = object.geometry.getAttribute('_medical_irradiance') || object.geometry.getAttribute('_MEDICAL_IRRADIANCE');
        if (!gi) throw new Error(`Baked lighting missing for ${object.name}`);
        object.geometry.setAttribute('medicalIrradiance', gi);
        object.geometry.deleteAttribute('_medical_irradiance');
        object.geometry.deleteAttribute('_MEDICAL_IRRADIANCE');
        object.castShadow = false;
        object.receiveShadow = false;
        const center = new THREE.Box3().setFromObject(object).getCenter(new THREE.Vector3());
        const probeIndex = manifest.reflectionRegions.findIndex(region => center.dot(new THREE.Vector3(...region.normal)) < region.maximum);
        if (probeIndex < 0) throw new Error('No Medical reflection region for ' + object.name);
        const sources = Array.isArray(object.material) ? object.material : [object.material];
        const shaded = sources.map(source => {
          const key = `${source.uuid}:${probeIndex}`;
          if (!materials.has(key)) {
            const material = source.clone();
            material.envMap = probes[probeIndex].texture;
            material.envMapIntensity = 1;
            material.envMapRotation.set(Math.PI / 2, 0, Math.PI / 2);
            if (material.map) material.map.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
            shade(material);
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
