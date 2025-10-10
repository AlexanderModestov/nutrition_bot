import logging
from aiogram import Bot
from bot.config import Config


async def check_user_subscription(bot: Bot, user_id: int) -> bool:
    """
    Check if user is subscribed to the channel

    Args:
        bot: Aiogram Bot instance
        user_id: Telegram user ID

    Returns:
        True if user is subscribed, False otherwise
    """
    try:
        # Get channel username with @ prefix
        channel_username = f"@{Config.CHANNEL_USERNAME}"

        # Check user's membership status in the channel
        member = await bot.get_chat_member(
            chat_id=channel_username,
            user_id=user_id
        )

        # User is considered subscribed if their status is:
        # - creator (channel owner)
        # - administrator
        # - member (regular subscriber)
        # NOT: left, kicked, restricted
        is_subscribed = member.status in ['creator', 'administrator', 'member']

        logging.info(f"User {user_id} subscription check: {member.status} - {'✅ Subscribed' if is_subscribed else '❌ Not subscribed'}")

        return is_subscribed

    except Exception as e:
        logging.error(f"Error checking subscription for user {user_id}: {e}")
        # If there's an error (e.g., user not found, channel not accessible),
        # we assume user is not subscribed
        return False
