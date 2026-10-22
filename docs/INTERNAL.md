# Internal contracts (between Pages Functions and the realtime Worker)

The realtime Worker (`workers/realtime`, script name `movingatoms-realtime`) exports one Durable Object class,
`ProjectRoom` (SQLite-backed), one instance per project: `env.PROJECT_ROOM.idFromName(projectId)`.
Pages Functions reach it with `room(env, pid).fetch('https://room/<route>', …)` (src/projects.ts).
Every request carries the project id (`?project_id=` or the JSON body's `project_id`).

| Route | Body / query | Answer |
|---|---|---|
| `GET /ws?project_id=` (Upgrade: websocket) | forwarded browser request | 101; protocol below |
| `POST /emit` | `{project_id, events: LiveEvent[]}` | 204; broadcast to subscribed sockets |
| `GET /model/seq?project_id=` | | `{seq, base: ModelBase \| null}` |
| `GET /model?project_id=&since_seq=&cursor=` | | `ModelRead` (§17.4) |
| `GET /model/elements/:id?project_id=` | | `{element}` or 404 |
| `POST /model/ops` | `{project_id, batch_id, ops, note?, author:{kind,id,name}}` | `{seq, applied:[{id,version}], cascaded:[]}`, 409 `{error:'conflict', conflicts}` |
| `POST /model/undo` · `/model/redo` | `{project_id, batch_id?, author}` | `{seq, applied}` or 409 `{error}` |
| `POST /turn` | `{project_id, message_id, user:{id,email,name}}` | 202; runs an agent turn in the background |
| `POST /stop` | `{project_id}` | `{stopped: boolean}` |

Live socket protocol (browser ⇄ room), matching web/src/lib/live.ts:
client `{"type":"auth","token":<access token>}` → `{"type":"auth.ok","user_id"}` (or `{"type":"error"}` + close);
client `{"type":"subscribe","project_id"}` → membership checked in D1 → `{"type":"subscribed","project_id"}`;
client `{"type":"ping"}` → `{"type":"pong"}`. Then `LiveEvent`s as JSON text frames.
The browser opens `/app/ws?project_id=<pid>` (the app bundle is patched to add the query) so the Function can route
the upgrade to the right room.
