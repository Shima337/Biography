# Environment Variables Setup

Since `.env.example` creation was blocked, create a `.env` file manually with these variables:

```env
# Database
DATABASE_URL=postgresql://lifebook:lifebook_dev@localhost:5432/lifebook_lab

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# LLM Provider (openai or mock)
LLM_PROVIDER=openai

# Backend
BACKEND_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Quick Setup

```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql://lifebook:lifebook_dev@localhost:5432/lifebook_lab
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
LLM_PROVIDER=openai
BACKEND_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

Then edit `.env` and replace `your_key_here` with your actual OpenAI API key.
