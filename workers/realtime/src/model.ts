// The live model (CONTRACTS §17) kept in the project room's SQLite: elements and types with versions, a seq per applied
// batch, and a log of batches with their inverses for undo/redo. Semantics follow the app's LiveState (applyOps,
// mergePatch) and the contract's mock (if_version conflicts, per-author undo/redo).

export type Op = { op: string; [k: string]: any }
export interface Author {
  kind: string
  id: string
  name: string
}
export interface Element {
  id: string
  kind: string
  version: number
  deleted?: boolean
  [k: string]: any
}

const PAGE = 5000

const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)

/** RFC 7386 merge patch, as the app applies it. */
export function mergePatch(target: unknown, patch: unknown): unknown {
  if (!isObj(patch)) return patch
  const out: Record<string, unknown> = isObj(target) ? { ...target } : {}
  for (const [k, v] of Object.entries(patch)) {
    if (v === null) delete out[k]
    else out[k] = mergePatch(out[k], v)
  }
  return out
}

function patchInto(cur: Record<string, unknown>, patch: Record<string, unknown>) {
  const next: Record<string, unknown> = { ...cur }
  for (const [k, v] of Object.entries(patch ?? {})) {
    const m = mergePatch(next[k], v)
    next[k] = m === undefined ? null : m
  }
  return next
}

type Row = {
  id: string
  json: string
  version: number
  deleted: number
  kind?: string
  changed_seq: number
}

type BatchRow = {
  seq: number
  batch_id: string
  author_id: string
  author: string
  ops: string
  inverse: string
  undoes: number | null
  redoes: number | null
  note: string | null
  created_at: string
}

export class LiveModel {
  constructor(private sql: SqlStorage) {
    sql.exec(`CREATE TABLE IF NOT EXISTS elements (id TEXT PRIMARY KEY, json TEXT NOT NULL, version INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0, kind TEXT NOT NULL, changed_seq INTEGER NOT NULL)`)
    sql.exec(`CREATE INDEX IF NOT EXISTS elements_changed ON elements(changed_seq)`)
    sql.exec(`CREATE TABLE IF NOT EXISTS types (id TEXT PRIMARY KEY, json TEXT NOT NULL, version INTEGER NOT NULL, deleted INTEGER NOT NULL DEFAULT 0, changed_seq INTEGER NOT NULL)`)
    sql.exec(`CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)`)
    sql.exec(
      `CREATE TABLE IF NOT EXISTS batches (seq INTEGER PRIMARY KEY, batch_id TEXT NOT NULL, author_id TEXT NOT NULL, author TEXT NOT NULL, ops TEXT NOT NULL, inverse TEXT NOT NULL, undoes INTEGER, redoes INTEGER, note TEXT, created_at TEXT NOT NULL)`,
    )
    sql.exec(`CREATE INDEX IF NOT EXISTS batches_author ON batches(author_id, seq)`)
  }

  private meta(k: string): string | null {
    const r = this.sql.exec<{ v: string }>('SELECT v FROM meta WHERE k = ?', k).toArray()[0]
    return r ? r.v : null
  }
  private setMeta(k: string, v: string) {
    this.sql.exec('INSERT INTO meta (k, v) VALUES (?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v', k, v)
  }

  get seq(): number {
    return Number(this.meta('seq') ?? 0)
  }
  get base(): unknown {
    const b = this.meta('base')
    return b ? JSON.parse(b) : null
  }
  setBase(base: unknown) {
    this.setMeta('base', JSON.stringify(base))
  }

  private toEl(r: Row): Element {
    return { ...(JSON.parse(r.json) as Element), version: r.version, deleted: Boolean(r.deleted) }
  }
  element(id: string): Element | null {
    const r = this.sql.exec<Row>('SELECT * FROM elements WHERE id = ?', id).toArray()[0]
    return r ? this.toEl(r) : null
  }
  private type(id: string): Element | null {
    const r = this.sql.exec<Row>('SELECT * FROM types WHERE id = ?', id).toArray()[0]
    return r ? this.toEl(r) : null
  }
  private putEl(e: Element, seq: number) {
    const { version, deleted, ...rest } = e
    this.sql.exec(
      'INSERT INTO elements (id, json, version, deleted, kind, changed_seq) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET json = excluded.json, version = excluded.version, deleted = excluded.deleted, kind = excluded.kind, changed_seq = excluded.changed_seq',
      e.id,
      JSON.stringify(rest),
      version,
      deleted ? 1 : 0,
      String(e.kind ?? ''),
      seq,
    )
  }
  private putType(t: Element, seq: number) {
    const { version, deleted, ...rest } = t
    this.sql.exec(
      'INSERT INTO types (id, json, version, deleted, changed_seq) VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET json = excluded.json, version = excluded.version, deleted = excluded.deleted, changed_seq = excluded.changed_seq',
      t.id,
      JSON.stringify(rest),
      version,
      deleted ? 1 : 0,
      seq,
    )
  }

