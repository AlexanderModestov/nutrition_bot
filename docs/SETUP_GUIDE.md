# Setup Guide - Telegram AI Bot

This guide will help you set up the Telegram AI Bot with WebApp and RAG search functionality.

## Prerequisites

Before you begin, ensure you have:

- **Telegram Account** and ability to create bots
- **Supabase Account** (free tier available)
- **OpenAI API Key** (with credits)
- **Web Hosting** for the WebApp (Netlify, Vercel, etc.)
- **Python 3.8+** installed locally
- **Node.js 16+** installed locally

## Step 1: Create Telegram Bot

1. **Message @BotFather on Telegram:**
   ```
   /newbot
   ```

2. **Choose bot name and username:**
   - Name: "My AI Assistant"
   - Username: "my_ai_assistant_bot" (must end with 'bot')

3. **Save the bot token** - you'll need it later

4. **Set bot commands (optional):**
   ```
   /setcommands
   
   start - Start the bot and register
   content - Open content library
   question - Send message to support
   ```

## Step 2: Setup Supabase Database

1. **Create new Supabase project:**
   - Go to [supabase.com](https://supabase.com)
   - Create new project
   - Wait for setup to complete

2. **Enable pgvector extension:**
   - Go to Database > Extensions
   - Search for "vector" and enable it

3. **Run database schema:**
   - Go to SQL Editor
   - Copy contents of `docs/supabase_schema.sql`
   - Execute the script

4. **Get your credentials:**
   - Go to Settings > API
   - Save the Project URL and anon/public key

## Step 3: Setup OpenAI API

1. **Create OpenAI account:**
   - Go to [platform.openai.com](https://platform.openai.com)
   - Sign up and verify account

2. **Get API key:**
   - Go to API Keys section
   - Create new secret key
   - Save it securely

3. **Add credits to your account** (required for API usage)

## Step 4: Deploy WebApp

### Option A: Deploy to Netlify

1. **Prepare WebApp:**
   ```bash
   cd webapp
   cp .env.example .env
   ```

2. **Configure .env:**
   ```env
   VITE_SUPABASE_URL=your_supabase_project_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Build the app:**
   ```bash
   npm install
   npm run build
   ```

4. **Deploy to Netlify:**
   - Create account at netlify.com
   - Drag & drop the `dist` folder
   - Note your app URL (e.g., https://amazing-app-123.netlify.app)

### Option B: Deploy to Vercel

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   cd webapp
   vercel --prod
   ```

3. **Set environment variables:**
   - Go to Vercel dashboard
   - Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

## Step 5: Configure Bot Backend

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure your .env:**
   ```env
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=1234567890:ABCDEFghijklmnopqrstuvwxyz123456789
   TELEGRAM_ADMIN_ID=123456789
   
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   
   # OpenAI Configuration
   OPENAI_API_KEY=sk-...your-api-key
   
   # App Configuration
   DEBUG=False
   RATE_LIMIT_REQUESTS_PER_DAY=50
   WEBAPP_URL=https://your-webapp-url.netlify.app
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Step 6: Configure WebApp in Telegram Bot

1. **Set WebApp URL in BotFather:**
   ```
   /setmenubutton
   # Select your bot
   # Set button text: "Open App"
   # Set WebApp URL: https://your-webapp-url.netlify.app
   ```

2. **Test WebApp integration:**
   - Start your bot locally: `python bot/main.py`
   - Send `/start` to your bot
   - Try opening the WebApp

## Step 7: Test the Complete System

1. **Start the bot:**
   ```bash
   python bot/main.py
   ```

2. **Test bot commands:**
   - Send `/start` to register
   - Send `/content` to open WebApp
   - Send `/question` to test support messaging

3. **Test WebApp:**
   - Upload a document
   - Add a video URL
   - Check that content appears

4. **Test AI functionality:**
   - Upload some content via WebApp
   - Ask the bot questions about your content
   - Verify you get relevant answers

## Step 8: Production Deployment

### Deploy Bot to Production

**Option A: Heroku**
```bash
# Install Heroku CLI
# Create Procfile:
echo "worker: python bot/main.py" > Procfile

# Deploy:
heroku create your-bot-name
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set SUPABASE_URL=your_url
# ... set other env vars
heroku git:remote -a your-bot-name
git add .
git commit -m "Deploy bot"
git push heroku main
```

**Option B: VPS/Cloud Server**
```bash
# Use systemd, docker, or process manager like PM2
# Example systemd service:
sudo nano /etc/systemd/system/telegram-bot.service

[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/bot
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

**1. Bot not responding:**
- Check bot token is correct
- Verify bot is running without errors
- Check firewall/network settings

**2. WebApp not loading:**
- Verify WebApp URL in bot settings
- Check environment variables in deployment
- Ensure HTTPS (required for Telegram WebApps)

**3. Database connection errors:**
- Verify Supabase credentials
- Check if database schema was applied
- Ensure pgvector extension is enabled

**4. OpenAI API errors:**
- Verify API key is correct
- Check account has sufficient credits
- Monitor rate limits

**5. File uploads not working:**
- Check Supabase storage bucket configuration
- Verify file size limits
- Test bucket permissions

### Monitoring and Logs

1. **Enable logging:**
   ```python
   # In bot/main.py
   logging.basicConfig(level=logging.INFO)
   ```

2. **Monitor error rates:**
   - Check bot logs regularly
   - Monitor Supabase dashboard
   - Set up alerts for API failures

3. **User feedback:**
   - Monitor support messages via `/question`
   - Check user ratings in query history
   - Analyze usage patterns

## Security Considerations

1. **Keep secrets secure:**
   - Never commit API keys to git
   - Use environment variables
   - Rotate keys periodically

2. **Implement rate limiting:**
   - Already included in the bot
   - Monitor usage patterns
   - Adjust limits as needed

3. **Validate user input:**
   - Bot includes input sanitization
   - Monitor for malicious content
   - Implement content filtering if needed

## Scaling Considerations

1. **Database optimization:**
   - Monitor vector search performance
   - Consider database indexing
   - Plan for storage growth

2. **Cost management:**
   - Monitor OpenAI API usage
   - Implement user limits
   - Consider caching strategies

3. **Performance monitoring:**
   - Track response times
   - Monitor server resources
   - Set up alerts

## Getting Help

- Check the main README.md for detailed documentation
- Review error logs for specific issues
- Test each component individually
- Use the bot's `/question` command for user support
- Check Supabase, OpenAI, and Telegram documentation

## Next Steps

Once your bot is running:

1. **Customize the experience:**
   - Modify prompts in RAG pipeline
   - Add new commands
   - Enhance WebApp UI

2. **Add features:**
   - Analytics dashboard
   - Multi-language support
   - Advanced admin tools

3. **Monitor and improve:**
   - Track user engagement
   - Optimize AI responses
   - Gather user feedback