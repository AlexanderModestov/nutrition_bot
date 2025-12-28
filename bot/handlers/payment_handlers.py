import logging
from decimal import Decimal
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from bot.services.yookassa_service import YooKassaService
from bot.config import Config
from .payment_states import PaymentStates
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

# Create router for payment handlers
payment_router = Router()

@payment_router.message(Command('pay'))
async def cmd_pay(message: types.Message, state: FSMContext, supabase_client):
    """
    /pay command - show available payment products
    """
    try:
        # Get active products from database
        products = await supabase_client.get_active_payment_products()

        if not products:
            await message.answer(
                "В данный момент нет доступных услуг для оплаты.\n"
                "Попробуйте позже или свяжитесь с администратором."
            )
            return

        # Create inline keyboard with products
        keyboard_buttons = []
        for product in products:
            button_text = f"{product.name} - {product.price_amount} ₽"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"pay_product_{product.id}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await message.answer(
            "💳 <b>Оплата услуг</b>\n\n"
            "Выберите услугу для оплаты:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.set_state(PaymentStates.selecting_product)

    except Exception as e:
        logger.error(f"Error in /pay command: {e}")
        await message.answer("Произошла ошибка при загрузке услуг. Попробуйте позже.")

@payment_router.callback_query(F.data.startswith('pay_product_'))
async def handle_product_selection(callback_query: types.CallbackQuery, state: FSMContext, supabase_client):
    """
    Handle product selection
    """
    try:
        product_id = int(callback_query.data.split('_')[2])

        # Get product details
        product = await supabase_client.get_payment_product_by_id(product_id)

        if not product:
            await callback_query.answer("Услуга не найдена")
            return

        # Store product in state
        await state.update_data(selected_product_id=product_id)

        # Create confirmation keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Оплатить", callback_data=f"confirm_payment_{product_id}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment")
            ]
        ])

        product_details = (
            f"💳 <b>Подтверждение оплаты</b>\n\n"
            f"<b>Услуга:</b> {product.name}\n"
        )

        if product.description:
            product_details += f"<b>Описание:</b> {product.description}\n"

        product_details += (
            f"\n<b>Стоимость:</b> {product.price_amount} {product.price_currency}\n\n"
            f"Нажмите 'Оплатить' для продолжения."
        )

        await callback_query.message.edit_text(
            product_details,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.set_state(PaymentStates.confirming_payment)
        await callback_query.answer()

    except Exception as e:
        logger.error(f"Error in product selection: {e}")
        await callback_query.answer("Произошла ошибка")

@payment_router.callback_query(F.data.startswith('confirm_payment_'))
async def handle_payment_confirmation(callback_query: types.CallbackQuery, state: FSMContext, supabase_client):
    """
    Create payment and redirect to YooKassa
    """
    try:
        product_id = int(callback_query.data.split('_')[2])

        # Get product
        product = await supabase_client.get_payment_product_by_id(product_id)
        if not product:
            await callback_query.answer("Услуга не найдена")
            return

        # Get or create user
        user = await supabase_client.get_user_by_telegram_id(callback_query.from_user.id)
        if not user:
            user_data = {
                'telegram_id': callback_query.from_user.id,
                'username': callback_query.from_user.username
            }
            user = await supabase_client.create_or_update_user(user_data)

        # Initialize YooKassa service
        yookassa_service = YooKassaService()

        # Generate idempotence key
        idempotence_key = yookassa_service.generate_idempotence_key()

        # Create payment metadata
        metadata = {
            'telegram_id': str(callback_query.from_user.id),
            'username': callback_query.from_user.username or '',
            'product_id': str(product.id),
            'product_name': product.name
        }

        # Create embedded payment in YooKassa (for WebApp widget)
        payment_result = yookassa_service.create_embedded_payment(
            amount=product.price_amount,
            currency=product.price_currency,
            description=f"Оплата: {product.name}",
            metadata=metadata,
            idempotence_key=idempotence_key
        )

        # Save transaction to database
        transaction_data = {
            'user_id': user.id if user else None,
            'telegram_id': callback_query.from_user.id,
            'product_id': product.id,
            'yookassa_payment_id': payment_result['payment_id'],
            'idempotence_key': idempotence_key,
            'amount': float(product.price_amount),
            'currency': product.price_currency,
            'status': payment_result['status'],
            'confirmation_url': payment_result.get('confirmation_token'),  # Store token for embedded payments
            'confirmation_type': payment_result['confirmation_type'],
            'metadata': metadata
        }

        transaction = await supabase_client.create_payment_transaction(transaction_data)

        if not transaction:
            await callback_query.message.edit_text(
                "❌ Ошибка при создании платежа. Попробуйте позже."
            )
            await state.clear()
            return

        # Create WebApp payment button
        webapp_params = urlencode({
            'payment_id': payment_result['confirmation_token'],  # Pass confirmation token for widget
            'product_name': product.name,
            'product_description': product.description or '',
            'amount': str(product.price_amount),
            'currency': product.price_currency,
            'return_url': Config.YOOKASSA_RETURN_URL  # Return URL after payment
        })

        webapp_url = f"{Config.WEBAPP_URL}/payment?{webapp_params}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💳 Оплатить",
                web_app=WebAppInfo(url=webapp_url)
            )],
            [InlineKeyboardButton(
                text="❌ Отменить платеж",
                callback_data=f"cancel_payment_{transaction.id}"
            )]
        ])

        await callback_query.message.edit_text(
            f"✅ <b>Платеж создан</b>\n\n"
            f"<b>Номер платежа:</b> <code>{payment_result['payment_id']}</code>\n"
            f"<b>Сумма:</b> {product.price_amount} {product.price_currency}\n\n"
            f"Нажмите кнопку ниже для перехода на страницу оплаты.\n"
            f"После оплаты вернитесь в бот для получения подтверждения.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(
            transaction_id=transaction.id,
            payment_id=payment_result['payment_id']
        )
        await state.set_state(PaymentStates.awaiting_payment)
        await callback_query.answer("Платеж создан успешно!")

        logger.info(f"Payment created: user_id={callback_query.from_user.id}, payment_id={payment_result['payment_id']}, amount={product.price_amount}")

    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        await callback_query.message.edit_text(
            "❌ Произошла ошибка при создании платежа.\n"
            "Попробуйте позже или свяжитесь с поддержкой."
        )
        await state.clear()

