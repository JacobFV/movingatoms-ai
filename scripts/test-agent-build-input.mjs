import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import vm from 'node:vm'
import ts from 'typescript'
import { publishBuildInput } from '../workers/realtime/src/build-input.ts'

const source = readFileSync(new URL('../workers/realtime/src/agent.ts', import.meta.url), 'utf8')
const parsed = ts.createSourceFile('agent.ts', source, ts.ScriptTarget.Latest, true)
const toolsDeclaration = parsed.statements.flatMap(s => ts.isVariableStatement(s) ? [...s.declarationList.declarations] : []).find(d => d.name.getText(parsed) === 'TOOLS')
const tools = vm.runInNewContext(`(${toolsDeclaration.initializer.getText(parsed)})`)
const toolFunction = parsed.statements.find(s => ts.isFunctionDeclaration(s) && s.name?.text === 'runTool')
const compiled = ts.transpileModule(toolFunction.getText(parsed), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } }).outputText
const runTool = vm.runInNewContext(`${compiled};runTool`, { publishBuildInput, crypto: globalThis.crypto })

function host() {
  const jobs = [], activities = []
  return {
    jobs, activities, pid: 'project-test',
    env: { DB: { prepare: () => ({ bind: (...args) => ({ run: async () => { jobs.push(JSON.parse(args[3])) } }) }) } },
    emit() {}, async jobQueued() {}, async activity(text) { activities.push(text) },
  }
}

test('ordinary and legacy checkpoints retain their exact input', () => {
  const expected = { title: 'Checkpoint', notes: 'Changed walls', by: 'agent' }
  assert.deepEqual(publishBuildInput({ title: expected.title, notes: expected.notes }), expected)
  assert.deepEqual(publishBuildInput({ title: expected.title, notes: expected.notes, experimental_native_rvt: false, acknowledge_native_hypotheses: false }), expected)
  assert.deepEqual(publishBuildInput({ title: 'Export .rvt', acknowledge_native_hypotheses: true }), { title: 'Export .rvt', notes: '', by: 'agent' })
  assert.equal(publishBuildInput({ title: 'x'.repeat(300), notes: 'y'.repeat(5000) }).title.length, 200)
  assert.equal(publishBuildInput({ notes: 'y'.repeat(5000) }).notes.length, 4000)
})

test('experimental selection requires a boolean acknowledgment and no coercion', () => {
  for (const value of [undefined, false, null, 'true', 1]) {
    assert.throws(() => publishBuildInput({ experimental_native_rvt: true, acknowledge_native_hypotheses: value }))
  }
  for (const value of [null, 'true', 1, [], {}]) {
    assert.throws(() => publishBuildInput({ experimental_native_rvt: value, acknowledge_native_hypotheses: true }))
  }
  assert.deepEqual(publishBuildInput({ experimental_native_rvt: true, acknowledge_native_hypotheses: true }), {
    title: '', notes: '', by: 'agent', experimental_native_rvt: true, acknowledge_native_hypotheses: true,
  })
})

test('actual strict publish tool exposes explicit false-by-default boolean choices', () => {
  const tool = tools.find(t => t.name === 'publish_revision')
  assert.equal(tool.strict, true)
  assert.equal(tool.input_schema.additionalProperties, false)
  for (const key of ['experimental_native_rvt', 'acknowledge_native_hypotheses']) {
    assert.equal(tool.input_schema.properties[key].type, 'boolean')
    assert.ok(tool.input_schema.required.includes(key))
    assert.match(tool.input_schema.properties[key].description, /False by default/)
  }
  assert.match(tool.description, /unverified/)
})

test('actual agent tool queues selected flags and qualified wording', async () => {
  const h = host()
  const result = await runTool(h, 'publish_revision', { title: 'Native trial', notes: '', experimental_native_rvt: true, acknowledge_native_hypotheses: true })
  assert.equal(h.jobs.length, 1)
  assert.equal(h.jobs[0].experimental_native_rvt, true)
  assert.equal(h.jobs[0].acknowledge_native_hypotheses, true)
  assert.match(h.activities[0], /experimental native RVT/)
  assert.match(JSON.parse(result.content).note, /unverified/)
})

test('actual agent tool refuses invalid selection before enqueue and keeps defaults', async () => {
  const h = host()
  const result = await runTool(h, 'publish_revision', { experimental_native_rvt: true })
  assert.equal(result.isError, true)
  assert.equal(h.jobs.length, 0)
  await runTool(h, 'publish_revision', { title: 'Usual', notes: '' })
  assert.deepEqual(h.jobs, [{ title: 'Usual', notes: '', by: 'agent' }])
  assert.equal(h.activities[0], 'Started build on the processing workers')
})
