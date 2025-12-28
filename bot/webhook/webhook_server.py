"""
YooKassa Webhook Server

This server runs alongside the Telegram bot to receive payment notifications from YooKassa.
When a payment is successful, it updates the database and notifies the user via Telegram.
"""

import asyncio
import logging
from aiohttp import web
from typing import Optional
from bot.config import Config
from bot.supabase_client import SupabaseClient
from bot.services.yookassa_service import YooKassaService
from aiogram import Bot

logger = logging.getLogger(__name__)


class WebhookServer:
    """Webhook server for YooKassa payment notifications"""

    def __init__(self, bot: Bot, supabase_client: SupabaseClient):
        """
        Initialize webhook server

        Args:
            bot: Telegram Bot instance for sending notifications
            supabase_client: Supabase client for database operations
        """
        self.bot = bot
        self.supabase_client = supabase_client
        self.yookassa_service = YooKassaService()
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_post('/webhook/yookassa', self.handle_yookassa_webhook)
        self.app.router.add_get('/webhook/health', self.health_check)

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({'status': 'ok', 'service': 'yookassa-webhook'})

    async def handle_yookassa_webhook(self, request: web.Request) -> web.Response:
        """
        Handle YooKassa webhook notifications

        Receives payment status updates from YooKassa and processes them:
        - Verifies the request comes from YooKassa servers
        - Updates payment transaction in database
        - Notifies user via Telegram bot
        """
        try:
            # Get client IP
            client_ip = request.remote
            logger.info(f"Webhook received from IP: {client_ip}")

            # Verify IP is from YooKassa
            if not self.yookassa_service.verify_webhook_ip(client_ip):
                logger.warning(f"Webhook rejected: invalid IP {client_ip}")
                return web.Response(status=403, text="Forbidden: Invalid IP")

            # Parse notification data
            notification_data = await request.json()
            logger.info(f"Webhook notification received: {notification_data.get('event')}")

            # Process notification using YooKassa service
            result = self.yookassa_service.process_webhook_notification(notification_data)

            event = result['event']
            payment_id = result['payment_id']
            status = result['status']
            metadata = result['metadata'] or {}

            logger.info(f"Processing webhook: event={event}, payment_id={payment_id}, status={status}")

            # Find transaction by YooKassa payment ID
            transaction = await self.supabase_client.get_transaction_by_yookassa_id(payment_id)

            if not transaction:
                logger.warning(f"Transaction not found for payment_id: {payment_id}")
                # Still return 200 to prevent YooKassa retries
                return web.Response(status=200, text="Transaction not found")

            # Handle different events
            if event == 'payment.succeeded':
                await self._handle_payment_success(transaction, result, metadata)

            elif event == 'payment.canceled':
                await self._handle_payment_canceled(transaction, result, metadata)

            elif event == 'payment.waiting_for_capture':
                await self._handle_payment_waiting(transaction, result, metadata)

            elif event == 'refund.succeeded':
                await self._handle_refund_success(transaction, result, metadata)

            else:
                logger.info(f"Unhandled event type: {event}")
                # Update status anyway
                await self.supabase_client.update_payment_transaction(
                    transaction.id,
                    {'status': status}
                )

            # Return 200 to acknowledge receipt
            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            # Return 500 so YooKassa will retry
            return web.Response(status=500, text="Internal Server Error")

    async def _handle_payment_success(self, transaction, result, metadata):
        """Handle successful payment"""
        try:
            # Update transaction in database
            update_data = {
                'status': 'succeeded',
                'paid_at': 'now()',
                'payment_method_type': result.get('payment_method_type'),
                'metadata': {**transaction.metadata, 'webhook_received': True}
            }

            await self.supabase_client.update_payment_transaction(
                transaction.id,
                update_data
            )

            telegram_id = transaction.telegram_id

            # Check if this is a lottery payment
            is_lottery = metadata.get('source') == 'lottery'

            if is_lottery:
                # ===== LOTTERY PAYMENT =====
                prize_id = metadata.get('prize_id', 'N/A')
                username = metadata.get('username', 'Не указан')

                # Send success message to USER
                message_text = (
                    f"✅ <b>Оплата успешно завершена!</b>\n\n"
                    f"<b>Сумма:</b> {result['amount']} {result['currency']}\n"
                    f"<b>Номер платежа:</b> <code>{result['payment_id']}</code>\n\n"
                    f"Поздравляем! Ваш приз ждет вас 🎁\n\n"
                    f"В ближайшее время с вами свяжется Анастасия для уточнения деталей."
                )

                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )

                logger.info(
                    f"Lottery payment success: transaction_id={transaction.id}, "
                    f"prize_id={prize_id}"
                )

                # Send notification to ADMINS
                from bot.config import Config
                admin_ids = Config.get_admin_ids()

                admin_notification = (
                    f"💰 <b>Новая оплата в лотерее!</b>\n\n"
                    f"<b>Пользователь:</b> @{username if username != 'Не указан' else 'username_not_set'}\n"
                    f"<b>Telegram ID:</b> <code>{telegram_id}</code>\n"
                    f"<b>Приз:</b> #{prize_id}\n"
                    f"<b>Сумма:</b> {result['amount']} {result['currency']}\n"
                    f"<b>Платёж ID:</b> <code>{result['payment_id']}</code>"
                )

                for admin_id in admin_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=admin_notification,
                            parse_mode="HTML"
                        )
                        logger.info(f"Admin notification sent to {admin_id} for lottery payment {result['payment_id']}")
                    except Exception as admin_error:
                        logger.error(f"Failed to send admin notification to {admin_id}: {admin_error}")

            else:
                # ===== REGULAR PAYMENT =====
                # Get product info
                product = await self.supabase_client.get_payment_product_by_id(transaction.product_id)
                product_name = product.name if product else "услуга"

                message_text = (
                    f"✅ <b>Платеж успешно завершен!</b>\n\n"
                    f"<b>Услуга:</b> {product_name}\n"
                    f"<b>Сумма:</b> {result['amount']} {result['currency']}\n"
                    f"<b>Номер платежа:</b> <code>{result['payment_id']}</code>\n\n"
                    f"Спасибо за оплату! 🙏"
                )

                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message_text,
                    parse_mode="HTML"
                )

                logger.info(f"Payment success notification sent: transaction_id={transaction.id}, telegram_id={telegram_id}")

        except Exception as e:
            logger.error(f"Error handling payment success: {e}", exc_info=True)

    async def _handle_payment_canceled(self, transaction, result, metadata):
        """Handle canceled payment"""
        try:
            # Update transaction
            await self.supabase_client.update_payment_transaction(
                transaction.id,
                {
                    'status': 'canceled',
                    'canceled_at': 'now()',
                    'metadata': {**transaction.metadata, 'webhook_received': True}
                }
            )

            # Notify user
            telegram_id = transaction.telegram_id
            message_text = (
                f"❌ <b>Платеж отменен</b>\n\n"
                f"<b>Номер платежа:</b> <code>{result['payment_id']}</code>\n\n"
                f"Если у вас возникли вопросы, обратитесь в поддержку."
            )

            await self.bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode="HTML"
            )

            logger.info(f"Payment canceled notification sent: transaction_id={transaction.id}")

        except Exception as e:
            logger.error(f"Error handling payment cancellation: {e}", exc_info=True)

    async def _handle_payment_waiting(self, transaction, result, metadata):
        """Handle payment waiting for capture"""
        try:
            # Update status
            await self.supabase_client.update_payment_transaction(
                transaction.id,
                {'status': 'waiting_for_capture'}
            )

            logger.info(f"Payment waiting for capture: transaction_id={transaction.id}")

        except Exception as e:
            logger.error(f"Error handling waiting payment: {e}", exc_info=True)

    async def _handle_refund_success(self, transaction, result, metadata):
        """Handle successful refund"""
        try:
            # Update transaction
            await self.supabase_client.update_payment_transaction(
                transaction.id,
                {
                    'status': 'refunded',
                    'metadata': {**transaction.metadata, 'refund_received': True}
                }
            )

            # Notify user
            telegram_id = transaction.telegram_id
            message_text = (
                f"💰 <b>Возврат средств выполнен</b>\n\n"
                f"<b>Сумма:</b> {result['amount']} {result['currency']}\n"
                f"<b>Номер платежа:</b> <code>{result['payment_id']}</code>\n\n"
                f"Средства будут зачислены на вашу карту в течение 3-5 рабочих дней."
            )

            await self.bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode="HTML"
            )

            logger.info(f"Refund notification sent: transaction_id={transaction.id}")

        except Exception as e:
            logger.error(f"Error handling refund: {e}", exc_info=True)

    async def start(self, host: str = '0.0.0.0', port: int = 8443):
        """
        Start webhook server

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to listen on (default: 8443)
        """
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Webhook server started on http://{host}:{port}")
        logger.info(f"Webhook endpoint: http://{host}:{port}/webhook/yookassa")
        logger.info(f"Health check: http://{host}:{port}/webhook/health")


async def run_webhook_server(bot: Bot, supabase_client: SupabaseClient):
    """
    Run webhook server as a background task

    Args:
        bot: Telegram Bot instance
        supabase_client: Supabase client instance
    """
    webhook_host = Config.WEBHOOK_HOST
    webhook_port = Config.WEBHOOK_PORT

    server = WebhookServer(bot, supabase_client)
    await server.start(host=webhook_host, port=webhook_port)

    # Keep running forever
    await asyncio.Event().wait()
