"""
Новогодняя Лотерея - модуль для игрового функционала бота.

Триггеры:
- Команда /game
- Текст "🎄 Испытать удачу"
"""

import logging
import random
import json
import os
from pathlib import Path
from enum import Enum
from typing import Optional, Set, Dict
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import BaseModel, Field

from bot.services.yookassa_service import YooKassaService
from bot.config import Config


# Configure logging
logger = logging.getLogger(__name__)

# Create router
lottery_router = Router()

# Base path for cards (using os.path.join as per requirements)
CARDS_DIR = os.path.join(os.getcwd(), 'bot', 'cards')

# Path to participants storage (temporary file for the campaign)
PARTICIPANTS_FILE = os.path.join(os.getcwd(), 'bot', 'lottery_participants.json')


class LotteryParticipants:
    """Управление участниками лотереи (временное хранилище)"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._participants: Set[int] = self._load()

    def _load(self) -> Set[int]:
        """Загрузить список участников из файла"""
        if not os.path.exists(self.file_path):
            return set()

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('participants', []))
        except Exception as e:
            logger.error(f"Error loading participants file: {e}")
            return set()

    def _save(self):
        """Сохранить список участников в файл"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({'participants': list(self._participants)}, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving participants file: {e}")

    def has_participated(self, telegram_id: int) -> bool:
        """Проверить, участвовал ли пользователь"""
        return telegram_id in self._participants

    def add_participant(self, telegram_id: int):
        """Добавить пользователя в список участников"""
        self._participants.add(telegram_id)
        self._save()
        logger.info(f"User {telegram_id} added to lottery participants")

    def get_total_participants(self) -> int:
        """Получить общее количество участников"""
        return len(self._participants)


# Initialize participants manager
participants_manager = LotteryParticipants(PARTICIPANTS_FILE)


class PrizeType(str, Enum):
    """Типы призов"""
    LINK = "link"
    FILE = "file"
    PAYMENT_FLOW = "payment_flow"  # Платные услуги с анкетой


class Button(BaseModel):
    """Модель кнопки"""
    text: str = Field(..., description="Текст на кнопке")
    url: Optional[str] = Field(None, description="URL ссылки (для обычных кнопок)")


class Prize(BaseModel):
    """Модель приза лотереи"""
    id: int = Field(..., description="Уникальный ID приза")
    image: str = Field(..., description="Имя файла картинки (в папке cards/)")
    caption: str = Field(..., description="Описание приза (поддерживает HTML)")
    type: PrizeType = Field(..., description="Тип приза")

    # Для типа FILE
    payload: Optional[str] = Field(None, description="file_id для документов")

    # Для типа PAYMENT_FLOW
    price: Optional[Decimal] = Field(None, description="Цена услуги (для платных призов)")
    currency: Optional[str] = Field("RUB", description="Валюта")
    form_url: Optional[str] = Field(None, description="URL анкеты (отправляется после оплаты)")

    # Кнопки
    primary_btn: Optional[Button] = Field(None, description="Основная кнопка (Оплатить/Написать/Скачать)")
    secondary_btn: Optional[Button] = Field(None, description="Дополнительная кнопка (Анкета)")

    class Config:
        use_enum_values = True


