// ProjectRoom: one Durable Object per project (docs/INTERNAL.md). It holds the project's live sockets (hibernating),
// its live model (SQLite), and runs Atom's turns.
import { DurableObject } from 'cloudflare:workers'
import type Anthropic from '@anthropic-ai/sdk'
import type { Env } from '../../../src/env'
import { claimsFrom } from '../../../src/auth'
import { addMessage, getMessage, listMessages, type Message } from '../../../src/messages'
import { accountSummary, loadProject, platformSettings, postLedger, SCAN_JSON } from '../../../src/projects'
import { now, parseRows, uuid } from '../../../src/util'
import { LiveModel, type Author, type Op } from './model'
import { AGENT_AUTHOR, costOf, historyFrom, runAgent } from './agent'

interface Attachment {
  project_id: string
  user_id: string | null
  authed: boolean
  subscribed: boolean
}

interface Running {
  turnId: string
  pid: string
  agentMessageId: number
  items: { kind: 'command' | 'edit' | 'tool' | 'thought'; text: string; status: 'ok' | 'running' }[]
  abort: AbortController
  steered: string[]
  startedAt: number
  done: boolean
}

const MAX_EVENT_BYTES = 512 * 1024
const UUID = /^[0-9a-f-]{36}$/

const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })

export class ProjectRoom extends DurableObject<Env> {
  private model: LiveModel
  private running: Running | null = null

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env)
    this.model = new LiveModel(ctx.storage.sql)
    ctx.setWebSocketAutoResponse(new WebSocketRequestResponsePair('{"type":"ping"}', '{"type":"pong"}'))
  }

  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url)
    const path = url.pathname
    try {
      if (path === '/ws') return this.upgrade(req, url)
      if (req.method === 'GET') {
        const pid = url.searchParams.get('project_id') ?? ''
        if (!UUID.test(pid)) return json({ error: 'project_id required' }, 400)
        if (path === '/model/seq') return json({ seq: this.model.seq, base: this.model.base })
        if (path === '/model') {
          const since = url.searchParams.get('since_seq')
          return json(this.model.read(since === null || since === '' ? null : Number(since), url.searchParams.get('cursor')))
        }
        const el = /^\/model\/elements\/([^/]+)$/.exec(path)
        if (el) {
          const e = this.model.element(decodeURIComponent(el[1]))
          return e ? json({ element: e }) : json({ error: 'element not found' }, 404)
        }
        return json({ error: 'not found' }, 404)
      }
      if (req.method !== 'POST') return json({ error: 'method not allowed' }, 405)
      const body = (await req.json().catch(() => ({}))) as Record<string, any>
      const pid = String(body.project_id ?? '')
      if (!UUID.test(pid)) return json({ error: 'project_id required' }, 400)
      switch (path) {
        case '/emit':
          for (const e of (body.events ?? []) as Record<string, unknown>[]) this.broadcast(pid, e)
          return new Response(null, { status: 204 })
        case '/model/ops': {
          const r = this.applyBatch(pid, body.author as Author, String(body.batch_id ?? uuid()), body.ops as Op[], { note: body.note ?? null })
          if ('error' in r) return json({ error: r.error }, 400)
          if ('conflicts' in r) return json({ error: 'conflict', conflicts: r.conflicts }, 409)
          return json({ seq: r.seq, applied: r.applied, cascaded: [] })
        }
        case '/model/undo':
        case '/model/redo': {
          const which = path.endsWith('undo') ? 'undo' : 'redo'
          const author = body.author as Author
          if (!author?.id) return json({ error: 'author required' }, 400)
          const step = this.model.pickStep(author.id, which)
          if (!step) return json({ error: `nothing to ${which}` }, 409)
          const r = this.applyBatch(pid, author, String(body.batch_id ?? uuid()), step.inverse, {
            note: `${which} ${step.seq}`,
            ...(which === 'undo' ? { undoes: step.seq } : { redoes: step.seq }),
          })
          if ('error' in r) return json({ error: r.error }, 409)
          if ('conflicts' in r) return json({ error: 'conflict', conflicts: r.conflicts }, 409)
          return json({ seq: r.seq, applied: r.applied })
        }
        case '/turn':
          return this.turn(pid, Number(body.message_id), body.user)
        case '/stop':
          return json({ stopped: await this.stop(pid) })
      }
      return json({ error: 'not found' }, 404)
    } catch (e) {
      console.error('room', path, e)
      return json({ error: 'server_error', message: (e as Error).message }, 500)
    }
  }

  // ---------- live sockets ----------

  private upgrade(req: Request, url: URL) {
    if (req.headers.get('Upgrade')?.toLowerCase() !== 'websocket') return new Response('Expected a WebSocket', { status: 426 })
    const pid = url.searchParams.get('project_id') ?? ''
    if (!UUID.test(pid)) return new Response('project_id required', { status: 400 })
    const pair = new WebSocketPair()
    const [client, server] = Object.values(pair)
    this.ctx.acceptWebSocket(server)
    server.serializeAttachment({ project_id: pid, user_id: null, authed: false, subscribed: false } satisfies Attachment)
    return new Response(null, { status: 101, webSocket: client })
  }

  async webSocketMessage(ws: WebSocket, raw: string | ArrayBuffer) {
    let m: { type?: string; token?: string; project_id?: string }
    try {
      m = JSON.parse(typeof raw === 'string' ? raw : new TextDecoder().decode(raw))
    } catch {
      return
    }
    const a = ws.deserializeAttachment() as Attachment
    const send = (d: unknown) => {
      try {
        ws.send(JSON.stringify(d))
      } catch {
        /* closed */
      }
    }
    if (m.type === 'ping') return send({ type: 'pong' })
    if (m.type === 'auth') {
      const c = await claimsFrom(this.env, m.token)
      const s = c ? await this.env.DB.prepare('SELECT revoked FROM sessions WHERE id = ?').bind(c.sid).first<{ revoked: number }>() : null
      if (!c || !s || s.revoked) {
        send({ type: 'error', error: 'unauthorized' })
        return ws.close(4001, 'unauthorized')
      }
      ws.serializeAttachment({ ...a, user_id: c.sub, authed: true } satisfies Attachment)
      return send({ type: 'auth.ok', user_id: c.sub })
    }
    if (m.type === 'subscribe') {
      if (!a.authed || !a.user_id) return send({ type: 'error', error: 'auth first' })
      if (m.project_id !== a.project_id) return send({ type: 'error', error: 'wrong project for this socket' })
      const ok = await this.env.DB.prepare(
        'SELECT 1 AS ok FROM project_members WHERE project_id = ? AND user_id = ? UNION SELECT 1 FROM users WHERE id = ? AND is_admin = 1 LIMIT 1',
      )
        .bind(a.project_id, a.user_id, a.user_id)
        .first()
      if (!ok) {
        send({ type: 'error', error: 'not_found' })
        return ws.close(4004, 'not found')
      }
      ws.serializeAttachment({ ...a, subscribed: true } satisfies Attachment)
      return send({ type: 'subscribed', project_id: a.project_id })
    }
  }

  async webSocketClose(ws: WebSocket, code: number) {
    try {
      ws.close(code === 1005 || code === 1006 ? 1000 : code, 'closing')
    } catch {
      /* already closed */
    }
  }

  async webSocketError(ws: WebSocket) {
    try {
      ws.close(1011, 'error')
    } catch {
      /* already closed */
    }
  }

  private broadcast(pid: string, event: Record<string, unknown>) {
    const data = JSON.stringify(event)
    for (const ws of this.ctx.getWebSockets()) {
      const a = ws.deserializeAttachment() as Attachment | null
      if (!a?.subscribed || a.project_id !== pid) continue
      try {
        ws.send(data)
      } catch {
        /* closing */
      }
    }
  }

  // ---------- the live model ----------

  private applyBatch(pid: string, author: Author, batchId: string, ops: Op[], extra: { undoes?: number; redoes?: number; note?: string | null }) {
    if (!author?.id) return { error: 'author required' as const }
    const r = this.model.applyBatch(author, batchId, ops, extra)
    if ('seq' in r) {
      const event: Record<string, unknown> = {
        type: 'model.ops',
        seq: r.seq,
        batch_id: batchId,
        author,
        ops,
        note: extra.note ?? null,
        undoes: extra.undoes ?? null,
        redoes: extra.redoes ?? null,
      }
      if (JSON.stringify(ops).length > MAX_EVENT_BYTES) Object.assign(event, { ops: null, truncated: true })
      this.broadcast(pid, event)
    }
    return r
  }

  // ---------- chat helpers (local broadcast: the room never fetches itself) ----------

  private async post(pid: string, m: { role: Message['role']; body: Message['body']; turn_id?: string | null }) {
    const msg = await addMessage(this.env, pid, m, { silent: true })
    this.broadcast(pid, { type: 'message.created', message: msg })
    return msg
  }

  private async setBody(pid: string, id: number, body: Message['body'], turnId?: string | null) {
    const sets = ['body = ?', 'updated_at = ?']
    const vals: unknown[] = [JSON.stringify(body), now()]
    if (turnId !== undefined) {
      sets.push('turn_id = ?')
      vals.push(turnId)
    }
    await this.env.DB.prepare(`UPDATE messages SET ${sets.join(', ')} WHERE project_id = ? AND id = ?`).bind(...vals, pid, id).run()
    this.broadcast(pid, { type: 'message.updated', id, body })
  }

  private async setTurn(pid: string, turnId: string, patch: { status: string; ended_at?: string | null; error?: string | null }) {
    await this.env.DB.prepare('UPDATE turns SET status = ?, ended_at = ?, error = ? WHERE id = ?')
      .bind(patch.status, patch.ended_at ?? null, patch.error ?? null, turnId)
      .run()
    const turn = await this.env.DB.prepare('SELECT * FROM turns WHERE id = ?').bind(turnId).first()
    this.broadcast(pid, { type: 'turn.updated', turn })
  }

  // ---------- agent turns ----------

  private async turn(pid: string, messageId: number, user: { id: string; email: string; name: string | null }) {
    const msg = Number.isFinite(messageId) ? await getMessage(this.env, pid, messageId) : null
    if (this.running && !this.running.done) {
      // mid-turn input steers the running turn (Codex's steering)
      if (msg) {
        await this.setBody(pid, msg.id, { ...msg.body, queued: false, steered: true }, this.running.turnId)
        this.running.steered.push(`${user?.name || user?.email || 'Someone'}: ${msg.body.text ?? ''}`)
      }
      return json({ steered: true, turn_id: this.running.turnId }, 202)
    }
    const project = await loadProject(this.env, pid)
    if (!project) return json({ error: 'project not found' }, 404)

    if (!this.env.ANTHROPIC_API_KEY) {
      await this.post(pid, {
        role: 'agent',
        body: { text: 'The agent isn’t switched on for this server yet (no Anthropic API key is configured). The team has been told; your message is saved.', phase: 'final_answer' },
      })
      return json({ started: false, reason: 'agent_not_configured' }, 202)
    }
    const account = await accountSummary(this.env, project.account_id)
    if (!account || account.balance <= 0) {
      await this.post(pid, { role: 'system', body: { text: 'Your account is out of credits. Top up to keep working with Atom.', note: 'out_of_credits' } })
      return json({ started: false, reason: 'out_of_credits' }, 202)
    }
    if (project.spend_cap_usd != null && Number(project.spend_usd) >= Number(project.spend_cap_usd)) {
      await this.post(pid, { role: 'system', body: { text: 'This project reached its spending cap. Raise it in the project settings to continue.', note: 'project_cap_reached' } })
      return json({ started: false, reason: 'project_cap_reached' }, 202)
    }

    // a turn the room lost track of (evicted mid-turn) is closed before the next one starts
    const stale = await this.env.DB.prepare("UPDATE turns SET status = 'error', ended_at = ?, error = 'interrupted' WHERE project_id = ? AND status IN ('queued','running') RETURNING *")
      .bind(now(), pid)
      .all()
    for (const s of stale.results) this.broadcast(pid, { type: 'turn.updated', turn: s })

    const turnId = uuid()
    const t = now()
    await this.env.DB.prepare("INSERT INTO turns (id, project_id, status, kind, started_at, created_at) VALUES (?, ?, 'running', 'user', ?, ?)").bind(turnId, pid, t, t).run()
    this.broadcast(pid, { type: 'turn.updated', turn: { id: turnId, project_id: pid, status: 'running', kind: 'user', started_at: t, ended_at: null, error: null, created_at: t } })
    // the person's waiting messages join this turn
    const { results: queued } = await this.env.DB.prepare(`SELECT id, body FROM messages WHERE project_id = ? AND role = 'user' AND body LIKE '%"queued":true%'`).bind(pid).all<{ id: number; body: string }>()
    for (const q of queued) await this.setBody(pid, q.id, { ...JSON.parse(q.body), queued: false }, turnId)
    if (msg && !msg.turn_id) await this.env.DB.prepare('UPDATE messages SET turn_id = ? WHERE id = ?').bind(turnId, msg.id).run()

    const agentMsg = await this.post(pid, { role: 'agent', turn_id: turnId, body: { text: '', blocks: [{ type: 'activity', status: 'running', summary: 'Starting…', items: [] }] } })
    const run: Running = { turnId, pid, agentMessageId: agentMsg.id, items: [], abort: new AbortController(), steered: [], startedAt: Date.now(), done: false }
    this.running = run
    this.ctx.waitUntil(this.runTurn(run, project.account_id))
    return json({ started: true, turn_id: turnId }, 202)
  }

  private async runTurn(run: Running, accountId: string) {
    const { pid, turnId } = run
    const env = this.env
    const modelId = env.AGENT_MODEL || 'claude-opus-5-5'
    const activity = async (status: string, summary: string, meta?: Record<string, unknown>) =>
      this.setBody(pid, run.agentMessageId, { text: '', blocks: [{ type: 'activity', status, summary, items: run.items.map((x) => ({ ...x })), ...(meta ? { meta } : {}) }] })
    try {
      const rows = (await listMessages(env, pid, { limit: 40 })).filter((m) => m.id !== run.agentMessageId)
      const history = historyFrom(rows)
      const state = await this.projectState(pid)
      const last = history[history.length - 1]
      const stateBlock: Anthropic.Beta.BetaTextBlockParam = { type: 'text', text: `<project_state>\n${JSON.stringify(state)}\n</project_state>` }
      if (last?.role === 'user') last.content = [stateBlock, ...(typeof last.content === 'string' ? [{ type: 'text' as const, text: last.content }] : last.content)]
      else history.push({ role: 'user', content: [stateBlock, { type: 'text', text: 'Carry on.' }] })

      const result = await runAgent(
        {
          env,
          pid,
          model: this.model,
          projectInfo: () => this.projectInfo(pid),
          applyOps: (ops, note) => {
            const r = this.applyBatch(pid, AGENT_AUTHOR, uuid(), ops, { note })
            return 'conflicts' in r ? { error: 'conflict', conflicts: r.conflicts } : r
          },
          postMessage: (body) => this.post(pid, { role: 'agent', turn_id: turnId, body }),
          emit: (event) => this.broadcast(pid, event),
          activity: async (summary, item) => {
            run.items.forEach((x) => (x.status = 'ok'))
            if (item) run.items.push({ ...item, status: 'running' })
            await activity('running', summary)
          },
          drainSteered: () => run.steered.splice(0),
        },
        env.ANTHROPIC_API_KEY!,
        modelId,
        history,
        run.abort.signal,
      )
      if (run.done) return // stopped meanwhile
      if (result.text) await this.post(pid, { role: 'agent', turn_id: turnId, body: { text: result.text, phase: 'final_answer', item: `msg_${uuid().slice(0, 8)}` } })
      run.items.forEach((x) => (x.status = 'ok'))
      const cost = await this.meter(pid, accountId, turnId, modelId, result.usage)
      const secs = Math.round((Date.now() - run.startedAt) / 1000)
      const edits = run.items.filter((x) => x.kind === 'edit').length
      const tools = run.items.length - edits
      const parts = [`Worked ${secs}s`, tools ? `${tools} step${tools === 1 ? '' : 's'}` : '', edits ? `${edits} edit${edits === 1 ? '' : 's'}` : ''].filter(Boolean)
      await activity(result.stop === 'refusal' ? 'error' : 'done', parts.join(' · '), { cost, calls: result.calls })
      run.done = true
      await this.setTurn(pid, turnId, { status: 'done', ended_at: now() })
    } catch (e) {
      if (run.done) return
      run.done = true
      const aborted = (e as Error).name === 'AbortError' || run.abort.signal.aborted
      if (aborted) return
      console.error('turn', pid, e)
      run.items.forEach((x) => (x.status = 'ok'))
      await activity('error', 'Stopped by an error').catch(() => {})
      await this.post(pid, { role: 'system', turn_id: turnId, body: { text: `Atom ran into a problem and stopped: ${String((e as Error).message ?? e).slice(0, 300)}` } }).catch(() => {})
      await this.setTurn(pid, turnId, { status: 'error', ended_at: now(), error: String((e as Error).message ?? e).slice(0, 500) }).catch(() => {})
    } finally {
      if (this.running === run) this.running = null
      await this.projectUpdated(pid).catch(() => {})
    }
  }

  private async stop(pid: string) {
    const run = this.running
    if (!run || run.done || run.pid !== pid) {
      // a turn left running by an evicted room: close it
      const r = await this.env.DB.prepare("UPDATE turns SET status = 'stopped', ended_at = ? WHERE project_id = ? AND status IN ('queued','running') RETURNING id").bind(now(), pid).all<{ id: string }>()
      for (const t of r.results) await this.setTurn(pid, t.id, { status: 'stopped', ended_at: now() })
      return r.results.length > 0
    }
    run.done = true
    run.abort.abort()
    const msg = await getMessage(this.env, pid, run.agentMessageId)
    const act = msg?.body.blocks?.find((b: any) => b.type === 'activity')
    await this.setBody(pid, run.agentMessageId, { text: '_Stopped._', blocks: act ? [{ ...act, status: 'stopped', summary: 'Stopped' }] : [] })
    await this.setTurn(pid, run.turnId, { status: 'stopped', ended_at: now() })
    this.running = null
    await this.projectUpdated(pid)
    return true
  }

  /** Credits for the turn: ledger, project spend, and the live account/project events. */
  private async meter(pid: string, accountId: string, turnId: string, modelId: string, usage: { input_tokens: number; output_tokens: number; cache_creation_input_tokens: number; cache_read_input_tokens: number; model: string }[]) {
    const settings = await platformSettings(this.env)
    const cost = costOf(usage, settings.prices?.models ?? {}, modelId, settings.markup ?? 1)
    if (cost <= 0) return 0
    const tokens = usage.reduce(
      (a, u) => ({ input: a.input + u.input_tokens + u.cache_read_input_tokens + u.cache_creation_input_tokens, output: a.output + u.output_tokens }),
      { input: 0, output: 0 },
    )
    await postLedger(this.env, accountId, 'usage', -cost, {
      project_id: pid,
      ref: `turn:${turnId}:${usage.length}`,
      meta: { model: modelId, input_tokens: tokens.input, output_tokens: tokens.output, turn_id: turnId },
    })
    await this.env.DB.prepare('UPDATE projects SET spend_usd = ROUND(spend_usd + ?, 6), last_active_at = ? WHERE id = ?').bind(cost, now(), pid).run()
    const account = await accountSummary(this.env, accountId)
    if (account) this.broadcast(pid, { type: 'account.updated', account })
    return cost
  }

  private async projectUpdated(pid: string) {
    const p = await this.env.DB.prepare('SELECT id, spend_usd, spend_cap_usd FROM projects WHERE id = ?').bind(pid).first()
    if (p) this.broadcast(pid, { type: 'project.updated', project: p })
  }

  /** The short, volatile state that leads each turn's newest user message. */
  private async projectState(pid: string) {
    const p = await loadProject(this.env, pid)
    const s = this.model.summary({ limit: 1 })
    return { project: p ? { name: p.name, status: p.status, scope: p.settings?.scope ?? null } : null, model: { seq: s.seq, counts: s.counts, types: s.types } }
  }

  private async projectInfo(pid: string) {
    const p = await loadProject(this.env, pid)
    const scans = parseRows<any>(
      (await this.env.DB.prepare('SELECT * FROM scans WHERE project_id = ? ORDER BY created_at').bind(pid).all()).results,
      SCAN_JSON,
    ).map((s) => ({ id: s.id, name: s.name, status: s.status, stage_detail: s.stage_detail, points: s.point_count, bounds: s.bounds, frame: s.frame, labels: s.labels, brief: s.brief, error: s.error }))
    const { results: files } = await this.env.DB.prepare("SELECT id, kind, name, size_bytes, content_type, created_at FROM files WHERE project_id = ? AND status = 'ready' ORDER BY created_at DESC LIMIT 100").bind(pid).all()
    const { results: revisions } = await this.env.DB.prepare('SELECT number, title, notes, status, created_at FROM revisions WHERE project_id = ? ORDER BY number').bind(pid).all()
    return {
      project: p ? { id: p.id, name: p.name, status: p.status, scope: p.settings?.scope ?? null, spend_usd: p.spend_usd, spend_cap_usd: p.spend_cap_usd } : null,
      scans,
      files,
      revisions,
      model_seq: this.model.seq,
    }
  }
}
