# 📦 KarmaBox Bot

> **Sistema de captación de leads multicanal con FastAPI, Google Sheets, bots Telegram/WhatsApp y UI de gestión.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-Integration-34A853?logo=google-sheets&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram&logoColor=white)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Cloud%20API-25D366?logo=whatsapp&logoColor=white)

---

## 📋 Descripción del Proyecto

**KarmaBox Bot** es una prueba técnica que implementa un sistema completo de captación y gestión de leads mediante múltiples canales:

### Requisitos de la Prueba

- **API REST** con validación y deduplicación
- **Persistencia sin servidor de BD** (Google Sheets como backend)
- **Bot conversacional** con flujo guiado paso a paso
- **Soporte multicanal**: Telegram y WhatsApp Cloud API
- **UI web** para visualización y edición de leads
- **IA opcional** para respuestas fuera del flujo de registro

### ¿Qué hace el proyecto?

| Componente        | Funcionalidad                                                             |
| ----------------- | ------------------------------------------------------------------------- |
| **API REST**      | CRUD de leads con validación teléfono ES, deduplicación (409 Conflict)    |
| **Google Sheets** | Almacenamiento persistente via Service Account                            |
| **Bot Telegram**  | Webhook con flujo conversacional: `/start`, `/cancel`, confirmación       |
| **Bot WhatsApp**  | Webhook verificado, recibe/responde mensajes, idempotencia por message_id |
| **UI Web**        | Listado, búsqueda, filtro por source, ordenación, paginación, edición     |
| **IA Groq**       | Respuestas inteligentes fuera del flujo de registro (opcional)            |

---

## 🏗️ Arquitectura

```
                    ┌─────────────────┐     ┌─────────────────┐
                    │   Telegram Bot  │     │  WhatsApp Bot   │
                    │   (Webhook)     │     │  (Cloud API)    │
                    └────────┬────────┘     └────────┬────────┘
                             │                       │
                             └───────────┬───────────┘
                                         ▼
┌─────────────┐              ┌───────────────────┐              ┌─────────────────┐
│   UI Web    │─────────────▶│    FastAPI App    │─────────────▶│  Google Sheets  │
│  (/ui/)     │              │   main.py / bot/  │              │  (gspread)      │
└─────────────┘              └───────────────────┘              └─────────────────┘
                                         │
                                         ▼
                             ┌─────────────────┐
                             │  Groq AI (opt.) │
                             └─────────────────┘
```

### Estructura de Carpetas

```
karmabox-bot/
├── main.py                    # Punto de entrada FastAPI (monta /ui/, redirige / → /ui/)
├── requirements.txt           # Dependencias del proyecto
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Exclusiones (secrets, venv, .env)
├── secrets/                   # ⚠️ LOCAL, NO VERSIONADO
│   └── service_account.json   # Credenciales Google (crear manualmente)
└── bot/
    ├── routers/
    │   ├── leads.py               # GET /health, POST /leads, GET /leads, PATCH /leads/{id}
    │   ├── telegram_webhook.py    # POST /webhook/telegram
    │   └── whatsapp_webhook.py    # GET/POST /webhook/whatsapp
    ├── schemas/
    │   └── lead.py                # LeadCreate, LeadOut, LeadUpdate (Pydantic)
    ├── services/
    │   ├── sheets_service.py      # CRUD Google Sheets + idempotencia WhatsApp
    │   ├── conversation_flow.py   # Máquina de estados del bot
    │   └── ai_client.py           # Cliente Groq para IA
    ├── utils/
    │   ├── phone.py               # Validación teléfono España
    │   └── lead_mapper.py         # Normalización de datos
    └── ui/
        ├── index.html             # Dashboard HTML
        └── assets/
            ├── css/app.css
            └── js/app.js          # Lógica frontend (fetch API)
```

---

## 📡 Endpoints

| Método  | Ruta                | Descripción                                   | Códigos                   |
| ------- | ------------------- | --------------------------------------------- | ------------------------- |
| `GET`   | `/health`           | Health check                                  | 200                       |
| `POST`  | `/leads`            | Crear lead (con validación y deduplicación)   | 201, 409 (duplicado), 422 |
| `GET`   | `/leads`            | Listar todos los leads                        | 200                       |
| `PATCH` | `/leads/{lead_id}`  | Actualizar lead parcialmente                  | 200, 400, 404, 409        |
| `POST`  | `/webhook/telegram` | Webhook Telegram                              | 200                       |
| `GET`   | `/webhook/whatsapp` | Verificación webhook WhatsApp (hub.challenge) | 200, 403                  |
| `POST`  | `/webhook/whatsapp` | Recepción mensajes WhatsApp                   | 200                       |