@payment_router.callback_query(F.data == 'cancel_payment')
async def handle_payment_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    """Cancel payment flow"""
    await callback_query.message.edit_text("❌ Оплата отменена")
    await state.clear()
    await callback_query.answer()

@payment_router.callback_query(F.data.startswith('cancel_payment_'))
async def handle_active_payment_cancel(callback_query: types.CallbackQuery, state: FSMContext, supabase_client):
    """Cancel active payment"""
    try:
        transaction_id = int(callback_query.data.split('_')[2])

        # Get transaction
        transaction = await supabase_client.get_transaction_by_id(transaction_id)
        if not transaction:
            await callback_query.answer("Транзакция не найдена")
            return

        # Initialize YooKassa service
        yookassa_service = YooKassaService()

        # Check current status in YooKassa first
        try:
            payment_status = yookassa_service.get_payment_status(transaction.yookassa_payment_id)
            current_status = payment_status['status']

            # Update our database with current status
            if current_status != transaction.status:
                await supabase_client.update_payment_transaction(transaction_id, {
                    'status': current_status
                })

            # Check if payment can be canceled
            if current_status == 'succeeded':
                await callback_query.answer("Платеж уже выполнен, отмена невозможна", show_alert=True)
                await callback_query.message.edit_text(
                    "✅ Платеж уже успешно выполнен.\n"
                    "Если нужен возврат, обратитесь в поддержку."
                )
                await state.clear()
                return
            elif current_status == 'canceled':
                await callback_query.answer("Платеж уже отменен")
                await callback_query.message.edit_text("❌ Платеж уже отменен")
                await state.clear()
                return
            elif current_status != 'pending':
                await callback_query.answer(f"Платеж в статусе '{current_status}', отмена невозможна", show_alert=True)
                return

        except Exception as status_error:
            logger.error(f"Error checking payment status: {status_error}")
            # If we can't check status, try to cancel anyway
            pass

        # Only cancel if payment is still pending
        if transaction.status not in ['pending', 'waiting_for_capture']:
            await callback_query.answer("Платеж не может быть отменен в текущем статусе")
            return

        # Attempt to cancel in YooKassa
        try:
            yookassa_service.cancel_payment(transaction.yookassa_payment_id)

            # Update transaction
            await supabase_client.update_payment_transaction(transaction_id, {
                'status': 'canceled',
                'canceled_at': 'now()'
            })

            await callback_query.message.edit_text("❌ Платеж успешно отменен")
            await state.clear()
            await callback_query.answer("Платеж отменен")

        except Exception as cancel_error:
            error_msg = str(cancel_error)

            # Handle specific YooKassa errors
            if 'capture = true' in error_msg or 'can\'t cancel' in error_msg:
                await callback_query.answer("Платеж нельзя отменить. Закройте окно оплаты или дождитесь истечения времени", show_alert=True)
                await callback_query.message.edit_text(
                    "⚠️ <b>Платеж нельзя отменить напрямую</b>\n\n"
                    "Чтобы отменить платеж:\n"
                    "1. Закройте окно оплаты YooKassa, не завершая оплату\n"
                    "2. Платеж автоматически отменится через 15 минут\n"
                    "3. Используйте /check_payment для проверки статуса",
                    parse_mode="HTML"
                )
            else:
                await callback_query.answer("Не удалось отменить платеж")
                await callback_query.message.edit_text(
                    f"⚠️ Ошибка при отмене платежа.\n\n"
                    f"Попробуйте закрыть окно оплаты или дождитесь автоматической отмены."
                )

            await state.clear()

    except Exception as e:
        logger.error(f"Error canceling payment: {e}")
        await callback_query.answer("Произошла ошибка при отмене платежа")

