# 🎓 Nia Learning Assistant

COPPA-compliant AI learning assistant for K-12 students with RAG-powered educational content.

## ✨ Features

- 🔐 Parent-controlled accounts with child PIN authentication
- 📚 RAG system with curated educational content
- 🗂️ Automatic conversation categorization by subject
- 📊 3-level progressive tutoring depth
- 🌐 Bilingual support (English/Spanish)
- ♿ Learning accommodations (autism, dyslexia, ADHD, visual learners)
- 📖 Source attribution (curriculum vs. general knowledge)

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your keys:
# - DATABASE_URL (PostgreSQL connection string)
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - ANTHROPIC_API_KEY
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```

The API will be available at:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

## 📊 Project Structure
```
nia-learning-assistant/
├── main.py                    # FastAPI app
├── config.py                  # Settings
├── database.py                # Database connection
├── models.py                  # SQLAlchemy models
├── auth.py                    # Authentication
├── services/
│   ├── rag_service.py        # AI & RAG
│   ├── content_service.py    # Content ingestion
│   └── conversation_service.py
├── routers/
│   ├── auth.py               # Login/register
│   ├── children.py           # Child management
│   └── conversation.py       # Chat endpoints
└── educational_content/      # Curated content
```

## 🧪 Testing

```bash
pytest -q tests
```

The model probe is separate from the test suite and requires an API key:

```bash
ANTHROPIC_API_KEY=... python model_probe.py
```

Visit http://localhost:8000/docs for interactive API documentation.

## 🚀 Deployment

Before deployment:

1. Back up the production database.
2. Run `python3 -m migrations.migrate_child_pins` with the production `DATABASE_URL`.
3. Set a strong `SECRET_KEY`, `ANTHROPIC_API_KEY`, `CORS_ORIGINS`, and `DEBUG=false`.
4. Configure HTTPS and database backups.
5. Use a distributed rate-limit store such as Redis when running multiple instances.

---

Built with ❤️ for kids' learning
