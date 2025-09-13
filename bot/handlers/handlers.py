import logging
import tempfile
import os
import json
import time
from aiogram import Router, types, F
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from bot.services.rag_pipeline import RAGPipeline
from bot.services.elevenlabs import TextToSpeechService
from bot.config import Config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, FSInputFile
import openai

# Create routers for question handling
question_router = Router()
query_router = Router()

def get_proper_title(content_type, original_title):
    """Get proper title from config files based on content type and original title"""
    try:
        # Map content_type to config file
        config_files = {
            'text': 'text_descriptions.json',
            'video': 'video_descriptions.json', 
            'podcast': 'podcast_descriptions.json',
            'audio': 'podcast_descriptions.json',  # Use podcast config for audio
            'url': 'url_descriptions.json'
        }
        
        config_file = config_files.get(content_type)
        if not config_file:
            return original_title
            
        # Load config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', config_file)
        if not os.path.exists(config_path):
            return original_title
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            
        # Find matching entry in config
        content_key = 'texts' if content_type == 'text' else 'videos'
        if content_key in config_data and original_title in config_data[content_key]:
            return config_data[content_key][original_title]['name']
            
        return original_title
        
    except Exception as e:
        logging.warning(f"Error getting proper title: {e}")
        return original_title

# In-memory storage for pagination (in production, use Redis or database)
user_pagination_data = {}

async def transcribe_voice_cloud(message: types.Message) -> str:
    """Transcribe voice message using OpenAI Whisper API"""
    # Get the file
    file_id = message.voice.file_id if message.voice else message.audio.file_id
    file = await message.bot.get_file(file_id)
    
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            await message.bot.download_file(file.file_path, temp_file.name)
            
            # Use OpenAI Whisper API for transcription (v1.0+ syntax)
            client = openai.AsyncOpenAI()
            with open(temp_file.name, 'rb') as audio_file:
                transcript = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )
            
            return transcript.text.strip()
            
    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


