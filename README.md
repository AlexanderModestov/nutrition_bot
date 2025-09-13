# Nutrition Bot

A Telegram bot for nutrition consultation with AI-powered responses and interactive features.

## Features

- 🤖 **AI-Powered Responses**: Get answers to nutrition questions using RAG (Retrieval-Augmented Generation)
- 📚 **Resources Access**: Access materials (videos, texts, podcasts) via web app
- 📝 **Interactive Quizzes**: Topic-based quizzes with pagination
- 📅 **Session Booking**: Schedule consultation sessions with date and time selection
- ⚙️ **User Settings**: Customize response format (text/audio) and notifications
- 🎤 **Voice Support**: Voice message transcription using OpenAI Whisper
- 🔔 **Smart Notifications**: Timezone-aware notification system
- 🗣️ **Text-to-Speech**: Audio responses using ElevenLabs

## Commands

- `/start` - Start the bot and register user
- `/resources` - Access all materials via web app
- `/quiz` - Start topic-based quizzes
- `/booking` - Schedule a consultation session
- `/settings` - Configure bot settings
- `/help` - Ask questions directly

## Tech Stack

- **Bot Framework**: Aiogram (Python)
- **Database**: Supabase (PostgreSQL)
- **AI/ML**: OpenAI (GPT, Whisper, Embeddings)
- **Voice**: ElevenLabs Text-to-Speech
- **Search**: RAG pipeline with vector embeddings

## Project Structure

```
bot/
├── commands/           # Command handlers
├── handlers/           # Message handlers
├── services/           # Core services (RAG, TTS, notifications)
├── supabase_client/    # Database client and models
├── configs/            # Configuration files
└── messages.py         # Message templates

docs/
└── supabase_schema.sql # Database schema
```

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env`
4. Run the bot: `python -m bot.main`

## Environment Variables

See `.env.example` for required configuration variables including:
- Telegram Bot Token
- Supabase credentials
- OpenAI API key
- ElevenLabs API key
- Web app URL