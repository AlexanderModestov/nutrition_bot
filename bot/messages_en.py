class Messages:
    START_CMD = {
        "welcome": lambda user_name: (
            f"👋 Hello, {user_name}!\n\n"
            "I'm Vlada's assistant bot. \n"
            "Feel free to ask me any questions! Just type your question, and I'll do my best to help you 💬\nI use the knowledge from Vlada's videos. \n\n"
            "As well I can suggest to you next options:\n"
            "• 🎥 Watching Vlada's educational videos\n"
            "• 🔍 Finding specific topics discussed in the videos\n"
            "• 📝 Getting video summaries\n"
            "• ❓ Answering your questions about any topic\n\n"
            "Extra available commands:\n"
            "/help - Show help message\n"
            "Let's start! Write your questions or choose the option from the list."
        )
    }


    WARNINGS_AND_ERRORS = {
        "general": lambda error: f"An error occurred: {error}",
        "video_not_found": "Video not found",
        "no_access": "You don't have access to this video",
        "BOT_STOPPED_MESSAGE": "Bot has been stopped. Goodbye! 👋",
        "MAIN_ERROR_MESSAGE": "An error occurred in the main loop: {}",
        "DB_CONNECTION_CLOSED_MESSAGE": "Database connection has been closed. 🔒",
        "MESSAGE_PROCESSING_ERROR": "Error processing message: {}"
    }

    ABOUT_MESSAGE = (
        "🤖 *AI Assistant*\n\n"
        "I am your personal AI assistant. "
        "I can help you with various tasks and questions.\n\n"
        "Use /help to ask questions directly."
    )

    HELP_MESSAGE = (
        "🔍 *Available Commands*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "You can also:\n"
        "• Send text messages to ask questions\n"
        "• Send voice messages for voice-to-text conversion"
    )




    AUDIO_CMD = {
        "processing": "🎧 Processing your audio message...",
        "no_speech_detected": "❌ Sorry, I couldn't detect any speech in this audio.",
        "transcription_error": "❌ Sorry, I had trouble understanding the audio. Please try again.",
        "processing_error": "❌ An error occurred while processing your audio message. Please try again.",
    }