  /** `GET …/model` (§17.4). */
  read(since: number | null, cursor: string | null) {
    const levels: Element[] = this.sql
      .exec<Row>("SELECT * FROM elements WHERE kind = 'level' AND deleted = 0 ORDER BY id")
      .toArray()
      .map((r) => this.toEl(r))
    const rows = this.sql
      .exec<Row>(
        `SELECT * FROM elements WHERE kind != 'level' AND deleted = 0 ${since === null ? '' : 'AND changed_seq > ?'} ${cursor ? 'AND id > ?' : ''} ORDER BY id LIMIT ?`,
        ...([since, cursor].filter((x) => x !== null) as (string | number)[]),
        PAGE + 1,
      )
      .toArray()
    const more = rows.length > PAGE
    const elements = rows.slice(0, PAGE).map((r) => this.toEl(r))
    const types = this.sql
      .exec<Row>('SELECT * FROM types ORDER BY id')
      .toArray()
      .map((r) => this.toEl(r))
    const deleted =
      since === null ? undefined : this.sql.exec<{ id: string }>('SELECT id FROM elements WHERE deleted = 1 AND changed_seq > ?', since).toArray().map((r) => r.id)
    return {
      seq: this.seq,
      levels,
      types,
      elements,
      ...(deleted ? { deleted } : {}),
      ...(more ? { next_cursor: elements[elements.length - 1].id } : {}),
    }
  }

  /** Counts and a filtered list, for the agent. */
  summary(filter: { kind?: string | null; ids?: string[] | null; limit?: number | null }) {
    const counts = Object.fromEntries(
      this.sql.exec<{ kind: string; n: number }>('SELECT kind, COUNT(*) AS n FROM elements WHERE deleted = 0 GROUP BY kind').toArray().map((r) => [r.kind, r.n]),
    )
    const limit = Math.max(1, Math.min(300, filter.limit ?? 100))
    let rows: Row[]
    if (filter.ids?.length) {
      rows = filter.ids.slice(0, limit).flatMap((id) => this.sql.exec<Row>('SELECT * FROM elements WHERE id = ?', id).toArray())
    } else if (filter.kind) {
      rows = this.sql.exec<Row>('SELECT * FROM elements WHERE deleted = 0 AND kind = ? ORDER BY id LIMIT ?', filter.kind, limit).toArray()
    } else rows = this.sql.exec<Row>('SELECT * FROM elements WHERE deleted = 0 ORDER BY kind, id LIMIT ?', limit).toArray()
    const types = this.sql.exec<{ n: number }>('SELECT COUNT(*) AS n FROM types WHERE deleted = 0').toArray()[0]?.n ?? 0
    return { seq: this.seq, counts, types, elements: rows.map((r) => this.toEl(r)) }
  }

  private applyOps(seq: number, ops: Op[]) {
    for (const op of ops) {
      switch (op.op) {
        case 'create': {
          const e = op.element as Element
          if (!e?.id) break
          this.putEl({ ...e, version: 1, deleted: false }, seq)
          break
        }
        case 'update': {
          const cur = this.element(op.id)
          if (!cur) break
          this.putEl({ ...(patchInto(cur, op.patch) as Element), id: cur.id, version: cur.version + 1, deleted: cur.deleted }, seq)
          break
        }
        case 'delete': {
          const cur = this.element(op.id)
          if (!cur || cur.deleted) break
          this.putEl({ ...cur, deleted: true, version: cur.version + 1 }, seq)
          break
        }
        case 'restore': {
          const cur = this.element(op.id)
          if (!cur || !cur.deleted) break
          this.putEl({ ...cur, deleted: false, version: cur.version + 1 }, seq)
          break
        }
        case 'type.create': {
          const t = op.type as Element
          if (!t?.id) break
          this.putType({ ...t, version: 1, deleted: false }, seq)
          break
        }
        case 'type.update': {
          const cur = this.type(op.id)
          if (!cur) break
          this.putType({ ...(patchInto(cur, op.patch) as Element), id: cur.id, version: cur.version + 1, deleted: cur.deleted }, seq)
          break
        }
        case 'type.delete':
        case 'type.restore': {
          const cur = this.type(op.id)
          const del = op.op === 'type.delete'
          if (!cur || Boolean(cur.deleted) === del) break
          this.putType({ ...cur, deleted: del, version: cur.version + 1 }, seq)
          break
        }
      }
    }
  }

