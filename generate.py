#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de estructura completa con SSL auto (Let's Encrypt):
• Crea carpeta raíz <proyecto> o agrega/edita servicios a uno existente
• Back-end ⇒ api_<nombre>  (se agrega SIEMPRE api_socket)
• Front-end ⇒ front_<nombre> (Vue 3 / Vite ó Nuxt 3)
• docker-compose.yml (dev) con (opcionales) Postgres/pgAdmin, Mongo y Redis
  ─ En DEV no se usa Nginx; cada servicio se expone en su puerto local:
    - Back-ends: localhost:8000, 8001, 8002, ...
    - Fronts Vue: localhost:5173, 5174, ...
    - Fronts Nuxt: localhost:3000, 3001, ...
    - Mongo (para Compass): localhost:27017
• compose.prod.yml (prod con (opcionales) Postgres/pgAdmin, Mongo y Redis + Certbot + Nginx)
• nginx (solo PROD) con reverse-proxy http + https
• Modo 'editar' para cambiar dominio/email/staging, agregar/quitar/renombrar servicios
• Puedes activar Postgres, MongoDB y Redis (con volúmenes persistentes).
• Para cada front en producción se generan host sin-www y con-www (ambos con SSL);
  el host con-www redirige 301 al sin-www.
• Se crea SIEMPRE un backend de sockets: api_socket (host: api.socket.<proyecto>.<dominio>).
  En producción corre con gunicorn/uvicorn con -w 1 (un solo worker).

NOTA MongoDB:
- En DEV, conecta con Compass: mongodb://admin:admin@localhost:27017/?authSource=admin
- En PROD, no se publica 27017 por seguridad; usa túnel SSH/VPN si necesitas acceder con Compass.

Correcciones importantes:
- Todos los container_name incluyen el nombre del proyecto (evita conflictos entre stacks).
- Redis: los backends usan REDIS_URL apuntando al servicio 'redis' dentro de la red de Docker
  (no a localhost). Se agrega por defecto REDIS_URL=redis://:redispass@redis:6379/0 en los .env
  de backend, y depends_on: [redis] cuando Redis está habilitado.
"""

import os
import re
import json
import shutil
import textwrap as tw
from pathlib import Path
import subprocess
import shlex
from typing import List, Optional, Tuple, Dict, Any, Union


def _path_for_docker_mount(p: Path) -> str:
    """
    Normaliza rutas para -v en Docker en Windows/Linux/Mac.
    En Windows, convierte D:\a\b -> /d/a/b para minimizar problemas de path escaping.
    """
    s = str(p.resolve())
    if os.name == "nt":
        drive, rest = os.path.splitdrive(s)
        drive = drive.rstrip(":").lower()
        rest = rest.replace("\\", "/")
        return f"/{drive}{rest}"
    return s

def run_node(workdir: Path, commands: List[str]) -> None:
    """
    Intenta ejecutar una lista de comandos Node/NPM:
    1) Local (si existe npm/pnpm/yarn)
    2) Docker (node:20-alpine)
    Lanza excepción si todos fallan.
    """
    have_local = shutil.which("npm") or shutil.which("pnpm") or shutil.which("yarn")
    errors = []

    # 1) Intentar LOCAL
    if have_local:
        for cmd in commands:
            try:
                print("→ Ejecutando local:", cmd)
                subprocess.run(cmd, cwd=workdir, shell=True, check=True)
                return
            except subprocess.CalledProcessError as e:
                errors.append(f"[LOCAL] {cmd}\n  exit={e.returncode}")
                continue

    # 2) Fallback a DOCKER
    workdir_mount = _path_for_docker_mount(workdir)
    for cmd in commands:
        try:
            print("→ Ejecutando en Docker:", cmd)
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{workdir_mount}:/app",
                "-w", "/app",
                "node:20-alpine",
                "sh", "-lc",  # -l para login shell (carga PATH), -c para el comando
                # Prepara entorno npm para menos ruido y más compatibilidad
                "set -e; "
                "npm config set fund false; "
                "npm config set audit false; "
                + cmd
            ], check=True)
            return
        except subprocess.CalledProcessError as e:
            errors.append(f"[DOCKER] {cmd}\n  exit={e.returncode}")
            continue

    # Si llegamos aquí, todo falló
    msg = "No se pudo ejecutar ningún comando de scaffolding.\n" + "\n".join(errors)
    raise RuntimeError(msg)


# ─────────── plantillas fijas ────────────────────────────────────────────
DOCKERIGNORE = "__pycache__/\n*.py[cod]\n.venv/\nnode_modules/\n.git/\n"
GITIGNORE_PY = "__pycache__/\n*.py[cod]\n.venv/\nvenv/\ndist/\nbuild/\n.env\n"
GITIGNORE_NODE = "node_modules/\ndist/\n.env\nnpm-debug.log*\nyarn-debug.log*\n"

# .env por defecto de cada backend (ahora incluye Redis apuntando al servicio 'redis')
DOTENV_BACK = (
    "DB_USER=postgres\n"
    "DB_PASSWORD=postgres\n"
    "DB_HOST=postgres\n"
    "DB_PORT=5432\n"
    "DB_NAME=mydb\n"
    "SECRET_KEY=change_me\n"
    "# Redis interno en Docker (no uses localhost aquí)\n"
    "REDIS_URL=redis://:redispass@redis:6379/0\n"
)

# .env compartido para Postgres/pgAdmin + Mongo + Redis (en ./db/.env)
DB_DOTENV = (
    "# ==== Postgres / pgAdmin ====\n"
    "POSTGRES_USER=postgres\n"
    "POSTGRES_PASSWORD=postgres\n"
    "POSTGRES_DB=mydb\n"
    "PGADMIN_DEFAULT_EMAIL=admin@example.com\n"
    "PGADMIN_DEFAULT_PASSWORD=admin\n"
    "\n"
    "# ==== Mongo ====\n"
    "MONGO_INITDB_ROOT_USERNAME=admin\n"
    "MONGO_INITDB_ROOT_PASSWORD=admin\n"
    "MONGO_INITDB_DATABASE=mydb\n"
    "\n"
    "# ==== Redis ====\n"
    "REDIS_PASSWORD=redispass\n"
)

DOCKERFILE_BACK = tw.dedent("""
    FROM python:3.12 AS base
    WORKDIR /code
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    FROM base AS dev
    ENV PYTHONUNBUFFERED=1
    COPY ./app /code/
    CMD ["uvicorn","main:app","--host","0.0.0.0","--port","80","--reload"]

    FROM base AS prod
    RUN pip install --no-cache-dir gunicorn uvicorn[standard]
    COPY ./app /code/
    CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","-w","4","-t","1","-b","0.0.0.0:80","main:app"]
""").strip() + "\n"

# 🔧 SPA: Nginx de front Vue con fallback a index.html (solo para imagen de PROD del front)
VUE_NGINX_CONF = tw.dedent("""
    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        # History mode SPA fallback
        location / {
            try_files $uri $uri/ /index.html;
        }

        # estáticos (fonts)
        location ~* \\.(?:svg|ttf|otf|eot|woff|woff2)$ {
            add_header Access-Control-Allow-Origin "*";
        }
    }
""").lstrip()

DOCKERFILE_VUE = tw.dedent("""
    FROM node:20-alpine AS base
    WORKDIR /app

    FROM base AS dev
    COPY ./app/package*.json ./
    RUN npm install
    EXPOSE 5173
    CMD ["npm","run","dev","--","--host","0.0.0.0","--port","5173"]

    FROM base AS builder
    COPY ./app/package*.json ./
    RUN npm install
    COPY ./app .
    COPY .env_prod .env
    RUN npm run build

    FROM nginx:1.27-alpine AS prod
    COPY --from=builder /app/dist /usr/share/nginx/html
    COPY nginx/default.conf /etc/nginx/conf.d/default.conf
    CMD ["nginx","-g","daemon off;"]
