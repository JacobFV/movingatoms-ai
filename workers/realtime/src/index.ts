// The realtime Worker: home of the ProjectRoom Durable Object. Pages Functions reach it through the PROJECT_ROOM
// binding (script_name = movingatoms-realtime); it serves nothing on its own.
import { ProjectRoom } from './room'

export default {
  async fetch(): Promise<Response> {
    return new Response('Not found', { status: 404 })
  },
} satisfies ExportedHandler

export { ProjectRoom }
