# Настройка платежного функционала лотереи

## ✅ Реализовано

Модуль лотереи теперь поддерживает **полный платежный flow с автоматической отправкой анкет**:

1. **Создание платежа** для платных призов
2. **Webhook обработка** после успешной оплаты
3. **Автоматическая отправка анкеты** пользователю после оплаты
4. **Персонализация** анкет через query параметры

## 🎯 Как это работает

### Workflow для платных призов:

```
1. Пользователь выигрывает приз типа PAYMENT_FLOW
   ↓
2. Бот создает платеж в YooKassa с метаданными:
   - telegram_id: ID пользователя
   - prize_id: ID приза
   - source: "lottery"
   - form_url: URL анкеты
   ↓
3. Бот отправляет карточку приза с кнопкой "Оплатить"
   ↓
4. Пользователь переходит на оплату → оплачивает
   ↓
5. YooKassa отправляет webhook на ваш сервер
   ↓
6. Бот получает webhook, проверяет source="lottery"
   ↓
7. Бот автоматически отправляет пользователю:
   a) Сообщение об успешной оплате
   b) Ссылку на персонализированную анкету
```

## 📋 Настройка

### Шаг 1: Обновить URL форм в lottery.py

Откройте `bot/handlers/lottery.py` и найдите призы с типом `PAYMENT_FLOW`:

```python
# Prize 2: Наставничество
Prize(
    id=2,
    type=PrizeType.PAYMENT_FLOW,
    price=Decimal("1"),
    form_url="https://forms.gle/YOUR_MENTORSHIP_FORM_ID",  # ← Замените
    ...
)

# Prize 4: Аудио-консультация
Prize(
    id=4,
    type=PrizeType.PAYMENT_FLOW,
    price=Decimal("990"),
    form_url="https://forms.gle/YOUR_AUDIO_FORM?entry.telegram_id={telegram_id}",  # ← Замените
    ...
)
```

**Важно:** Используйте плейсхолдер `{telegram_id}` в URL - он будет автоматически заменен на реальный ID пользователя.

### Шаг 2: Создать Google Forms с предзаполнением

#### Как создать форму с предзаполнением telegram_id:

1. Создайте Google Form для услуги (например, "Анкета для аудио-консультации")
2. Добавьте поле "Telegram ID" (короткий ответ)
3. Откройте форму в режиме редактирования
4. Нажмите F12 (DevTools) → вкладка Elements
5. Найдите input поле для "Telegram ID", оно будет выглядеть так:
   ```html
   <input name="entry.1234567890" ...>
   ```
6. Скопируйте номер `entry.XXXXXXXXXX`
7. Создайте URL:
   ```
   https://docs.google.com/forms/d/e/FORM_ID/viewform?entry.1234567890={telegram_id}
   ```

**Пример готового URL:**
```
https://docs.google.com/forms/d/e/1FAIpQLSexample123/viewform?entry.1234567890={telegram_id}&entry.9876543210=audio_consultation
```

### Шаг 3: Настроить Webhook YooKassa

#### 3.1 Настройка webhook в YooKassa

1. Войдите в личный кабинет YooKassa
2. Перейдите в **Настройки** → **Уведомления**
3. Добавьте URL вебхука:
   ```
   https://your-domain.com/webhook/yookassa
   ```
4. Выберите события:
   - ✅ `payment.succeeded`
   - ✅ `payment.canceled`
   - ✅ `refund.succeeded`

#### 3.2 Проверка настроек в .env

Убедитесь что в `.env` файле заданы:

```env
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443
WEBHOOK_URL=https://your-domain.com/webhook/yookassa
```

#### 3.3 Запуск webhook сервера

Webhook сервер должен запускаться вместе с ботом. Проверьте `bot/main.py`:

```python
# Должно быть что-то похожее на:
from bot.webhook.webhook_server import run_webhook_server

# В main():
webhook_task = asyncio.create_task(run_webhook_server(bot, supabase_client))
```

Если webhook сервер не настроен, см. документацию YooKassa.

### Шаг 4: Настроить цены

Обновите цены для платных призов в `lottery.py`:

```python
# Prize 2: Наставничество (бронь)
price=Decimal("1"),  # Символическая цена или реальная со скидкой

# Prize 4: Аудио-консультация
price=Decimal("990"),  # Реальная цена
```

## 🧪 Тестирование

### 1. Тестирование создания платежа

```bash
# Запустите бота
python -m bot.main

# В Telegram:
1. Отправьте /game
2. Нажмите "Крутить колесо удачи"
3. Если выпадет приз #2 или #4 (платные), проверьте:
   - ✅ Карточка приза отправилась
   - ✅ Кнопка "Оплатить" присутствует
   - ✅ Ссылка ведет на страницу YooKassa
```

### 2. Тестирование webhook

```bash
# В логах бота должно быть:
# "Lottery payment created: user_id=..., prize_id=..., payment_id=..."
```

После оплаты (используйте тестовую карту YooKassa):
```
4111 1111 1111 1111
12/25
123
```

Проверьте:
- ✅ Webhook получен (в логах: "Webhook received from IP: ...")
- ✅ Оплата обработана (в логах: "Lottery payment success: ...")
- ✅ Бот отправил 2 сообщения:
  1. "✅ Оплата успешно завершена!"
  2. "📋 Заполните анкету" с ссылкой

### 3. Проверка персонализации анкеты

Откройте ссылку на анкету из сообщения бота:
- ✅ В URL должен быть ваш реальный telegram_id
- ✅ Поле "Telegram ID" должно быть предзаполнено

## 📊 Структура метаданных платежа

Каждый платеж лотереи содержит метаданные:

```json
{
  "telegram_id": "123456789",
  "username": "john_doe",
  "prize_id": "4",
  "source": "lottery",
  "form_url": "https://forms.gle/xyz?entry.123={telegram_id}"
}
```

- **source**: `"lottery"` - идентифицирует платеж как из лотереи
- **prize_id**: ID приза для статистики
- **form_url**: URL анкеты с плейсхолдером

## 🔍 Отладка

### Проблема: Анкета не приходит после оплаты

1. Проверьте логи webhook:
   ```bash
   grep "Lottery payment success" logs/bot.log
   ```

2. Убедитесь что `form_url` задан в Prize:
   ```python
   form_url="https://forms.gle/..."  # Не должно быть None
   ```

3. Проверьте что webhook сервер запущен:
   ```bash
   curl http://localhost:8443/webhook/health
   # Должно вернуть: {"status": "ok", "service": "yookassa-webhook"}
   ```

### Проблема: {telegram_id} не заменяется

Это нормально! Плейсхолдер заменяется **только в webhook**, когда бот отправляет анкету пользователю.

### Проблема: Платеж не создается

Проверьте логи:
```bash
grep "Error creating lottery payment" logs/bot.log
```

Возможные причины:
- YooKassa credentials не настроены
- Неправильная цена (должна быть Decimal)
- Отсутствует интернет-соединение

## 📁 Измененные файлы

```
bot/handlers/lottery.py              # Основной модуль с платежами
bot/webhook/webhook_server.py        # Обработка webhook с отправкой анкет
LOTTERY_PAYMENT_SETUP.md             # Эта инструкция
```

## 🎉 Готово!

После настройки платежный flow работает полностью автоматически:
1. Пользователь выигрывает → платит
2. Webhook приходит → бот отправляет анкету
3. Пользователь заполняет анкету → вы получаете заявку

Никакой ручной работы! 🚀
