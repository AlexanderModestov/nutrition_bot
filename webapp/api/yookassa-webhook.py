"""
Vercel Serverless Function для обработки webhook от YooKassa
Endpoint: https://your-app.vercel.app/api/yookassa-webhook
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import logging
from urllib import request, parse

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# YooKassa IP ranges для проверки безопасности
YOOKASSA_IPS = [
    '185.71.76.0/27',
    '185.71.77.0/27',
    '77.75.153.0/25',
    '77.75.156.11',
    '77.75.156.35',
    '77.75.154.128/25',
    '2a02:5180::/32'
]


class handler(BaseHTTPRequestHandler):
    """Serverless handler для Vercel"""

    def do_POST(self):
        """Обработка POST запроса от YooKassa"""
        try:
            # Читаем тело запроса
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            notification_data = json.loads(body.decode('utf-8'))

            logger.info(f"Webhook received: {notification_data.get('event')}")

            # Извлекаем данные
            event = notification_data.get('event')
            payment_object = notification_data.get('object', {})

            payment_id = payment_object.get('id')
            status = payment_object.get('status')
            amount_value = payment_object.get('amount', {}).get('value', '0')
            currency = payment_object.get('amount', {}).get('currency', 'RUB')
            metadata = payment_object.get('metadata', {})
            payment_method = payment_object.get('payment_method', {})
            payment_method_type = payment_method.get('type', 'unknown')

            # Проверяем что это событие успешной оплаты
            if event != 'payment.succeeded':
                logger.info(f"Ignoring event: {event}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                return

            # Проверяем что это платеж из лотереи
            source = metadata.get('source')
            if source != 'lottery':
                logger.info(f"Not a lottery payment, ignoring")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                return

            # Извлекаем данные из metadata
            telegram_id = metadata.get('telegram_id')
            username = metadata.get('username', 'Не указан')
            prize_id = metadata.get('prize_id', 'N/A')

            if not telegram_id:
                logger.error("No telegram_id in metadata")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')
                return

            # Обновляем транзакцию в Supabase
            transaction = self._update_transaction(payment_id, status, payment_method_type)

            # Удаляем кнопку оплаты из сообщения с призом
            logger.info(f"Transaction received: {transaction}")
            if transaction:
                metadata = transaction.get('metadata', {})
                logger.info(f"Transaction metadata: {metadata}")
                prize_message_id = metadata.get('prize_message_id')
                logger.info(f"Prize message_id: {prize_message_id}")
                if prize_message_id:
                    self._remove_payment_button(telegram_id, prize_message_id)
                else:
                    logger.warning("No prize_message_id in transaction metadata")
            else:
                logger.warning("No transaction returned from _update_transaction")

            # Отправляем уведомление пользователю
            self._send_user_notification(telegram_id, amount_value, currency, payment_id)

            # Отправляем уведомления админам
            self._send_admin_notifications(telegram_id, username, prize_id, amount_value, currency, payment_id)

            # Возвращаем успех
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

            logger.info(f"Webhook processed successfully for payment {payment_id}")

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')

    def _update_transaction(self, payment_id, status, payment_method_type):
        """Обновляет статус транзакции в Supabase и возвращает транзакцию"""
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                logger.warning("Supabase credentials not configured")
                return None

            # Найти транзакцию по yookassa_payment_id
            url = f"{supabase_url}/rest/v1/payment_transactions?yookassa_payment_id=eq.{payment_id}"
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }

            req = request.Request(url, headers=headers, method='GET')
            with request.urlopen(req) as response:
                transactions = json.loads(response.read().decode('utf-8'))

            if not transactions:
                logger.warning(f"Transaction not found for payment_id: {payment_id}")
                return None

            transaction = transactions[0]
            transaction_id = transaction['id']

            # Обновить статус
            update_url = f"{supabase_url}/rest/v1/payment_transactions?id=eq.{transaction_id}"
            update_data = json.dumps({
                'status': status,
                'payment_method_type': payment_method_type,
                'paid_at': 'now()'
            }).encode('utf-8')

            update_req = request.Request(update_url, data=update_data, headers=headers, method='PATCH')
            with request.urlopen(update_req) as response:
                logger.info(f"Transaction {transaction_id} updated successfully")

            return transaction

        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            return None

    def _send_user_notification(self, telegram_id, amount, currency, payment_id):
        """Отправляет уведомление пользователю"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return

            message_text = (
                f"✅ <b>Оплата успешно завершена!</b>\n\n"
                f"<b>Сумма:</b> {amount} {currency}\n"
                f"<b>Номер платежа:</b> <code>{payment_id}</code>\n\n"
                f"Поздравляем! Ваш приз ждет вас 🎁\n\n"
                f"В ближайшее время с вами свяжется Анастасия для уточнения деталей."
            )

            self._send_telegram_message(bot_token, telegram_id, message_text)
            logger.info(f"User notification sent to {telegram_id}")

        except Exception as e:
            logger.error(f"Error sending user notification: {e}")

    def _send_admin_notifications(self, telegram_id, username, prize_id, amount, currency, payment_id):
        """Отправляет уведомления всем админам"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            admin_ids_str = os.getenv('TELEGRAM_ADMIN_IDS', '')

            if not bot_token or not admin_ids_str:
                logger.error("Bot token or admin IDs not configured")
                return

            admin_ids = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]

            message_text = (
                f"💰 <b>Новая оплата в лотерее!</b>\n\n"
                f"<b>Пользователь:</b> @{username if username != 'Не указан' else 'username_not_set'}\n"
                f"<b>Telegram ID:</b> <code>{telegram_id}</code>\n"
                f"<b>Приз:</b> #{prize_id}\n"
                f"<b>Сумма:</b> {amount} {currency}\n"
                f"<b>Платёж ID:</b> <code>{payment_id}</code>"
            )

            for admin_id in admin_ids:
                try:
                    self._send_telegram_message(bot_token, admin_id, message_text)
                    logger.info(f"Admin notification sent to {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send admin notification to {admin_id}: {e}")

        except Exception as e:
            logger.error(f"Error sending admin notifications: {e}")

    def _send_telegram_message(self, bot_token, chat_id, text):
        """Отправляет сообщение через Telegram Bot API"""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        data = json.dumps({
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }).encode('utf-8')

        headers = {
            'Content-Type': 'application/json'
        }

        req = request.Request(url, data=data, headers=headers, method='POST')
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            if not result.get('ok'):
                raise Exception(f"Telegram API error: {result}")

    def _remove_payment_button(self, chat_id, message_id):
        """Удаляет кнопку оплаты из сообщения с призом"""
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return

            url = f"https://api.telegram.org/bot{bot_token}/editMessageReplyMarkup"

            data = json.dumps({
                'chat_id': chat_id,
                'message_id': int(message_id),
                'reply_markup': {'inline_keyboard': []}  # Пустая клавиатура = удаление кнопок
            }).encode('utf-8')

            headers = {
                'Content-Type': 'application/json'
            }

            req = request.Request(url, data=data, headers=headers, method='POST')
            with request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    logger.info(f"Payment button removed from message {message_id}")
                else:
                    logger.warning(f"Failed to remove button: {result}")

        except Exception as e:
            logger.error(f"Error removing payment button: {e}")

    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({'status': 'ok', 'service': 'yookassa-webhook'})
        self.wfile.write(response.encode('utf-8'))