@question_router.message(F.text | F.voice | F.audio)
async def handle_user_question(message: types.Message, state: FSMContext, supabase_client):
    """Handle user questions with RAG pipeline"""
    # Extract text from message (text or voice)
    user_text = None
    
    if message.text:
        user_text = message.text
    elif message.voice or message.audio:
        # Show processing message for voice
        processing_voice_message = await message.answer("🎤 Распознаю голосовое сообщение...")
        
        try:
            user_text = await transcribe_voice_cloud(message)
            await processing_voice_message.delete()
            
            if not user_text or user_text.strip() == "":
                await message.answer("Не удалось распознать речь. Попробуйте еще раз или отправьте текстовое сообщение.")
                return
                
        except Exception as e:
            logging.error(f"Error transcribing voice: {e}")
            await processing_voice_message.edit_text("Ошибка при распознавании голосового сообщения. Попробуйте еще раз.")
            return
    else:
        await message.answer("Пожалуйста, отправьте текстовое или голосовое сообщение с вашим запросом.")
        return
    
    # Show processing message
    processing_message = await message.answer("🤔 Обрабатываю ваш вопрос...")

        # Send typing action
    await message.bot.send_chat_action(
        chat_id=message.from_user.id, 
        action=ChatAction.TYPING
    )
    
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline(supabase_client)
        
        # Get user from database, create if doesn't exist
        user = await supabase_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            # Try using create_or_update_user which might handle RLS better
            user_data = {
                'telegram_id': message.from_user.id,
                'username': message.from_user.username
            }
            user = await supabase_client.create_or_update_user(user_data)
            if not user:
                await processing_message.edit_text("Для использования бота выполните команду /start")
                return
        
        # Process question through RAG
        result = await rag.search_and_answer(
            user_id=user.id,
            question=user_text
        )
        
        if result.get('error'):
            await processing_message.edit_text(
                f"Произошла ошибка: {result.get('error', 'Неизвестная ошибка')}"
            )
            return
        
        # Format response with sources
        logging.info(f"📋 RAG Step 5: Response Formatting - Processing answer with {len(result.get('sources', []))} sources")
        response_text = result['answer']
        
        # Create webapp buttons for sources
        keyboard = None

        if result.get('sources'):
            
            buttons = []

            # Map content types to emojis
            source_type_icons = {
                'video': '🎥',
                'audio': '🎧', 
                'text': '📄',
                'podcast': '🎙️'
            }
            
            # Remove duplicates based on title, keep first occurrence, exclude audio type
            seen_titles = set()
            unique_sources = []
            for source in result['sources']:
                title = source.get('title', '')
                source_type = source.get('type', '')
                if title not in seen_titles and source_type != 'audio':
                    seen_titles.add(title)
                    unique_sources.append(source)
            
            for i, source in enumerate(unique_sources[:3], 1):  # Limit to 3 sources
                # Extract content type from metadata
                content_type = source.get('type')  # Default to 'text' if no type specified
                source_type = source_type_icons.get(content_type)  # Default to document icon
                
                # Get proper title from config files
                original_title = source['title']
                proper_title = get_proper_title(content_type, original_title)
                
                # Add source to text (removed duplicate logging)
                
                # Create webapp button for the source based on content type
                if content_type == 'video':
                    # For video: get file_id from config and use name as text
                    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'video_descriptions.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            video_config = json.load(f)
                        # Find matching video by title (remove .txt if present)
                        title_key = original_title.replace('.txt', '')
                        if title_key in video_config.get('videos', {}):
                            video_data = video_config['videos'][title_key]
                            proper_title = video_data['name']
                            webapp_url = f"{Config.WEBAPP_URL}/{video_data['file_id']}"
                        else:
                            webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                    else:
                        webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                elif content_type == 'podcast' or content_type == 'audio':
                    # For podcast: get file_id from config and use name as text
                    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'podcast_descriptions.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            podcast_config = json.load(f)
                        # Find matching podcast by title (remove .txt if present)
                        title_key = original_title.replace('.txt', '')
                        if title_key in podcast_config.get('videos', {}):  # Note: podcast config uses 'videos' key
                            podcast_data = podcast_config['videos'][title_key]
                            proper_title = podcast_data['name']
                            webapp_url = f"{Config.WEBAPP_URL}/{podcast_data['file_id']}"
                        else:
                            webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                    else:
                        webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                elif content_type == 'text':
                    # For text: get file_id from config and use name as text, URL format is different
                    config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'text_descriptions.json')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            text_config = json.load(f)
                        # Find matching text by title (remove .txt if present)
                        title_key = original_title.replace('.txt', '')
                        if title_key in text_config.get('texts', {}):
                            text_data = text_config['texts'][title_key]
                            proper_title = text_data['name']
                            webapp_url = f"{Config.WEBAPP_URL}/texts/{text_data['file_id']}"
                        else:
                            webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                    else:
                        webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"
                else:
                    webapp_url = f"{Config.WEBAPP_URL}/{content_type}s"

                button = InlineKeyboardButton(
                    text=f"{source_type_icons[content_type]} {proper_title}",
                    web_app=WebAppInfo(url=webapp_url)
                )
                buttons.append([button])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            logging.info(f"✅ RAG Step 5: Response Formatting - Created {len(buttons)} webapp buttons")
        
        # Check if user prefers audio responses
        if user.isAudio:
            try:
                # Generate audio using ElevenLabs
                logging.info(f"🎧 Generating audio response for user {message.from_user.id}")
                tts_service = TextToSpeechService()
                
                # Generate audio file in OGG format for voice messages
                audio_path = tts_service.text_to_speech(
                    text=response_text,
                    quality_preset="conversational",  # Good for bot responses
                    output_filename=f"response_{message.from_user.id}_{int(time.time())}.ogg"
                )
                
                # Send audio file
                audio_file = FSInputFile(audio_path)
                await processing_message.delete()  # Delete processing message
                
                if keyboard:
                    # Send voice message with sources buttons
                    await message.answer_voice(
                        voice=audio_file,
                        reply_markup=keyboard
                    )
                else:
                    # Send voice message without buttons
                    await message.answer_voice(
                        voice=audio_file
                    )
                
                # Clean up audio file
                try:
                    os.unlink(audio_path)
                except OSError:
                    pass  # File cleanup failed, but not critical
                
                logging.info(f"✅ Successfully sent audio response to user {message.from_user.id}")
                return
                
            except Exception as audio_error:
                logging.error(f"⚠️ Audio generation failed, falling back to text: {audio_error}")
                # Fall back to text response if audio generation fails
        
        # Send text response (either user prefers text or audio generation failed)
        logging.info(f"📤 RAG Step 5: Response Formatting - Sending final response (length: {len(response_text)} chars)")
        try:
            await processing_message.edit_text(response_text, reply_markup=keyboard, parse_mode="Markdown")
            logging.info(f"✅ RAG Step 5: Response Formatting - Successfully sent response with Markdown")
        except Exception as markdown_error:
            # Fallback: send without markdown if parsing fails
            logging.warning(f"⚠️ RAG Step 5: Response Formatting - Markdown parsing failed, sending as plain text: {markdown_error}")
            await processing_message.edit_text(response_text, reply_markup=keyboard)
            logging.info(f"✅ RAG Step 5: Response Formatting - Successfully sent response as plain text")
        
    except Exception as e:
        logging.error(f"❌ RAG Pipeline: Fatal error processing question for user {message.from_user.id}: {e}")
        await processing_message.edit_text(
            "Произошла ошибка при обработке вашего вопроса. Попробуйте еще раз или обратитесь к администратору."
        )


