// Rotterdam display derivative. Same registered geometry and materials as the
// AgentThread source; full-canvas scissor comparison matches the other samples.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {EXRLoader} from 'three/addons/loaders/EXRLoader.js';
import {createSceneEditor} from '/shared/scene-editor/editor.js?v=20261019-rotterdam-objects';
const MODEL='./';
const linear=v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4;
function half(v){const s=v&32768?-1:1,e=(v>>10)&31,f=v&1023;return e===0?s*2**-14*f/1024:e===31?(f?NaN:s*Infinity):s*2**(e-15)*(1+f/1024);}
async function getBuffer(url,progress,total){const r=await fetch(url);if(!r.ok)throw Error('Scene data could not be loaded.');const reader=r.body.getReader(),chunks=[];let n=0;while(true){const {done,value}=await reader.read();if(done)break;chunks.push(value);n+=value.byteLength;progress('Loading the reconstruction',`${(n/1048576).toFixed(1)} / ${(total/1048576).toFixed(1)} MB`);}const blob=new Blob(chunks),head=new Uint8Array(await blob.slice(0,2).arrayBuffer());if(head[0]!==31||head[1]!==139)return blob.stream();if(typeof DecompressionStream!=='undefined')return blob.stream().pipeThrough(new DecompressionStream('gzip'));const {gunzipSync}=await import('three/addons/libs/fflate.module.js');return new Blob([gunzipSync(new Uint8Array(await blob.arrayBuffer()))]).stream();}
async function getScene(manifest,progress){
 if(!manifest.parts)return new Response(await getBuffer(MODEL+'assets/'+manifest.model,progress,manifest.compressed_bytes)).arrayBuffer();
 const result=new Uint8Array(manifest.uncompressed_bytes);let next=0,loaded=0;
 async function partWorker(){while(next<manifest.parts.length){const p=manifest.parts[next++],stream=await getBuffer(MODEL+'assets/'+p.file,()=>{},p.compressed_bytes),chunk=await new Response(stream).arrayBuffer();if(chunk.byteLength!==p.bytes)throw Error('A scene section is incomplete.');result.set(new Uint8Array(chunk),p.offset);loaded+=p.compressed_bytes;progress('Loading the reconstruction',`${(loaded/1048576).toFixed(1)} / ${(manifest.compressed_bytes/1048576).toFixed(1)} MB`);}}
 await Promise.all([partWorker(),partWorker(),partWorker()]);return result.buffer;
}
export default async function createLive({canvas,camera:initial,progress,onMove=()=>{}}){
 const r=await fetch(MODEL+'assets/manifest.json');if(!r.ok)throw Error('The 3D manifest is unavailable.');const manifest=await r.json();if(!['rotterdam-owner-cache-v3'].includes(manifest.format))throw Error('Unsupported scene format.');
 const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});renderer.setPixelRatio(Math.min(devicePixelRatio,1.25));renderer.setClearColor(0x000000,0);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.AgXToneMapping;renderer.toneMappingExposure=2**(manifest.exposure??0);renderer.shadowMap.enabled=false;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
 const scene=new THREE.Scene();const camera=new THREE.PerspectiveCamera(60,1,.025,350);camera.up.set(0,0,1);const controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.minDistance=.15;controls.maxDistance=160;controls.maxPolarAngle=Math.PI-.01;
 const state={ready:false,owners:manifest.owners.length,triangles:manifest.triangles,vertices:manifest.vertices,master:manifest.master_sha256,errors:[],renderCalls:0};
 const pointPromise=loadPoints();const bufferPromise=getScene(manifest,progress);const exr=await new EXRLoader().loadAsync(MODEL+'assets/'+manifest.reflection);exr.mapping=THREE.EquirectangularReflectionMapping;const pmrem=new THREE.PMREMGenerator(renderer);pmrem.compileEquirectangularShader();const probe=pmrem.fromEquirectangular(exr);exr.dispose();pmrem.dispose();
 const mat=new THREE.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness:1,metalness:1,envMap:probe.texture,envMapIntensity:1});mat.envMapRotation.set(Math.PI/2,0,Math.PI/2);
 const texLoader=new THREE.TextureLoader();const textures=await Promise.all(['paving.png','concrete-detail.png','trailer-side.png'].map(n=>texLoader.loadAsync(MODEL+'assets/'+n)));for(const [i,tex] of textures.entries()){tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());tex.wrapS=tex.wrapT=i===2?THREE.ClampToEdgeWrapping:THREE.RepeatWrapping;}
 mat.onBeforeCompile=shader=>{Object.assign(shader.uniforms,{pavingTexture:{value:textures[0]},concreteTexture:{value:textures[1]},trailerTexture:{value:textures[2]}});shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nattribute vec3 cachedGI;attribute vec2 surface;attribute float textureId;attribute vec2 detailUV;varying vec3 vCachedGI;varying vec2 vSurface;varying float vTextureId;varying vec2 vDetailUV;').replace('#include <worldpos_vertex>','#include <worldpos_vertex>\nvCachedGI=cachedGI;vSurface=surface;vTextureId=textureId;vDetailUV=detailUV;');shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec3 vCachedGI;varying vec2 vSurface;varying float vTextureId;varying vec2 vDetailUV;uniform sampler2D pavingTexture;uniform sampler2D concreteTexture;uniform sampler2D trailerTexture;').replace('#include <color_fragment>','#include <color_fragment>\nif(vTextureId>.5&&vTextureId<1.5)diffuseColor.rgb*=texture2D(pavingTexture,vDetailUV).rgb*vec3(.43,.38,.32);else if(vTextureId>1.5&&vTextureId<2.5)diffuseColor.rgb*=texture2D(concreteTexture,vDetailUV).rgb;else if(vTextureId>2.5)diffuseColor.rgb*=texture2D(trailerTexture,vDetailUV).rgb;').replace('#include <roughnessmap_fragment>','#include <roughnessmap_fragment>\nroughnessFactor=clamp(vSurface.y,0.08,1.0);').replace('#include <metalnessmap_fragment>','#include <metalnessmap_fragment>\nmetalnessFactor=vSurface.x;').replace('#include <lights_fragment_maps>',THREE.ShaderChunk.lights_fragment_maps.replace('iblIrradiance += getIBLIrradiance( geometryNormal );','iblIrradiance += vCachedGI * PI;'));};mat.customProgramCacheKey=()=> 'rotterdam-complete-v3-local-textures-full-baked-diffuse';

 const buffer=await bufferPromise;progress('Opening the scene','Preparing individually selectable equipment…');const dv=new DataView(buffer);if(buffer.byteLength!==manifest.uncompressed_bytes)throw Error('Scene buffer is incomplete.');const precision=true,normalOffset=precision?12:6,colorOffset=precision?18:12,lightOffset=precision?21:15,surfaceOffset=precision?27:21,colorLUT=Uint16Array.from({length:256},(_,i)=>Math.round(linear(i/255)*65535));const lo=manifest.bounds.min,span=manifest.bounds.max.map((v,i)=>v-lo[i]),meshes=[];
 for(let k=0;k<manifest.owners.length;k++){
  const o=manifest.owners[k],n=o.vertices,p=new Float32Array(n*3),normal=new Int16Array(n*3),color=new Uint16Array(n*3),light=new Uint16Array(n*3),surface=new Uint8Array(n*2),textureId=new Uint8Array(n),detailUV=new Float32Array(n*2);
  for(let i=0;i<n;i++){const at=o.vertexOffset+i*o.stride;for(let c=0;c<3;c++){p[i*3+c]=(precision?dv.getFloat32(at+c*4,true):lo[c]+dv.getUint16(at+c*2,true)/65535*span[c])-o.pivot[c];normal[i*3+c]=dv.getInt16(at+normalOffset+c*2,true);color[i*3+c]=colorLUT[dv.getUint8(at+colorOffset+c)];light[i*3+c]=dv.getUint16(at+lightOffset+c*2,true);}surface[i*2]=dv.getUint8(at+surfaceOffset);surface[i*2+1]=dv.getUint8(at+surfaceOffset+1);textureId[i]=dv.getUint8(at+29);detailUV[i*2]=dv.getFloat32(at+30,true);detailUV[i*2+1]=dv.getFloat32(at+34,true);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p,3));g.setAttribute('normal',new THREE.BufferAttribute(normal,3,true));g.setAttribute('color',new THREE.BufferAttribute(color,3,true));g.setAttribute('cachedGI',new THREE.Float16BufferAttribute(light,3));g.setAttribute('surface',new THREE.BufferAttribute(surface,2,true));g.setAttribute('textureId',new THREE.BufferAttribute(textureId,1));g.setAttribute('detailUV',new THREE.BufferAttribute(detailUV,2));g.setIndex(new THREE.BufferAttribute(new Uint32Array(buffer,o.indexOffset,o.indexBytes/4).slice(),1));g.computeBoundingSphere();const mesh=new THREE.Mesh(g,mat);mesh.castShadow=true;mesh.receiveShadow=true;mesh.name=o.id;mesh.userData=o;mesh.position.fromArray(o.pivot);scene.add(mesh);meshes.push(mesh);
  if(k%25===0){progress('Opening the scene',`${k+1} / ${manifest.owners.length} assets ready`);await new Promise(resolve=>setTimeout(resolve,0));}
 }
 let dirty=true,split=.5,editor=null;const keys=new Set();
 canvas.addEventListener('pointerdown',()=>{if(editor?.active)return;canvas.focus({preventScroll:true});onMove();});
 const moving=['KeyW','KeyA','KeyS','KeyD','KeyQ','KeyE','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'];canvas.addEventListener('keydown',e=>{if(editor?.active)return;if(moving.includes(e.code)){e.preventDefault();keys.add(e.code);onMove();}});canvas.addEventListener('keyup',e=>keys.delete(e.code));canvas.addEventListener('blur',()=>keys.clear());controls.addEventListener('change',()=>dirty=true);canvas.addEventListener('wheel',onMove,{passive:true});
 function preset(v){camera.position.fromArray(v.eye);camera.fov=v.vfov;controls.target.copy(camera.position).addScaledVector(new THREE.Vector3(...v.forward),4);camera.lookAt(controls.target);camera.updateProjectionMatrix();controls.update();dirty=true;state.camera={position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};}
 function resize(){const r=canvas.parentElement.getBoundingClientRect();if(!r.width||!r.height)return;renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();dirty=true;}
 let last=performance.now();function loop(now){requestAnimationFrame(loop);const dt=Math.min((now-last)/1000,.05);last=now;if(editor?.active){editor.frame(dt);return;}if(keys.size&&canvas.offsetParent){const forward=new THREE.Vector3();camera.getWorldDirection(forward);forward.z=0;forward.normalize();const right=new THREE.Vector3().crossVectors(forward,camera.up).normalize(),d=new THREE.Vector3();if(keys.has('KeyW')||keys.has('ArrowUp'))d.add(forward);if(keys.has('KeyS')||keys.has('ArrowDown'))d.sub(forward);if(keys.has('KeyD')||keys.has('ArrowRight'))d.add(right);if(keys.has('KeyA')||keys.has('ArrowLeft'))d.sub(right);if(keys.has('KeyE'))d.z+=1;if(keys.has('KeyQ'))d.z-=1;d.multiplyScalar(dt*2);camera.position.add(d);controls.target.add(d);dirty=true;}if(dirty&&canvas.offsetParent){renderPair();dirty=false;state.renderCalls=renderer.info.render.calls;state.camera={position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov};}}

 const pointData=await pointPromise;const sourceScene=pointData.scene,cloud=pointData.cloud;state.points=pointData.count;state.coverage=pointData.coverage;const sky=await texLoader.loadAsync(MODEL+'assets/'+manifest.sky);sky.mapping=THREE.EquirectangularReflectionMapping;sky.colorSpace=THREE.SRGBColorSpace;scene.background=sky;scene.backgroundRotation.set(Math.PI/2,0,0);scene.backgroundIntensity=1.3;
 function getPose(){return {position:camera.position.toArray(),target:controls.target.toArray(),fov:camera.fov,aspect:camera.aspect};}
 function setPose(p){camera.position.fromArray(p.position);controls.target.fromArray(p.target);camera.fov=p.fov;camera.updateProjectionMatrix();controls.update();dirty=true;}
 function renderPair(){
  const {width:w,height:h}=canvas.getBoundingClientRect(),sx=Math.round(split*w);
  renderer.setViewport(0,0,w,h);camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setScissorTest(true);
  if(sx>0){renderer.setScissor(0,0,sx,h);renderer.render(sourceScene,camera);}
  if(sx<w){renderer.setScissor(sx,0,w-sx,h);renderer.render(scene,camera);}
  renderer.setScissorTest(false);state.camera=getPose();state.sharedCamera=true;state.split=split;
 }
 preset(initial);resize();
 editor=createSceneEditor({renderer,camera,canvas,stage:canvas.parentElement,comparisonScene:scene,
  async loadObjects(){
   const root=new THREE.Group(),assets=new Map();
   for(const source of meshes){
    const mesh=source.clone();root.add(mesh);mesh.updateMatrix();mesh.updateWorldMatrix(true,false);
    mesh.userData.editorOwner=source.name;
    assets.set(source.name,{id:source.name,name:source.userData.label||source.name,root:mesh,
     original:mesh.matrix.clone(),meshes:[mesh],bounds:new THREE.Box3().setFromObject(mesh)});
   }
   return {root,assets,baked:true};
  },
  onEnter(){onMove();keys.clear();controls.enabled=false;},
  onExit(){controls.enabled=true;keys.clear();resize();dirty=true;},
  invalidate(){dirty=true;}
 });
 Object.defineProperty(state,'editor',{enumerable:true,get:()=>editor.state});
 requestAnimationFrame(loop);state.ready=true;progress('Ready','');
 return {state,preset,resize,getPose,setPose,exitObjects(){editor.exit();},setSplit(value){split=Math.max(0,Math.min(1,value));dirty=true;}};

}

