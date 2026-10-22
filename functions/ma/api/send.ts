// First-party analytics: an Umami-compatible collector for public/ma/stats.js (POST {type, payload}).
// Cookieless: no IP or user agent is stored, only a visitor hash that changes every day.
// stats.js reads the JSON answer's `disabled` (stop sending) and `cache` (echoed back as x-umami-cache).
import type { Env } from '../../../src/env'
import { now, sha256 } from '../../../src/util'

const BOT = /bot|crawl|spider|slurp|bingpreview|facebookexternalhit|headless|lighthouse|pingdom|uptime|monitor|curl|wget|python-requests|httpclient|go-http/i
const MAX = 8 * 1024
const cors = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'Content-Type, x-umami-website-id, x-umami-hostname, x-umami-cache', 'Access-Control-Allow-Methods': 'POST, OPTIONS' }
const answer = (data: Record<string, unknown> = { cache: '' }, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', ...cors } })

const str = (v: unknown, n: number) => (typeof v === 'string' ? v.slice(0, n) : null)

export const onRequestOptions: PagesFunction<Env> = () => new Response(null, { status: 204, headers: cors })

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  const ua = request.headers.get('User-Agent') ?? ''
  if (!ua || BOT.test(ua)) return answer()
  const len = Number(request.headers.get('Content-Length') ?? 0)
  if (len > MAX) return answer({ cache: '' }, 413)
  const raw = await request.text()
  if (raw.length > MAX) return answer({ cache: '' }, 413)
  let msg: { type?: string; payload?: Record<string, unknown> }
  try {
    msg = JSON.parse(raw)
  } catch {
    return answer({ cache: '' }, 400)
  }
  const p = msg.payload ?? {}
  const type = msg.type === 'event' && !p.name ? 'pageview' : (str(msg.type, 20) ?? 'event')
  if (!['event', 'pageview', 'identify', 'performance'].includes(type)) return answer({ cache: '' }, 400)

  const day = new Date().toISOString().slice(0, 10)
  const ip = request.headers.get('CF-Connecting-IP') ?? ''
  const visitor = (await sha256(`${env.SESSION_SECRET}:${day}:${ip}:${ua}`)).slice(0, 16)
  const cf = (request as unknown as { cf?: { country?: string } }).cf
  const data = type === 'performance' ? p : (p.data ?? null)
  const dataJson = data ? JSON.stringify(data).slice(0, 4000) : null

  await env.DB.prepare('INSERT INTO events (ts, type, name, url, referrer, title, screen, language, country, visitor, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
    .bind(
      now(),
      type,
      str(p.name, 100),
      str(p.url, 500),
      str(p.referrer, 500),
      str(p.title, 200),
      str(p.screen, 20),
      str(p.language, 20),
      cf?.country ?? null,
      visitor,
      dataJson,
    )
    .run()
  return answer()
}
