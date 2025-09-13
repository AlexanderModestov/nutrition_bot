# Telegram AI Bot with WebApp and RAG Search

A comprehensive Telegram bot that provides AI-generated answers based on users' personal content using Retrieval-Augmented Generation (RAG) with Supabase and LangChain.

## 🚀 Features

### Core Features
- **AI-Powered Q&A**: Ask questions and get answers based on your personal content
- **Document Management**: Upload and manage PDF, DOC, DOCX, and TXT files
- **Video Content**: Add YouTube, Vimeo, and other video links with automatic transcription
- **Voice Message Support**: Send voice messages for both queries and support
- **Telegram WebApp**: Modern web interface for content management
- **User-to-Admin Messaging**: Direct support communication through the bot

### Advanced Features
- **RAG Search Pipeline**: Advanced semantic search using vector embeddings
- **Favorites System**: Mark important content for prioritized search
- **Query History**: Track all conversations and responses
- **User Settings**: Customize AI behavior, answer style, and filters
- **Responsive WebApp**: Works seamlessly on mobile and desktop

## 🛠 Tech Stack

- **Backend**: Python with Aiogram framework
- **Database**: Supabase (PostgreSQL + pgvector)
- **AI Pipeline**: LangChain + OpenAI (GPT-3.5-turbo & text-embedding-ada-002)
- **Frontend**: React with TypeScript + Vite
- **Authentication**: Telegram WebApp authentication
- **Voice Processing**: OpenAI Whisper for transcription

## 📁 Project Structure

```
telegramBot/
├── bot/                    # Python bot backend
│   ├── handlers/          # Command and message handlers
│   ├── services/          # RAG pipeline and transcription
│   ├── supabase_client/   # Database client and models
│   ├── config.py          # Configuration management
│   └── main.py           # Bot entry point
├── webapp/                # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # WebApp pages
│   │   ├── hooks/        # Custom React hooks
│   │   ├── utils/        # Utilities and API clients
│   │   └── types/        # TypeScript type definitions
│   └── package.json
├── docs/                  # Documentation
│   ├── supabase_schema.sql
│   └── README.md
└── requirements.txt
```

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Node.js 16+
- Supabase account
- OpenAI API key
- Telegram Bot Token

### 2. Backend Setup

1. **Clone and navigate to project:**
   ```bash
   cd telegramBot
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Configure your .env file:**
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_ADMIN_ID=your_admin_telegram_id
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   OPENAI_API_KEY=your_openai_api_key
   WEBAPP_URL=https://your-webapp-domain.com
   ```

### 3. Database Setup

1. **Create a new Supabase project**

2. **Run the SQL schema:**
   ```bash
   # Copy the content of docs/supabase_schema.sql
   # and execute it in your Supabase SQL editor
   ```

3. **Enable pgvector extension:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### 4. WebApp Setup

1. **Navigate to webapp directory:**
   ```bash
   cd webapp
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit with your Supabase configuration
   ```

4. **Build the WebApp:**
   ```bash
   npm run build
   ```

5. **Deploy to your hosting service** (Netlify, Vercel, etc.)

### 5. Running the Bot

```bash
cd bot
python main.py
```

## 📱 Bot Commands

- `/start` - Register user and show welcome message
- `/content` - Open WebApp content library
- `/question` - Send message to support/admin

## 🌐 WebApp Features

### Dashboard
- Overview of user content and statistics
- Quick access to all features
- Getting started guide for new users

### Documents Management
- Drag & drop file upload
- Support for PDF, DOC, DOCX, TXT
- Favorite documents
- Content preview

### Videos Management
- Add video URLs (YouTube, Vimeo, Loom)
- Automatic transcription
- Metadata management
- Favorite videos

### Chat History
- View all AI conversations
- Rate previous answers
- Search through history
- Detailed source information

### Settings
- Customize AI answer style (concise/detailed/step-by-step)
- Content filtering options
- Search result limits
- Privacy preferences

## 🔄 RAG Pipeline Flow

1. **Content Ingestion:**
   - Documents uploaded via WebApp
   - Text extracted and chunked
   - Embeddings generated using OpenAI
   - Stored in Supabase with pgvector

2. **Query Processing:**
   - User sends question to bot
   - Question converted to embedding
   - Semantic search in vector database
   - Relevant content retrieved

3. **Answer Generation:**
   - Context + question sent to GPT-3.5-turbo
   - AI generates comprehensive answer
   - Sources cited in response
   - Query and answer saved to history

## 🔧 Configuration Options

### User Settings
- **Answer Style**: Concise, Detailed, or Step-by-step
- **Content Filter**: All, Favorites only, Documents only, Videos only
- **Search Limit**: Number of sources to consider (3, 5, or 10)
- **Rating System**: Enable/disable answer rating

### Admin Features
- Message forwarding from users
- Reply to user messages
- Access to all user interactions
- Content moderation capabilities

## 🔒 Security & Privacy

- Telegram WebApp authentication
- User data isolation
- Rate limiting
- Input sanitization
- Secure API key management
- Optional conversation logging

## 📊 Monitoring & Analytics

The system logs:
- User interactions and message types
- Query performance and response times
- Content upload and processing status
- User engagement metrics
- Error tracking and debugging info

## 🛠 Development

### Adding New Features

1. **Bot Commands**: Add handlers in `bot/handlers/`
2. **WebApp Pages**: Create React components in `webapp/src/pages/`
3. **Database Changes**: Update schema and models
4. **API Endpoints**: Extend Supabase client methods

### Testing

```bash
# Backend testing
pytest bot/tests/

# Frontend testing
cd webapp && npm test
```

### Deployment

1. **Bot**: Deploy to VPS, Heroku, or similar
2. **WebApp**: Deploy to Netlify, Vercel, or CDN
3. **Database**: Supabase handles hosting
4. **Monitoring**: Use logging and error tracking

## 📝 API Documentation

### Supabase Tables

- `users` - User profiles and settings
- `documents` - Uploaded document metadata
- `video_contents` - Video content and transcripts
- `query_history` - AI conversation history
- `user_messages` - Support message logging

### Vector Search Functions

- `search_documents()` - Semantic document search
- `search_videos()` - Semantic video search

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- Create an issue for bugs
- Use discussions for questions
- Check documentation first
- Contact admin through the bot's `/question` command

## 🚀 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Integration with more video platforms
- [ ] Collaborative content libraries
- [ ] API for third-party integrations
- [ ] Enhanced admin panel
- [ ] Automated content suggestions
- [ ] Export conversation history