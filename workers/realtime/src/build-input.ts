/** Explicit experimental output selection; normal checkpoints retain their existing input. */
export function publishBuildInput(input: Record<string, unknown>): Record<string, unknown> {
  for (const key of ['experimental_native_rvt', 'acknowledge_native_hypotheses']) {
    if (input[key] !== undefined && typeof input[key] !== 'boolean') {
      throw new Error(`${key} must be a boolean.`)
    }
  }
  const result: Record<string, unknown> = {
    title: String(input.title ?? '').slice(0, 200),
    notes: String(input.notes ?? '').slice(0, 4000),
    by: 'agent',
  }
  if (input.experimental_native_rvt === true) {
    if (input.acknowledge_native_hypotheses !== true) {
      throw new Error('Experimental native RVT requires acknowledge_native_hypotheses: true. Revit opening, regeneration and saving have not been verified.')
    }
    result.experimental_native_rvt = true
    result.acknowledge_native_hypotheses = true
  }
  return result
}
