# IUSAI Backend

API para la gestión de documentos legales con extracción de texto y almacenamiento en la nube.

## 🚀 Características

- 📄 Manejo de documentos (PDF, DOC, DOCX, RTF)
- 🔍 Extracción de texto de documentos
- ☁️ Almacenamiento en Supabase
- 🗄️ Base de datos PostgreSQL con SQLAlchemy
- ⚡ API RESTful con FastAPI
- 🐍 Python 3.8+

## 🛠️ Requisitos Previos

- Python 3.8 o superior
- PostgreSQL con extensión pgvector
- Cuenta en Supabase (para almacenamiento de archivos)
- Git

### Instalación de pgvector

1. **En Ubuntu/Debian**:
   ```bash
   sudo apt-get install postgresql-contrib
   ```

2. **Habilitar la extensión en PostgreSQL**:
   Conéctate a tu base de datos PostgreSQL y ejecuta:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Verificar la instalación**:
   ```sql
   SELECT * FROM pg_available_extensions WHERE name = 'vector';
   ```

## 🚀 Instalación

1. Clona el repositorio:
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd lusai-backend/app
   ```

2. Crea y activa un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: .\venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno:
   Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/nombre_bd
   SUPABASE_URL=tu_url_supabase
   SUPABASE_KEY=tu_clave_supabase
   SUPABASE_BUCKET=nombre_bucket_supabase
   ```

## 🏃‍♂️ Ejecución en Desarrollo

1. Asegúrate de tener PostgreSQL en ejecución.

2. Crea la base de datos:
   ```bash
   createdb nombre_bd
   ```

3. Ejecuta las migraciones (si las hay):
   ```bash
   alembic upgrade head
   ```

4. Inicia el servidor de desarrollo:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   Donde:
   - `--host 0.0.0.0`: Hace que el servidor sea accesible desde cualquier dirección IP
   - `--port 8000`: Puerto donde se ejecutará el servidor
   - `--reload`: Recarga automáticamente el servidor cuando hay cambios en el código (solo para desarrollo)

5. La API estará disponible en:
   - URL: http://localhost:8000
   - Documentación interactiva: http://localhost:8000/docs
   - Documentación alternativa: http://localhost:8000/redoc

## 📚 Endpoints Principales

- `POST /api/files/upload_file` - Subir un nuevo documento
- `GET /api/files/documents` - Listar documentos (con paginación)
- `GET /api/files/{document_id}` - Obtener metadata de un documento
- `GET /api/files/{document_id}/text` - Obtener texto extraído

## 🧪 Ejecutando Tests

```bash
pytest
```

## 🏗️ Estructura del Proyecto

```
app/
├── api/                  # Configuración de la API
├── db/                   # Configuración de base de datos
├── models/               # Modelos de datos
├── routes/               # Rutas de la API
├── services/             # Lógica de negocio
├── utils/                # Utilidades
├── main.py               # Punto de entrada
└── requirements.txt      # Dependencias
```

## 📝 Variables de Entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | ✅ |
| `SUPABASE_URL` | URL de tu proyecto Supabase | ✅ |
| `SUPABASE_KEY` | Clave de API de Supabase | ✅ |
| `SUPABASE_BUCKET` | Nombre del bucket en Supabase Storage | ✅ |
| `OPENAI_API_KEY` | Clave de API de OpenAI | ✅ |

## 🤝 Contribución

1. Haz fork del proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Haz push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

[Incluir licencia si es necesario]

---

Desarrollado con ❤️ por Diego Belalcazar