### Schemas Pydantic

**LeadCreate** (POST):

```json
{
  "name": "string",
  "last_name": "string",
  "phone": "string", // 9 dígitos ES, empieza 6/7/8/9
  "address": "string",
  "source": "string" // opcional: "telegram" | "whatsapp"
}
```

**LeadOut** (respuesta):

```json
{
  "id": "uuid",
  "created_at": "ISO8601",
  "name": "string",
  "last_name": "string",
  "phone": "string",
  "address": "string",
  "source": "string"
}
```

**LeadUpdate** (PATCH):

```json
{
  "name": "string", // opcional
  "last_name": "string", // opcional
  "phone": "string", // opcional (validación si viene)
  "address": "string" // opcional
}
```

---

## 🚀 Setup Local Paso a Paso

### 1. Clonar y crear entorno virtual

```bash
git clone https://github.com/tu-usuario/karmabox-bot.git
cd karmabox-bot
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# Windows: venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores reales
```

### 4. Ejecutar servidor

```bash
uvicorn main:app --reload --port 8000
```

### 5. Verificar funcionamiento

```bash
curl http://localhost:8000/health
# Respuesta: {"status":"ok"}
```

La UI está disponible en: `http://localhost:8000/ui/` (la raíz `/` redirige automáticamente)

---

## 📊 Google Sheets Setup

### 1. Crear Spreadsheet

