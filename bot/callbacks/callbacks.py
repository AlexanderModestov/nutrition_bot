import logging
import os
from aiogram import Router, types
from aiogram.types import FSInputFile
from bot.messages import Messages
from bot.config import Config
from bot.utils.channel_checker import check_user_subscription


# Create router for callbacks
callback_router = Router()


@callback_router.callback_query(lambda c: c.data == 'check_channel_subscription')
async def handle_subscription_check(callback_query: types.CallbackQuery, supabase_client):
    """Handle subscription verification and send book if subscribed"""
    try:
        user_id = callback_query.from_user.id
        bot = callback_query.bot

        # Get user from database
        user = await supabase_client.get_user_by_telegram_id(user_id)

        if not user:
            await callback_query.answer("Ошибка: пользователь не найден. Попробуйте /start снова.")
            return

        # Check if user already received the book
        if user.book_received:
            await callback_query.answer()
            # Remove the button from the original message
            try:
                await callback_query.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass  # Message might be too old to edit
            await callback_query.message.answer(Messages.START_CMD["book_already_sent"])
            return

        # Check if user is subscribed to the channel
        is_subscribed = await check_user_subscription(bot, user_id)

        if is_subscribed:
            # User is subscribed - send the book
            try:
                # Check if book file exists
                if not os.path.exists(Config.VITAMIN_BOOK_PATH):
                    logging.error(f"Book file not found at {Config.VITAMIN_BOOK_PATH}")
                    await callback_query.answer("❌ Ошибка: файл книги не найден. Обратитесь к администратору.")
                    return

                # Send the PDF book
                book_file = FSInputFile(Config.VITAMIN_BOOK_PATH)
                await callback_query.message.answer_document(
                    document=book_file,
                    caption=Messages.START_CMD["book_sent"]
                )

                # Mark book as received in database
                await supabase_client.mark_book_received(user_id)

                # Remove the button from the original message
                try:
                    await callback_query.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass  # Message might be too old to edit

                # Answer the callback query
                await callback_query.answer("✅ Книга отправлена!")

                logging.info(f"✅ Vitamin book sent to user {user_id} (@{callback_query.from_user.username})")

            except Exception as e:
                logging.error(f"Error sending book to user {user_id}: {e}")
                await callback_query.answer("❌ Произошла ошибка при отправке книги. Попробуйте позже.")

        else:
            # User is not subscribed - show reminder
            await callback_query.answer()
            await callback_query.message.answer(Messages.START_CMD["not_subscribed"]())

    except Exception as e:
        logging.error(f"Error in subscription check callback: {e}")
        await callback_query.answer()
        await callback_query.message.answer(Messages.START_CMD["subscription_check_error"])
