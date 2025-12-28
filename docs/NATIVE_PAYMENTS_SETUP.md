# Telegram Native Payments & Webhook Setup Guide

This guide explains how to set up **Telegram Native Payments** with **YooKassa** and configure **webhook notifications** for real-time payment updates.

## Overview

The new payment system includes:
1. **Telegram Native Payments** - Users pay inside Telegram (no external browser)
2. **YooKassa Integration** - Payment processing via YooKassa
3. **Webhook Server** - Receives real-time payment notifications from YooKassa

## Architecture

```
User → /pay → Select Product → Telegram Invoice → User Pays →
  ↓                                                    ↓
  └─→ YooKassa Payment Created              Payment Processed
                                                      ↓
                                            Webhook Notification → Bot
                                                      ↓
                                            User Receives Confirmation
```

---

## Part 1: Setup Telegram Native Payments

### Step 1: Get YooKassa Provider Token from BotFather

1. **Open Telegram** and find @BotFather
2. Send `/mybots`
3. Select your bot
4. Click **"Payments"**
5. Select **"YooKassa"**
6. You'll be asked to provide:
   - **Shop ID** (from YooKassa account)
   - **Secret Key** (from YooKassa account)
7. BotFather will give you a **Provider Token** (starts with a number, e.g., `381764678:TEST:12345`)

### Step 2: Configure Environment Variables

Add to your `.env` file:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI
OPENAI_API_KEY=your_openai_key

# YooKassa Credentials
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key

# IMPORTANT: Provider Token from BotFather
YOOKASSA_PROVIDER_TOKEN=381764678:TEST:12345

# Webhook Configuration (see Part 2)
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443
WEBHOOK_URL=https://yourdomain.com/webhook/yookassa
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Test Native Payments

```bash
python bot/main.py
```

**Test in Telegram:**
1. Send `/pay` to your bot
2. Select a product
3. You'll see a **Telegram invoice** (native UI)
4. Use **test card**: `5555 5555 5555 4444`
   - Expiry: any future date (e.g., `12/25`)
   - CVC: any 3 digits (e.g., `123`)
5. Pay
6. Bot should send: "✅ Платеж успешно завершен!"

---

## Part 2: Setup Webhook for Real-Time Notifications

### Why Webhooks?

Without webhooks, the bot only knows payment status when:
- User completes payment in Telegram (immediate)
- User runs `/check_payment` command (manual)

**With webhooks**, your bot receives instant notifications from YooKassa for:
- ✅ Payment succeeded
- ❌ Payment canceled
- 💰 Refund processed
- And more events

### Step 1: Setup Public URL

Your webhook endpoint must be **publicly accessible** via HTTPS.

#### Option A: Production (VPS/Cloud Server)

If you have a server with a domain:

```bash
# Your server (Ubuntu/Debian)
# Bot will start webhook server on port 8443 automatically
python bot/main.py
```

Configure **nginx** to proxy HTTPS to port 8443:

```nginx
# /etc/nginx/sites-available/your-domain
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location /webhook/yookassa {
        proxy_pass http://127.0.0.1:8443/webhook/yookassa;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Your webhook URL: `https://yourdomain.com/webhook/yookassa`

#### Option B: Development/Testing (ngrok)

For local testing:

```bash
# Terminal 1: Start bot (webhook server starts automatically)
python bot/main.py

# Terminal 2: Expose webhook with ngrok
ngrok http 8443
```

You'll get: `https://abc123.ngrok-free.app`

Your webhook URL: `https://abc123.ngrok-free.app/webhook/yookassa`

Update `.env`:
```env
WEBHOOK_URL=https://abc123.ngrok-free.app/webhook/yookassa
```

### Step 2: Configure Webhook in YooKassa