@payment_router.message(Command('check_payment'))
async def cmd_check_payment(message: types.Message, supabase_client):
    """
    Check payment status manually
    """
    try:
        # Get last pending transaction
        transactions = await supabase_client.get_user_transactions(message.from_user.id, limit=5)

        pending_transactions = [tx for tx in transactions if tx.status == 'pending']

        if not pending_transactions:
            await message.answer("У вас нет активных платежей")
            return

        yookassa_service = YooKassaService()

        for transaction in pending_transactions:
            # Check status in YooKassa
            payment_status = yookassa_service.get_payment_status(transaction.yookassa_payment_id)

            # Update if status changed
            if payment_status['status'] != transaction.status:
                update_data = {'status': payment_status['status']}

                if payment_status['paid']:
                    update_data['paid_at'] = payment_status['paid_at']
                    update_data['payment_method_type'] = payment_status['payment_method']

                await supabase_client.update_payment_transaction(transaction.id, update_data)

                if payment_status['status'] == 'succeeded':
                    await message.answer(
                        f"✅ <b>Платеж успешно завершен!</b>\n\n"
                        f"<b>Номер платежа:</b> <code>{transaction.yookassa_payment_id}</code>\n"
                        f"<b>Сумма:</b> {transaction.amount} {transaction.currency}\n\n"
                        f"Спасибо за оплату!",
                        parse_mode="HTML"
                    )
                elif payment_status['status'] == 'canceled':
                    await message.answer(
                        f"❌ Платеж отменен\n\n"
                        f"<b>Номер платежа:</b> <code>{transaction.yookassa_payment_id}</code>",
                        parse_mode="HTML"
                    )

    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await message.answer("Ошибка при проверке статуса платежа")

@payment_router.message(Command('my_payments'))
async def cmd_my_payments(message: types.Message, supabase_client):
    """
    Show user's payment history
    """
    try:
        transactions = await supabase_client.get_user_transactions(message.from_user.id, limit=10)

        if not transactions:
            await message.answer("У вас пока нет платежей")
            return

        status_emoji = {
            'pending': '⏳',
            'succeeded': '✅',
            'canceled': '❌',
            'failed': '⚠️'
        }

        history_text = "💳 <b>История платежей</b>\n\n"

        for tx in transactions:
            emoji = status_emoji.get(tx.status, '❓')
            history_text += (
                f"{emoji} <b>{tx.amount} {tx.currency}</b>\n"
                f"   Статус: {tx.status}\n"
                f"   Дата: {tx.created_at.strftime('%d.%m.%Y %H:%M') if tx.created_at else 'N/A'}\n"
                f"   ID: <code>{tx.yookassa_payment_id}</code>\n\n"
            )

        await message.answer(history_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error showing payment history: {e}")
        await message.answer("Ошибка при загрузке истории платежей")

@payment_router.message(F.web_app_data)
async def handle_webapp_data(message: types.Message, supabase_client):
    """
    Handle data from WebApp (payment completion)
    """
    try:
        import json
        data = json.loads(message.web_app_data.data)

        logger.info(f"WebApp data received: {data}")

        payment_id = data.get('payment_id')
        status = data.get('status')

        if not payment_id:
            await message.answer("⚠️ Некорректные данные от WebApp")
            return

        # Get transaction
        transaction = await supabase_client.get_transaction_by_yookassa_id(payment_id)

        if not transaction:
            await message.answer("⚠️ Транзакция не найдена")
            return

        if status == 'success':
            # Payment completed successfully
            yookassa_service = YooKassaService()
            payment_status = yookassa_service.get_payment_status(payment_id)

            # Update transaction
            update_data = {'status': payment_status['status']}

            if payment_status['paid']:
                update_data['paid_at'] = payment_status['paid_at']
                update_data['payment_method_type'] = payment_status['payment_method']

            await supabase_client.update_payment_transaction(transaction.id, update_data)

            await message.answer(
                f"✅ <b>Платеж успешно завершен!</b>\n\n"
                f"<b>Номер платежа:</b> <code>{payment_id}</code>\n"
                f"<b>Сумма:</b> {transaction.amount} {transaction.currency}\n\n"
                f"Спасибо за оплату!",
                parse_mode="HTML"
            )

        elif status == 'error':
            error_msg = data.get('error', 'Unknown error')
            logger.error(f"Payment error from WebApp: {error_msg}")

            await message.answer(
                f"❌ <b>Ошибка при оплате</b>\n\n"
                f"Платеж не был завершен. Попробуйте снова или обратитесь в поддержку.\n\n"
                f"<b>Номер платежа:</b> <code>{payment_id}</code>",
                parse_mode="HTML"
            )

        elif status == 'canceled':
            # User canceled payment in WebApp
            await supabase_client.update_payment_transaction(transaction.id, {
                'status': 'canceled',
                'canceled_at': 'now()'
            })

            await message.answer(
                f"❌ Платеж отменен\n\n"
                f"<b>Номер платежа:</b> <code>{payment_id}</code>",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error handling WebApp data: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке данных оплаты")
