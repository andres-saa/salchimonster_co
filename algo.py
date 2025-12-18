import os
import yt_dlp
import time

# ================= CONFIGURACIÓN =================
# Archivo de entrada (El archivo único que genera el primer script)
ARCHIVO_ENTRADA = os.path.join("links_filtrados", "todos_los_links_acumulados.txt")

# Archivo de salida (Donde se guardarán los links .mp4/.m3u8 finales)
ARCHIVO_SALIDA_FINAL = "links_directos_finales.txt"

ARCHIVO_LOG = "errores_log.txt"
ARCHIVO_HISTORIAL = "historial_procesados.txt" # AQUÍ SE GUARDA EL PROGRESO

# TIEMPO DE ESPERA (en segundos)
TIEMPO_ESPERA = 300  # 5 minutos entre petición y petición
# =================================================

def cargar_historial():
    """Carga los links que ya se han intentado procesar anteriormente."""
    if not os.path.exists(ARCHIVO_HISTORIAL):
        return set()
    with open(ARCHIVO_HISTORIAL, 'r', encoding='utf-8') as f:
        # Usamos un set (conjunto) para que la búsqueda sea instantánea
        return set(line.strip() for line in f if line.strip())

def registrar_en_historial(url):
    """Guarda la URL en el historial para no volver a procesarla."""
    with open(ARCHIVO_HISTORIAL, 'a', encoding='utf-8') as f:
        f.write(url + '\n')

def extraer_url_directa(url_pagina):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'get_url': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'socket_timeout': 15,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
 
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_pagina, download=False)
            if info:
                return info.get('url', None)
    except Exception:
        return None
    return None

def procesar_archivo_unico():
    # 1. Verificar si existe el archivo de entrada
    if not os.path.exists(ARCHIVO_ENTRADA):
        print(f"ERROR: No existe el archivo de entrada: '{ARCHIVO_ENTRADA}'")
        print("Asegúrate de haber corrido el primer script primero.")
        return

    # 2. Cargar historial previo
    urls_ya_procesadas = cargar_historial()
    print(f"--- Historial cargado: {len(urls_ya_procesadas)} videos ya procesados anteriormente ---")

    # 3. Leer todos los links del archivo de entrada
    print(f">> Leyendo archivo maestro: {ARCHIVO_ENTRADA}...")
    with open(ARCHIVO_ENTRADA, 'r', encoding='utf-8') as f_in:
        # Leemos todas las líneas y quitamos espacios vacíos
        urls_videos = [line.strip() for line in f_in if line.strip()]

    total = len(urls_videos)
    print(f">> Se encontraron {total} enlaces para revisar.")

    # 4. Iterar sobre los links
    for i, url_web in enumerate(urls_videos):
        
        # --- VERIFICACIÓN DE HISTORIAL ---
        if url_web in urls_ya_procesadas:
            # Si ya está en la lista, saltamos sin esperar
            # print(f"  [{i+1}/{total}] Ya procesado anteriormente. Saltando...") 
            continue 

        # Si llegamos aquí, es un link NUEVO que no está en el historial
        print(f"  [{i+1}/{total}] Procesando NUEVO: {url_web}...")
        
        url_real = extraer_url_directa(url_web)
        
        # A. Guardar resultado (si fue exitoso)
        if url_real:
            with open(ARCHIVO_SALIDA_FINAL, 'a', encoding='utf-8') as f_out:
                f_out.write(url_real + '\n')
            print(f"      -> ÉXITO. Link guardado en '{ARCHIVO_SALIDA_FINAL}'")
        else:
            print(f"      -> FALLÓ. (Registrando error)")
            with open(ARCHIVO_LOG, 'a', encoding='utf-8') as f_log:
                f_log.write(f"FALLO: {url_web}\n")

        # B. IMPORTANTE: Registrar en el historial (haya funcionado o fallado)
        # Esto asegura que no se vuelva a intentar este link nunca más
        registrar_en_historial(url_web)
        urls_ya_procesadas.add(url_web) # Actualizar memoria local para este ciclo

        # C. ESPERA (TIEMPO DE ESPERA)
        # Solo esperamos si NO es el último elemento, para no esperar 5 mins al final de todo
        if i < total - 1:
            print(f"      -> Esperando {TIEMPO_ESPERA} segundos...\n")
            time.sleep(TIEMPO_ESPERA)

    print("\n--- Todos los enlaces del archivo han sido procesados ---")

if __name__ == "__main__":
    try:
        procesar_archivo_unico()
    except KeyboardInterrupt:
        print("\n\nScript detenido manualmente.")
        print("Tu progreso se guardó en 'historial_procesados.txt'.")
        print("Puedes volver a correrlo cuando quieras y continuará exactamente donde quedaste.")