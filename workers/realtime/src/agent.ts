// Atom, the project's scan-to-BIM agent: one turn of Claude with the project's tools (CONTRACTS §12). The room runs
// it, posts what it writes as chat messages, keeps its activity line current and meters its usage in credits.
import Anthropic from '@anthropic-ai/sdk'
import type { Env } from '../../../src/env'
import type { Message } from '../../../src/messages'
import type { Author, LiveModel, Op } from './model'

export const AGENT_AUTHOR: Author = { kind: 'agent', id: 'agent', name: 'Atom' }
const MAX_ITERATIONS = 25

// Frozen: no project state, dates or ids in here, so the prefix caches across turns and projects.
export const SYSTEM_PROMPT = `You are Atom, the scan-to-BIM agent of Moving Atoms. People upload LiDAR or SLAM scans of buildings, plants and sites; you build and edit a BIM model of what the scan shows, and talk with them about it in the project's chat.

How you work:
- Answer in plain, short sentences. Say what you did and what you found, with numbers and units (metres in the model, millimetres for tolerances).
- Use the tools to look before you answer: project_info for the scans, files and the agreed scope; read_model for the model's elements.
- Change the model only with apply_model_ops, in small batches with a clear note. Never invent measurements: when the scan or the brief doesn't tell you a size, ask.
- When you need a decision from the person (formats, level of detail, what to include), use ask_question and end your turn; they answer from the card.
- Use viewer_command to show them what you mean (isolate or highlight elements, fly the camera, draw a box).
- For long work, post_progress short notes so they can follow along. Your last text is your answer.
- Scan conversion runs on the platform's processing workers, not in your tools. You can start three kinds of work there, which finish in the background (the person sees progress in the project):
  publish_revision builds a checkpoint of the model: model.glb, IFC (it opens in Revit; a native .rvt file can't be produced here) and a new revision;
  fit_to_scan fits elements (walls, columns, beams, pipes, ducts) to the scan points and updates them;
  compute_heatmap measures the scan's deviation from the model.
  Start them when the person asks, or when a checkpoint is due after a batch of edits; say what you started.

The model (CONTRACTS §17). Each element: { id, kind, ifc_class, type_id, level_id, parent_id, params, geometry, relations: {connects: []}, props: {name, ...}, provenance: {status: "observed" | "designed" | "assumed", ...}, version }.
Kinds include level, wall, slab, column, beam, door, window, opening, stair, railing, pipe, duct, cable_tray, equipment, furniture and mesh. Levels carry params.elevation (m). Walls carry params.start and params.end ([x, y], m), thickness and height; doors and windows sit in a wall (parent_id) with params.along, width, height and sill; columns carry params.position ([x, y]) and a section; pipes carry params.od (m), a path and a spec.
Coordinates are the project's working frame: metres, Z up.
Ops (apply_model_ops takes a JSON array):
  {"op":"create","element":{...full element without version...}}
  {"op":"update","id":"…","patch":{...JSON merge patch per top-level field...},"if_version":N}
  {"op":"delete","id":"…","if_version":N}   {"op":"restore","id":"…"}
  {"op":"type.create","type":{"id","kind","name","params"}}  {"op":"type.update","id","patch"}  {"op":"type.delete","id"}
Pass if_version (the version you read) so you never overwrite someone's newer edit; on a conflict, read again and redo.
Element ids: a short kind prefix and 16 random letters or digits, e.g. "wall_k3j9x0q2m7b1c8d4".`

