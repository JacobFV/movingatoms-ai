// The viewer's asset links (§11): /app/a/<pid>.<token>/<key> → R2 `projects/<pid>/<key>`, with Range support.
// The token is the signed prefix from assetBase(); it expires after a few hours and the viewer asks for a fresh one.
import type { Env } from '../../../src/env'
import { checkAssetToken } from '../../../src/projects'
import { serveObject } from '../../../src/r2'

export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const path = new URL(request.url).pathname.slice('/app/a/'.length)
  const m = /^([0-9a-f-]{36})\.([^/]+)\/(.+)$/.exec(path)
  if (!m) return new Response('Not found', { status: 404 })
  const [, pid, token, rest] = m
  if (!(await checkAssetToken(env, pid, decodeURIComponent(token)))) return new Response('This link has expired.', { status: 403 })
  const key = decodeURIComponent(rest)
  if (key.includes('..')) return new Response('Not found', { status: 404 })
  return serveObject(env.UPLOADS, `projects/${pid}/${key}`, request, { cache: 'private, max-age=3600' })
}
export const onRequestHead = onRequestGet