async function loadPoints(){
 const res=await fetch('assets/points-full-r002.json');if(!res.ok)throw Error('Point-cloud manifest is unavailable.');const m=await res.json(),pos=new Float32Array(m.point_count*3),rgb=new Uint8Array(m.point_count*3);let offset=0;
 for(const part of m.parts){const raw=await new Response(await getBuffer('assets/'+part.file,()=>{},part.bytes)).arrayBuffer();if(raw.byteLength!==part.points*9)throw Error('Point-cloud section is incomplete.');const v=new DataView(raw);for(let i=0;i<part.points;i++)for(let c=0;c<3;c++){pos[(offset+i)*3+c]=m.bounds.min[c]+v.getUint16(i*9+c*2,true)/65535*(m.bounds.max[c]-m.bounds.min[c]);rgb[(offset+i)*3+c]=v.getUint8(i*9+6+c);}offset+=part.points;}
 const scene=new THREE.Scene();scene.background=new THREE.Color(0x181e22);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('color',new THREE.BufferAttribute(rgb,3,true));g.computeBoundingSphere();
 const mat=new THREE.ShaderMaterial({uniforms:{size:{value:2.4}},vertexShader:'attribute vec3 color;varying vec3 vColor;uniform float size;void main(){vColor=color;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);gl_PointSize=size;}',fragmentShader:'varying vec3 vColor;void main(){if(length(gl_PointCoord-vec2(.5))>.5)discard;gl_FragColor=vec4(vColor,1.0);}',toneMapped:false});Object.defineProperty(mat,'size',{get(){return mat.uniforms.size.value;},set(v){mat.uniforms.size.value=v;}});const cloud=new THREE.Points(g,mat);scene.add(cloud);return{scene,cloud,count:m.point_count,coverage:m.coverage};
}
