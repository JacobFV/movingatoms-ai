// One-hour file links (GET /api/files/:id/url): /app/f/<token>/<name>. `d` in the token asks for a download.
import type { Env } from '../../../src/env'
import { serveObject } from '../../../src/r2'
import { verifyToken } from '../../../src/util'

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const [token, ...name] = new URL(request.url).pathname.slice('/app/f/'.length).split('/')
  const t = await verifyToken<{ f: string; k: string; typ: string; d?: number }>(env.SESSION_SECRET, decodeURIComponent(token ?? ''))
  if (!t || t.typ !== 'file') return new Response('This link has expired. Open the file again from the project.', { status: 403 })
  return serveObject(env.UPLOADS, t.k, request, { download: t.d ? decodeURIComponent(name.join('/')) : undefined })
}
export const onRequestHead = onRequestGet
