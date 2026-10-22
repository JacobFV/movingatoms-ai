// Camera-independent Cycles irradiance and reflections from this factory.
// Source recipe and cache builder: RobotGym infra/factory_render/.
import * as THREE from 'three';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';

const IRRADIANCE_SCALE = 16;
const detailFunctions = 'varying vec3 vFactoryGI;';

// linear: corrected presentation models store irradiance linearly; the original bake stored sqrt(radiance/16).
function surfaceShader(material, linear=false) {
  material.onBeforeCompile=shader => {
    shader.vertexShader=shader.vertexShader.replace('#include <common>',
      '#include <common>\nattribute vec3 factoryIrradiance;\nvarying vec3 vFactoryGI;');
    shader.vertexShader=shader.vertexShader.replace('#include <worldpos_vertex>',
      '#include <worldpos_vertex>\nvFactoryGI=factoryIrradiance;');
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>', '#include <common>\n'+detailFunctions);
    // DIFFUSE bake excludes albedo and stores outgoing unit-albedo radiance.
    // Convert it to irradiance before Three's Lambert BRDF divides by PI.
    const maps=THREE.ShaderChunk.lights_fragment_maps
      .replace('iblIrradiance += getIBLIrradiance( geometryNormal );',
        linear ? 'iblIrradiance += vFactoryGI * PI;' : `iblIrradiance += vFactoryGI * vFactoryGI * ${IRRADIANCE_SCALE.toFixed(1)} * PI;`);
    // The physical IBL path already evaluates both diffuse and specular
    // multiscattering. Feeding the direct-diffuse accumulator too would count
    // the baked illumination twice.
    shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_maps>',maps);
    // Keep the measured area lights' view-dependent highlights. Their diffuse
    // contribution is already in the Cycles bake.
    shader.fragmentShader=shader.fragmentShader.replace('#include <lights_fragment_begin>',
      '#include <lights_fragment_begin>\nreflectedLight.directDiffuse=vec3(0.);');
  };
  material.customProgramCacheKey=()=>linear?'factory-presentation-linear-v1':`factory-light-v4`;
  material.needsUpdate=true;
}

export async function createFactoryLighting(renderer, scene, urls) {
  const loader=new EXRLoader().setDataType(THREE.HalfFloatType);
  const images=await Promise.all(urls.map(url=>loader.loadAsync(url)));
  const pmrem=new THREE.PMREMGenerator(renderer);
  const targets=images.map(texture=>{
    texture.mapping=THREE.EquirectangularReflectionMapping;
    const result=pmrem.fromEquirectangular(texture);texture.dispose();return result;
  });
  pmrem.dispose();
  renderer.toneMapping=THREE.AgXToneMapping;
  renderer.toneMappingExposure=1.0;
  renderer.shadowMap.enabled=false;
  scene.environment=targets[0].texture;scene.environmentIntensity=1;
  const yaw=THREE.MathUtils.degToRad(-4.05);
  const fixtures=[[-1.13915944,-3.46161342,4.65453339],[2.96091390,-3.41256547,4.65253353],
    [-.86793041,-8.37564850,4.58153343],[3.07206964,-8.43024349,4.64553308]];
  // These panels used to be RectAreaLights. Area lights cost several texture lookups per pixel per
  // light, and five of them made every frame about 3x more expensive. A panel this small, seen from
  // metres away, lights surfaces like a downward spotlight of the same luminous intensity (luminance
  // x area, one-sided): rendered side by side the two differ by under 2/255 on average.
  for(const [u,v,z] of fixtures) {
    const x=u*Math.cos(yaw)-v*Math.sin(yaw), y=u*Math.sin(yaw)+v*Math.cos(yaw);
    const luminance=180/(1.32*.16*Math.PI);
    const spot=new THREE.SpotLight(new THREE.Color(1,.947,.86),luminance*1.32*.16,0,THREE.MathUtils.degToRad(80),1,2);
    spot.position.set(x,y,z-.035);spot.target.position.set(x,y,0);scene.add(spot,spot.target);
  }
  const bayLuminance=700/(8*4*Math.PI);
  const bay=new THREE.SpotLight(new THREE.Color(.85,.92,1),bayLuminance*8*4,0,THREE.MathUtils.degToRad(80),1,2);
  bay.position.set(0,-10.5,3.5);bay.target.position.set(0,-1,1.5);scene.add(bay,bay.target);
  return {
    apply(root) {
      root.updateMatrixWorld(true);
      let meshes=0;
      root.traverse(object=>{
        if(!object.isMesh)return;
        const baked=object.geometry.getAttribute('_factory_irradiance') || object.geometry.getAttribute('_FACTORY_IRRADIANCE');
        let gi=baked || object.geometry.getAttribute('_presentation_irradiance') || object.geometry.getAttribute('_PRESENTATION_IRRADIANCE');
        const linear=!baked;
        const materials=Array.isArray(object.material)?object.material:[object.material];
        // Emissive fixture instances do not need diffuse illumination.
        if(!gi && materials.every(m=>m.userData.factorySurface==='luminaire')) {
          gi=new THREE.Float32BufferAttribute(new Float32Array(object.geometry.getAttribute('position').count*3),3);
        }
        // Corrected models may not carry the luminaire tag; unlit parts fall back to no baked diffuse.
        if(!gi){console.warn(`Baked lighting missing for ${object.name}`);gi=new THREE.Float32BufferAttribute(new Float32Array(object.geometry.getAttribute('position').count*3),3);}
        object.geometry.setAttribute('factoryIrradiance',gi);
        object.castShadow=false;object.receiveShadow=false;
        const center=new THREE.Box3().setFromObject(object).getCenter(new THREE.Vector3());
        const probe=targets[center.y>1.5 ? 1:0].texture;
        object.material=(Array.isArray(object.material)?object.material:[object.material]).map(source=>{
          const mat=source.clone();mat.envMap=probe;mat.envMapIntensity=1;
          mat.envMapRotation.set(Math.PI/2,0,Math.PI/2);
          if(mat.map)mat.map.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
          surfaceShader(mat,linear);return mat;
        });
        if(object.material.length===1)object.material=object.material[0];
        meshes++;
      });
      root.userData.factoryLighting={meshes,baked:true,recipe:'20261006-station-render1'};
    },
    dispose(){for(const target of targets)target.dispose();},
  };
}
