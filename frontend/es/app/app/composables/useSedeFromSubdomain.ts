// composables/useSedeFromSubdomain.ts
export const useSedeFromSubdomain = () => {
  const getSede = (host: string | null) => {
    if (!host) return null

    const hostname = host.split(':')[0] // ej: cali.localhost
    const parts = hostname.split('.')

    // Caso especial: *.localhost → cali.localhost, bogota.localhost, etc.
    if (hostname.endsWith('.localhost')) {
      // parts = ["cali", "localhost"]
      return parts[0] || null
    }

    // Dominio normal: cali.salchi.com, bogota.salchi.com, etc.
    if (parts.length < 3) return null

    const sub = parts[0] === 'www' ? parts[1] : parts[0]
    return sub
  }

  // SSR
  if (import.meta.server) {
    const host = useRequestHeader('host') || null
    return getSede(host)
  }

  // Cliente
  const host = window.location.host
  return getSede(host)
}
