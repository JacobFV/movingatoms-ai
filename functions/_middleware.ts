// Runs in front of every request that public/_routes.json sends to Functions.
//  - security headers on HTML pages;
//  - a static 404 under /app/ is the app's client-side route: serve the app shell (/app/index.html);
//  - any other GET/HEAD 404 is looked up in the MEDIA bucket (site files too big for Pages: the sample Revit zips,
//    the factory scene's .glb/.bin), with Range support; then the site's own 404 page.
// Bodies are streamed, never buffered; WebSocket upgrades pass straight through.
import type { Env } from '../src/env'
import { serveObject } from '../src/r2'

const NOT_SPA = /^\/app\/(api|a|f|assets|potree|ws)(\/|$)/

const HTML_HEADERS: Record<string, string> = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'X-Frame-Options': 'SAMEORIGIN',
}

function withHtmlHeaders(res: Response): Response {
  const type = res.headers.get('Content-Type') ?? ''
  if (!type.includes('text/html')) return res
  const out = new Response(res.body, res)
  for (const [k, v] of Object.entries(HTML_HEADERS)) if (!out.headers.has(k)) out.headers.set(k, v)
  return out
}

export const onRequest: PagesFunction<Env> = async ({ request, env, next }) => {
  if (request.headers.get('Upgrade')?.toLowerCase() === 'websocket') return next()
  const res = await next()
  const method = request.method
  if (res.status !== 404 || (method !== 'GET' && method !== 'HEAD')) return withHtmlHeaders(res)

  const url = new URL(request.url)
  const path = decodeURIComponent(url.pathname)

  // the app's routes (/app/p/<id>, /app/sign-in, /app/s/<token>, …)
  if (path.startsWith('/app/') && !NOT_SPA.test(path)) {
    await res.body?.cancel()
    const shell = await env.ASSETS.fetch(new URL('/app/index.html', url))
    return withHtmlHeaders(new Response(shell.body, { status: 200, headers: shell.headers }))
  }

  // big public files kept in R2
  const key = path.replace(/^\/+/, '')
  if (key && !key.endsWith('/') && !key.includes('..')) {
    const obj = await serveObject(env.MEDIA, key, request, { cache: 'public, max-age=86400' })
    if (obj.status !== 404) {
      await res.body?.cancel()
      return obj
    }
  }
  return withHtmlHeaders(res)
}
