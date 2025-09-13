# Psychology Bot

A Telegram bot for psychology-related video content with subscription management and RAG-based question answering.

## Features

- 🎥 **Video Content Management**: Access and view psychology-related videos
- 🤖 **AI-Powered Responses**: Get answers to psychology questions using RAG (Retrieval-Augmented Generation)
- 💬 **Subscription System**: Free tier with limited requests and premium subscription for unlimited access
- 📊 **Usage Tracking**: Track user requests and subscription status
- 📱 **Telegram Integration**: Seamless interaction through Telegram
- 🔍 **Search Functionality**: Search through video content for specific topics
- 📝 **Video Summaries**: Automatically generated summaries of video content

## Project Structure

```
psychology_bot/
├── bot/                      # Telegram bot implementation
│   ├── commands/             # Bot command handlers
│   │   └── commands.py       # Command implementations
│   ├── utils/                # Utility functions
│   │   ├── text_segments.py  # Text processing utilities
│   │   └── video_manager.py  # Video file management
│   ├── messages.py           # Message templates
│   └── bot_instance.py       # Bot initialization
├── configs/                  # Configuration files
│   ├── config.py             # Main configuration
│   └── video_descriptions.json # Video metadata
├── databases/                # Database integration
│   └── database/
│       ├── postgresql.py     # PostgreSQL database handler
│       └── init_db.py        # Database initialization script
├── data/                     # Data storage
│   ├── videos/               # Local video storage
│   ├── texts/                # Video transcripts
│   ├── summary/              # Video summaries
│   └── faiss/                # Vector database for RAG
│       └── vectorstore/      # Vector embeddings
├── preprocessing/            # Data preprocessing
│   └── summarization.py      # Text summarization
├── rag_engine/               # RAG implementation
│   ├── rag.py                # RAG query processing
│   └── openai_logger.py      # OpenAI API call logging
├── webapp/                   # Web application (optional)
│   ├── static/               # Static files
│   ├── templates/            # HTML templates
│   └── app.py                # Flask web application
├── .env                      # Environment variables
├── requirements.txt          # Project dependencies
├── run.py                    # Main entry point
└── README.md                 # This file
```

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- OpenAI API Key (for RAG functionality)
- Anthropic API Key (optional, for summarization)
- Storage solution (local or Replit)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/psychology_bot.git
   cd psychology_bot
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables in `.env` file:
   ```
   # Telegram Bot
   TOKEN=your_telegram_bot_token
   
   # Database
   DATABASE=psychology_bot
   DB_USER=postgres
   PASSWORD=your_password
   HOST=localhost
   PORT=5432
   DB_SCHEMA=public
   
   # OpenAI API
   OPENAI_API_KEY=your_openai_api_key
   MODEL_OPENAI=gpt-3.5-turbo
   MODEL_OPENAI_EMBEDDINGS=text-embedding-ada-002
   
   # Anthropic API (optional)
   CLAUDE_API_KEY=your_claude_api_key
   
   # Subscription settings
   DEFAULT_SUBSCRIPTION_DAYS=30
   FREE_REQUESTS_LIMIT=10
   
   # Web app (optional)
   WEBAPP_BASE_URL=your_webapp_url
   
   # Storage settings (optional)
   AZURE_CONNECTION_STRING=your_azure_connection_string
   AZURE_CONTAINER_NAME=your_container_name
   
   # LangSmith settings (optional, for tracing)
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=your_langsmith_api_key
   LANGSMITH_PROJECT=your_project_name
   ```

5. Create necessary directories:
   ```bash
   mkdir -p data/videos data/texts data/summary data/faiss/vectorstore
   ```

6. Initialize the database:
   ```bash
   python -m databases.database.init_db
   ```

7. Process video transcripts (if available):
   ```bash
   python -m preprocessing.summarization
   ```

8. Build the vector database for RAG:
   ```bash
   python -m rag_engine.build_vectorstore
   ```

## Usage

### Running the Bot

```bash
python run.py
```

For production deployment, consider using a process manager like Supervisor:

```bash
# Example supervisor configuration
[program:psychology_bot]
command=/path/to/venv/bin/python /path/to/psychology_bot/run.py
directory=/path/to/psychology_bot
autostart=true
autorestart=true
stderr_logfile=/path/to/psychology_bot/logs/err.log
stdout_logfile=/path/to/psychology_bot/logs/out.log
```

### Available Commands

- `/start` - Start the bot
- `/help` - Show help message
- `/videos` - List available videos
- `/video_info [video_name]` - Get detailed video information
- `/about` - Show information about the bot
- `/search [query]` - Search through video content
- `/info` - Get video summaries
- `/history` - View interaction history
- `/subscription` - Check subscription status
- `/subscribe` - Get a subscription for unlimited access
- `/requests` - Check remaining free requests
- `/booking` - Book a session (if enabled)
- `/unsubscribe` - Unsubscribe from notifications

### Subscription System

The bot implements a freemium model:
- **Free tier**: Limited to 10 requests (configurable via `FREE_REQUESTS_LIMIT`)
- **Premium subscription**: Unlimited requests for a specified duration (default: 30 days)

Users can check their subscription status with `/subscription` and subscribe with `/subscribe`.

#### Subscription Flow

