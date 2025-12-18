import { getCountries, getCountryCallingCode } from 'libphonenumber-js'
import * as isoCountries from 'i18n-iso-countries'
import en from 'i18n-iso-countries/langs/en.json'
import es from 'i18n-iso-countries/langs/es.json'

isoCountries.registerLocale(en as any)
isoCountries.registerLocale(es as any)

export type CountryOption = {
  code: string;   // "US", "CO"
  name: string;   // "United States", "Colombia"
  dialCode: string; // "+1", "+57"
  flag: string;   // flagcdn url
  label: string;  // mostrado en el Select (p.ej. "+57")
  dialDigits?: string; // "1", "57" (opcional)
}

export function buildCountryOptions(locale: 'es'|'en' = 'es'): CountryOption[] {
  const codes = getCountries()
  const opts: CountryOption[] = codes.map(code => {
    const name = isoCountries.getName(code, locale) || code
    const dial = '+' + getCountryCallingCode(code)
    const flag = `https://flagcdn.com/w20/${code.toLowerCase()}.png`
    return {
      code,
      name,
      dialCode: dial,
      flag,
      label: `${dial}`,
      dialDigits: dial.replace(/\D+/g, '')
    }
  })
  opts.sort((a, b) => a.name.localeCompare(b.name, locale))
  return opts
}