1. Ve a [sheets.google.com](https://sheets.google.com/)
2. Crea un nuevo spreadsheet llamado **exactamente**: `KarmaBox Leads`
3. En la primera fila, escribe estos headers **EXACTAMENTE** (orden y nombre):

| A   | B          | C    | D         | E     | F       | G      |
| --- | ---------- | ---- | --------- | ----- | ------- | ------ |
| id  | created_at | name | last_name | phone | address | source |

### 2. Crear Service Account

1. Ve a [console.cloud.google.com](https://console.cloud.google.com/)
2. Crea o selecciona un proyecto
3. Habilita **Google Sheets API** y **Google Drive API**
4. Ve a **APIs & Services → Credentials**
5. Click **Create Credentials → Service Account**
6. Nombre: `karmabox-sheets` (o cualquiera)
7. Click **Done**
8. Entra al Service Account → **Keys → Add Key → Create new key → JSON**
9. Descarga el archivo y renómbralo a `service_account.json`
10. Colócalo en `secrets/service_account.json`

### 3. Compartir Sheet con Service Account

1. Abre el JSON descargado
2. Copia el valor de `"client_email"` (ej: `karmabox@proyecto.iam.gserviceaccount.com`)
3. En Google Sheets, click **Compartir**
4. Pega el email → selecciona **Editor** → **Enviar**

---

## 🤖 Telegram Bot

### Configuración

1. Crea un bot con [@BotFather](https://t.me/BotFather) y obtén el token
2. Añade `TELEGRAM_BOT_TOKEN` a tu `.env`

### Exponer webhook con ngrok

```bash
ngrok http 8000
# Copia la URL HTTPS (ej: https://xxxx.ngrok-free.app)
```

### Registrar webhook

```bash
curl "https://api.telegram.org/bot<TU_TOKEN>/setWebhook?url=https://xxxx.ngrok-free.app/webhook/telegram"
```

### Verificar webhook

```bash
curl "https://api.telegram.org/bot<TU_TOKEN>/getWebhookInfo"
```

### Comandos disponibles

| Comando   | Acción                                                 |
| --------- | ------------------------------------------------------ |
| `/start`  | Inicia flujo de registro (también: "start", "empezar") |
| `/cancel` | Cancela flujo actual (también: "cancel")               |
| (texto)   | Fuera del flujo: respuesta IA (si configurada)         |

### Flujo de registro

1. Usuario envía `/start`
2. Bot pide: nombre → apellidos → teléfono → dirección
3. Bot muestra resumen y pide confirmación (sí/no)
4. Si "sí": guarda lead con `source=telegram`
5. Si "no": cancela y permite reiniciar

---

## 📱 WhatsApp Cloud API

### Configuración en Meta Developers

1. Crea una app en [developers.facebook.com](https://developers.facebook.com/)
2. Añade el producto **WhatsApp**
3. Configura el webhook con:
   - **Callback URL**: `https://tu-url-publica.com/webhook/whatsapp`
   - **Verify Token**: el valor de `WHATSAPP_VERIFY_TOKEN` en tu `.env`
4. **Suscríbete al campo `messages`** ← **CRÍTICO** para recibir mensajes

### Variables de entorno

```bash
WHATSAPP_VERIFY_TOKEN=tu_token_de_verificacion
WHATSAPP_ACCESS_TOKEN=tu_access_token_de_meta
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_GRAPH_VERSION=v19.0
```

### Verificación del webhook (GET)

Meta envía una petición GET con `hub.verify_token`. Si coincide con `WHATSAPP_VERIFY_TOKEN`, responde `hub.challenge`. Si no coincide, devuelve **403 Forbidden**.

### Idempotencia

Para evitar procesar mensajes duplicados, el sistema usa una worksheet/tab llamada `processed_messages` (configurable via `PROCESSED_MESSAGES_TAB`). Cada `message_id` procesado se guarda ahí y se ignoran duplicados.

### Probar envío/recepción

1. Desde WhatsApp, envía un mensaje al número de prueba de Meta
2. Verifica en logs que llega el POST a `/webhook/whatsapp`
3. El bot responde y marca el mensaje como leído

---

## 🖥️ UI Web

> **⚠️ ADVERTENCIA DE SEGURIDAD:**
>
> **LA UI NO TIENE AUTENTICACIÓN.** Cualquier persona con acceso a la URL puede ver y editar leads.
>
> **NO EXPONER PÚBLICAMENTE SIN PROTECCIÓN** (proxy con auth, VPN, o implementar login).

### Acceso

```
http://localhost:8000/ui/
```

### Funcionalidades

| Feature           | Descripción                                       |
| ----------------- | ------------------------------------------------- |
| Listado           | Muestra todos los leads con paginación (10/20/50) |
| Búsqueda          | Por nombre, apellidos, teléfono, dirección o ID   |
| Filtro por source | WhatsApp, Telegram o todos                        |
| Ordenación        | Por fecha (recientes/antiguos) o nombre (A-Z)     |
| Panel detalle     | Click en lead para ver info completa              |
| Modal edición     | Editar campos con validación y feedback           |
| Copiar ID         | Botón para copiar UUID al portapapeles            |

### Endpoints consumidos

- `GET /leads` — Listar leads
- `PATCH /leads/{id}` — Actualizar lead

> **Nota:** La UI es para **visualizar y editar**. Los leads se crean via **bots** o **API REST**.

---

## 🔐 Variables de Entorno (.env.example)

```bash
# =========================
# KarmaBox Bot - Variables
# =========================

# --- Telegram ---
# Token del bot creado con @BotFather
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- URL pública (para webhooks) ---
# Usar ngrok en desarrollo o URL de producción
API_BASE_URL=https://tu-app.ngrok-free.app

# --- Google Sheets ---
# Ruta al JSON del Service Account (NO subir a git)
GOOGLE_SERVICE_ACCOUNT_FILE=secrets/service_account.json

# Nombre exacto del Google Sheet
SHEET_NAME=KarmaBox Leads

# Tab para idempotencia WhatsApp (default: processed_messages)
PROCESSED_MESSAGES_TAB=processed_messages

# --- Groq IA (Opcional) ---
# Dejar vacío si no se usa
GROQ_API_KEY=
AI_MODEL=llama-3.3-70b-versatile

# --- WhatsApp Cloud API ---
# Token que TÚ defines para verificar el webhook
WHATSAPP_VERIFY_TOKEN=mi_token_seguro

# Token de acceso de Meta
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxx

# Phone Number ID de tu cuenta WhatsApp Business
WHATSAPP_PHONE_NUMBER_ID=123456789012345

# Versión de Graph API
WHATSAPP_GRAPH_VERSION=v19.0
```

---

## ☁️ Despliegue en Render

> El proyecto está desplegado en **Render.com** (tier gratuito).

### Pasos para desplegar

1. **Subir código a GitHub** (sin secrets ni `.env`)
2. Ve a [render.com](https://render.com/) → **New → Web Service**
3. Conecta tu repositorio de GitHub
4. Configura el servicio:

| Campo             | Valor                                          |
| ----------------- | ---------------------------------------------- |
| **Build Command** | `pip install -r requirements.txt`              |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

### Configurar variables de entorno

En Render → **Environment**, añade todas las variables de `.env.example` con sus valores reales.

### Gestión del `service_account.json`

**Método recomendado: Secret Files**

1. En Render → **Environment → Secret Files**
2. Añade un archivo con path: `/etc/secrets/service_account.json`
3. Pega el contenido del JSON
4. Configura la variable de entorno:
   ```
   GOOGLE_SERVICE_ACCOUNT_FILE=/etc/secrets/service_account.json
   ```

> El proyecto ya soporta esta variable, no requiere cambios en el código.

### Actualizar webhooks tras despliegue

**Telegram:**

```bash
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://tu-app.onrender.com/webhook/telegram"
```

**WhatsApp:**
Actualiza la Callback URL en Meta Developers con tu URL de Render.

---

## 🐛 Troubleshooting

### 403 Forbidden en verificación WhatsApp

**Causa**: El `hub.verify_token` enviado por Meta no coincide con `WHATSAPP_VERIFY_TOKEN`.

**Solución**:

1. Verifica que el token en Meta Developers sea **exactamente igual** al de `.env`
2. Reinicia el servidor después de cambiar `.env`

### No llegan mensajes WhatsApp (POST)

**Causa**: No estás suscrito al campo `messages` en el webhook de Meta.

**Solución**:

1. En Meta Developers → WhatsApp → Configuration
2. En **Webhook fields**, asegúrate de que `messages` esté **suscrito** (checkbox activo)

### ngrok offline / URL cambia

**Causa**: ngrok genera URLs temporales que cambian al reiniciar.

**Solución**:

```bash
# Cada vez que reinicies ngrok, actualiza el webhook:
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://NUEVA-URL.ngrok-free.app/webhook/telegram"
```

Para WhatsApp, actualiza la Callback URL en Meta Developers.

### SpreadsheetNotFound

**Causa**: El nombre del Sheet no coincide o no está compartido.

**Solución**:

1. Verifica que se llame exactamente `KarmaBox Leads`
2. Comparte el Sheet con el `client_email` del Service Account como **Editor**

### No such file: service_account.json

**Causa**: El archivo de credenciales no existe.

**Solución**:

```bash
mkdir -p secrets
# Coloca tu service_account.json descargado de Google Cloud
ls secrets/service_account.json
```

### 409 Conflict (teléfono duplicado)

**Causa**: Ya existe un lead con ese número de teléfono.

**Solución**: Usa un teléfono diferente o actualiza el lead existente via PATCH.

### 422 Unprocessable Entity (validación teléfono)

**Causa**: El teléfono no cumple la validación española.

**Requisitos**:

- 9 dígitos exactos (después de normalizar)
- Debe empezar por 6, 7, 8 o 9
- Se acepta prefijo +34 o 34 (se normaliza automáticamente)

### IA no responde

**Causa**: `GROQ_API_KEY` no configurada o inválida.

**Solución**:

1. Verifica que exista la variable en `.env`
2. Comprueba que la API Key sea válida en [console.groq.com](https://console.groq.com/)

---

## ✅ Checklist de Entrega

### Código y Configuración

- [ ] Repositorio limpio (sin secrets, sin `.env` real)
- [ ] `.gitignore` incluye: `.env`, `secrets/`, `venv/`, `__pycache__/`
- [ ] `requirements.txt` actualizado
- [ ] `.env.example` con todas las variables documentadas

### Google Sheets

- [ ] Spreadsheet creado con nombre exacto
- [ ] Headers correctos: `id`, `created_at`, `name`, `last_name`, `phone`, `address`, `source`
- [ ] Service Account creado y JSON descargado
- [ ] Sheet compartido con `client_email` como Editor

### Telegram Bot

- [ ] Bot creado con @BotFather
- [ ] Webhook configurado
- [ ] Flujo `/start` → registro → confirmación funciona
- [ ] Captura/video de demostración

### WhatsApp Bot

- [ ] App creada en Meta Developers
- [ ] Webhook verificado (GET responde hub.challenge)
- [ ] Suscripción a `messages` activa
- [ ] Recepción y respuesta de mensajes funciona
- [ ] Idempotencia verificada (mensajes duplicados ignorados)
- [ ] Captura/video de demostración

### UI Web

- [ ] Acceso via `/ui/` funciona
- [ ] Listado de leads correcto
- [ ] Filtro por source funciona
- [ ] Búsqueda funciona
- [ ] Edición via modal funciona
- [ ] Captura de demostración

### API REST

- [ ] `POST /leads` crea lead (201)
- [ ] `POST /leads` rechaza duplicado (409)
- [ ] `POST /leads` valida teléfono (422)
- [ ] `PATCH /leads/{id}` actualiza (200)
- [ ] `PATCH /leads/{id}` sin campos (400)
- [ ] `PATCH /leads/{id}` no existe (404)

### Demo

- [ ] README actualizado con instrucciones claras
- [ ] Capturas o video mostrando flujo completo
- [ ] Pruebas documentadas de cada endpoint

---

## 📄 Licencia

Proyecto desarrollado como prueba técnica. Consultar con el autor para uso comercial.

---

## 👤 Autor

Desarrollado por **Daniel Alcaraz López** como parte de proceso de selección.

- GitHub: [@Dani1lopez](https://github.com/Dani1lopez)
- LinkedIn: [Dani Alcaraz López](https://www.linkedin.com/in/dani-alcaraz-lópez-774aa8251)
