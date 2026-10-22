// The scan-processing worker on Cloudflare Containers: the image in processing/ runs `python -m ma_proc.runner`, which
// claims jobs from the site's worker API. A cron wakes instances while jobs are queued; an instance that has gone
// quiet sleeps (onActivityExpired) once the queue it can take is empty. Machines elsewhere (the DGX box) claim from
// the same queue; claims are atomic, so nothing is processed twice.
import { Container, getContainer } from '@cloudflare/containers'
import type { Env } from '../../../src/env'

export type ProcEnv = Env & { PROCESSOR: DurableObjectNamespace<Processor>; WORKER_TOKEN?: string; PROCESSOR_INSTANCES?: string }

/** What a container instance can take: its disk is ~20 GB, so sources up to 8 GB (the rest goes to a bigger machine). */
export const CONTAINER_MAX_SOURCE = 8 * 1024 ** 3

export class Processor extends Container<ProcEnv> {
  sleepAfter = '5m'
  enableInternet = true

  /** Start the runner if it isn't running, and keep it awake. */
  async wake() {
    const state = await this.getState()
    if (state.status !== 'running' && state.status !== 'healthy') {
      await this.start({
        envVars: {
          MA_SITE: this.env.SITE_URL,
          WORKER_TOKEN: this.env.WORKER_TOKEN ?? '',
          MA_MAX_SOURCE_BYTES: String(CONTAINER_MAX_SOURCE),
          MA_WORKER_NAME: `cf-container-${this.ctx.id.toString().slice(0, 8)}`,
        },
      })
    }
    this.renewActivityTimeout()
    return state.status
  }

  /** Quiet for `sleepAfter`: keep going while there is work this instance could take, else stop. */
  async onActivityExpired() {
    if ((await queued(this.env)) > 0) return this.renewActivityTimeout()
    await this.stop()
  }
}

/** Jobs waiting (or claimed by an instance that went away) that a container can take. */
export async function queued(env: Env) {
  const r = await env.DB.prepare(
    `SELECT COUNT(*) AS n FROM jobs WHERE (status = 'queued' OR (status = 'running' AND claimed_at < ?))
       AND COALESCE(json_extract(input, '$.size'), 0) <= ?`,
  )
    .bind(Date.now() - 15 * 60_000, CONTAINER_MAX_SOURCE)
    .first<{ n: number }>()
  return r?.n ?? 0
}

/** The cron: wake one instance per waiting job, up to PROCESSOR_INSTANCES (default 2). */
export async function scheduleProcessors(env: ProcEnv) {
  if (!env.WORKER_TOKEN) return { queued: 0, woke: [], note: 'no WORKER_TOKEN' }
  const n = await queued(env)
  if (!n) return { queued: 0, woke: [] }
  const max = Math.max(1, Number(env.PROCESSOR_INSTANCES ?? 2))
  const woke = await Promise.all(
    Array.from({ length: Math.min(n, max) }, (_, i) =>
      getContainer(env.PROCESSOR, `pool-${i}`)
        .wake()
        .then((was) => ({ i, was }))
        .catch((e: unknown) => {
          console.error('processor wake', i, e)
          return { i, error: String((e as Error)?.stack ?? e) }
        }),
    ),
  )
  console.log('processors', JSON.stringify({ queued: n, woke }))
  return { queued: n, woke }
}
