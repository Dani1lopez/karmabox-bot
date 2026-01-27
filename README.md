# 📦 KarmaBox Bot

> **Backend FastAPI para captación de leads con integración a Google Sheets, bot Telegram y UI web de gestión.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Integration-34A853?logo=google-sheets&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)

---

## 📋 Resumen

**KarmaBox** es un proyecto de prueba técnica que implementa un sistema de captación y gestión de leads mediante:

- **API REST** (FastAPI) con endpoints para crear, listar y actualizar leads
- **Persistencia en Google Sheets** como base de datos (sin necesidad de servidor de BD)
- **Bot conversacional Telegram** con flujo guiado para registrar leads paso a paso
- **IA opcional (Groq)** para responder preguntas cuando el usuario no está en flujo de registro
- **UI web** para visualizar, filtrar, buscar y editar leads
- **Webhook WhatsApp** (preparado pero bloqueado por limitaciones de Meta)

---

## ✨ Features

| Feature              | Estado        | Descripción                                            |
| -------------------- | ------------- | ------------------------------------------------------ |
| ✅ API REST `/leads` | **Funcional** | CRUD de leads con validación de teléfono ES            |
| ✅ Google Sheets     | **Funcional** | Almacenamiento persistente vía Service Account         |
| ✅ Bot Telegram      | **Funcional** | Flujo conversacional completo para registro            |
| ✅ UI Web            | **Funcional** | Dashboard para ver/editar leads                        |
| ⚠️ IA Groq           | **Opcional**  | Respuestas inteligentes si se configura `GROQ_API_KEY` |
| ❌ WhatsApp          | **Bloqueado** | Rate limiting de Meta (cuenta nueva/sandbox)           |

---

## 🏗️ Arquitectura

```
                    ┌─────────────────┐
                    │   Telegram Bot  │
                    │   (Webhook)     │
                    └────────┬────────┘
                             │
                             ▼
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐
│   UI Web    │────▶│    FastAPI App    │────▶│  Google Sheets  │
│  (browser)  │     │   main.py / bot/  │     │  (gspread)      │
└─────────────┘     └───────────────────┘     └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Groq AI (opt.) │
                    └─────────────────┘
```

### Estructura de Carpetas

```
karmabox-bot/
├── main.py                    # Punto de entrada FastAPI
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Exclusiones (secrets, venv, .env)
├── sheets_test.py             # Script de prueba para Google Sheets
├── secrets/                   # ⚠️ DIRECTORIO LOCAL, NO VERSIONADO
│   └── service_account.json   # (debes crearlo tú, NO existe en el repo)
└── bot/
    ├── __init__.py
    ├── app.py                 # Configuración app (placeholder)
    ├── routers/
    │   ├── __init__.py
    │   ├── leads.py           # Endpoints: /health, /leads (GET/POST/PATCH)
    │   ├── telegram_webhook.py    # POST /webhook/telegram
    │   └── whatsapp_webhook.py    # GET/POST /webhook/whatsapp
    ├── schemas/
    │   ├── __init__.py
    │   └── lead.py            # Pydantic models: LeadCreate, LeadOut, LeadUpdate
    ├── services/
    │   ├── __init__.py
    │   ├── sheets_service.py  # Conexión gspread + CRUD
    │   ├── conversation_flow.py   # Máquina de estados del bot
    │   └── ai_client.py       # Cliente Groq para IA opcional
    ├── utils/
    │   ├── __init__.py
    │   ├── phone.py           # Validación teléfono España (9 dígitos)
    │   └── lead_mapper.py     # Normalización de registros
    └── ui/
        ├── index.html         # Dashboard HTML
        └── assets/
            ├── css/app.css
            └── js/app.js      # Lógica frontend (fetch API)
```

---

## 📌 Requisitos

