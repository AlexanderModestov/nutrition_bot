-- YooKassa Payment Integration Schema
-- Tables for payment products and transactions

-- Payment Products Table
-- Stores available services/products for purchase
CREATE TABLE payment_products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price_amount DECIMAL(10, 2) NOT NULL,
    price_currency VARCHAR(3) DEFAULT 'RUB',
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Payment Transactions Table
-- Tracks all payment attempts and their status
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    telegram_id BIGINT NOT NULL,
    product_id INTEGER REFERENCES payment_products(id) ON DELETE SET NULL,

    -- YooKassa fields
    yookassa_payment_id VARCHAR(255) UNIQUE,
    idempotence_key VARCHAR(255) UNIQUE NOT NULL,

    -- Payment details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(50) DEFAULT 'pending',

    -- Confirmation details
    confirmation_url TEXT,
    confirmation_type VARCHAR(50),

    -- Payment method and timestamps
    payment_method_type VARCHAR(50),
    paid_at TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Additional data
    metadata JSONB,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_payment_products_active ON payment_products(is_active);
CREATE INDEX idx_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX idx_transactions_telegram_id ON payment_transactions(telegram_id);
CREATE INDEX idx_transactions_yookassa_id ON payment_transactions(yookassa_payment_id);
CREATE INDEX idx_transactions_status ON payment_transactions(status);
CREATE INDEX idx_transactions_created_at ON payment_transactions(created_at DESC);

-- Row Level Security (RLS) policies
ALTER TABLE payment_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

-- Products: Everyone can read active products
CREATE POLICY "Anyone can read active products" ON payment_products
    FOR SELECT
    USING (is_active = true);

-- Transactions: System can manage all transactions
CREATE POLICY "System can manage transactions" ON payment_transactions
    FOR ALL
    USING (true)
    WITH CHECK (true);

-- Triggers for updating updated_at timestamp
CREATE TRIGGER update_payment_products_updated_at
    BEFORE UPDATE ON payment_products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_transactions_updated_at
    BEFORE UPDATE ON payment_transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial products
INSERT INTO payment_products (name, description, price_amount, price_currency, is_active)
VALUES
    (
        'Консультация',
        'Консультация 60 минут: разбор анкеты, пищевого дневника за 3 дня, PDF-файл с рекомендациями, ответы на вопросы в течение 14 дней',
        5000.00,
        'RUB',
        true
    ),
    (
        'Сопровождение',
        'Сопровождение от 4 недель: консультация, ежедневное ведение, материалы, поддержка',
        15000.00,
        'RUB',
        true
    );

-- Comments for documentation
COMMENT ON TABLE payment_products IS 'Available payment products/services';
COMMENT ON TABLE payment_transactions IS 'Payment transaction tracking';
COMMENT ON COLUMN payment_transactions.status IS 'Payment status: pending, waiting_for_capture, succeeded, canceled, failed';
COMMENT ON COLUMN payment_transactions.yookassa_payment_id IS 'Unique payment ID from YooKassa';
COMMENT ON COLUMN payment_transactions.idempotence_key IS 'Idempotence key for safe retries';