export const TOOLS: Anthropic.Beta.BetaTool[] = [
  {
    name: 'project_info',
    description: 'The project: name, status, agreed scope, its scans (status, points, bounds, brief), files and revisions.',
    input_schema: { type: 'object', properties: {}, required: [], additionalProperties: false },
    strict: true,
  },
  {
    name: 'read_model',
    description: 'The live BIM model: element counts by kind, the levels, and elements filtered by kind or ids (up to 300).',
    input_schema: {
      type: 'object',
      properties: {
        kind: { type: ['string', 'null'], description: 'Only this kind (e.g. "wall"), or null for any.' },
        ids: { type: ['array', 'null'], items: { type: 'string' }, description: 'These element ids, or null.' },
        limit: { type: ['integer', 'null'], description: 'How many elements to return (default 100, max 300).' },
      },
      required: ['kind', 'ids', 'limit'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'apply_model_ops',
    description: 'Apply one batch of ops to the live model as Atom. Everyone watching sees the change. Returns the new seq, or the conflicts.',
    input_schema: {
      type: 'object',
      properties: {
        ops_json: { type: 'string', description: 'A JSON array of ops, as described in the system prompt.' },
        note: { type: 'string', description: 'What this batch does, in a few words (shown in the model history).' },
      },
      required: ['ops_json', 'note'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'ask_question',
    description: 'Ask the person one or more questions on a card in the chat. End your turn after asking; the answer arrives as their next message.',
    input_schema: {
      type: 'object',
      properties: {
        questions: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              id: { type: 'string' },
              question: { type: 'string' },
              options: {
                type: 'array',
                items: { type: 'object', properties: { label: { type: 'string' } }, required: ['label'], additionalProperties: false },
              },
              other: { type: 'boolean', description: 'Whether they may write their own answer.' },
            },
            required: ['id', 'question', 'options', 'other'],
            additionalProperties: false,
          },
        },
      },
      required: ['questions'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'viewer_command',
    description:
      'Drive the person\'s 3D viewer, and leave a button in the chat that repeats it. command_json is one of: {"op":"isolate","element_ids":[…]}, {"op":"highlight","element_ids":[…]}, {"op":"clear"}, {"op":"fly_to","eye":[x,y,z],"target":[x,y,z]}, {"op":"box","min":[…],"max":[…],"label":"…"}, {"op":"color","mode":"rgb"|"intensity"|"elevation"|"labels"|"heatmap"}, {"op":"layers","scan":bool,"model":bool,"split":bool}.',
    input_schema: {
      type: 'object',
      properties: {
        label: { type: 'string', description: 'The button text, e.g. "Show pipe 101".' },
        command_json: { type: 'string' },
      },
      required: ['label', 'command_json'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'publish_revision',
    description: 'Build a checkpoint of the current model on the processing workers: a new revision with model.glb and an IFC file (IFC opens in Revit). Returns the job id.',
    input_schema: {
      type: 'object',
      properties: { title: { type: 'string', description: 'Short revision title' }, notes: { type: 'string', description: 'What changed since the last revision' } },
      required: ['title', 'notes'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'fit_to_scan',
    description: 'Fit elements to the scan points on the processing workers (walls, columns, beams, pipes, ducts; doors, windows, openings and levels are skipped). The fitted elements are updated in the model. Returns the job id.',
    input_schema: {
      type: 'object',
      properties: { element_ids: { type: 'array', items: { type: 'string' }, description: 'Up to 500 element ids' } },
      required: ['element_ids'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'compute_heatmap',
    description: 'Measure how far the scan points are from the model (a deviation heatmap per scan, with p50/p95 and the share within 25 mm). revision: a revision number, or 0 for the live model. Returns the job id.',
    input_schema: {
      type: 'object',
      properties: { revision: { type: 'integer', description: 'Revision number, or 0 for the live model' } },
      required: ['revision'],
      additionalProperties: false,
    },
    strict: true,
  },
  {
    name: 'post_progress',
    description: 'Post a short progress note in the chat while you keep working.',
    input_schema: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'], additionalProperties: false },
    strict: true,
  },
]

const VIEWER_OPS = new Set(['fly_to', 'highlight', 'isolate', 'clear', 'box', 'heatmap', 'revision', 'color', 'layers'])

/** What the tools do; the room supplies the side effects. */
export interface AgentHost {
  env: Env
  pid: string
  model: LiveModel
  projectInfo(): Promise<unknown>
  applyOps(ops: Op[], note: string): unknown
  postMessage(body: Message['body']): Promise<Message>
  emit(event: Record<string, unknown>): void
  activity(summary: string, item?: { kind: 'command' | 'edit' | 'tool' | 'thought'; text: string }): Promise<void>
  /** People's messages that arrived mid-turn (steering), drained by the loop before its next call. */
  drainSteered(): string[]
  /** A job was queued: make sure a processor will pick it up. */
  jobQueued(): Promise<void>
}

export interface TurnResult {
  text: string
  usage: { input_tokens: number; output_tokens: number; cache_creation_input_tokens: number; cache_read_input_tokens: number; model: string }[]
  calls: number
  asked: boolean
  stop: 'end_turn' | 'refusal' | 'max_tokens' | 'iterations' | 'asked'
}

async function runTool(host: AgentHost, name: string, input: any): Promise<{ content: string; isError?: boolean; asked?: boolean }> {
  switch (name) {
    case 'project_info':
      await host.activity('Reading the project', { kind: 'tool', text: 'project_info' })
      return { content: JSON.stringify(await host.projectInfo()) }
    case 'read_model': {
      await host.activity('Reading the model', { kind: 'tool', text: `read_model${input.kind ? ` ${input.kind}` : ''}` })
      const s = host.model.summary({ kind: input.kind, ids: input.ids, limit: input.limit })
      let out = JSON.stringify(s)
      if (out.length > 60_000) out = JSON.stringify({ ...s, elements: s.elements.slice(0, 20), truncated: true, note: 'Too large: ask for fewer elements or one kind.' })
      return { content: out }
    }
    case 'apply_model_ops': {
      let ops: Op[]
      try {
        ops = JSON.parse(input.ops_json)
        if (!Array.isArray(ops)) throw new Error('not an array')
      } catch (e) {
        return { content: `ops_json isn't a JSON array of ops: ${(e as Error).message}`, isError: true }
      }
      await host.activity(`Editing the model: ${input.note}`, { kind: 'edit', text: `${ops.length} op${ops.length === 1 ? '' : 's'} · ${input.note}` })
      return { content: JSON.stringify(host.applyOps(ops, input.note)) }
    }
    case 'ask_question': {
      const qs = (input.questions ?? []).slice(0, 6)
      if (!qs.length) return { content: 'No questions given.', isError: true }
      await host.postMessage({
        text: qs.length === 1 ? qs[0].question : 'A few questions before I go on.',
        phase: 'final_answer',
        item: `ask_${crypto.randomUUID().slice(0, 8)}`,
        blocks: [{ type: 'question', id: `call_${crypto.randomUUID().slice(0, 12)}`, mode: 'async', questions: qs }],
      })
      return { content: 'Asked. End your turn now; their answer arrives as their next message.', asked: true }
    }
    case 'viewer_command': {
      let command: any
      try {
        command = JSON.parse(input.command_json)
      } catch {
        return { content: 'command_json is not JSON.', isError: true }
      }
      if (!command || !VIEWER_OPS.has(command.op)) return { content: `Unknown viewer op. Use one of: ${[...VIEWER_OPS].join(', ')}.`, isError: true }
      host.emit({ type: 'viewer.command', command })
      await host.postMessage({ text: '', phase: 'commentary', blocks: [{ type: 'viewer', label: String(input.label).slice(0, 80), command }] })
      return { content: 'Shown.' }
    }
    case 'publish_revision':
    case 'fit_to_scan':
    case 'compute_heatmap': {
      const type = name === 'publish_revision' ? 'build' : name === 'fit_to_scan' ? 'model_fit' : 'heatmap'
      let jobInput: Record<string, unknown>
      if (type === 'build') jobInput = { title: String(input.title ?? '').slice(0, 200), notes: String(input.notes ?? '').slice(0, 4000), by: 'agent' }
      else if (type === 'model_fit') {
        const ids = [...new Set(((input.element_ids ?? []) as unknown[]).map(String))].slice(0, 500)
        if (!ids.length) return { content: 'Give at least one element id.', isError: true }
        jobInput = { element_ids: ids, by: 'agent' }
      } else jobInput = Number(input.revision) > 0 ? { revision: Number(input.revision) } : { live: true }
      const id = crypto.randomUUID()
      const t = new Date().toISOString()
      await host.env.DB.prepare("INSERT INTO jobs (id, project_id, type, status, input, created_at, updated_at) VALUES (?, ?, ?, 'queued', ?, ?, ?)")
        .bind(id, host.pid, type, JSON.stringify(jobInput), t, t)
        .run()
      host.emit({ type: 'job.updated', id, type_: type, status: 'queued', stage: null, progress: 0, job: { id, type, status: 'queued', stage: null, progress: 0 } })
      await host.jobQueued()
      await host.activity(`Started ${type.replace('_', ' ')} on the processing workers`, { kind: 'tool', text: `${name} → job ${id.slice(0, 8)}` })
      return { content: JSON.stringify({ job_id: id, type, status: 'queued', note: 'Runs in the background; the person sees its progress. Do not wait for it.' }) }
    }
    case 'post_progress':
      await host.postMessage({ text: String(input.text), phase: 'commentary', item: `msg_${crypto.randomUUID().slice(0, 8)}` })
      return { content: 'Posted.' }
  }
  return { content: `No tool named ${name}.`, isError: true }
}

export async function runAgent(host: AgentHost, apiKey: string, model: string, history: Anthropic.Beta.BetaMessageParam[], signal: AbortSignal): Promise<TurnResult> {
  const client = new Anthropic({ apiKey })
  const messages = [...history]
  const result: TurnResult = { text: '', usage: [], calls: 0, asked: false, stop: 'end_turn' }

  for (let i = 0; i < MAX_ITERATIONS; i++) {
    const steered = host.drainSteered()
    if (steered.length) {
      const last = messages[messages.length - 1]
      const note: Anthropic.Beta.BetaTextBlockParam = { type: 'text', text: steered.map((s) => `New message from the person while you work:\n${s}`).join('\n\n') }
      if (last?.role === 'user') last.content = [...(typeof last.content === 'string' ? [{ type: 'text' as const, text: last.content }] : last.content), note]
      else messages.push({ role: 'user', content: [note] })
    }

    const response = await client.beta.messages.create(
      {
        model,
        max_tokens: 16000,
        betas: ['server-side-fallback-2026-07-01'],
        fallbacks: 'default',
        thinking: { type: 'adaptive' },
        output_config: { effort: 'medium' },
        cache_control: { type: 'ephemeral' },
        system: SYSTEM_PROMPT,
        tools: TOOLS,
        tool_choice: { type: 'auto' },
        messages,
      },
      { signal },
    )
    result.calls++
    const u = response.usage
    result.usage.push({
      input_tokens: u.input_tokens ?? 0,
      output_tokens: u.output_tokens ?? 0,
      cache_creation_input_tokens: u.cache_creation_input_tokens ?? 0,
      cache_read_input_tokens: u.cache_read_input_tokens ?? 0,
      model: response.model,
    })
    const text = response.content
      .filter((b): b is Anthropic.Beta.BetaTextBlock => b.type === 'text')
      .map((b) => b.text)
      .join('\n\n')
      .trim()

    if (response.stop_reason === 'refusal') {
      result.text = text || 'I can’t help with that request.'
      result.stop = 'refusal'
      return result
    }
    if (response.stop_reason === 'pause_turn') {
      messages.push({ role: 'assistant', content: response.content })
      continue
    }
    const uses = response.content.filter((b): b is Anthropic.Beta.BetaToolUseBlock => b.type === 'tool_use')
    if (response.stop_reason === 'max_tokens' && !uses.length) {
      result.text = text ? `${text}\n\n_(cut short)_` : 'My answer ran too long and was cut short. Ask me for a shorter version.'
      result.stop = 'max_tokens'
      return result
    }
    if (!uses.length) {
      result.text = text
      result.stop = 'end_turn'
      return result
    }
    // text written between tool calls reads as a progress note
    if (text) await host.postMessage({ text, phase: 'commentary', item: response.id })

    messages.push({ role: 'assistant', content: response.content })
    const results: Anthropic.Beta.BetaToolResultBlockParam[] = []
    for (const use of uses) {
      try {
        const r = await runTool(host, use.name, use.input)
        if (r.asked) result.asked = true
        results.push({ type: 'tool_result', tool_use_id: use.id, content: r.content, ...(r.isError ? { is_error: true } : {}) })
      } catch (e) {
        results.push({ type: 'tool_result', tool_use_id: use.id, content: `The tool failed: ${(e as Error).message}`, is_error: true })
      }
    }
    messages.push({ role: 'user', content: results })
    if (result.asked) {
      result.stop = 'asked'
      return result
    }
  }
  result.stop = 'iterations'
  result.text = 'I’ve stopped here to check in: this took more steps than one turn allows. Tell me to carry on and I’ll pick up where I left off.'
  return result
}

/** The chat as Claude reads it: people's messages and Atom's answers, alternating, from the newest ~40. */
export function historyFrom(rows: Message[]): Anthropic.Beta.BetaMessageParam[] {
  const out: Anthropic.Beta.BetaMessageParam[] = []
  const push = (role: 'user' | 'assistant', text: string) => {
    if (!text.trim()) return
    const last = out[out.length - 1]
    if (last && last.role === role && typeof last.content === 'string') last.content = `${last.content}\n\n${text}`
    else out.push({ role, content: text })
  }
  for (const m of rows) {
    const b = m.body ?? {}
    if (m.role === 'user') {
      const who = m.author?.name || m.author?.email || 'Someone'
      const extras: string[] = []
      for (const blk of b.blocks ?? []) {
        if (blk.type === 'selection') extras.push(`(selected in the viewer: ${(blk.element_ids ?? []).join(', ')}${blk.label ? ` — ${blk.label}` : ''})`)
        if (blk.type === 'point') extras.push(`(placed point ${blk.point_id})`)
        if (blk.type === 'file') extras.push(`(attached file ${blk.file_id})`)
      }
      push('user', `${who}: ${b.text ?? ''}${extras.length ? `\n${extras.join('\n')}` : ''}`)
    } else if (m.role === 'agent') {
      if (b.phase === 'final_answer' && b.text) push('assistant', String(b.text))
    } else if (m.role === 'system' && b.text) push('user', `[platform] ${b.text}`)
  }
  while (out.length && out[0].role !== 'user') out.shift()
  return out
}

/** Credits for a turn's calls: tokens × the platform's prices per million (for the configured model) × markup. */
export function costOf(usage: TurnResult['usage'], prices: Record<string, { input: number; cached_input: number; cache_write: number; output: number }>, fallbackModel: string, markup: number) {
  let total = 0
  for (const u of usage) {
    const p = prices[u.model] ?? prices[fallbackModel]
    if (!p) continue
    total += (u.input_tokens * p.input + u.cache_read_input_tokens * p.cached_input + u.cache_creation_input_tokens * p.cache_write + u.output_tokens * p.output) / 1e6
  }
  return Math.round(total * (markup || 1) * 1e4) / 1e4
}
