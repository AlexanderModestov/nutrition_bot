# Настройка базы данных для Новогодней Лотереи

## Обязательные шаги перед запуском

### 1. Выполнить SQL миграцию в Supabase

#### Способ 1: Через Supabase Dashboard (Рекомендуется)

1. Откройте [Supabase Dashboard](https://supabase.com/dashboard)
2. Выберите ваш проект
3. Перейдите в **SQL Editor** (в левом меню)
4. Нажмите **New Query**
5. Скопируйте и вставьте содержимое файла `lottery_migration.sql`:

```sql
-- Migration: Add lottery_participated column to users table
-- Date: 2025-12-28
-- Description: Track whether user has participated in New Year lottery

-- Add lottery_participated column with default value false
ALTER TABLE users
ADD COLUMN IF NOT EXISTS lottery_participated BOOLEAN DEFAULT FALSE NOT NULL;

-- Add comment to the column
COMMENT ON COLUMN users.lottery_participated IS 'Indicates if user has participated in New Year lottery (one-time participation)';

-- Optional: Create index for faster lookups (if needed for analytics)
CREATE INDEX IF NOT EXISTS idx_users_lottery_participated
ON users(lottery_participated)
WHERE lottery_participated = TRUE;
```

6. Нажмите **Run** (или Ctrl+Enter)
7. Убедитесь, что миграция выполнена успешно (должно появиться "Success")

#### Способ 2: Через psql (если есть прямой доступ к БД)

```bash
psql -h your-project.supabase.co -U postgres -d postgres -f docs/lottery_migration.sql
```

### 2. Проверить наличие колонки

После выполнения миграции проверьте, что колонка добавлена:

```sql
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'users' AND column_name = 'lottery_participated';
```

**Ожидаемый результат:**

| column_name | data_type | column_default | is_nullable |
|-------------|-----------|----------------|-------------|
| lottery_participated | boolean | false | NO |

### 3. Проверить работу методов (опционально)

После миграции можно проверить, что все работает:

```sql
-- Посмотреть текущее состояние
SELECT telegram_id, username, lottery_participated
FROM users
LIMIT 10;

-- Проверить, что можно обновить поле
UPDATE users
SET lottery_participated = TRUE
WHERE telegram_id = 123456789;  -- Замените на реальный telegram_id

-- Откатить тестовое изменение
UPDATE users
SET lottery_participated = FALSE
WHERE telegram_id = 123456789;
```

## Что делает миграция

1. **Добавляет колонку `lottery_participated`**
   - Тип: BOOLEAN
   - Значение по умолчанию: FALSE
   - Обязательное поле (NOT NULL)

2. **Добавляет комментарий к колонке**
   - Для документирования назначения поля

3. **Создает индекс**
   - Для быстрого поиска пользователей, которые участвовали в лотерее
   - Частичный индекс (только для TRUE значений) для оптимизации

## Откат миграции (если нужно)

Если по какой-то причине нужно откатить миграцию:

```sql
-- Удалить индекс
DROP INDEX IF EXISTS idx_users_lottery_participated;

-- Удалить колонку
ALTER TABLE users
DROP COLUMN IF EXISTS lottery_participated;
```

⚠️ **Внимание**: При откате все данные об участии в лотерее будут потеряны!

## Что дальше?

После успешной миграции:

1. ✅ Модуль лотереи готов к использованию
2. ✅ Данные об участии будут сохраняться автоматически
3. ✅ Пользователи смогут участвовать только один раз

Вернитесь к [LOTTERY_QUICKSTART.md](../LOTTERY_QUICKSTART.md) для продолжения настройки.

## Устранение неполадок

### Ошибка: "column already exists"

Это нормально - колонка уже существует. Миграция использует `IF NOT EXISTS`.

### Ошибка: "permission denied"

Убедитесь, что вы используете пользователя с правами на изменение схемы (обычно `postgres`).

### Ошибка при создании индекса

Индекс опционален. Если он не создается, лотерея все равно будет работать.

## Поддержка

Если возникли проблемы с миграцией:
1. Проверьте подключение к Supabase
2. Убедитесь, что таблица `users` существует
3. Проверьте права доступа к базе данных
