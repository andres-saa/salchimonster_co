import os
import yt_dlp
import time

# ================= CONFIGURACIÓN =================
CARPETA_ENTRADA = "links_filtrados"    # Donde están los txt con links de páginas
CARPETA_SALIDA = "direct_links_videos" # Donde se guardarán los links directos .mp4/.m3u8
# =================================================

def extraer_url_video(page_url):
    """
    Usa yt-dlp para obtener la URL directa del recurso multimedia.
    No descarga el video, solo extrae la info.
    """
    opciones = {
        'quiet': True,
        'no_warnings': True,
        'get_url': True,       # Solo obtener la URL
        'skip_download': True, # Asegurar que no descargue nada
        # 'format': 'best',    # Opcional: intentar obtener la mejor calidad
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # extract_info con download=False devuelve un diccionario de metadatos
            info = ydl.extract_info(page_url, download=False)
            
            # A veces 'url' está en el nivel superior, a veces dentro de 'formats'
            if 'url' in info:
                return info['url']
            else:
                return "No se pudo extraer URL directa"
                
    except Exception as e:
        return f"Error: {str(e)}"

def procesar_archivos():
    # 1. Crear carpeta de salida si no existe
    if not os.path.exists(CARPETA_SALIDA):
        os.makedirs(CARPETA_SALIDA)

    # 2. Listar todos los archivos .txt en la carpeta de entrada
    archivos_txt = [f for f in os.listdir(CARPETA_ENTRADA) if f.endswith('.txt')]
    
    if not archivos_txt:
        print(f"No se encontraron archivos .txt en la carpeta '{CARPETA_ENTRADA}'")
        return

    print(f"Se encontraron {len(archivos_txt)} archivos para procesar.")

    # 3. Recorrer cada archivo de texto
    for archivo in archivos_txt:
        ruta_entrada = os.path.join(CARPETA_ENTRADA, archivo)
        ruta_salida = os.path.join(CARPETA_SALIDA, f"directos_{archivo}")
        
        print(f"\nProcesando archivo: {archivo}...")
        
        links_procesados = []

        with open(ruta_entrada, 'r', encoding='utf-8') as f_in:
            urls_paginas = f_in.readlines()

        total_urls = len(urls_paginas)
        
        # 4. Procesar cada URL dentro del archivo
        for indice, url_pagina in enumerate(urls_paginas):
            url_pagina = url_pagina.strip()
            if not url_pagina: continue

            print(f"  [{indice+1}/{total_urls}] Extrayendo: {url_pagina[:50]}...")
            
            url_directa = extraer_url_video(url_pagina)
            
            # Verificar si obtuvimos una URL válida (usualmente empiezan por http)
            if url_directa and url_directa.startswith('http'):
                links_procesados.append(url_directa)
            else:
                print(f"   -> Falló extracción: {url_directa}")

            # Pequeña pausa para no saturar
            time.sleep(1)

        # 5. Guardar los resultados en el archivo de salida
        if links_procesados:
            with open(ruta_salida, 'w', encoding='utf-8') as f_out:
                for link in links_procesados:
                    f_out.write(link + '\n')
            print(f"--- Guardado {ruta_salida} con {len(links_procesados)} enlaces directos ---")
        else:
            print(f"--- No se encontraron enlaces válidos en {archivo} ---")

if __name__ == "__main__":
    # Asegúrate de tener instalado yt-dlp: pip install yt-dlp
    procesar_archivos()