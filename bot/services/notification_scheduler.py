import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Bot
from bot.supabase_client.client import SupabaseClient
from bot.services.notification_service import NotificationService

class NotificationScheduler:
    def __init__(self, bot: Bot, supabase_client: SupabaseClient):
        self.bot = bot
        self.supabase_client = supabase_client
        self.notification_service = NotificationService(bot, supabase_client)
        self.running = False
    
    async def send_notifications_now(self) -> dict:
        """Send notifications for current time - can be called manually or by cron"""
        logging.info("Manual notification trigger activated")
        result = await self.notification_service.send_scheduled_notifications()
        return result
    
    async def send_test_notification(self, telegram_id: int) -> bool:
        """Send a test notification to specific user"""
        return await self.notification_service.test_notification(telegram_id)
    
    async def get_notification_status(self) -> dict:
        """Get current notification system status"""
        try:
            current_time = datetime.now()
            current_hour = f"{current_time.hour:02d}:00"
            current_weekday = current_time.strftime('%A').lower()
            
            # Get users who should receive notifications now
            users_to_notify = await self.supabase_client.get_users_for_notification(
                current_hour, current_weekday
            )
            
            # Get total users with notifications enabled
            users_response = self.supabase_client.client.table('users').select('id').eq('notification', True).execute()
            total_enabled_users = len(users_response.data) if users_response.data else 0
            
            return {
                "current_time": current_hour,
                "current_weekday": current_weekday,
                "users_scheduled_now": len(users_to_notify),
                "total_users_with_notifications": total_enabled_users,
                "scheduler_running": self.running
            }
            
        except Exception as e:
            logging.error(f"Error getting notification status: {e}")
            return {
                "error": str(e)
            }
    
    def start_background_scheduler(self, check_interval_minutes: int = 60):
        """Start background scheduler (for development/testing)"""
        if self.running:
            logging.warning("Scheduler already running")
            return
        
        self.running = True
        asyncio.create_task(self._background_loop(check_interval_minutes))
        logging.info(f"Background notification scheduler started (check every {check_interval_minutes} minutes)")
    
    def stop_background_scheduler(self):
        """Stop background scheduler"""
        self.running = False
        logging.info("Background notification scheduler stopped")
    
    async def _background_loop(self, check_interval_minutes: int):
        """Background loop for checking notifications (for development only)"""
        while self.running:
            try:
                current_minute = datetime.now().minute
                # Only send notifications at the top of the hour (minute 0)
                if current_minute == 0:
                    await self.send_notifications_now()
                
                # Wait for next check
                await asyncio.sleep(check_interval_minutes * 60)
                
            except Exception as e:
                logging.error(f"Error in background notification loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

# Usage functions for easy integration
async def send_notifications(bot: Bot, supabase_client: SupabaseClient) -> dict:
    """Standalone function to send notifications - perfect for cron jobs"""
    scheduler = NotificationScheduler(bot, supabase_client)
    return await scheduler.send_notifications_now()

async def get_users_for_current_time(supabase_client: SupabaseClient) -> dict:
    """Get information about users scheduled for current time"""
    current_time = datetime.now()
    current_hour = f"{current_time.hour:02d}:00"
    current_weekday = current_time.strftime('%A').lower()
    
    users = await supabase_client.get_users_for_notification(current_hour, current_weekday)
    
    return {
        "current_time": current_hour,
        "current_weekday": current_weekday,
        "users_count": len(users),
        "users": users
    }