# Конфигурация призов
PRIZES = [
    # Prize 1: 3 вопроса по питанию
    Prize(
        id=1,
        image="prize_1.jpg",
        caption=(
            "🎁 <b>Поздравляем!</b>\n\n"
            "Вы выиграли возможность задать <b>3 вопроса по питанию</b> Анастасии Шарковой!\n\n"
            "Получите персональные ответы на ваши наболевшие вопросы 💬"
        ),
        type=PrizeType.LINK,
        primary_btn=Button(text="✍️ Написать Анастасии", url="https://t.me/sharkova_na")
    ),

    # Prize 2: Наставничество со скидкой
    Prize(
        id=2,
        image="prize_2.jpg",
        caption=(
            "🏆 <b>Главный куш!</b>\n\n"
            "Вы получили <b>скидку на программу наставничества</b> от Анастасии Шарковой!\n\n"
            "Это ваш шанс начать путь к здоровому образу жизни с персональной поддержкой 🌟\n\n"
            "➡️ Забронируйте скидку и заполните анкету для начала работы."
        ),
        type=PrizeType.PAYMENT_FLOW,
        price=Decimal("1"),  # Символическая цена для бронирования (или реальная цена со скидкой)
        currency="RUB",
        form_url="https://forms.gle/YOUR_MENTORSHIP_FORM_ID",  # Замените на реальную форму
        primary_btn=Button(text="🎯 Забронировать скидку")  # URL создается динамически
    ),

    # Prize 3: Сборник десертов (FILE)
    Prize(
        id=3,
        image="prize_3.jpg",
        caption=(
            "✨ Секрет вкусного Нового Года и праздников без чувства вины!\n\n"
            "В вашем выигрыше — не просто сборник, а готовое меню из 10 праздничных десертов, "
            "печенья, запеканки, кексы. Теперь ваш стол будет самым красивым, полезным и безопасным для фигуры.\n\n"
            "Файл можно скачать ниже."
        ),
        type=PrizeType.FILE,
        payload="Новогодние десерты _ Шаркова Диетолог.pdf"
    ),

    # Prize 4: Аудио-консультация 990₽ (PAYMENT_FLOW)
    Prize(
        id=4,
        image="prize_4.jpg",
        caption=(
            "🎧 <b>Аудио-консультация всего за 990₽!</b>\n\n"
            "Полноценный разбор вашего запроса, но в формате удобного аудио. "
            "Слушайте в машине, на прогулке или за чаем — когда вам комфортно.\n\n"
            "➡️ Кликайте «Записаться за 990₽», чтобы оплатить и получить анкету для аудио-консультации."
        ),
        type=PrizeType.PAYMENT_FLOW,
        price=Decimal("990"),
        currency="RUB",
        form_url="https://forms.gle/YOUR_AUDIO_CONSULT_FORM?entry.telegram_id={telegram_id}",  # Замените
        primary_btn=Button(text="🎤 Записаться за 990₽")  # URL создается динамически
    ),

    # Prize 5: Чек-лист 10 шагов (FILE)
    Prize(
        id=5,
        image="prize_5.jpg",
        caption=(
            "Вам выпал не просто чек-лист, а понятный план из 10 шагов, который заменит тонну запутанной информации от разных экспертов. "
            "Можно применять уже сейчас.\n\n"
            "Чек-лист можно скачать ниже."
        ),
        type=PrizeType.FILE,
        payload="10 шагов к осознанному питанию.pdf"
    ),

    # Prize 6: Меню на Новый год (FILE)
    Prize(
        id=6,
        image="prize_6.jpg",
        caption=(
            "🎇 Встречайте 2026 год вкусно и легко!\n\n"
            "Ваш выигрыш — не просто список блюд. Это готовое праздничное меню с точными рецептами. "
            "Я включила совершенно разные позиции, и построенные на принципах диетической кулинарии, "
            "и самые что ни на есть питательные :)\n\n"
            "Порадуйте себя и близких!\n\n"
            "Рецепты можно скачать ниже."
        ),
        type=PrizeType.FILE,
        payload="Новогоднее меню 2026.pdf"
    ),

    # Prize 7: Срочный вопрос
    Prize(
        id=7,
        image="prize_7.jpg",
        caption=(
            "Задайте свой наболевший вопрос по питанию и получите ясный и персональный ответ от меня. "
            "Я разберу именно вашу ситуацию и дам направление. Срок ответа — 2 дня.\n\n"
            "➡️ Жмите «Задать срочный вопрос», чтобы написать мне и получить разбор в формате аудио!"
        ),
        type=PrizeType.LINK,
        primary_btn=Button(text="💬 Задать срочный вопрос", url="https://t.me/sharkova_na")
    ),

    # Prize 8: Идеальный день питания
    Prize(
        id=8,
        image="prize_8.jpg",
        caption=(
            "✨ Попробуйте «идеальный день» в питании — созданный лично для вас. "
            "Вы выиграли пример меню на день с учётом ваших «не люблю». "
            "Скажите, что вы не едите, и я подберу вкусную и полезную альтернативу в каждом приёме пищи.\n\n"
            "➡️ Жмите «Составить мой день» и напишите мне 2-3 продукта, которые избегаете. "
            "Я отправлю ваш персональный план в течение 24 часов."
        ),
        type=PrizeType.LINK,
        primary_btn=Button(text="🍽️ Составить мой день", url="https://t.me/sharkova_na")
    ),
]


