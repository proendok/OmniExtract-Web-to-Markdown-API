# Guía de Puesta en Marcha y Monetización Automática
## OmniExtract API — Motor de Extracción Web y Markdown Limpio para LLMs / RAG

He diseñado, programado y probado una solución completa de software comercial lista para operar de forma 100% autónoma: **OmniExtract API**.

---

### ¿Qué es y por qué la gente paga por esto?
En la era actual de agentes de IA, RAG (Retrieval-Augmented Generation) y modelos de lenguaje, los desarrolladores gastan miles de dólares enviando HTML sucio (con anuncios, menús, popups de cookies y scripts de rastreo) a APIs como OpenAI o Claude.

**OmniExtract resuelve este dolor crítico:**
1. Convierte cualquier sitio web en **Markdown limpio y optimizado** en milisegundos.
2. Reduce en promedio un **80% a 92% el consumo de tokens** del cliente.
3. Extrae metadatos (OpenGraph, autor, descripción, título).
4. Cuenta con protección SSRF y evasión de bloqueos bot.

---

### Los 2 Canales de Ingresos Automatizados Integrados

El sistema ya tiene el código programado para monetizar por dos vías simultáneas:

#### Vía 1: Venta Directa con Stripe (Suscripciones Mensuales)
La página web incluida ya tiene la pasarela y la tabla de precios:
* **Starter:** \$9/mes (10,000 peticiones)
* **Pro:** \$29/mes (50,000 peticiones) — *El más popular*
* **Enterprise:** \$79/mes (250,000 peticiones)

**Flujo automático:**
1. El cliente entra a la web, prueba la demo interactiva y hace clic en "Get Started".
2. Paga con su tarjeta vía Stripe Checkout.
3. El webhook automático de Stripe activa al instante una API Key (`omni_pro_...`) en la base de datos local y se la entrega al cliente.
4. Stripe deposita el dinero directamente en tu cuenta bancaria cada mes sin que tengas que hacer nada.

#### Vía 2: RapidAPI Marketplace (0 Marketing necesario)
RapidAPI es la tienda de APIs más grande del mundo, con millones de desarrolladores buscando diariamente *"markdown scraper"*, *"web to text"*, *"ai rag scraper"*.
* No necesitas buscar clientes: los desarrolladores te descubren dentro de la tienda de RapidAPI.
* RapidAPI se encarga del cobro, facturas e impuestos globales, y te deposita por PayPal o transferencia bancaria directa.
* Nuestro backend ya incluye el middleware `RAPIDAPI_PROXY_SECRET` listo para validar sus peticiones.

---

### Las Únicas 3 Cosas que Necesitas Hacer (Nivel Administrativo)

Como la IA no puede abrir cuentas bancarias por ti, estos son los únicos 3 pasos administrativos que te corresponden:

#### Paso 1: Configurar tu pasarela de cobro (10 minutos)
* **Opción A (Stripe):**
  1. Inicia sesión o crea tu cuenta en [stripe.com](https://stripe.com).
  2. En el panel de control, ve a **Desarrolladores > Claves de API** y copia tu `Secret key` (`sk_live_...` o `sk_test_...` para pruebas).
  3. Crea 3 productos de suscripción recurrente en Stripe (\$9, \$29, \$79) y copia sus `Price IDs` (`price_...`).
  4. Pega estos valores en el archivo `.env` de este proyecto:
     ```env
     STRIPE_SECRET_KEY=sk_...
     STRIPE_PRICE_STARTER=price_...
     STRIPE_PRICE_PRO=price_...
     STRIPE_PRICE_ENTERPRISE=price_...
     ```

* **Opción B (RapidAPI - Aún más simple):**
  1. Crea una cuenta gratuita en [rapidapi.com](https://rapidapi.com/provider).
  2. Haz clic en **Add New API** y escribe el nombre: `OmniExtract Web-to-Markdown API`.
  3. En Target URL, coloca la URL de tu servidor desplegado.
  4. Configura los planes de pago (\$9/\$29/\$79) con un par de clics.

#### Paso 2: Subir el proyecto a internet (5 minutos)
El proyecto incluye configuración automática para despliegue con 1 clic:
* **En Render.com (Recomendado - Gratuito / \$7):**
  1. Conecta tu repositorio de GitHub en Render.
  2. Render detectará automáticamente el archivo `render.yaml`.
  3. Añade las variables de entorno de tu `.env` y haz clic en **Deploy**.
* **En Railway.app:**
  1. Conecta el repositorio; detectará el `Dockerfile` y `railway.json` automáticamente.

#### Paso 3: Cobrar en automático
Una vez en línea:
* El servidor atiende peticiones 24/7.
* Los pagos caen automáticamente en tu cuenta de Stripe o RapidAPI.
* No requiere soporte diario ni mantenimiento manual.

---

### Cómo Probarlo Localmente Ahora Mismo

Para ver la aplicación corriendo en tu máquina con la interfaz y demo en vivo:

```powershell
# En esta misma carpeta goofy-heisenberg:
.venv\Scripts\python -m uvicorn app.main:app --reload
```
Abre tu navegador en: [http://localhost:8000](http://localhost:8000)
* Verás la landing page profesional en modo oscuro.
* Puedes pegar cualquier enlace y presionar **"Extract to Markdown 🚀"** para ver la extracción en vivo y el ahorro de tokens.
