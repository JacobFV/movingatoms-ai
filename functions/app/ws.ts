// The app's live socket (CONTRACTS §5): the upgrade goes to the project's room, which authenticates and subscribes.
import type { Env } from '../../src/env'
import { room } from '../../src/projects'

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  if (request.headers.get('Upgrade')?.toLowerCase() !== 'websocket') return new Response('Expected a WebSocket upgrade', { status: 426 })
  const pid = new URL(request.url).searchParams.get('project_id') ?? ''
  if (!/^[0-9a-f-]{36}$/.test(pid)) return new Response('project_id required', { status: 400 })
  // the room routes on its own paths: /ws?project_id=…
  return room(env, pid).fetch(new Request(`https://room/ws?project_id=${pid}`, request))
}
