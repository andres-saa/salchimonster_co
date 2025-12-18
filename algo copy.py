import requests
from bs4 import BeautifulSoup
import os
import time

# ==========================================
#             CONFIGURACIÓN
# ==========================================

DOMINIO_PRINCIPAL = "https://www.xvideos.com" 
URL_BUSQUEDA = "https://www.xvideos.com/?k=bbc&durf=1-3min"
PARAMETRO_PAGINACION = "&p=" 
FILTRO_INICIO = "https://www.xvideos.com/video."

PAGINA_INICIO = 1
PAGINA_FIN = 149

CARPETA_SALIDA = "links_filtrados"
ARCHIVO_LINKS = os.path.join(CARPETA_SALIDA, "todos_los_links_acumulados.txt")
ARCHIVO_PROGRESO = "progreso.txt" # Aquí guardaremos en qué página vamos

# ==========================================

def cargar_progreso():
    """Lee el archivo de progreso para saber dónde continuar."""
    if os.path.exists(ARCHIVO_PROGRESO):
        try:
            with open(ARCHIVO_PROGRESO, 'r') as f:
                pagina = int(f.read().strip())
                print(f"[INFO] Se encontró progreso previo. Reanudando en página {pagina}.")
                return pagina
        except:
            print("[INFO] Error leyendo progreso, iniciando desde cero.")
            return PAGINA_INICIO
    else:
        return PAGINA_INICIO

def guardar_progreso(pagina):
    """Guarda el número de la SIGUIENTE página a procesar."""
    with open(ARCHIVO_PROGRESO, 'w') as f:
        f.write(str(pagina))

def guardar_links_en_disco(nuevos_links):
    """Añade los links al archivo inmediatamente (Append mode)."""
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)
        
    with open(ARCHIVO_LINKS, 'a', encoding='utf-8') as f: # 'a' es para añadir (append)
        for link in nuevos_links:
            f.write(link + '\n')
    print(f"    -> {len(nuevos_links)} links guardados en '{ARCHIVO_LINKS}'")

def obtener_links_exactos():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # 1. Determinar página de inicio
    pagina_actual = cargar_progreso()

    if pagina_actual > PAGINA_FIN:
        print("!!! El script ya había completado todas las páginas anteriormente.")
        return

    print(f"--- Iniciando búsqueda desde pág {pagina_actual} hasta {PAGINA_FIN} ---")
    print(f"--- Modo: 1 página por minuto | Guardado automático ---")

    while pagina_actual <= PAGINA_FIN:
        url_actual = f"{URL_BUSQUEDA}{PARAMETRO_PAGINACION}{pagina_actual}"
        print(f"\n--> Procesando página {pagina_actual}...")

        nuevos_links = [] # Lista temporal solo para esta página

        try:
            response = requests.get(url_actual, headers=headers, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                elementos = soup.find_all('a', href=True)
                
                for elem in elementos:
                    raw_link = elem['href']
                    link_completo = raw_link

                    # Completar URL relativa
                    if raw_link.startswith('/'):
                        link_completo = DOMINIO_PRINCIPAL + raw_link
                    
                    # Filtrar
                    if link_completo.startswith(FILTRO_INICIO):
                        nuevos_links.append(link_completo)
                
                # Quitar duplicados internos de esta página solamente
                nuevos_links = list(set(nuevos_links))

                if nuevos_links:
                    # 2. GUARDAR INMEDIATAMENTE
                    guardar_links_en_disco(nuevos_links)
                else:
                    print("    (No se encontraron links válidos en esta página)")

                # 3. ACTUALIZAR PROGRESO (Para que si falla, empiece en la siguiente)
                guardar_progreso(pagina_actual + 1)
                
                # Avanzar contador local
                pagina_actual += 1

            else:
                print(f"    Error {response.status_code}. Reintentando misma página en 60s...")
                # No avanzamos 'pagina_actual' ni actualizamos progreso para reintentar luego

        except Exception as e:
            print(f"    Error conexión: {e}. Reintentando misma página en 60s...")
            # No avanzamos para reintentar

        # 4. ESPERA DE 1 MINUTO
        if pagina_actual <= PAGINA_FIN: # Solo esperar si quedan páginas
            print("    ... Esperando 60 segundos ...")
            time.sleep(60) 

    print("\n=== Búsqueda Finalizada con Éxito ===")
    # Opcional: Borrar el archivo de progreso al terminar
    # if os.path.exists(ARCHIVO_PROGRESO):
    #    os.remove(ARCHIVO_PROGRESO)

if __name__ == "__main__":
    obtener_links_exactos()