  /** if_version checks, then apply and log with an inverse. Returns the new seq or the conflicts. */
  applyBatch(author: Author, batchId: string, ops: Op[], extra: { undoes?: number; redoes?: number; note?: string | null } = {}) {
    if (!Array.isArray(ops) || !ops.length) return { error: 'no ops' as const }
    const conflicts: { id: string; version: number; element: Element }[] = []
    for (const o of ops) {
      if (o.if_version === undefined || !o.id) continue
      const cur = o.op.startsWith('type.') ? this.type(o.id) : this.element(o.id)
      if (cur && cur.version !== o.if_version) conflicts.push({ id: o.id, version: cur.version, element: cur })
    }
    if (conflicts.length) return { conflicts }
    const inverse: Op[] = []
    for (const op of ops) {
      if (op.op === 'create') {
        if (op.element?.id) inverse.unshift({ op: 'delete', id: op.element.id, if_version: 1 })
      } else if (op.op === 'update' || op.op === 'type.update') {
        const cur = op.op === 'update' ? this.element(op.id) : this.type(op.id)
        if (!cur) continue
        const back: Record<string, unknown> = {}
        for (const k of Object.keys(op.patch ?? {})) back[k] = cur[k] ?? null
        inverse.unshift({ op: op.op, id: op.id, patch: back, if_version: cur.version + 1 })
      } else if (op.op === 'delete') {
        const cur = this.element(op.id)
        if (cur && !cur.deleted) inverse.unshift({ op: 'restore', id: op.id, if_version: cur.version + 1 })
      } else if (op.op === 'restore') {
        const cur = this.element(op.id)
        if (cur?.deleted) inverse.unshift({ op: 'delete', id: op.id, if_version: cur.version + 1 })
      } else if (op.op === 'type.create') {
        if (op.type?.id) inverse.unshift({ op: 'type.delete', id: op.type.id, if_version: 1 })
      } else if (op.op === 'type.delete' || op.op === 'type.restore') {
        const cur = this.type(op.id)
        if (cur) inverse.unshift({ op: op.op === 'type.delete' ? 'type.restore' : 'type.delete', id: op.id, if_version: cur.version + 1 })
      }
    }
    const seq = this.seq + 1
    this.applyOps(seq, ops)
    this.setMeta('seq', String(seq))
    this.sql.exec(
      'INSERT INTO batches (seq, batch_id, author_id, author, ops, inverse, undoes, redoes, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
      seq,
      batchId,
      author.id,
      JSON.stringify(author),
      JSON.stringify(ops),
      JSON.stringify(inverse),
      extra.undoes ?? null,
      extra.redoes ?? null,
      extra.note ?? null,
      new Date().toISOString(),
    )
    const applied = ops
      .map((o) => (o.op === 'create' ? o.element?.id : o.op === 'type.create' ? o.type?.id : o.id) as string | undefined)
      .filter((id): id is string => Boolean(id))
      .map((id) => ({ id, version: (this.element(id) ?? this.type(id))?.version ?? 1 }))
    return { seq, applied }
  }

  /** The author's newest batch that isn't undone (and isn't an undo), or the newest undone one to redo. */
  pickStep(authorId: string, which: 'undo' | 'redo'): { seq: number; inverse: Op[] } | null {
    const mine = this.sql.exec<BatchRow>('SELECT seq, inverse, undoes, redoes FROM batches WHERE author_id = ? ORDER BY seq', authorId).toArray()
    const undone = new Set(mine.filter((b) => b.undoes !== null).map((b) => b.undoes!))
    const redone = new Set(mine.filter((b) => b.redoes !== null).map((b) => b.redoes!))
    if (which === 'undo') {
      for (const b of [...mine].reverse()) {
        if (b.undoes !== null) continue
        if (!undone.has(b.seq) || redone.has(b.seq)) return { seq: b.seq, inverse: JSON.parse(b.inverse) }
      }
      return null
    }
    const last = mine[mine.length - 1]
    if (!last || last.undoes === null || redone.has(last.undoes)) return null
    // redo re-applies what the undo reversed: the undo batch's own inverse
    return { seq: last.undoes, inverse: JSON.parse(last.inverse) }
  }
}