1. **Login to YooKassa Dashboard**: https://yookassa.ru
2. Go to **"Settings"** → **"Notifications"**
3. Enable **"HTTP notifications"**
4. Set **Notification URL**: `https://yourdomain.com/webhook/yookassa`
5. Select events to receive:
   - ✅ `payment.succeeded`
   - ❌ `payment.canceled`
   - 💰 `refund.succeeded`
   - ⏳ `payment.waiting_for_capture`
6. **Save**

YooKassa will send a test notification to verify the URL.

### Step 3: Verify Webhook is Working

#### Check Logs

When bot starts, you should see:
```
Webhook server started on http://0.0.0.0:8443
Webhook endpoint: http://0.0.0.0:8443/webhook/yookassa
Health check: http://0.0.0.0:8443/webhook/health
```

#### Test Health Check

```bash
curl http://localhost:8443/webhook/health
# Response: {"status":"ok","service":"yookassa-webhook"}
```

#### Test Payment Flow

1. Make a payment using `/pay`
2. Check bot logs for:
   ```
   Webhook received from IP: 185.71.76.xxx
   Webhook notification received: payment.succeeded
   Processing webhook: event=payment.succeeded, payment_id=...
   Payment success notification sent: transaction_id=...
   ```

### Step 4: Security Verification

The webhook server automatically:
- ✅ Verifies requests come from YooKassa IP addresses
- ✅ Rejects unauthorized IPs (403 Forbidden)
- ✅ Validates payment data before processing

**Valid YooKassa IPs** (hardcoded in `yookassa_service.py`):
- `185.71.76.*`
- `185.71.77.*`
- `77.75.153.*`
- `77.75.154.*`
- `77.75.156.*`

---

## Part 3: How Payment Flow Works

### User Pays with Telegram Native Payment

```
1. User: /pay
2. Bot: Shows products
3. User: Selects product
4. Bot: Creates YooKassa payment & sends Telegram invoice
5. User: Enters card details in Telegram
6. Telegram: Validates with bot (pre_checkout_query)
7. Bot: Approves payment
8. Telegram: Processes payment via YooKassa
9. User: Receives confirmation (successful_payment message)
10. Bot: Updates database & notifies user
```

### YooKassa Sends Webhook Notification

```
1. YooKassa: Processes payment
2. YooKassa: Sends webhook to your server
3. Webhook Server: Verifies IP & parses notification
4. Webhook Server: Updates database
5. Webhook Server: Sends message to user via bot
```

**Both happen simultaneously!** User gets:
- Immediate confirmation from Telegram payment
- Secondary confirmation from webhook (if webhook is configured)

---

## Part 4: File Structure

```
bot/
├── config.py                    # Updated with webhook settings
├── main.py                      # Runs bot + webhook server
├── handlers/
│   ├── payment_native.py        # NEW: Native payment handlers
│   └── payment_handlers.py      # OLD: WebApp payment (deprecated)
├── services/
│   └── yookassa_service.py      # YooKassa API wrapper
└── webhook/
    ├── __init__.py
    └── webhook_server.py        # NEW: Webhook endpoint server
```

---

## Part 5: Commands & Usage

### User Commands

- `/pay` - Start payment flow
- `/check_payment` - Manually check pending payment status
- `/my_payments` - View payment history

### Payment States

- `pending` - Payment created, awaiting user action
- `waiting_for_capture` - Payment authorized, awaiting capture
- `succeeded` - Payment successful ✅
- `canceled` - Payment canceled ❌
- `refunded` - Payment refunded 💰

---

## Part 6: Testing

### Test Payment Success

1. Send `/pay`
2. Select product
3. Pay with test card: `5555 5555 5555 4444`
4. Verify you receive:
   - Telegram confirmation message
   - Webhook notification (check logs)

### Test Payment Cancellation

1. Send `/pay`
2. Select product
3. Close invoice without paying
4. Wait ~15 minutes
5. YooKassa will auto-cancel and send webhook

### Test Webhook Reception

```bash
# Check webhook health
curl http://localhost:8443/webhook/health

# Simulate webhook (requires YooKassa IP)
# NOTE: This will be rejected by IP verification
curl -X POST http://localhost:8443/webhook/yookassa \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.succeeded","object":{"id":"test123"}}'
```