""").strip() + "\n"

DOCKERFILE_NUXT = tw.dedent("""
    FROM node:20-alpine AS base
    WORKDIR /app
    ENV NODE_ENV=development

    FROM base AS dev
    COPY ./app/package*.json ./
    RUN npm install
    EXPOSE 3000
    CMD ["npm","run","dev","--","--host"]

    FROM base AS builder
    COPY ./app/package*.json ./
    RUN npm install
    COPY ./app .
    COPY .env_prod .env
    RUN npm run build

    FROM node:20-alpine AS prod
    ENV NODE_ENV=production
    COPY --from=builder /app/.output ./.output
    COPY --from=builder /app/node_modules ./node_modules
    EXPOSE 3000
    CMD ["node",".output/server/index.mjs"]
""").strip() + "\n"

# Imagen del proxy de PROD con script auto-enable HTTPS
DOCKERFILE_PROXY = tw.dedent("""
    FROM nginx:1.27-alpine
    COPY docker-entrypoint.d/ /docker-entrypoint.d/
    RUN chmod +x /docker-entrypoint.d/*.sh || true \
     && sed -i 's/\\r$//' /docker-entrypoint.d/*.sh || true
""").lstrip()

# ⚠️ Archivo (no carpeta) para incluir en Nginx (PROD)
PROXY_PARAMS = (
    "proxy_set_header Host $host;\n"
    "proxy_set_header X-Real-IP $remote_addr;\n"
    "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
    "proxy_set_header X-Forwarded-Proto $scheme;\n"
    "proxy_set_header X-Forwarded-Host $host;\n"
    "proxy_http_version 1.1;\n"
    "\n"
    "# WebSocket\n"
    "proxy_set_header Upgrade $http_upgrade;\n"
    "proxy_set_header Connection \"upgrade\";\n"
    "\n"
    "proxy_read_timeout 300;\n"
    "proxy_connect_timeout 300;\n"
    "proxy_redirect off;\n"
)

# HTTP (80) para PROD
SERVER_HTTP = tw.dedent("""
    server {{
        listen 80;
        server_name {host};

        # ACME HTTP-01
        location ^~ /.well-known/acme-challenge/ {{
            root /var/www/certbot;
        }}

        location / {{
            return 301 https://$host$request_uri;
        }}
    }}
""")

# HTTP (80): www → no-www (solo fronts) PROD
SERVER_HTTP_WWW_REDIRECT = tw.dedent("""
    server {{
        listen 80;
        server_name www.{host};

        location ^~ /.well-known/acme-challenge/ {{
            root /var/www/certbot;
        }}

        location / {{
            return 301 https://{host}$request_uri;
        }}
    }}
""")

# HTTPS (443) PROD
SERVER_HTTPS = tw.dedent("""
    server {{
        listen 443 ssl;
        http2 on;
        server_name {host};

        ssl_certificate /etc/letsencrypt/live/{host}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/{host}/privkey.pem;
        include /etc/nginx/conf.d/ssl_params.conf;

        location / {{
            proxy_pass http://{upstream}:{port};
            include /etc/nginx/proxy_params.conf;
        }}
    }}
""")

# HTTPS (443): www → no-www PROD
SERVER_HTTPS_WWW_REDIRECT = tw.dedent("""
    server {{
        listen 443 ssl;
        http2 on;
        server_name www.{host};

        ssl_certificate /etc/letsencrypt/live/www.{host}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/www.{host}/privkey.pem;
        include /etc/nginx/conf.d/ssl_params.conf;

        location / {{
            return 301 https://{host}$request_uri;
        }}
    }}
""")

SSL_PARAMS = tw.dedent("""
    # ssl_params.conf
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
""").lstrip()

# pgAdmin servers.json preconfigurado
def PGADMIN_SERVERS_JSON(user, db):
    return json.dumps({
        "Servers": {
            "1": {
                "Name": "Proyecto Postgres",
                "Group": "Servers",
                "Host": "postgres",
                "Port": 5432,
                "MaintenanceDB": db or "postgres",
                "Username": user or "postgres",
                "SSLMode": "prefer",
                "ConnectNow": True
            }
        }
    }, indent=2)

BASE_PY = (
    "from pydantic import BaseModel, ConfigDict\n\n"
    "class DBModel(BaseModel):\n"
    "    model_config = ConfigDict(extra='ignore')\n"
)

CONFIG_PY = "import os\nDATABASE_URL = os.getenv('DATABASE_URL','')\n"

DATABASE_PY = """
import os
import inspect
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor, Json
from pydantic import BaseModel

class DBModel(BaseModel):
    model_config = {"extra": "ignore"}
    __schema__: str = ''
    __tablename__: str | None = None

    @classmethod
    def _to_snake(cls, name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    @classmethod
    def table_fullname(cls) -> str:
        name = cls.__tablename__ or cls._to_snake(cls.__name__)
        return f'{cls.__schema__}.{name}' if cls.__schema__ else name

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

class Db:
    def __init__(self) -> None:
        self.conn_str = (
            f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} "
            f"host={DB_HOST} port={DB_PORT}"
        )
        self.conn = psycopg2.connect(self.conn_str)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def close_connection(self):
        self.conn.close()

    @staticmethod
    def _get_table(model_or_cls: Union[DBModel, type[DBModel]]) -> str:
        cls = model_or_cls if isinstance(model_or_cls, type) else model_or_cls.__class__
        if hasattr(cls, "table_fullname"):
            return cls.table_fullname()
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

    @staticmethod
    def _to_payload(data: BaseModel) -> Dict[str, Any]:
        return data.model_dump(exclude_none=True)

    def execute_query(
        self,
        query: str,
        params: Optional[Union[Dict[str, Any], Tuple, List]] = None,
        fetch: bool = False,
    ):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                result = None
                if fetch:
                    rows = cursor.fetchall()
                    if not rows:
                        result = None
                    elif len(rows) == 1:
                        result = rows[0]
                    else:
                        result = rows
                self.conn.commit()
                return result
        except Exception as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")

    def _process_json_params(self, params):
        if params is None:
            return None
        if isinstance(params, (list, tuple)):
            return type(params)(
                Json(p) if isinstance(p, (dict, list)) else p for p in params
            )
        if isinstance(params, dict):
            return {k: Json(v) if isinstance(v, (dict, list)) else v for k, v in params.items()}
        return params

    def execute_query_json(
        self,
        query: str,
        params: Optional[Union[Dict, Tuple, List]] = None,
        fetch: bool = False,
    ):
        processed = self._process_json_params(params)
        return self.execute_query(query, processed, fetch)

    def build_select_query(
        self,
        target: Union[type[DBModel], DBModel, str],
        fields: Optional[List[str]] = None,
        condition: str = '',
        order_by: str = '',
        limit: int = 0,
        offset: int = 0,
        *,
        schema: str = ''
    ) -> str:
        if isinstance(target, str):
            table = f'{schema}.{target}' if schema else target
        else:
            table = self._get_table(target)
        cols = ', '.join(fields) if fields else '*'
        query = f'SELECT {cols} FROM {table}'
        if condition:
            query += f' WHERE {condition}'
        if order_by:
            query += f' ORDER BY {order_by}'
        if limit:
            query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'
        return query

    def build_insert_query(
        self,
        data: DBModel,
        returning: str = ''
    ) -> Tuple[str, Dict[str, Any]]:
        table = self._get_table(data)
        payload = self._to_payload(data)
        cols = ', '.join(payload.keys())
        vals = ', '.join(f'%({k})s' for k in payload)
        query = f'INSERT INTO {table} ({cols}) VALUES ({vals})'
        if returning:
            query += f' RETURNING {returning}'
        return query, payload

    def build_bulk_insert_query(
        self,
        data_list: List[DBModel],
        returning: str = ''
    ) -> Tuple[str, List[Dict[str, Any]]]:
        if not data_list:
            raise ValueError("data_list no puede estar vacío")
        table = self._get_table(data_list[0])
        first_payload = self._to_payload(data_list[0])
        cols = ', '.join(first_payload.keys())
        placeholders = ', '.join(f'%({k})s' for k in first_payload)
        values_block = ', '.join(f'({placeholders})' for _ in data_list)
        query = f'INSERT INTO {table} ({cols}) VALUES {values_block}'
        if returning:
            query += f' RETURNING {returning}'
        params = [self._to_payload(m) for m in data_list]
        return query, params

    def execute_bulk_insert(
        self,
        query: str,
        params: List[Dict[str, Any]],
        fetch: bool = False,
    ):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.executemany(query, params)
                self.conn.commit()
                if fetch:
                    return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")

    def build_update_query(
        self,
        data: DBModel,
        condition: str,
        returning: str = ''
    ) -> Tuple[str, Dict[str, Any]]:
        table = self._get_table(data)
        payload = self._to_payload(data)
        set_clause = ', '.join(f'{k} = %({k})s' for k in payload)
        query = f'UPDATE {table} SET {set_clause} WHERE {condition}'
        if returning:
            query += f' RETURNING {returning}'
        return query, payload

    def execute_bulk_update(
        self,
        query: str,
        params: List[Dict[str, Any]],
        fetch: bool = False,
    ):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.executemany(query, params)
                self.conn.commit()
                if fetch:
                    return cursor.fetchall()
        except Exception as e:
            self.conn.rollback()
            print(f"An error occurred: {e}")

    def build_soft_delete_query(
        self,
        model_cls: type[DBModel],
        condition: str,
        returning: str = ''
    ) -> str:
        table = self._get_table(model_cls)
        query = f'UPDATE {table} SET exist = FALSE WHERE {condition}'
        if returning:
            query += f' RETURNING {returning}'
        return query

    def build_delete_query(
        self,
        model_cls: type[DBModel],
        condition: str,
        returning: str = ''
    ) -> str:
        table = self._get_table(model_cls)
        query = f'DELETE FROM {table} WHERE {condition}'
        if returning:
            query += f' RETURNING {returning}'
        return query

    def fetch_one(self, query: str, params=None):
        return self.execute_query(query, params, fetch=True)

    def fetch_all(self, query: str, params=None):
        result = self.execute_query(query, params, fetch=True)
        return result

    def cargar_archivo_sql(self, nombre_archivo: str) -> Optional[str]:
        try:
            ruta_llamador = os.path.dirname(
                os.path.abspath(inspect.stack()[1].filename)
            )
            ruta_archivo = os.path.join(ruta_llamador, nombre_archivo)
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                return archivo.read()
        except FileNotFoundError:
            print(f"El archivo '{nombre_archivo}' no fue encontrado en '{ruta_llamador}'.")
        except Exception as e:
            print(f"Ocurrió un error al leer el archivo: {e}")
        return None
"""

SECURITY_PY = "# Helpers de hash y JWT\n"

SQL_EXAMPLE = tw.dedent("""
    -- 00_init.sql
    CREATE SCHEMA IF NOT EXISTS users;
    CREATE TABLE IF NOT EXISTS users.customer (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );
""").lstrip()

CONFIG_FILE = ".stack_config.json"

# ─────────── utilidades ──────────────────────────────────────────
def host_label(name: str) -> str:
    """
    Normaliza un nombre a etiqueta de host DNS válida:
    - minúsculas
    - '_' y espacios → '-'
    - elimina caracteres no [a-z0-9-]
    - quita guiones al inicio/fin
    """
    s = name.lower().replace('_', '-',).replace(' ', '-')
    s = re.sub(r'[^a-z0-9-]+', '-', s).strip('-')
    return s or 'app'

def ask_int(msg: str) -> int:
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("  Número inválido.")

def ask_bool(msg: str) -> bool:
    return input(f"{msg} (y/n) ").lower().startswith("y")

def ask_choice(msg: str, options: List[str]) -> str:
    opts = "/".join(options)
    while True:
        v = input(f"{msg} [{opts}]: ").strip().lower()
        if v in options:
            return v
        print("  Opción inválida.")

def mk(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def wr(path: Path, txt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt, encoding="utf-8")

def wrexec(path: Path, txt: str) -> None:
    wr(path, txt)
    os.chmod(path, 0o755)

def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None

def write_json(path: Path, data: Dict[str, Any]) -> None:
    wr(path, json.dumps(data, indent=2, ensure_ascii=False))

# ─────────── helpers de node ────────────────────────────────────
def run_in_node_container(workdir: Path, command: str) -> None:
    subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{workdir.resolve()}:/app",
        "-w", "/app",
        "node:20-alpine",
        "sh", "-c", command
    ], check=True)

def init_vue(app_dir: Path) -> None:
    print("\nCreando proyecto Vue en", app_dir)
    # Intentos en orden: npx create-vue, npm init, instalar global y ejecutar
    commands = [
        "npx --yes create-vue@latest .",
        "npm init vue@latest -y",
        "npm i -g create-vue@latest && create-vue . -- --yes"
    ]
    run_node(app_dir, commands)
    # Instalar dependencias tras generar
    run_node(app_dir, ["npm install"])

def init_nuxt(app_dir: Path) -> None:
    print("\nCreando proyecto Nuxt en", app_dir)
    commands = [
        "npx --yes nuxi@latest init .",
        "npm i -g nuxi@latest && nuxi init ."
    ]
    run_node(app_dir, commands)
    run_node(app_dir, ["npm install"])


# ─────────── generadores ────────────────────────────────────────
def make_env_files(front_base: Path, kind: str, *, project: str, domain: str, backs: List[str]) -> None:
    """
    Genera .env y .env_prod en la raíz del front-end (NO dentro de /app)
    y elimina los antiguos si estaban en app/.  En PROD:
    - backs normales -> https://api.<back>.<dominio>
    - socket        -> https://api.socket.<proyecto>.<dominio>
    """
    prefix = "VITE_" if kind == "vue" else "NUXT_PUBLIC_"

    # Limpieza previa (por si el scaffolder los creó dentro de app/)
    for p in (front_base / "app" / ".env", front_base / "app" / ".env_prod"):
        if p.exists():
            p.unlink()

    # Dev: apunta a puertos locales de los backs (8000+i)
    lines_dev = [f"{prefix}API_{n.upper()}_URL=http://localhost:{8000 + i}" for i, n in enumerate(backs)]
    (front_base / ".env").write_text("\n".join(lines_dev) + "\n", encoding="utf-8")

    # Prod: dominios
    prod_lines = []
    for n in backs:
        if n == "socket":
            prod_lines.append(f"{prefix}API_{n.upper()}_URL=https://api.socket.{host_label(project)}.{domain}")
        else:
            prod_lines.append(f"{prefix}API_{n.upper()}_URL=https://api.{host_label(n)}.{domain}")
    (front_base / ".env_prod").write_text("\n".join(prod_lines) + "\n", encoding="utf-8")

def create_backend(root: Path, name: str, *, is_socket: bool = False) -> None:
    base = root / "backend" / name
    mk(base / "app" / "core")
    mk(base / "app" / "models")
    mk(base / "app" / "routes")
    mk(base / "app" / "schemas")

    wr(base / "app/core/base.py", BASE_PY)
    wr(base / "app/core/config.py", CONFIG_PY)
    wr(base / "app/core/database.py", DATABASE_PY)
    wr(base / "app/core/security.py", SECURITY_PY)

    if is_socket:
        # WebSocket básico con FastAPI
        wr(
            base / "app/main.py",
            tw.dedent("""
            from fastapi import FastAPI, WebSocket, WebSocketDisconnect
            from typing import List

            app = FastAPI(title="socket")

            class ConnectionManager:
                def __init__(self):
                    self.active: List[WebSocket] = []

                async def connect(self, websocket: WebSocket):
                    await websocket.accept()
                    self.active.append(websocket)

                def disconnect(self, websocket: WebSocket):
                    if websocket in self.active:
                        self.active.remove(websocket)

                async def broadcast(self, message: str):
                    for ws in list(self.active):
                        try:
                            await ws.send_text(message)
                        except Exception:
                            self.disconnect(ws)

            manager = ConnectionManager()

            @app.get("/")
            def hi():
                return {"msg": "socket"}

            @app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                await manager.connect(websocket)
                try:
                    while True:
                        data = await websocket.receive_text()
                        await manager.broadcast(f"echo: {data}")
                except WebSocketDisconnect:
                    manager.disconnect(websocket)
            """).strip() + "\n",
        )
    else:
        wr(
            base / "app/main.py",
            f"from fastapi import FastAPI\napp=FastAPI(title='{name}')\n\n@app.get('/')\n"
            f"def hi():\n    return {{'msg':'{name}'}}\n",
        )

    wr(base / ".env", DOTENV_BACK)
    wr(base / ".dockerignore", DOCKERIGNORE)
    wr(base / ".gitignore", GITIGNORE_PY)
    wr(
        base / "requirements.txt",
        "fastapi\nuvicorn\npsycopg2-binary\npython-jose\npasslib[bcrypt]\npython-dotenv\nredis\n",
    )
    wr(base / "Dockerfile", DOCKERFILE_BACK)

def create_frontend(root: Path, name: str, kind: str, project: str, domain: str, backs: List[str]) -> None:
    """
    1) Crea carpeta base y 'app' vacía
    2) Ejecuta scaffolding (Vue o Nuxt) DENTRO de 'app' con el directorio vacío
    3) Recién entonces crea Dockerfile, nginx (si Vue), ignores y .envs
    """
    base = root / "frontend" / name
    app_dir = base / "app"

    # Asegura carpeta y deja app VACÍA (evita prompt "Target directory is not empty")
    if app_dir.exists():
        if any(app_dir.iterdir()):
            print(f"⚠️  {app_dir} tenía archivos. Eliminando para scaffolding limpio...")
            shutil.rmtree(app_dir)
    mk(app_dir)

    # 1) Scaffolding primero
    if kind == "vue":
        init_vue(app_dir)
    else:
        init_nuxt(app_dir)

    # 2) Archivos extra
    wr(base / ".dockerignore", DOCKERIGNORE)
    wr(base / ".gitignore", GITIGNORE_NODE)
    if kind == "vue":
        wr(base / "Dockerfile", DOCKERFILE_VUE)
        mk(base / "nginx")
        wr(base / "nginx/default.conf", VUE_NGINX_CONF)
    else:
        wr(base / "Dockerfile", DOCKERFILE_NUXT)

    # 3) Variables de entorno para front (dev/prod)
    make_env_files(base, kind, project=project, domain=domain, backs=backs)

def ensure_db_assets(root: Path, db_user: str = "postgres", db_name: str = "mydb") -> None:
    """Crea ./db con .env, init SQL y pgadmin preset (si aplica)."""
    db_base = root / "db"
    mk(db_base / "init")
    mk(db_base / "pgadmin")
    # .env compartido
    env_path = db_base / ".env"
    if not env_path.exists():
        wr(env_path, DB_DOTENV)
    # SQL de ejemplo (idempotente) para Postgres
    init_sql = db_base / "init/00_init.sql"
    if not init_sql.exists():
        wr(init_sql, SQL_EXAMPLE)
    # pgAdmin servers.json preconfigurado
    servers_json = db_base / "pgadmin" / "servers.json"
    if not servers_json.exists():
        wr(servers_json, PGADMIN_SERVERS_JSON(db_user, db_name))

def render_dev_compose(project: str,
                       backs: List[str],
                       fronts: List[Tuple[str, str]],
                       *,
                       use_pg: bool,
                       use_mongo: bool,
                       use_redis: bool) -> str:
    """
    DEV: sin proxy Nginx. Cada servicio expone puerto único en localhost.
    - Backends: host 8000 + i -> contenedor 80
    - Fronts Vue: host 5173, 5174, ... -> contenedor 5173
    - Fronts Nuxt: host 3000, 3001, ... -> contenedor 3000
    - Mongo: host 27017 -> contenedor 27017 (para Compass)
    """
    dev = ["version: '3.9'\nservices:"]
    defined_vols: List[str] = []

    # postgres
    if use_pg:
        dev += [
            "  postgres:",
            "    image: postgres:16-alpine",
            f"    container_name: {project}_postgres_dev",
            "    env_file: ./db/.env",
            "    environment:",
            "      - TZ=America/Bogota",
            "    volumes:",
            "      - ./db/init:/docker-entrypoint-initdb.d:ro",
            "      - pg_data:/var/lib/postgresql/data",
            "    ports:",
            "      - '5432:5432'",
            "    restart: unless-stopped",
            "",
            "  pgadmin:",
            "    image: dpage/pgadmin4:8.10",
            f"    container_name: {project}_pgadmin_dev",
            "    env_file: ./db/.env",
            "    environment:",
            "      - PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION=True",
            "      - PGADMIN_CONFIG_LOGIN_BANNER='\"Bienvenido a pgAdmin\"'",
            "    volumes:",
            "      - pgadmin_data:/var/lib/pgadmin",
            "      - ./db/pgadmin/servers.json:/pgadmin4/servers.json:ro",
            "    ports:",
            "      - '5050:80'",
            "    depends_on: [postgres]",
            "    restart: unless-stopped",
            "",
        ]
        defined_vols += ["pg_data", "pgadmin_data"]

    # mongo (sin mongo-express)
    if use_mongo:
        dev += [
            "  mongo:",
            "    image: mongo:7",
            f"    container_name: {project}_mongo_dev",
            "    env_file: ./db/.env",
            "    volumes:",
            "      - mongo_data:/data/db",
            "    ports:",
            "      - '27017:27017'",
            "    restart: unless-stopped",
            "",
        ]
        defined_vols.append("mongo_data")

    # redis
    if use_redis:
        dev += [
            "  redis:",
            "    image: redis:7-alpine",
            f"    container_name: {project}_redis_dev",
            "    env_file: ./db/.env",
            "    command: ['redis-server','--appendonly','yes','--requirepass','${REDIS_PASSWORD}']",
            "    volumes:",
            "      - redis_data:/data",
            "    ports:",
            "      - '6379:6379'",
            "    restart: unless-stopped",
            "",
        ]
        defined_vols.append("redis_data")

    # backs
    for i, name in enumerate(backs):
        svc = f"api_{name}"
        depends = []
        if use_pg: depends.append("postgres")
        if use_mongo: depends.append("mongo")
        if use_redis: depends.append("redis")
        dep_line = f"    depends_on: [{', '.join(depends)}]" if depends else None

        container_name = f"{project}_{svc}_dev"

        dev += [
            f"  {svc}:",
            f"    build: {{ context: ./backend/{name}, target: dev }}",
            f"    container_name: {container_name}",
            f"    env_file: ./backend/{name}/.env",
            f"    volumes:",
            f"      - ./backend/{name}/app:/code",
            f"    environment:",
            f"      CHOKIDAR_USEPOLLING: \"true\"",
        ]
        if dep_line: dev += [dep_line]
        dev += [
            f"    ports:",
            f"      - '{8000 + i}:80'",
            "    restart: unless-stopped",
            "",
        ]

    # fronts (puertos únicos por tipo)
    front_ports = {"vue": 5173, "nuxt": 3000}
    for name, kind in fronts:
        svc = f"front_{name}"
        cont_port = "5173" if kind == "vue" else "3000"
        host_port = front_ports[kind]
        front_ports[kind] += 1  # siguiente disponible
        vol = f"{svc}_node_modules"
        defined_vols.append(vol)

        dev += [
            f"  {svc}:",
            f"    build: {{ context: ./frontend/{name}, target: dev }}",
            f"    container_name: {project}_{svc}_dev",
            f"    volumes:",
            f"      - ./frontend/{name}/app:/app",
            f"      - {vol}:/app/node_modules",
            f"    environment:",
            f"      CHOKIDAR_USEPOLLING: \"true\"",
            f"    env_file: ./frontend/{name}/.env",
            f"    command: npm run dev -- --host 0.0.0.0",
            f"    ports:",
            f"      - '{host_port}:{cont_port}'",
            "    restart: unless-stopped",
            "",
        ]

    # Volúmenes (solo si hay)
    if defined_vols:
        dev.append("volumes:")
        for v in sorted(set(defined_vols)):
            dev.append(f"  {v}:")
        dev.append("")  # newline final

    return "\n".join(dev)

def render_prod_compose(
    project: str,
    domain: str,
    email: str,
    use_staging: bool,
    backs: List[str],
    fronts: List[Tuple[str, str]],
    *,
    use_pg: bool,
    use_mongo: bool,
    use_redis: bool
) -> Tuple[str, List[str]]:
    prod = ["version: '3.9'\nservices:"]
    deps_list = []
    defined_vols: List[str] = []

    # postgres / pgadmin (opcionales)
    if use_pg:
        prod += [
            "  postgres:",
            "    image: postgres:16-alpine",
            f"    container_name: {project}_postgres",
            "    env_file: ./db/.env",
            "    environment:",
            "      - TZ=America/Bogota",
            "    volumes:",
            "      - ./db/init:/docker-entrypoint-initdb.d:ro",
            "      - pg_data:/var/lib/postgresql/data",
            "    restart: unless-stopped",
            "",
            "  pgadmin:",
            "    image: dpage/pgadmin4:8.10",
            f"    container_name: {project}_pgadmin",
            "    env_file: ./db/.env",
            "    environment:",
            "      - PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION=True",
            "      - PGADMIN_CONFIG_LOGIN_BANNER='\"Bienvenido a pgAdmin\"'",
            "    volumes:",
            "      - pgadmin_data:/var/lib/pgadmin",
            "      - ./db/pgadmin/servers.json:/pgadmin4/servers.json:ro",
            "    depends_on: [postgres]",
            "    restart: unless-stopped",
            "",
        ]
        deps_list += ["postgres", "pgadmin"]
        defined_vols += ["pg_data", "pgadmin_data"]

    # mongo (opcional, sin mongo-express en prod)
    if use_mongo:
        prod += [
            "  mongo:",
            "    image: mongo:7",
            f"    container_name: {project}_mongo",
            "    env_file: ./db/.env",
            "    volumes:",
            "      - mongo_data:/data/db",
            "    restart: unless-stopped",
            "",
        ]
        deps_list += ["mongo"]
        defined_vols.append("mongo_data")

    # redis (opcional)
    if use_redis:
        prod += [
            "  redis:",
            "    image: redis:7-alpine",
            f"    container_name: {project}_redis",
            "    env_file: ./db/.env",
            "    command: ['redis-server','--appendonly','yes','--requirepass','${REDIS_PASSWORD}']",
            "    volumes:",
            "      - redis_data:/data",
            "    restart: unless-stopped",
            "",
        ]
        deps_list.append("redis")
        defined_vols.append("redis_data")

    # backs
    for name in backs:
        svc = f"api_{name}"
        container_name = f"{project}_{svc}"

        prod += [
            f"  {svc}:",
            f"    build: {{ context: ./backend/{name}, target: prod }}",
            f"    container_name: {container_name}",
            f"    env_file: ./backend/{name}/.env",
        ]
        depends = []
        if use_pg: depends.append("postgres")
        if use_mongo: depends.append("mongo")
        if use_redis: depends.append("redis")
        if depends:
            prod += [f"    depends_on: [{', '.join(depends)}]"]
        # sockets: single worker en prod
        if name == "socket":
            prod += [
                "    command: [\"gunicorn\",\"-k\",\"uvicorn.workers.UvicornWorker\",\"-w\",\"1\",\"-t\",\"1\",\"-b\",\"0.0.0.0:80\",\"main:app\"]"
            ]
        prod += [
            f"    restart: unless-stopped",
            "",
        ]
        deps_list.append(svc)

    # fronts
    for name, _ in fronts:
        svc = f"front_{name}"
        prod += [
            f"  {svc}:",
            f"    build: {{ context: ./frontend/{name}, target: prod }}",
            f"    container_name: {project}_{svc}",
            f"    env_file: ./frontend/{name}/.env_prod",
            f"    restart: unless-stopped",
            "",
        ]
        deps_list.append(svc)

    # Dominios a certificar (incluye api.socket.<proyecto>.<dominio>)
    unique_hosts = sorted({
        *(f"{host_label(n)}.{domain}" for n, _ in fronts),
        *(f"www.{host_label(n)}.{domain}" for n, _ in fronts),
        *( [f"api.socket.{host_label(project)}.{domain}"] ),
        *(f"api.{host_label(n)}.{domain}" for n in backs if n != 'socket'),
        *( [f"pgadmin.{domain}"] if use_pg else [] ),
    })

    hosts_space = " ".join(unique_hosts)
    staging_flag = "--staging" if use_staging else ""
    deps_yaml = ", ".join(deps_list)

    # Proxy + Certbot
    prod += [
        "  proxy:",
        "    build: { context: ./nginx }",
        f"    container_name: {project}_proxy",
        "    ports: [ '80:80', '443:443' ]",
        "    volumes:",
        "      - ./nginx/conf.d:/etc/nginx/conf.d:rw",
        "      - ./nginx/proxy_params.conf:/etc/nginx/proxy_params.conf:ro",
        "      - ./nginx/certbot/www:/var/www/certbot:ro",
        "      - ./nginx/letsencrypt:/etc/letsencrypt:ro",
        f"    depends_on: [{deps_yaml}]" if deps_list else "    depends_on: []",
        "    restart: unless-stopped",
        "",
        "  certbot:",
        "    image: certbot/certbot:latest",
        f"    container_name: {project}_certbot",
        "    volumes:",
        "      - ./nginx/certbot/www:/var/www/certbot",
        "      - ./nginx/letsencrypt:/etc/letsencrypt",
        "    depends_on: [proxy]",
        "    entrypoint: sh",
        f"    command: -c \"if [ -n '{hosts_space}' ]; then for d in {hosts_space}; do certbot certonly -n --keep-until-expiring --webroot -w /var/www/certbot -d $$d --email \\\"{email}\\\" --agree-tos --no-eff-email {staging_flag}; done; fi; trap exit TERM; while :; do certbot renew -n --webroot -w /var/www/certbot --quiet || true; sleep 12h; done\"",
        "    restart: unless-stopped",
        "",
    ]

    if defined_vols:
        prod += ["volumes:"]
        for v in sorted(set(defined_vols)):
            prod += [f"  {v}:"]
        prod.append("")

    return "\n".join(prod), unique_hosts

def write_prod_nginx(root: Path,
                     project: str,
                     domain: str,
                     backs: List[str],
                     fronts: List[Tuple[str, str]],
                     *,
                     use_pg: bool,
                     use_mongo: bool) -> List[str]:
    mk(root / "nginx/certbot/www")
    mk(root / "nginx/letsencrypt")
    mk(root / "nginx/conf.d")

    wr(root / "nginx/conf.d/ssl_params.conf", SSL_PARAMS)
    wr(root / "nginx/proxy_params.conf", PROXY_PARAMS)

    servers_http: List[str] = []
    servers_https: List[str] = []

    # fronts https + redirecciones www
    for name, kind in fronts:
        basehost = f"{host_label(name)}.{domain}"
        upstream = f"front_{name}"
        port = "80" if kind == "vue" else "3000"

        # HTTP 80 (no-www y www→no-www)
        servers_http.append(SERVER_HTTP.format(host=basehost))
        servers_http.append(SERVER_HTTP_WWW_REDIRECT.format(host=basehost))

        # HTTPS 443 (no-www proxy + www→no-www con su cert)
        servers_https.append(SERVER_HTTPS.format(host=basehost, upstream=upstream, port=port))
        servers_https.append(SERVER_HTTPS_WWW_REDIRECT.format(host=basehost))

    # backs https (solo no-www)
    for name in backs:
        if name == "socket":
            host = f"api.socket.{host_label(project)}.{domain}"
        else:
            host = f"api.{host_label(name)}.{domain}"
        upstream = f"api_{name}"
        port = "80"
        servers_http.append(SERVER_HTTP.format(host=host))
        servers_https.append(SERVER_HTTPS.format(host=host, upstream=upstream, port=port))

    # pgadmin https (solo no-www si Postgres)
    if use_pg:
        host_pg = f"pgadmin.{domain}"
        servers_http.append(SERVER_HTTP.format(host=host_pg))
        servers_https.append(SERVER_HTTPS.format(host=host_pg, upstream="pgadmin", port="80"))

    wr(root / "nginx/conf.d/reverse-proxy.http.conf", "".join(servers_http))
    wr(root / "nginx/conf.d/reverse-proxy.https.conf.disabled", "".join(servers_https))

    # Dockerfile y entrypoint para proxy (auto-enable https)
    wr(root / "nginx/Dockerfile", DOCKERFILE_PROXY)
    unique_hosts = sorted({
        *(f"{host_label(n)}.{domain}" for n, _ in fronts),
        *(f"www.{host_label(n)}.{domain}" for n, _ in fronts),
        *( [f"api.socket.{host_label(project)}.{domain}"] ),
        *(f"api.{host_label(n)}.{domain}" for n in backs if n != "socket"),
        *( [f"pgadmin.{domain}"] if use_pg else [] ),
    })
    first_host = unique_hosts[0] if unique_hosts else ""
    entrypoint_script = f"""#!/bin/sh
set -eu
(
  TARGET="/etc/nginx/conf.d/reverse-proxy.https.conf"
  DISABLED="/etc/nginx/conf.d/reverse-proxy.https.conf.disabled"
  FIRST_DOMAIN="{first_host}"
  if [ -n "$FIRST_DOMAIN" ]; then
    while [ ! -f "/etc/letsencrypt/live/$FIRST_DOMAIN/fullchain.pem" ]; do
      sleep 5
    done
    if [ -f "$DISABLED" ]; then
      cp "$DISABLED" "$TARGET"
    fi
    nginx -t && nginx -s reload || true
    while :; do
      sleep 21600
      nginx -s reload || true
    done
  fi
) &
"""
    mk(root / "nginx/docker-entrypoint.d")
    wrexec(root / "nginx/docker-entrypoint.d/50-enable-https.sh", entrypoint_script)
    return unique_hosts

# ─────────── helpers de configuración ────────────────────────────
def to_front_list(cfg_fronts: List[Dict[str, str]]) -> List[Tuple[str, str]]:
    return [(f["name"], f["kind"]) for f in cfg_fronts]

def create_needed_envs_for_front(root: Path, name: str, kind: str, project: str, domain: str, backs: List[str]) -> None:
    base = root / "frontend" / name
    if base.exists():
        make_env_files(base, kind, project=project, domain=domain, backs=backs)

def sanitize_services(existing: List[str], remove_list: List[str]) -> List[str]:
    existing_set = set(existing)
    for r in remove_list:
        existing_set.discard(r)
    return sorted(existing_set)

def rename_backend(root: Path, backs: List[str], old: str, new: str) -> List[str]:
    """Renombra carpeta backend/<old> → backend/<new> y actualiza lista."""
    src = root / "backend" / old
    dst = root / "backend" / new
    if not src.exists():
        print(f"  ⚠️  Backend '{old}' no existe.")
        return backs
    if dst.exists():
        print(f"  ⚠️  Ya existe backend '{new}'.")
        return backs
    src.rename(dst)
    # opcional: actualizar mensaje de main.py si existe
    main_py = dst / "app" / "main.py"
    if main_py.exists():
        try:
            txt = main_py.read_text(encoding="utf-8")
            txt = re.sub(r"return\\s+\\{\\s*'msg'\\s*:\\s*'[^']*'\\s*\\}", f"return {{'msg':'{new}'}}", txt)
            main_py.write_text(txt, encoding="utf-8")
        except Exception:
            pass
    return [new if b == old else b for b in backs]

def rename_frontend(root: Path, fronts: List[Tuple[str, str]], old: str, new: str) -> List[Tuple[str, str]]:
    """Renombra carpeta frontend/<old> → frontend/<new> y actualiza lista."""
    src = root / "frontend" / old
    dst = root / "frontend" / new
    if not src.exists():
        print(f"  ⚠️  Frontend '{old}' no existe.")
        return fronts
    if dst.exists():
        print(f"  ⚠️  Ya existe frontend '{new}'.")
        return fronts
    src.rename(dst)
    return [(new, k) if n == old else (n, k) for (n, k) in fronts]

# ─────────── flujo principal ────────────────────────────────────
def main():
    mode = ask_choice("¿Qué deseas hacer?", ["nuevo", "agregar", "editar"])

    if mode == "nuevo":
        project = input("Nombre del proyecto: ").strip()
        domain = input("\nDominio base para producción (ej. midominio.com): ").strip()
        le_email = input("Email para Let's Encrypt: ").strip()
        use_staging = ask_bool("¿Usar entorno de pruebas (staging) de Let's Encrypt? (recomendado en pruebas)")
        # DBs
        use_pg = ask_bool("¿Incluir Postgres + pgAdmin?")
        use_mongo = ask_bool("¿Incluir MongoDB (conexión por Compass)?")
        use_redis = ask_bool("¿Incluir Redis (persistente AOF)?")

        n_back = ask_int("¿Cuántos back-end adicionales? (0..n) [además de 'socket' obligatorio]: ")
        backs = [input(f"  Nombre back #{i+1}: ").strip() for i in range(n_back)]
        # agrega siempre 'socket'
        if "socket" not in backs:
            backs.append("socket")

        n_front = ask_int("¿Cuántos front-end? (0..n): ")
        fronts: List[Tuple[str, str]] = []
        for i in range(n_front):
            n = input(f"  Nombre front #{i+1}: ").strip()
            t = ""
            while t not in ("vue", "nuxt"):
                t = input("    Tipo (vue/nuxt): ").strip().lower()
            fronts.append((n, t))

        root = Path.cwd() / project
        mk(root)

        cfg = {
            "project": project,
            "domain": domain,
            "email": le_email,
            "staging": bool(use_staging),
            "use_pg": bool(use_pg),
            "use_mongo": bool(use_mongo),
            "use_redis": bool(use_redis),
            "backs": backs,
            "fronts": [{"name": n, "kind": k} for n, k in fronts],
        }
        write_json(root / CONFIG_FILE, cfg)
        cfg_out = None  # para que el código de abajo use cfg

    elif mode == "agregar":
        project_dir = input("Ruta de la carpeta del proyecto existente: ").strip()
        root = Path(project_dir).resolve()
        cfg_path = root / CONFIG_FILE
        cfg = read_json(cfg_path)
        if not cfg:
            print("\n⚠️  No se encontró .stack_config.json; voy a pedir datos básicos.")
            project = root.name
            domain = input("Dominio base para producción (ej. midominio.com): ").strip()
            le_email = input("Email para Let's Encrypt: ").strip()
            use_staging = ask_bool("¿Usar entorno de pruebas (staging) de Let's Encrypt? ")
            # flags DB
            use_pg = ask_bool("¿Incluir Postgres + pgAdmin?")
            use_mongo = ask_bool("¿Incluir MongoDB (conexión por Compass)?")
            use_redis = ask_bool("¿Incluir Redis (persistente AOF)?")
            backs = sorted([p.name for p in (root / "backend").glob("*") if p.is_dir()])
            if "socket" not in backs: backs.append("socket")
            fronts: List[Tuple[str, str]] = []
            for p in (root / "frontend").glob("*"):
                if not p.is_dir():
                    continue
                kind = "vue" if (p / "nginx" / "default.conf").exists() else "nuxt"
                fronts.append((p.name, kind))
            cfg = {
                "project": project,
                "domain": domain,
                "email": le_email,
                "staging": bool(use_staging),
                "use_pg": bool(use_pg),
                "use_mongo": bool(use_mongo),
                "use_redis": bool(use_redis),
                "backs": backs,
                "fronts": [{"name": n, "kind": k} for n, k in fronts],
            }
        else:
            project = cfg["project"]
            domain = cfg["domain"]
            le_email = cfg["email"]
            use_staging = bool(cfg.get("staging", False))
            # backcompat
            if "use_pg" not in cfg and "use_db" in cfg:
                cfg["use_pg"] = bool(cfg["use_db"])
            if "use_mongo" not in cfg:
                cfg["use_mongo"] = False
            if "use_redis" not in cfg:
                cfg["use_redis"] = False

            backs = list(cfg.get("backs", []))
            if "socket" not in backs: backs.append("socket")
            fronts = [(f["name"], f["kind"]) for f in cfg.get("fronts", [])]

        print("\n¿Qué quieres agregar?")
        add_back = ask_bool("¿Agregar nuevos back-end?")
        if add_back:
            nb = ask_int("  ¿Cuántos backs nuevos?: ")
            for i in range(nb):
                n = input(f"    Nombre back nuevo #{i+1}: ").strip()
                if n and n not in backs:
                    backs.append(n)
        if "socket" not in backs:
            backs.append("socket")

        add_front = ask_bool("¿Agregar nuevos front-end?")
        if add_front:
            nf = ask_int("  ¿Cuántos fronts nuevos?: ")
            for i in range(nf):
                n = input(f"    Nombre front nuevo #{i+1}: ").strip()
                t = ""
                while t not in ("vue", "nuxt"):
                    t = input("      Tipo (vue/nuxt): ").strip().lower()
                if n and all(n != f[0] for f in fronts):
                    fronts.append((n, t))

        # Permite activar/desactivar DBs
        if ask_bool("¿Cambiar flags de bases de datos?"):
            cfg["use_pg"] = ask_bool("  ¿Usar Postgres + pgAdmin?")
            cfg["use_mongo"] = ask_bool("  ¿Usar MongoDB (para Compass)?")
            cfg["use_redis"] = ask_bool("  ¿Usar Redis (persistente AOF)?")

        cfg_out = {
            "project": project,
            "domain": domain,
            "email": le_email,
            "staging": bool(use_staging),
            "use_pg": bool(cfg.get("use_pg", False)),
            "use_mongo": bool(cfg.get("use_mongo", False)),
            "use_redis": bool(cfg.get("use_redis", False)),
            "backs": sorted(backs),
            "fronts": [{"name": n, "kind": k} for n, k in sorted(fronts)],
        }
        write_json(root / CONFIG_FILE, cfg_out)

    else:  # editar
        project_dir = input("Ruta de la carpeta del proyecto existente: ").strip()
        root = Path(project_dir).resolve()
        cfg_path = root / CONFIG_FILE
        cfg = read_json(cfg_path)
        if not cfg:
            print("❌ No se encontró .stack_config.json en esa ruta.")
            return

        print(f"\nProyecto actual: {cfg['project']}")
        if ask_bool("¿Cambiar nombre del proyecto? (afecta nombres de contenedores, host de socket, etc.)"):
            new_project = input("  Nuevo nombre del proyecto: ").strip()
            if new_project:
                cfg["project"] = new_project
            else:
                print("  ⚠️ Nombre vacío, se mantiene el nombre anterior.")

        print(f"Dominio actual: {cfg['domain']}")
        if ask_bool("¿Cambiar dominio?"):
            cfg["domain"] = input("  Nuevo dominio base: ").strip()

        print(f"Email Let's Encrypt actual: {cfg['email']}")
        if ask_bool("¿Cambiar email de Let's Encrypt?"):
            cfg["email"] = input("  Nuevo email: ").strip()

        print(f"Staging actual: {bool(cfg.get('staging', False))}")
        if ask_bool("¿Cambiar flag de staging?"):
            cfg["staging"] = ask_bool("  ¿Usar staging de Let's Encrypt?")

        # backcompat
        if "use_pg" not in cfg and "use_db" in cfg:
            cfg["use_pg"] = bool(cfg["use_db"])
        if "use_mongo" not in cfg:
            cfg["use_mongo"] = False
        if "use_redis" not in cfg:
            cfg["use_redis"] = False

        print(f"Postgres+pgAdmin actual: {bool(cfg.get('use_pg', False))}")
        if ask_bool("¿Cambiar uso de Postgres+pgAdmin?"):
            cfg["use_pg"] = ask_bool("  ¿Incluir Postgres + pgAdmin?")

        print(f"MongoDB (Compass) actual: {bool(cfg.get('use_mongo', False))}")
        if ask_bool("¿Cambiar uso de MongoDB?"):
            cfg["use_mongo"] = ask_bool("  ¿Incluir MongoDB (para Compass)?")

        print(f"Redis (persistente) actual: {bool(cfg.get('use_redis', False))}")
        if ask_bool("¿Cambiar uso de Redis?"):
            cfg["use_redis"] = ask_bool("  ¿Incluir Redis (AOF)?")

        backs = list(cfg.get("backs", []))
        if "socket" not in backs:
            backs.append("socket")
        fronts = [(f["name"], f["kind"]) for f in cfg.get("fronts", [])]

        # Quitar servicios
        if ask_bool("¿Quitar back-ends existentes? (socket no se debe quitar)"):
            print("Backs actuales:", ", ".join(backs) or "-")
            to_remove = input("  Nombres a quitar (coma), vacío = ninguno: ").strip()
            if to_remove:
                remove_names = [s.strip() for s in to_remove.split(",")]
                if "socket" in remove_names:
                    print("  ⚠️  'socket' es obligatorio; se ignorará su eliminación.")
                    remove_names = [n for n in remove_names if n != "socket"]
                backs = sanitize_services(backs, remove_names)

        if ask_bool("¿Quitar front-ends existentes?"):
            print("Fronts actuales:", ", ".join([f"{n}({k})" for n, k in fronts]) or "-")
            to_remove = input("  Nombres a quitar (coma), vacío = ninguno: ").strip()
            if to_remove:
                remove_names = [s.strip() for s in to_remove.split(",")]
                fronts = [(n,k) for (n,k) in fronts if n not in remove_names]

        # Agregar servicios
        if ask_bool("¿Agregar nuevos back-end?"):
            nb = ask_int("  ¿Cuántos backs nuevos?: ")
            for i in range(nb):
                n = input(f"    Nombre back nuevo #{i+1}: ").strip()
                if n and n not in backs:
                    backs.append(n)

        if ask_bool("¿Agregar nuevos front-end?"):
            nf = ask_int("  ¿Cuántos fronts nuevos?: ")
            for i in range(nf):
                n = input(f"    Nombre front nuevo #{i+1}: ").strip()
                t = ""
                while t not in ("vue", "nuxt"):
                    t = input("      Tipo (vue/nuxt): ").strip().lower()
                if n and all(n != f[0] for f in fronts):
                    fronts.append((n, t))

        # RENOMBRAR servicios
        while ask_bool("¿Renombrar un back-end? (no 'socket')"):
            print("Backs:", ", ".join(backs) or "-")
            old = input("  Nombre actual: ").strip()
            if old not in backs:
                print("  ⚠️  No existe ese back.")
                continue
            if old == "socket":
                print("  ⚠️  'socket' es obligatorio y no se debe renombrar.")
                continue
            new = input("  Nuevo nombre: ").strip()
            if not new or new in backs:
                print("  ⚠️  Nuevo nombre vacío o ya existe.")
                continue
            backs = rename_backend(root, backs, old, new)
            print(f"  ✔ Renombrado backend: {old} → {new}")

        while ask_bool("¿Renombrar un front-end?"):
            print("Fronts:", ", ".join([n for n,_ in fronts]) or "-")
            old = input("  Nombre actual: ").strip()
            if all(n != old for n,_ in fronts):
                print("  ⚠️  No existe ese front.")
                continue
            new = input("  Nuevo nombre: ").strip()
            if not new or any(n == new for n,_ in fronts):
                print("  ⚠️  Nuevo nombre vacío o ya existe.")
                continue
            fronts = rename_frontend(root, fronts, old, new)
            print(f"  ✔ Renombrado frontend: {old} → {new}")

        cfg["backs"] = sorted(backs)
        cfg["fronts"] = [{"name": n, "kind": k} for n, k in sorted(fronts)]
        write_json(cfg_path, cfg)
        cfg_out = cfg

    # Estructura base
    if not (root / "backend").exists():
        mk(root / "backend")
    if not (root / "frontend").exists():
        mk(root / "frontend")

    # Crear assets DB compartidos (independiente de flags, para credenciales por defecto)
    ensure_db_assets(root)

    # Lista de backs final
    backs_iter = (cfg_out["backs"] if 'cfg_out' in locals() and cfg_out else cfg["backs"])
    # Garantizar 'socket'
    if "socket" not in backs_iter:
        backs_iter = backs_iter + ["socket"]

    # Crear backs nuevos
    for n in backs_iter:
        base = root / "backend" / n
        if not base.exists():
            print(f"Creando backend {n} ...")
            create_backend(root, n, is_socket=(n == "socket"))

    # Crear/actualizar fronts
    fr_list = [(f["name"], f["kind"]) for f in (cfg_out["fronts"] if 'cfg_out' in locals() and cfg_out else cfg["fronts"])]
    project_val = (cfg_out["project"] if 'cfg_out' in locals() and cfg_out else cfg["project"])
    domain_val = (cfg_out["domain"] if 'cfg_out' in locals() and cfg_out else cfg["domain"])
    for n, k in fr_list:
        base = root / "frontend" / n
        if not base.exists():
            print(f"Creando frontend {n} ({k}) ...")
            create_frontend(root, n, k, project_val, domain_val, backs_iter)
        else:
            create_needed_envs_for_front(root, n, k, project_val, domain_val, backs_iter)

    # SOLO PROD: Nginx y certificados
    mk(root / "nginx")
    use_pg_flag = bool((cfg_out["use_pg"] if 'cfg_out' in locals() and cfg_out else cfg.get("use_pg", False)))
    use_mongo_flag = bool((cfg_out["use_mongo"] if 'cfg_out' in locals() and cfg_out else cfg.get("use_mongo", False)))
    use_redis_flag = bool((cfg_out["use_redis"] if 'cfg_out' in locals() and cfg_out else cfg.get("use_redis", False)))

    unique_hosts_for_print = write_prod_nginx(
        root,
        project_val,
        domain_val,
        backs_iter,
        fr_list,
        use_pg=use_pg_flag,
        use_mongo=use_mongo_flag
    )

    # Compose dev (sin proxy)
    dev_yaml = render_dev_compose(
        project_val,
        backs_iter,
        fr_list,
        use_pg=use_pg_flag,
        use_mongo=use_mongo_flag,
        use_redis=use_redis_flag
    )
    wr(root / "docker-compose.yml", dev_yaml)

    # Compose prod
    prod_yaml, _hosts = render_prod_compose(
        project_val,
        domain_val,
        (cfg_out["email"] if 'cfg_out' in locals() and cfg_out else cfg["email"]),
        bool(cfg_out["staging"] if 'cfg_out' in locals() and cfg_out else cfg["staging"]),
        backs_iter,
        fr_list,
        use_pg=use_pg_flag,
        use_mongo=use_mongo_flag,
        use_redis=use_redis_flag
    )
    wr(root / "compose.prod.yml", prod_yaml)

    # .gitignore de raíz
    root_gitignore = root / ".gitignore"
    if not root_gitignore.exists():
        lines = [
            "db/pgadmin/*",
            "!db/pgadmin/servers.json",
            "nginx/letsencrypt/*",
            "node_modules/",
            "__pycache__/",
            ".venv/",
            ".env",
        ]
        wr(root_gitignore, "\n".join(lines) + "\n")

    print(f"\n✅  Proyecto '{project_val}' listo en {root}\n")
    print("Modo desarrollo:")
    print(f"  cd {root} && docker compose up -d")
    print("  Accesos dev (sin Nginx):")
    # fronts: puertos incrementales por tipo
    vue_port = 5173
    nuxt_port = 3000
    for n, k in fr_list:
        if k == "vue":
            print(f"    {n:>12s}: http://localhost:{vue_port}  (Vue)")
            vue_port += 1
        else:
            print(f"    {n:>12s}: http://localhost:{nuxt_port}  (Nuxt)")
            nuxt_port += 1
    # backs: 8000+i
    for i, n in enumerate(backs_iter):
        print(f"    api_{n:>8s}: http://localhost:{8000 + i}")
    if use_pg_flag:
        print("    pgAdmin:         http://localhost:5050")
    if use_mongo_flag:
        print("    Mongo (Compass): mongodb://admin:admin@localhost:27017/?authSource=admin")
    if use_redis_flag:
        print("    Redis:           localhost:6379 (AOF activado; pass en ./db/.env REDIS_PASSWORD)")

    print("\nProducción (SSL automático con Let's Encrypt):")
    print("  1) Apunta los DNS de cada host a tu servidor:")
    for h in unique_hosts_for_print:
        print("     -", h)
    print("  2) Levanta producción:")
    print("       docker compose -f compose.prod.yml up -d")
    print("  (Proxy arranca en HTTP; Certbot emite/renueva en segundo plano;")
    print("   el proxy habilita HTTPS y recarga Nginx automáticamente.)")
    print("  Nota sockets: 'api.socket.<dominio>' usa 1 worker en prod para compatibilidad WebSocket.")
    if use_mongo_flag:
        print("  Mongo en PROD: no se expone por puerto. Usa SSH/VPN para conectar Compass de forma segura.")

if __name__ == "__main__": 
    main()
