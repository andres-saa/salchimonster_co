// composables/useSubdomain.ts
export const useSubdomain = () => {
  if (process.server) return null

  const host = window.location.hostname // p.ej. tienda1.salchimonster.com
  const parts = host.split('.')

  // localhost o sin subdominio
  if (parts.length < 3) return null

  return parts[0] === 'www' ? parts[1] : parts[0]
}
