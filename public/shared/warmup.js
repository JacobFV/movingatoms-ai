// Prepare a scene for its first frame without freezing the page.
//
// By default three.js uploads every texture and compiles every shader inside the first render call,
// waiting on each shader in turn. On the larger samples that single frame froze the page for 2-5 s.
// warmUp() instead uploads textures in ~8 ms slices (one slice per frame) and then compiles all
// shaders in parallel (KHR_parallel_shader_compile via renderer.compileAsync), so the page keeps
// responding and the loader can show progress. Call it after the scene is assembled, before the first draw.
export async function warmUp(renderer, scenes, camera, { status = () => {}, budgetMs = 8 } = {}) {
  const textures = new Set();
  const add = (t) => { if (t && t.isTexture && !t.isRenderTargetTexture) textures.add(t); };
  for (const scene of scenes) {
    add(scene.environment);
    add(scene.background);
    scene.traverse((object) => {
      const materials = object.material ? (Array.isArray(object.material) ? object.material : [object.material]) : [];
      for (const material of materials) {
        for (const key in material) add(material[key]);
        if (material.uniforms) for (const key in material.uniforms) add(material.uniforms[key]?.value);
      }
    });
  }
  let done = 0, sliceStart = performance.now();
  for (const texture of textures) {
    renderer.initTexture(texture);
    done++;
    if (performance.now() - sliceStart > budgetMs) {
      status(`Preparing textures · ${done} / ${textures.size}`);
      await new Promise(requestAnimationFrame);
      sliceStart = performance.now();
    }
  }
  status("Preparing shaders…");
  for (const scene of scenes) await renderer.compileAsync(scene, camera);
}