- **Python 3.10+**
- **pip** (gestor de paquetes)
- **Cuenta Google** con acceso a Google Cloud Console
- **Bot Telegram** creado con [@BotFather](https://t.me/BotFather)
- **(Opcional)** API Key de [Groq](https://groq.com/) para IA
- **(Opcional)** Túnel HTTPS público (ngrok o similar) para webhooks

### Dependencias principales (instaladas vía pip)

| Paquete         | Uso                                         |
| --------------- | ------------------------------------------- |
| `fastapi`       | Framework web                               |
| `uvicorn`       | Servidor ASGI                               |
| `gspread`       | Cliente Google Sheets                       |
| `httpx`         | Cliente HTTP async (Telegram/Groq/WhatsApp) |
| `python-dotenv` | Carga de `.env`                             |
| `pydantic`      | Validación de datos                         |

---

## 🔧 Setup Google Sheets

### 1. Crear proyecto en Google Cloud Console

1. Ve a [console.cloud.google.com](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google Sheets API** y **Google Drive API**

### 2. Crear Service Account

1. Ve a **APIs & Services → Credentials**
2. Click **Create Credentials → Service Account**
3. Ponle un nombre (ej: `karmabox-sheets`)
4. Click **Done** (no necesitas roles adicionales para Sheets)
5. Entra en el Service Account creado → **Keys → Add Key → Create new key → JSON**
6. Descarga el archivo y **renómbralo** a `service_account.json`
7. Colócalo en `secrets/service_account.json`

### 3. Crear el Google Sheet

1. Ve a [sheets.google.com](https://sheets.google.com/)
2. Crea un nuevo spreadsheet llamado exactamente: **`KarmaBox Leads`**
3. En la primera fila (headers), escribe **exactamente** estas columnas:

| A   | B          | C    | D         | E     | F       |
| --- | ---------- | ---- | --------- | ----- | ------- |
| id  | created_at | name | last_name | phone | address |

4. **Importante**: Comparte el Sheet con el email del Service Account:
   - Abre el JSON, busca el campo `"client_email"`
   - Copia ese email (ej: `karmabox-sheets@proyecto.iam.gserviceaccount.com`)
   - En el Sheet, click **Compartir** → pega el email → **Editor** → **Enviar**

---

## 🔐 Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```bash
# Copia el ejemplo
cp .env.example .env
```

### Variables requeridas

| Variable                      | Descripción                      | Ejemplo                                          |
| ----------------------------- | -------------------------------- | ------------------------------------------------ |
| `TELEGRAM_BOT_TOKEN`          | Token del bot de @BotFather      | `7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Ruta al JSON del Service Account | `secrets/service_account.json`                   |
| `SHEET_NAME`                  | Nombre exacto del Google Sheet   | `KarmaBox Leads`                                 |

### Variables opcionales

| Variable                   | Descripción                      | Por defecto               |
| -------------------------- | -------------------------------- | ------------------------- |
| `GROQ_API_KEY`             | API Key de Groq para IA          | (vacío = IA desactivada)  |
| `AI_MODEL`                 | Modelo Groq a usar               | `llama-3.3-70b-versatile` |
| `API_BASE_URL`             | URL pública (para webhooks)      | —                         |
| `WHATSAPP_VERIFY_TOKEN`    | Token de verificación webhook WA | —                         |
| `WHATSAPP_ACCESS_TOKEN`    | Token Cloud API de Meta          | —                         |
| `WHATSAPP_PHONE_NUMBER_ID` | Phone Number ID de Meta          | —                         |
| `WHATSAPP_WABA_ID`         | WhatsApp Business Account ID     | —                         |
| `WHATSAPP_APP_SECRET`      | App Secret para validar firma    | —                         |

---

## 🚀 Instalación y Ejecución Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/karmabox-bot.git
cd karmabox-bot
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o en Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install fastapi uvicorn gspread httpx python-dotenv pydantic
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores reales
```

### 5. Colocar credenciales Google

```bash
# Coloca tu service_account.json en:
secrets/service_account.json
```

### 6. Ejecutar el servidor

```bash
uvicorn main:app --reload --port 8000
```

La API estará disponible en `http://localhost:8000`

---

## 📡 Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**

```json
{ "status": "ok" }
```

### Listar Leads

```bash
curl http://localhost:8000/leads
```

**Response:**

```json
[
  {
    "id": "abc123-...",
    "created_at": "2025-01-27T10:30:00+00:00",
    "name": "Juan",
    "last_name": "García",
    "phone": "654789012",
    "address": "Calle Mayor 123, Madrid"
  }
]
```

### Crear Lead

```bash
curl -X POST http://localhost:8000/leads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "María",
    "last_name": "López",
    "phone": "687654321",
    "address": "Av. Principal 45, Barcelona"
  }'
```

**Response (201):**

```json
{
  "id": "uuid-generado",
  "created_at": "2025-01-27T12:00:00+00:00",
  "name": "María",
  "last_name": "López",
  "phone": "687654321",
  "address": "Av. Principal 45, Barcelona"
}
```

**Errores posibles:**

- `409 Conflict`: Ya existe un lead con ese teléfono
- `422 Unprocessable Entity`: Teléfono inválido (debe ser 9 dígitos de España)

### Actualizar Lead (PATCH)

```bash
curl -X PATCH http://localhost:8000/leads/uuid-del-lead \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Nueva dirección 789"
  }'
```

**Response (200):**

```json
{
  "id": "uuid-del-lead",
  "created_at": "...",
  "name": "María",
  "last_name": "López",
  "phone": "687654321",
  "address": "Nueva dirección 789"
}
```

**Errores posibles:**

- `400 Bad Request`: No hay campos para actualizar
- `404 Not Found`: Lead no encontrado
- `409 Conflict`: El nuevo teléfono ya existe en otro lead

---

## 🖥️ UI Web

> **⚠️ ADVERTENCIA DE SEGURIDAD:**
>
> **LA UI NO TIENE AUTENTICACIÓN.** Cualquier persona con acceso a la URL puede ver y editar leads.
>
> **NO EXPONER PÚBLICAMENTE SIN PROTECCIÓN** (proxy con auth, VPN, o implementar login).

La interfaz web está servida automáticamente en:

```
http://localhost:8000/ui/
```

> **Nota:** La raíz `/` redirige automáticamente a `/ui/`

### Funcionalidades

- **Listado de leads** con paginación (10/20/50 por página)
- **Búsqueda** por nombre, apellidos, teléfono, dirección o ID
- **Ordenación** por fecha (recientes/antiguos) o nombre (A-Z/Z-A)
- **Panel de detalle** al seleccionar un lead
- **Edición modal** con validación y feedback de errores
- **Copia de ID** al portapapeles
- **Estado de sincronización** visual (dot verde/rojo)

### Flujo de creación de leads

> **Importante:** La UI es para **visualizar y editar** leads existentes, no para crearlos.
>
> Los leads se crean a través del **bot de Telegram** o vía **API REST**.

---

## 🤖 Telegram Bot

### Cómo funciona

1. El usuario inicia conversación con `/start`
2. El bot guía paso a paso: nombre → apellidos → teléfono → dirección
3. El usuario confirma con "sí" o "no"
4. Si confirma, el lead se guarda en Google Sheets
5. Fuera del flujo de registro, el bot responde con IA (si está configurada)

### Configurar Webhook

1. Exponer tu servidor localmente con ngrok:

   ```bash
   ngrok http 8000
   ```

2. Registrar el webhook con Telegram:

   ```bash
   curl "https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=https://xxxx.ngrok.io/webhook/telegram"
   ```

3. Verificar webhook:
   ```bash
   curl "https://api.telegram.org/bot<TU_TOKEN>/getWebhookInfo"
   ```

### Comandos disponibles

| Comando       | Descripción                           |
| ------------- | ------------------------------------- |
| `/start`      | Inicia el formulario de registro      |
| `/cancel`     | Cancela el flujo actual               |
| (texto libre) | Respuesta IA si Groq está configurado |

---

## 🧠 IA con Groq (Opcional)

El bot utiliza la API de Groq para responder preguntas cuando el usuario no está en flujo de registro.

### Activar IA

1. Crea cuenta en [console.groq.com](https://console.groq.com/)
2. Genera una API Key
3. Añade a tu `.env`:
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
   AI_MODEL=llama-3.3-70b-versatile
   ```

### Comportamiento

- **Con `GROQ_API_KEY`**: Responde preguntas sobre KarmaBox, horarios, servicios, etc.
- **Sin `GROQ_API_KEY`**: Responde "Ahora mismo no tengo IA configurada"

### Modelo por defecto

`llama-3.3-70b-versatile` — puede cambiarse vía variable `AI_MODEL`

---

## 📱 WhatsApp (Estado: Bloqueado)

### ¿Qué está implementado?

- **Router completo** en `bot/routers/whatsapp_webhook.py`
- **Verificación de webhook** (GET) para Meta
- **Recepción de mensajes** (POST) con validación de firma
- **Envío de respuestas** via Cloud API v19.0
- **Integración** con el mismo flujo conversacional que Telegram

### ¿Por qué no funciona?

> **⚠️ Bloqueo por Meta:**
>
> Las cuentas nuevas de WhatsApp Business están sujetas a **rate limiting** severo durante el periodo sandbox. Meta requiere:
>
> - Verificación del negocio
> - Template de mensajes aprobados para iniciar conversaciones
> - Periodo de "calentamiento" de la cuenta
>
> Hasta no superar estas restricciones, los mensajes enviados pueden ser rechazados o demorados indefinidamente.

### ¿Qué faltaría para completar?

1. **Verificar negocio** en Meta Business Manager
2. **Aprobar templates** de mensajes
3. **Configurar variables**:
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_WABA_ID`
4. **Probar** con número de teléfono verificado en sandbox

---

## ☁️ Despliegue GRATIS

### Opción 1: Render.com (Recomendado)

#### Pasos

1. Sube tu código a GitHub (sin secrets)
2. Ve a [render.com](https://render.com/) → New → Web Service
3. Conecta tu repo
4. Configura:
   - **Build Command**: `pip install fastapi uvicorn gspread httpx python-dotenv pydantic`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Gestión del `service_account.json`

**Secret File (Render) — método recomendado:**

1. En Render → Environment → Secret Files
2. Añade archivo con path `/etc/secrets/service_account.json`
3. Configura la variable de entorno:
   ```
   GOOGLE_SERVICE_ACCOUNT_FILE=/etc/secrets/service_account.json
   ```

> **Nota:** Esta es la forma más limpia ya que el proyecto ya soporta la variable `GOOGLE_SERVICE_ACCOUNT_FILE`.

### Opción 2: Railway.app

Similar a Render:

1. Conecta repo
2. Railway detecta Python automáticamente
3. Configura variables de entorno en dashboard
4. Usa secret files para `service_account.json`

### Opción 3: Fly.io

```bash
fly launch
fly secrets set TELEGRAM_BOT_TOKEN=xxx
fly secrets set GOOGLE_SERVICE_ACCOUNT_JSON="$(base64 secrets/service_account.json)"
fly deploy
```

### Webhook después del despliegue

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://tu-app.render.com/webhook/telegram"
```

---

## 🔒 Seguridad y Buenas Prácticas

### ✅ Implementado

- `.gitignore` excluye:
  - `.env` y variantes
  - `secrets/` (excepto `.gitkeep` si existe)
  - `**/service_account*.json`
  - `venv/`, `__pycache__/`
- Validación de teléfono español (9 dígitos, empieza por 6/7/8/9)
- Detección de duplicados por teléfono
- Escape HTML en frontend para prevenir XSS
- Validación opcional de firma HMAC en webhook WhatsApp

### ⚠️ IMPORTANTE: UI sin autenticación

> **La interfaz web (`/ui/`) no tiene sistema de login.**
>
> Si despliegas este proyecto en un servidor público, **cualquier persona podrá ver y modificar leads**.
>
> **Antes de exponer públicamente**, implementa una de estas protecciones:
>
> - Proxy reverso con autenticación (nginx + htpasswd)
> - Acceso solo via VPN
> - Implementar sistema de login en la aplicación

### 📋 Recomendaciones adicionales

- [ ] **Añadir autenticación a la UI (CRÍTICO si se despliega público)**
- [ ] Implementar rate limiting en endpoints
- [ ] Usar HTTPS en producción
- [ ] Logging estructurado con niveles
- [ ] Añadir tests unitarios e integración

---

## 🐛 Troubleshooting

### Error: "No such file or directory: 'secrets/service_account.json'"

**Causa:** El archivo de credenciales no existe o la ruta es incorrecta.

**Solución:**

```bash
mkdir -p secrets
# Coloca tu service_account.json ahí
ls -la secrets/
```

### Error: "SpreadsheetNotFound"

**Causa:** El nombre del Sheet no coincide exactamente o no está compartido.

**Solución:**

1. Verifica que el Sheet se llame exactamente `KarmaBox Leads`
2. Comparte el Sheet con el `client_email` del Service Account

### Error: "Ya existe un lead con ese teléfono" (409)

**Causa:** Teléfono duplicado en la base de datos.

**Solución:** Usa un teléfono diferente o actualiza el lead existente via PATCH.

### Error: "Teléfono inválido" (422)

**Causa:** El teléfono no cumple validación española.

**Requisitos:**

- 9 dígitos exactos
- Empezar por 6, 7, 8 o 9
- Sin espacios ni guiones

### Telegram no responde

**Verificar:**

```bash
# Comprobar webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Debe mostrar tu URL y pending_update_count
```

### IA no responde / "falta GROQ_API_KEY"

**Causa:** Variable no configurada o API Key inválida.

**Solución:** Verifica `GROQ_API_KEY` en `.env` y que sea válida en console.groq.com

---

## 🗺️ Roadmap / Próximos Pasos

Basado en el estado actual del repositorio:

### Corto plazo

- [ ] Crear `requirements.txt` o `pyproject.toml` para dependencias
- [ ] Añadir endpoint DELETE para eliminar leads
- [ ] Implementar autenticación básica en UI
- [ ] Añadir logs estructurados

### Medio plazo

- [ ] Completar integración WhatsApp (cuando Meta lo permita)
- [ ] Añadir tests con pytest
- [ ] Dockerizar la aplicación
- [ ] CI/CD con GitHub Actions

### Largo plazo

- [ ] Migrar a base de datos real (PostgreSQL)
- [ ] Dashboard de analíticas
- [ ] Exportación CSV de leads
- [ ] Webhooks salientes para integraciones

---

## 📄 Licencia

Proyecto desarrollado como prueba técnica. Consultar con el autor para uso comercial.

---

## 👥 Autor

Desarrollado por **[Daniel Alcaraz López]** como parte de proceso de selección.

- GitHub: [@Dani1lopez](https://github.com/Dani1lopez)
- LinkedIn: [Dani Alcaraz López](www.linkedin.com/in/dani-alcaraz-lópez-774aa8251)
