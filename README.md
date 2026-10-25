# ⚡ OmniExtract API

**High-Performance Web-to-Clean-Markdown & Structured Extraction API for LLMs, RAG, and Autonomous AI Agents.**

[![Tests](https://img.shields.io/badge/tests-9%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

---

## 🌟 Overview

OmniExtract is a production-ready, deployable Micro-SaaS API that solves one of the biggest bottlenecks for AI developers: converting messy, bloated web pages into clean, token-efficient Markdown stripped of cookie notices, navigation bars, tracking scripts, and advertisements.

### Key Capabilities
- **Noise Elimination:** Powered by Trafilatura & custom DOM pruning heuristics to extract pure article text and layout.
- **Token Analytics:** Measures token reduction between raw HTML and clean Markdown in real-time (typical savings: 80%–92%).
- **SSRF Hardened:** Built-in protection against private network probing and cloud metadata extraction (`169.254.169.254`).
- **Turnkey Monetization:**
  - Automated **Stripe Checkout & Webhook** integration for instant API key provisioning.
  - **RapidAPI Hub proxy-secret support** for listing directly on the RapidAPI marketplace.
  - Built-in SQLite-backed token bucket & quota tracker.
  - High-craft developer landing page with a live interactive playground.

---

## 🛠 Tech Stack

- **Backend:** Python 3.12+, FastAPI, Uvicorn, Pydantic v2
- **Scraping Engine:** Trafilatura, BeautifulSoup4, LXML, Markdownify, HTTPX
- **Billing & Auth:** Stripe SDK, Aiosqlite, RapidAPI proxy headers
- **Frontend:** Responsive Dark-Mode UI, vanilla JavaScript, CSS custom properties

---

## 🚀 Quickstart

### 1. Install & Run Locally

```bash
# Clone or navigate to the directory
cd goofy-heisenberg

# Install dependencies (or use existing .venv)
uv pip install -r requirements.txt

# Start the server
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit [http://localhost:8000](http://localhost:8000) to view the live playground.

### 2. Run Test Suite

```bash
.venv\Scripts\python -m pytest -v
```

All 9 unit and integration tests will verify SSRF filtering, token calculations, database quotas, and live extraction.

---

## 🔌 API Endpoints

### 1. Clean Markdown Extraction
`POST /v1/scrape`
```bash
curl -X POST "http://localhost:8000/v1/scrape" \
  -H "Authorization: Bearer omni_live_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Artificial_intelligence"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "title": "Artificial intelligence - Wikipedia",
    "markdown": "# Artificial intelligence\n\nArtificial intelligence (AI)...",
    "tokens_markdown": 4250,
    "tokens_raw_html": 38100,
    "tokens_saved": 33850,
    "savings_percentage": "88.8%"
  },
  "auth": {
    "tier": "pro",
    "quota_remaining": 49998
  }
}
```

### 2. Key Quota Check
`GET /v1/usage?key=omni_pro_...`

### 3. Automated Stripe Checkout
`POST /v1/billing/checkout`
```json
{
  "tier": "pro",
  "customer_email": "developer@example.com"
}
```

---

## 💼 Automated Monetization & Deployment

See [`DEPLOY_AND_EARN_GUIDE.md`](DEPLOY_AND_EARN_GUIDE.md) for the exact 3-step setup to connect Stripe/RapidAPI and start collecting automated recurring revenue.