---

## Part 7: Troubleshooting

### Problem: "Missing required environment variables: YOOKASSA_PROVIDER_TOKEN"

**Solution:** Get provider token from @BotFather (see Step 1) and add to `.env`

### Problem: Webhook not receiving notifications

**Check:**
1. Webhook server is running (check bot logs)
2. Public URL is accessible via HTTPS
3. URL is configured in YooKassa dashboard
4. Firewall allows port 8443 (or your configured port)
5. nginx/reverse proxy is configured correctly

**Test:**
```bash
# From external server
curl https://yourdomain.com/webhook/health
```

### Problem: Webhook receives 403 Forbidden

**Cause:** Request is not from YooKassa IP

**Check:** Bot logs will show:
```
Webhook rejected: invalid IP xxx.xxx.xxx.xxx
```

**Solution:** If using reverse proxy, ensure real client IP is forwarded:
```nginx
proxy_set_header X-Real-IP $remote_addr;
```

### Problem: Payment succeeds but user not notified

**Check:**
1. Database has correct `telegram_id`
2. Bot has permission to send messages to user
3. Check bot logs for errors in notification sending

---

## Part 8: Migration from WebApp Payments

If you used the old WebApp payment system:

### Old Flow (WebApp)
```
User → Bot → WebApp opens → YooKassa form → Payment → WebApp sends data to bot
```

### New Flow (Native)
```
User → Bot → Telegram Invoice → Payment → Telegram notifies bot
```

### Benefits of Native Payments

✅ **Better UX** - Fully native Telegram interface
✅ **More secure** - No external WebApp needed
✅ **Simpler** - Less code, fewer dependencies
✅ **Faster** - No WebApp loading time
✅ **More reliable** - Telegram handles payment UI

### To Migrate

1. **Keep old code** - Old `payment_handlers.py` still works for existing payments
2. **Switch router** - Already done in `main.py` (using `payment_native_router`)
3. **Update frontend** - Users will see new Telegram invoice UI
4. **Test thoroughly** - Both old and new payments should work

---

## Part 9: Production Checklist

Before going live:

- [ ] Get production YooKassa credentials
- [ ] Get provider token from @BotFather
- [ ] Configure all environment variables
- [ ] Setup HTTPS on server
- [ ] Configure webhook URL in YooKassa
- [ ] Test payment with small amount
- [ ] Test webhook reception
- [ ] Monitor logs for 24 hours
- [ ] Setup error alerts
- [ ] Document refund process
- [ ] Setup database backups

---

## Part 10: Environment Variables Reference

```env
# Required
TELEGRAM_BOT_TOKEN=your_bot_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_PROVIDER_TOKEN=381764678:TEST:12345  # From @BotFather

# Optional (webhook)
WEBHOOK_HOST=0.0.0.0                          # Default: 0.0.0.0
WEBHOOK_PORT=8443                              # Default: 8443
WEBHOOK_URL=https://domain.com/webhook/yookassa # For documentation only

# Optional (legacy)
YOOKASSA_RETURN_URL=https://t.me/your_bot
WEBAPP_URL=http://localhost:8080
```

---

## Support & Resources

- **YooKassa Documentation**: https://yookassa.ru/developers
- **Telegram Bot Payments**: https://core.telegram.org/bots/payments
- **aiogram Documentation**: https://docs.aiogram.dev/

---

## Summary

You now have:
1. ✅ **Telegram Native Payments** - Users pay inside Telegram
2. ✅ **Webhook Server** - Receives real-time payment notifications
3. ✅ **Automatic Processing** - Payments are verified and processed automatically
4. ✅ **User Notifications** - Users receive instant payment confirmations

**Next Steps:**
1. Get provider token from @BotFather
2. Configure webhook URL in YooKassa
3. Test with small payment
4. Monitor logs and enjoy! 🚀
