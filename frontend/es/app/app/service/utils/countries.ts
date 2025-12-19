import { getCountries, getCountryCallingCode } from 'libphonenumber-js'
import isoCountries from 'i18n-iso-countries'

// Importación ESTÁTICA de los idiomas (Crucial para que Vite/Rollup no fallen)
import en from 'i18n-iso-countries/langs/en.json'
import es from 'i18n-iso-countries/langs/es.json'

// Registrar los idiomas disponibles
// "as any" es necesario aquí porque la estructura del JSON a veces difiere 
// ligeramente de la interfaz estricta de la librería en TypeScript.
isoCountries.registerLocale(en as any)
isoCountries.registerLocale(es as any)

export type CountryOption = {
  code: string;       // Ejemplo: "CO"
  name: string;       // Ejemplo: "Colombia"
  dialCode: string;   // Ejemplo: "+57"
  flag: string;       // URL de la bandera
  label: string;      // Texto para el selector
  dialDigits?: string; // Solo números: "57"
}

export function buildCountryOptions(locale: 'es' | 'en' = 'es'): CountryOption[] {
  // 1. Obtener todos los códigos ISO disponibles en libphonenumber
  const codes = getCountries()

  // 2. Mapear a nuestro formato
  const opts: CountryOption[] = codes.map(code => {
    // Intentar obtener el nombre traducido, si falla usar el código
    const name = isoCountries.getName(code, locale) || code
    
    // Obtener código de llamada
    const dial = '+' + getCountryCallingCode(code)
    
    // Generar URL de la bandera (FlagCDN es rápido y gratuito)
    const flag = `https://flagcdn.com/w20/${code.toLowerCase()}.png`

    return {
      code,
      name,
      dialCode: dial,
      flag,
      label: `${dial}  ${name}`, // Ajusta esto según cómo quieras que se vea en el Select
      dialDigits: dial.replace(/\D+/g, '') // Elimina el "+" para dejar solo números
    }
  })

  // 3. Ordenar alfabéticamente por el nombre del país
  opts.sort((a, b) => a.name.localeCompare(b.name, locale))

  return opts
}