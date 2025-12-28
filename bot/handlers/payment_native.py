import logging
from decimal import Decimal
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from bot.services.yookassa_service import YooKassaService
from bot.config import Config
from .payment_states import PaymentStates

logger = logging.getLogger(__name__)

# Create router for native payment handlers
payment_native_router = Router()

@payment_native_router.message(Command('pay'))
async def cmd_pay_native(message: types.Message, state: FSMContext, supabase_client):
    """
    /pay command - show available payment products with Telegram native payments
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
                    callback_data=f"pay_native_{product.id}"
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


@payment_native_router.callback_query(F.data.startswith('pay_native_'))
async def handle_native_payment(callback_query: types.CallbackQuery, state: FSMContext, supabase_client):
    """
    Send Telegram native invoice for payment
    """
    try:
        product_id = int(callback_query.data.split('_')[2])

        # Get product details
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
            'product_name': product.name,
            'idempotence_key': idempotence_key
        }

        # Create payment in YooKassa (to get payment_id for tracking)
        payment_result = yookassa_service.create_payment(
            amount=product.price_amount,
            currency=product.price_currency,
            description=f"Оплата: {product.name}",
            metadata=metadata,
            idempotence_key=idempotence_key
        )

        # Save transaction to database with pending status
        transaction_data = {
            'user_id': user.id if user else None,
            'telegram_id': callback_query.from_user.id,
            'product_id': product.id,
            'yookassa_payment_id': payment_result['payment_id'],
            'idempotence_key': idempotence_key,
            'amount': float(product.price_amount),
            'currency': product.price_currency,
            'status': 'pending',
            'confirmation_url': payment_result['confirmation_url'],
            'confirmation_type': 'telegram_invoice',
            'metadata': metadata
        }

        transaction = await supabase_client.create_payment_transaction(transaction_data)

        if not transaction:
            await callback_query.message.edit_text(
                "❌ Ошибка при создании платежа. Попробуйте позже."
            )
            await state.clear()
            return

        # Store transaction info in state for pre-checkout validation
        await state.update_data(
            transaction_id=transaction.id,
            payment_id=payment_result['payment_id'],
            product_id=product.id
        )

        # Convert price to kopecks (smallest currency unit)
        # For RUB: 1 RUB = 100 kopecks
        price_in_kopecks = int(product.price_amount * 100)

        # Send Telegram invoice (native payment)
        await callback_query.message.answer_invoice(
            title=product.name,
            description=product.description or f"Оплата услуги: {product.name}",
            payload=f"{transaction.id}:{payment_result['payment_id']}",  # transaction_id:yookassa_payment_id
            provider_token=Config.YOOKASSA_PROVIDER_TOKEN,
            currency=product.price_currency,
            prices=[LabeledPrice(label=product.name, amount=price_in_kopecks)],
            start_parameter=f"pay-{product.id}",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )

        await state.set_state(PaymentStates.awaiting_payment)
        await callback_query.answer("Счет на оплату отправлен!")

        logger.info(f"Native invoice sent: user_id={callback_query.from_user.id}, payment_id={payment_result['payment_id']}, amount={product.price_amount}")

    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await callback_query.message.edit_text(
            "❌ Произошла ошибка при создании счета.\n"
            "Попробуйте позже или свяжитесь с поддержкой."
        )
        await state.clear()


@payment_native_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, state: FSMContext, supabase_client):
    """
    Handle pre-checkout validation before payment is processed
    This is required by Telegram before processing the payment
    """
    try:
        logger.info(f"Pre-checkout query: user_id={pre_checkout_query.from_user.id}, payload={pre_checkout_query.invoice_payload}")

        # Parse payload: transaction_id:yookassa_payment_id
        payload_parts = pre_checkout_query.invoice_payload.split(':')
        if len(payload_parts) != 2:
            await pre_checkout_query.answer(ok=False, error_message="Неверный формат платежа")
            return

        transaction_id = int(payload_parts[0])
        yookassa_payment_id = payload_parts[1]

        # Verify transaction exists and is pending
        transaction = await supabase_client.get_transaction_by_id(transaction_id)
        if not transaction:
            await pre_checkout_query.answer(ok=False, error_message="Транзакция не найдена")
            return

        if transaction.status not in ['pending', 'waiting_for_capture']:
            await pre_checkout_query.answer(ok=False, error_message=f"Платеж имеет статус: {transaction.status}")
            return

        # Verify payment amount matches
        expected_amount = int(transaction.amount * 100)  # Convert to kopecks
        if pre_checkout_query.total_amount != expected_amount:
            await pre_checkout_query.answer(ok=False, error_message="Сумма платежа не совпадает")
            return

        # All checks passed - approve the payment
        await pre_checkout_query.answer(ok=True)
        logger.info(f"Pre-checkout approved: transaction_id={transaction_id}")

    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Ошибка проверки платежа")


@payment_native_router.message(F.successful_payment)
async def process_successful_payment(message: types.Message, state: FSMContext, supabase_client):
    """
    Handle successful payment notification from Telegram
    This is called AFTER Telegram processes the payment
    """
    try:
        payment_info = message.successful_payment
        logger.info(f"Successful payment received: user_id={message.from_user.id}, payload={payment_info.invoice_payload}")

        # Parse payload: transaction_id:yookassa_payment_id
        payload_parts = payment_info.invoice_payload.split(':')
        if len(payload_parts) != 2:
            logger.error(f"Invalid payload format: {payment_info.invoice_payload}")
            return

        transaction_id = int(payload_parts[0])
        yookassa_payment_id = payload_parts[1]

        # Get transaction
        transaction = await supabase_client.get_transaction_by_id(transaction_id)
        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            await message.answer("⚠️ Транзакция не найдена. Обратитесь в поддержку.")
            return

        # Store Telegram payment info
        telegram_payment_metadata = {
            'telegram_payment_charge_id': payment_info.telegram_payment_charge_id,
            'provider_payment_charge_id': payment_info.provider_payment_charge_id,
            'total_amount': payment_info.total_amount,
            'currency': payment_info.currency
        }

        # Update transaction status to succeeded
        update_data = {
            'status': 'succeeded',
            'paid_at': 'now()',
            'payment_method_type': 'telegram_native',
            'metadata': {**transaction.metadata, 'telegram_payment': telegram_payment_metadata}
        }

        await supabase_client.update_payment_transaction(transaction_id, update_data)

        # Get product for confirmation message
        product = await supabase_client.get_payment_product_by_id(transaction.product_id)
        product_name = product.name if product else "услуга"

        # Send success message
        await message.answer(
            f"✅ <b>Платеж успешно завершен!</b>\n\n"
            f"<b>Услуга:</b> {product_name}\n"
            f"<b>Сумма:</b> {transaction.amount} {transaction.currency}\n"
            f"<b>Номер платежа:</b> <code>{yookassa_payment_id}</code>\n\n"
            f"Спасибо за оплату! 🙏",
            parse_mode="HTML"
        )

        await state.clear()

        logger.info(f"Payment processed successfully: transaction_id={transaction_id}, yookassa_id={yookassa_payment_id}")

    except Exception as e:
        logger.error(f"Error processing successful payment: {e}")
        await message.answer(
            "⚠️ Платеж получен, но произошла ошибка при обработке.\n"
            "Обратитесь в поддержку для подтверждения."
        )


@payment_native_router.message(Command('check_payment'))
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


@payment_native_router.message(Command('my_payments'))
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
