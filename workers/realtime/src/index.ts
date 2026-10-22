// The realtime Worker: home of the ProjectRoom Durable Object (Pages Functions reach it through the PROJECT_ROOM
// binding, script_name = movingatoms-realtime) and of the scan-processing containers, woken by the cron below.
import { ProjectRoom } from './room'
import { Processor, scheduleProcessors, type ProcEnv } from './processor'

export default {
  async fetch(req, env): Promise<Response> {
    // operations: wake the processors now and report (bearer WORKER_TOKEN)
    const url = new URL(req.url)
    if (url.pathname === '/__processors' && env.WORKER_TOKEN && req.headers.get('Authorization') === `Bearer ${env.WORKER_TOKEN}`)
      return Response.json(await scheduleProcessors(env))
    return new Response('Not found', { status: 404 })
  },
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(scheduleProcessors(env))
  },
} satisfies ExportedHandler<ProcEnv>

export { ProjectRoom, Processor }