1. User sends a question or uses `/requests` to check remaining free requests
2. When free requests are exhausted, the bot prompts to subscribe
3. User subscribes with `/subscribe` command
4. A payment record is created (integration with actual payment processors can be added)
5. User now has unlimited access for the subscription period

## Database Schema

The database consists of the following tables:

1. **users**: Stores user information
   - `id`: Serial ID
   - `user_id`: Telegram user ID (unique)
   - `full_name`: User's name
   - `created_at`: Registration timestamp

2. **requests**: Logs user questions
   - `id`: Serial ID
   - `user_id`: Telegram user ID
   - `timestamp`: Request timestamp
   - `question`: User's question

3. **subscriptions**: Tracks user subscriptions
   - `id`: Serial ID
   - `user_id`: Telegram user ID
   - `start_date`: Subscription start date
   - `end_date`: Subscription end date
   - `created_at`: Creation timestamp
   - `active`: Boolean indicating if subscription is active

4. **payments**: Records payment information
   - `id`: Serial ID
   - `user_id`: Telegram user ID
   - `subscription_id`: Subscription ID
   - `payment_date`: Payment timestamp
   - `amount`: Payment amount
   - `status`: Payment status ('completed', 'pending', 'failed')
   - `transaction_id`: External transaction ID

### Database Functions

The `postgresql.py` module provides the following key functions:

- **User Management**: `insert_user()`, `get_user()`
- **Request Tracking**: `insert_resquest()`, `log_request()`, `count_user_requests()`
- **Subscription Management**: `create_subscription()`, `get_active_subscription()`, `check_subscription_status()`
- **Payment Processing**: `add_payment()`, `get_user_payments()`
- **Usage Statistics**: `get_user_subscription_stats()`, `check_request_limit()`

## RAG System

The Retrieval-Augmented Generation (RAG) system uses OpenAI models to provide accurate answers based on video content.

### Components

1. **Vector Database**: FAISS stores embeddings of video transcript segments
2. **Embeddings**: OpenAI embeddings model converts text to vector representations
3. **Retriever**: Finds relevant context from the vector database
4. **LLM**: OpenAI's GPT model generates responses based on retrieved context
5. **Logger**: Tracks API usage and tokens consumed

### RAG Flow

1. User question is embedded using OpenAI's embedding model
2. Similar content is retrieved from the vector database
3. Retrieved content and question are sent to the LLM
4. LLM generates a response based on the context
5. Response is returned to the user
6. API calls are logged for tracking

## Development

### Adding New Videos

1. Place video files in `data/videos/` directory
2. Place transcript files in `data/texts/` directory (format: `video_name.txt`)
3. Run the summarization script:
   ```bash
   python -m preprocessing.summarization
   ```
4. Rebuild the vector database:
   ```bash
   python -m rag_engine.build_vectorstore
   ```

### Video Format Support

The bot supports the following video formats:
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)

### Storage Options

The bot supports multiple storage options:

1. **Local Storage**: Videos stored in `data/videos/` directory
2. **Replit Storage**: Automatically used when running on Replit
3. **Azure Blob Storage**: Configure with `AZURE_CONNECTION_STRING` and `AZURE_CONTAINER_NAME`

### Extending the Bot

- Add new commands in `bot/commands/commands.py`
- Modify message templates in `bot/messages.py`
- Update database functions in `databases/database/postgresql.py`
- Customize RAG behavior in `rag_engine/rag.py`

### API Integration

#### OpenAI API

The bot uses OpenAI's API for:
- Generating embeddings for video content
- Retrieving relevant context
- Generating responses to user questions

Configure with:
```
OPENAI_API_KEY=your_openai_api_key
MODEL_OPENAI=gpt-3.5-turbo  # or gpt-4, etc.
MODEL_OPENAI_EMBEDDINGS=text-embedding-ada-002
```

#### Anthropic API (Optional)

Used for generating summaries of video content:

```
CLAUDE_API_KEY=your_claude_api_key
```

### Payment Integration

The current implementation includes a basic payment tracking system. To integrate with actual payment processors:

1. Modify the `/subscribe` command handler in `bot/commands/commands.py`
2. Implement payment gateway callbacks
3. Update the `add_payment()` function in `databases/database/postgresql.py`

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Ensure PostgreSQL is running
   - Verify database credentials in `.env`
   - Check that the database and schema exist

2. **API Key Issues**:
   - Verify OpenAI API key is valid and has sufficient credits
   - Check for proper environment variable configuration

3. **Storage Problems**:
   - For local storage, ensure directories exist and have proper permissions
   - For Replit, check that the storage module is properly initialized
   - For Azure, verify connection string and container name

4. **Bot Command Errors**:
   - Ensure commands are registered with BotFather
   - Check for proper command handler registration in the code

### Logs

Check the following logs for troubleshooting:
- `logs/rag_process.log`: RAG system logs
- `logs/openai_requests.log`: OpenAI API call logs
- `logs/bot.log`: Telegram bot logs

## License

[MIT License](LICENSE)

## Acknowledgements

- [Aiogram](https://github.com/aiogram/aiogram) for Telegram bot framework
- [OpenAI](https://openai.com/) for AI models
- [PostgreSQL](https://www.postgresql.org/) for database
- [LangChain](https://github.com/langchain-ai/langchain) for RAG implementation
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [Anthropic](https://www.anthropic.com/) for Claude AI (optional)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or support, please open an issue on the GitHub repository.


source .venv/bin/activate
python -m bot.main