def get_start_keyboard():
    """Создает клавиатуру для стартового сообщения"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎰 Крутить колесо удачи", callback_data="start_lottery")
    return builder.as_markup()


def get_prize_keyboard(prize: Prize, payment_url: Optional[str] = None):
    """
    Создает клавиатуру для приза

    Args:
        prize: Объект приза
        payment_url: URL для оплаты (для типа PAYMENT_FLOW)

    Returns:
        InlineKeyboardMarkup или None
    """
    builder = InlineKeyboardBuilder()

    # Добавляем основную кнопку
    if prize.primary_btn:
        if prize.type == PrizeType.PAYMENT_FLOW and payment_url:
            # Для платежа используем динамически созданный URL
            builder.button(text=prize.primary_btn.text, url=payment_url)
        elif prize.primary_btn.url:
            # Для обычных ссылок используем URL из модели
            builder.button(text=prize.primary_btn.text, url=prize.primary_btn.url)

    # Добавляем дополнительную кнопку (если есть)
    if prize.secondary_btn and prize.secondary_btn.url:
        builder.button(text=prize.secondary_btn.text, url=prize.secondary_btn.url)

    builder.adjust(1)  # По одной кнопке в ряд

    # Возвращаем клавиатуру или None если нет кнопок
    return builder.as_markup() if builder.export() else None


async def send_image_with_fallback(
    message_or_query,
    image_path: str,
    caption: str,
    reply_markup=None
) -> Optional[Message]:
    """
    Отправляет изображение с fallback на текст, если файл не найден.

    Args:
        message_or_query: Message или CallbackQuery объект
        image_path: Путь к изображению (строка)
        caption: Подпись к изображению
        reply_markup: Клавиатура

    Returns:
        Отправленное сообщение или None
    """
    # Определяем, что пришло - Message или CallbackQuery
    if isinstance(message_or_query, CallbackQuery):
        message = message_or_query.message
        is_callback = True
    else:
        message = message_or_query
        is_callback = False

    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        photo = FSInputFile(image_path)

        if is_callback:
            # Для callback удаляем старое сообщение и отправляем новое
            await message.delete()
            return await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            return await message.answer_photo(
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    except FileNotFoundError as e:
        logger.warning(f"Image file not found: {image_path}. Sending text only. Error: {e}")

        if is_callback:
            await message.delete()
            return await message.answer(
                text=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            return await message.answer(
                text=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error sending image {image_path}: {e}")

        if is_callback:
            await message.delete()
            return await message.answer(
                text=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        else:
            return await message.answer(
                text=caption,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )


@lottery_router.message(Command("game"))
async def cmd_game(message: Message):
    """Обработчик команды /game"""
    await show_lottery_start(message)


@lottery_router.message(F.text == "🎄 Испытать удачу")
async def msg_test_luck(message: Message):
    """Обработчик текстового сообщения '🎄 Испытать удачу'"""
    await show_lottery_start(message)


async def show_lottery_start(message: Message):
    """
    Показывает стартовое меню лотереи.

    Args:
        message: Объект сообщения
    """
    # Проверяем, участвовал ли пользователь ранее
    if participants_manager.has_participated(message.from_user.id):
        logger.info(f"User {message.from_user.id} tried to participate again (already participated)")
        await message.answer(
            "❌ Вы уже участвовали в Новогодней Лотерее!\n\n"
            "Каждый пользователь может участвовать только один раз. 🎁\n\n"
            "Надеемся, вам понравился ваш приз! 🎄"
        )
        return

    start_image_path = os.path.join(CARDS_DIR, "start.jpg")

    welcome_text = (
        "Это беспроигрышная лотерея! Скорее нажимайте на кнопку \"Крутить колесо удачи\" "
        "и узнайте, что вам выпадет.\n\n"
        "Среди призов — мои полезные материалы и услуги для вашего здоровья и вкусного праздника. "
        "До конца не буду раскрывать все карточки, но про парочку расскажу ;)\n\n"
        "🧁 Рецепты\n"
        "🎙️ Секретная консультация\n"
        "📋 Полезные чек-листы\n"
        "❓ Вопрос-ответ\n"
        "🥗 Меню на пробу с учётом ваших пожеланий\n"
        "🏆 Главный приз (приятная скидка на услугу)\n\n"
        "Каждый приз — это физическая карточка с уникальным дизайном, которую вы получите после розыгрыша. "
        "Она станет не только напоминанием о подарке, но и приятным новогодним сувениром!\n\n"
        "Крутите колесо и забирайте свой подарок — без шанса проиграть! 🎄✨"
    )

    keyboard = get_start_keyboard()

    await send_image_with_fallback(
        message_or_query=message,
        image_path=start_image_path,
        caption=welcome_text,
        reply_markup=keyboard
    )

    logger.info(f"User {message.from_user.id} started lottery")


async def create_lottery_payment(
    telegram_id: int,
    username: Optional[str],
    prize: Prize
) -> Optional[str]:
    """
    Создает платеж для приза лотереи

    Args:
        telegram_id: ID пользователя в Telegram
        username: Username пользователя
        prize: Объект приза

    Returns:
        URL для оплаты или None в случае ошибки
    """
    try:
        yookassa_service = YooKassaService()

        # Generate idempotence key
        idempotence_key = yookassa_service.generate_idempotence_key()

        # Create payment metadata (важно! добавляем prize_id для идентификации в webhook)
        metadata = {
            'telegram_id': str(telegram_id),
            'username': username or '',
            'prize_id': str(prize.id),
            'source': 'lottery',  # Флаг что это платеж из лотереи
            'form_url': prize.form_url or ''  # URL анкеты для отправки после оплаты
        }

        # Create payment
        payment_result = yookassa_service.create_payment(
            amount=prize.price,
            currency=prize.currency,
            description=f"Лотерея: {prize.primary_btn.text if prize.primary_btn else 'Приз'}",
            metadata=metadata,
            idempotence_key=idempotence_key
        )

        logger.info(
            f"Lottery payment created: user_id={telegram_id}, prize_id={prize.id}, "
            f"payment_id={payment_result['payment_id']}, amount={prize.price}"
        )

        # Return confirmation URL for payment
        return payment_result.get('confirmation_url')

    except Exception as e:
        logger.error(f"Error creating lottery payment for user {telegram_id}, prize {prize.id}: {e}")
        return None


@lottery_router.callback_query(F.data == "start_lottery")
async def callback_start_lottery(callback: CallbackQuery):
    """Обработчик нажатия кнопки 'Крутить колесо удачи'"""
    # Проверяем, не участвовал ли пользователь уже (двойная проверка)
    if participants_manager.has_participated(callback.from_user.id):
        await callback.answer("❌ Вы уже участвовали в лотерее!", show_alert=True)
        logger.warning(f"User {callback.from_user.id} tried to spin wheel again (already participated)")
        return

    await callback.answer("🎰 Крутим колесо...")

    # Выбираем случайный приз
    prize = random.choice(PRIZES)

    logger.info(f"User {callback.from_user.id} won prize #{prize.id}: {prize.caption[:50]}...")

    # Путь к изображению приза (используем os.path.join согласно требованиям)
    prize_image_path = os.path.join(CARDS_DIR, prize.image)

    # Обработка приза в зависимости от типа
    if prize.type == PrizeType.PAYMENT_FLOW:
        # ===== ПЛАТНЫЕ ПРИЗЫ =====
        # Создаем платеж для приза
        payment_url = await create_lottery_payment(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            prize=prize
        )

        if not payment_url:
            await callback.message.answer(
                "❌ Произошла ошибка при создании платежа.\n"
                "Попробуйте позже или обратитесь к @sharkova_na"
            )
            return

        # Получаем клавиатуру с кнопкой оплаты
        keyboard = get_prize_keyboard(prize, payment_url=payment_url)

        # Отправляем приз с кнопкой оплаты
        await send_image_with_fallback(
            message_or_query=callback,
            image_path=prize_image_path,
            caption=prize.caption,
            reply_markup=keyboard
        )

        logger.info(f"Payment prize sent: user={callback.from_user.id}, prize={prize.id}, url={payment_url}")

    elif prize.type == PrizeType.FILE:
        # ===== ПРИЗЫ С ФАЙЛАМИ =====
        # Отправляем картинку
        await send_image_with_fallback(
            message_or_query=callback,
            image_path=prize_image_path,
            caption=prize.caption,
            reply_markup=None
        )

        # Отправляем файл
        if prize.payload:
            # Проверяем, является ли payload заглушкой
            if prize.payload.startswith("FILE_ID_"):
                # Заглушка - информируем пользователя
                await callback.message.answer(
                    "ℹ️ Файл будет доступен после настройки.\n"
                    "Пожалуйста, обратитесь к @sharkova_na"
                )
            else:
                try:
                    # Проверяем, является ли это локальным файлом (имя файла) или file_id
                    if os.path.exists(os.path.join(CARDS_DIR, prize.payload)):
                        # Локальный файл - используем FSInputFile
                        file_path = os.path.join(CARDS_DIR, prize.payload)
                        document = FSInputFile(file_path)
                        await callback.message.answer_document(
                            document=document,
                            caption="📎 Ваш файл"
                        )
                        logger.info(f"Local file sent: user={callback.from_user.id}, prize={prize.id}, file={prize.payload}")
                    else:
                        # Предполагаем, что это Telegram file_id
                        await callback.message.answer_document(
                            document=prize.payload,
                            caption="📎 Ваш файл"
                        )
                        logger.info(f"File sent: user={callback.from_user.id}, prize={prize.id}")
                except Exception as e:
                    logger.error(f"Error sending file for prize {prize.id}: {e}")
                    await callback.message.answer(
                        "⚠️ Файл временно недоступен. Обратитесь к @sharkova_na"
                    )

    elif prize.type == PrizeType.LINK:
        # ===== ПРИЗЫ СО ССЫЛКАМИ =====
        keyboard = get_prize_keyboard(prize)

        await send_image_with_fallback(
            message_or_query=callback,
            image_path=prize_image_path,
            caption=prize.caption,
            reply_markup=keyboard
        )

        logger.info(f"Link prize sent: user={callback.from_user.id}, prize={prize.id}")

    # Добавляем пользователя в список участников (после успешной отправки приза)
    participants_manager.add_participant(callback.from_user.id)


@lottery_router.callback_query(F.data.startswith("prize_action_"))
async def callback_prize_action(callback: CallbackQuery):
    """Обработчик кастомных действий для призов"""
    prize_id = int(callback.data.split("_")[-1])

    # Найти приз по ID
    prize = next((p for p in PRIZES if p.id == prize_id), None)

    if not prize:
        await callback.answer("❌ Приз не найден")
        return

    # Здесь можно добавить специфичную логику для разных призов
    await callback.answer("✅ Действие выполнено!")
    logger.info(f"User {callback.from_user.id} triggered action for prize #{prize_id}")
