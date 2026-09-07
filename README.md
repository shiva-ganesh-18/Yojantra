# SchemeMatch AI 🎯

**AI-driven government scheme matching platform for marginalized entrepreneurs in India.**

## What We Built

A complete production-ready foundation with:

### Backend (FastAPI + Python)
- ✅ **12 PostgreSQL tables** with full relationships
- ✅ **Neo4j graph schema** for scheme relationships
- ✅ **AI Matching Engine** — Hybrid rule-based + ML scoring with explainability
- ✅ **AI Chat Service** — LLM-powered with 12-language support and fallback
- ✅ **Document Upload + OCR** — Tesseract image OCR + PDF text extraction
- ✅ **Notification Service** — Multi-channel (Push/SMS/WhatsApp/Email) with priority matrix
- ✅ **CSC Locator** — Haversine distance-based nearest center finder
- ✅ **OTP Authentication** — JWT-based with 10-min expiry
- ✅ **Admin Analytics API** — Dashboard metrics, bias audit, scheme performance
- ✅ **30+ REST API endpoints** with Swagger docs
- ✅ **Security** — DPDP Act 2023 compliant, AES-256, TLS 1.3, rate limiting

### Frontend (React 18 + PWA)
- ✅ **Login** — OTP-based phone authentication
- ✅ **Onboarding Wizard** — 5-step profile creation
- ✅ **Dashboard** — Top matches, stats, quick actions, CSC finder
- ✅ **Matches** — AI-ranked schemes with match scores and explanations
- ✅ **Schemes Browser** — Search + filter by type
- ✅ **Applications Tracker** — Kanban-style status tracking
- ✅ **AI Chat** — Text-based assistant with typing indicators
- ✅ **Profile** — Tabs for Profile/Business/Documents with upload
- ✅ **Notification Bell** — Real-time notification dropdown
- ✅ **Document Uploader** — Camera capture + OCR preview
- ✅ **CSC Map** — Geolocation-based nearest center finder
- ✅ **Admin Dashboard** — 4-tab analytics (Overview/Users/Schemes/Bias Audit)
- ✅ **Offline-First PWA** — Service Workers + IndexedDB
- ✅ **Responsive Design** — Mobile-first with bottom navigation

### Infrastructure
- ✅ **Docker Compose** — PostgreSQL + Neo4j + Redis + Backend + Frontend
- ✅ **Seed Data** — 5 real government schemes + 5 CSC centers

---

## Quick Start

```bash
# 1. Enter directory
cd schemematch-ai

# 2. Start everything
./start.sh

# Or manually:
docker-compose up --build -d
docker-compose exec backend python scripts/seed_all.py

# 3. Access the app
Frontend:  http://localhost:3000
API Docs:  http://localhost:8000/docs
Health:    http://localhost:8000/health
```

---

## Project Structure

```
schemematch-ai/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, DB, Security
│   │   ├── models/            # 12 SQLAlchemy models
│   │   ├── routers/           # 10 API route modules
│   │   ├── services/          # 5 AI/service modules
│   │   ├── schemas.py         # Pydantic models
│   │   └── main.py            # FastAPI app
│   ├── scripts/
│   │   └── seed_all.py        # Seed schemes + CSCs
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/        # 4 reusable components
│   │   ├── pages/             # 9 page components
│   │   ├── hooks/             # Auth store
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js         # PWA config
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── Dockerfile
├── docker-compose.yml
├── start.sh
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/otp/send` | Send OTP |
| POST | `/auth/otp/verify` | Verify OTP → JWT |
| GET | `/users/me` | Get profile |
| PUT | `/users/me` | Update profile |
| POST | `/users/me/business` | Create business |
| GET | `/schemes` | List schemes |
| POST | `/schemes/match` | AI matching |
| GET | `/schemes/recommended` | Top matches |
| POST | `/applications` | Start application |
| GET | `/applications` | List applications |
| POST | `/chat/message` | AI chat |
| POST | `/documents/upload` | Upload + OCR |
| GET | `/documents/my-documents` | List documents |
| GET | `/notifications` | Get notifications |
| GET | `/csc/nearby` | Find nearest CSCs |
| GET | `/admin/analytics/dashboard` | Admin metrics |
| GET | `/admin/analytics/bias` | Bias audit |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | For AI chat |
| `DATABASE_URL` | Yes | PostgreSQL |
| `SECRET_KEY` | Yes | JWT signing |
| `NEO4J_URI` | No | Graph DB |
| `REDIS_URL` | No | Cache/queue |
| `TWILIO_*` | No | SMS/IVR |
| `WHATSAPP_API_KEY` | No | WhatsApp bot |

---

## Next Steps for Production

1. Add OpenAI API key to `.env`
2. Integrate Twilio for real OTP SMS
3. Connect DigiLocker/UDYAM APIs
4. Add WhatsApp Business API
5. Set up Firebase Cloud Messaging
6. Deploy to AWS/GCP
7. Add monitoring (Prometheus/Grafana/Sentry)
8. Load test with k6
9. Security audit
10. Pilot launch with 1000 entrepreneurs

---

**Built with ❤️ for marginalized entrepreneurs in India.**
