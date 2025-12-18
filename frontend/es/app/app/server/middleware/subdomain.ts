// server/middleware/subdomain.ts
import { defineEventHandler, getRequestHeader } from 'h3'

export default defineEventHandler((event) => {
  const host = getRequestHeader(event, 'host') || '' // tienda1.salchimonster.com:3000
  const hostname = host.split(':')[0]                // quita el puerto
  const parts = hostname.split('.')

  let subdomain: string | null = null

  if (parts.length >= 3) {
    subdomain = parts[0] === 'www' ? parts[1] : parts[0]
  }

  // lo guardas en el contexto para usar en cualquier handler/composable server-side
  // @ts-ignore
  event.context.subdomain = subdomain
})
