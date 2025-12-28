# WebApp Payments + Webhooks Setup (No Provider Token Needed!)

## ✅ What You Get

- **Payments Inside Telegram**: User never leaves the chat
- **Webhook Notifications**: Real-time payment updates from YooKassa
- **No Provider Token Required**: Works without BotFather payment connection

---

## 📋 Required Setup (3 Steps)

### Step 1: Configure Environment Variables

Your `.env` file must have:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# OpenAI (for your main bot features)
OPENAI_API_KEY=your_openai_key

# YooKassa Credentials (from yookassa.ru account)
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_RETURN_URL=https://t.me/your_bot_username

# WebApp URL (where payment form is hosted)
WEBAPP_URL=http://localhost:8080  # For testing
# WEBAPP_URL=https://yourdomain.com  # For production

# Webhook Settings
WEBHOOK_HOST=0.0.0.0
WEBHOOK_PORT=8443
```

**Note:** You do NOT need `YOOKASSA_PROVIDER_TOKEN` for WebApp payments!

### Step 2: Setup WebApp Server

The WebApp server hosts the payment form that opens inside Telegram.

#### For Local Testing:

**Terminal 1: Start WebApp Server**
```bash
cd webapp
python server.py
```

**Terminal 2: Expose with ngrok**
```bash
ngrok http 8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`) and update `.env`:
```env
WEBAPP_URL=https://abc123.ngrok-free.app
```

#### For Production:

Deploy `webapp/` folder to:
- **Vercel** (easiest, free)
- **Heroku**
- **Your VPS**

Update `.env` with your production URL:
```env
WEBAPP_URL=https://yourdomain.com
```

### Step 3: Run the Bot

```bash
python bot/main.py
```

You should see:
```
✓ Bot initialized successfully
✓ Webhook server started on http://0.0.0.0:8443
✓ Webhook endpoint: http://0.0.0.0:8443/webhook/yookassa
```

---

## 🧪 Test Payment Flow

1. **Start payment:**
   ```
   /pay
   ```

2. **Select product** → Click "💳 Оплатить"

3. **WebApp opens INSIDE Telegram** (you see a payment form)

4. **Enter test card:**
   - Card: `5555 5555 5555 4444`
   - Expiry: `12/25`
   - CVC: `123`

5. **Submit payment**

6. **WebApp closes automatically**

7. **Bot sends confirmation:** "✅ Платеж успешно завершен!"

**You never left Telegram!** ✨

---

## 🔔 Setup Webhooks for Real-Time Notifications

### Why Webhooks?

Without webhook:
- ✅ User gets confirmation immediately after paying in WebApp
- ❌ No notifications if payment is canceled later
- ❌ No notifications for refunds

With webhook:
- ✅ User gets confirmation from WebApp
- ✅ **PLUS** real-time notifications from YooKassa for all events
- ✅ Redundancy - if WebApp fails, webhook still works

### Step 1: Expose Webhook Endpoint

Your webhook server is already running (started automatically with bot).

#### For Testing (ngrok):

**Terminal 1: Bot running**
```bash
python bot/main.py
```

**Terminal 2: Expose webhook port**
```bash
ngrok http 8443
```

Copy the HTTPS URL: `https://xyz789.ngrok-free.app`

Your webhook URL is: `https://xyz789.ngrok-free.app/webhook/yookassa`

#### For Production (VPS with domain):

Setup nginx to proxy HTTPS to port 8443:

```nginx
# /etc/nginx/sites-available/yourbot
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

Your webhook URL is: `https://yourdomain.com/webhook/yookassa`

### Step 2: Configure in YooKassa Dashboard

1. Login to **https://yookassa.ru**
2. Go to **Settings** → **Notifications** → **HTTP notifications**
3. **Enable HTTP notifications**
4. **Set URL:** `https://yourdomain.com/webhook/yookassa`
5. **Select events:**
   - ✅ `payment.succeeded`
   - ✅ `payment.canceled`
   - ✅ `refund.succeeded`
   - ✅ `payment.waiting_for_capture`
6. **Save**

YooKassa will send a test request to verify.

### Step 3: Verify Webhook Works

**Check health:**
```bash
curl http://localhost:8443/webhook/health
# Response: {"status":"ok","service":"yookassa-webhook"}
```

**Make test payment and check logs:**
```
INFO - Webhook received from IP: 185.71.76.xxx
INFO - Webhook notification received: payment.succeeded
INFO - Processing webhook: event=payment.succeeded, payment_id=...
INFO - Payment success notification sent: transaction_id=...
```

---

## 🎯 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      USER EXPERIENCE                        │
└─────────────────────────────────────────────────────────────┘

1. User: /pay
   ↓
2. Bot: Shows products
   ↓
3. User: Clicks product → "💳 Оплатить"
   ↓
4. WebApp opens INSIDE Telegram
   ↓
5. User: Enters card details
   ↓
6. User: Clicks "Оплатить"
   ↓
7. Payment processed by YooKassa
   ↓
8. WebApp closes automatically
   ↓
9. Bot: "✅ Платеж успешно завершен!"

┌─────────────────────────────────────────────────────────────┐
│                    TECHNICAL FLOW                           │
└─────────────────────────────────────────────────────────────┘

User clicks "Оплатить"
   ↓
Bot creates payment in YooKassa
   ↓
Bot sends WebApp button with payment_id
   ↓
User opens WebApp (stays in Telegram)
   ↓
User pays → YooKassa processes payment
   ↓
WebApp sends success data to bot ───────┐
   ↓                                     │
Bot updates database                    │
   ↓                                     │
Bot notifies user ✅                    │
                                        │
SIMULTANEOUSLY:                         │
   ↓                                     │
YooKassa sends webhook notification ────┘
   ↓
Webhook server receives notification
   ↓
Webhook updates database (redundancy)
   ↓
Webhook sends notification to user ✅
```

---

## 📊 Comparison: WebApp vs Native Payments

| Feature | WebApp (Your Setup) | Native (Needs Token) |
|---------|---------------------|----------------------|
| **Stays in Telegram?** | ✅ Yes | ✅ Yes |
| **Needs Provider Token?** | ❌ No | ✅ Yes |
| **Webhooks Work?** | ✅ Yes | ✅ Yes |
| **User Interface** | Web form in Telegram | Native Telegram invoice |
| **Setup Difficulty** | Easy | Medium |
| **Reliability** | ✅ Very good | ✅ Very good |

**Both methods keep users inside Telegram!** The only difference is the UI style.

---

## 🔧 What You Need to Make It Work

### ✅ Required (You must have these):

1. **YooKassa Account** with Shop ID and Secret Key
2. **WebApp Server** running (local or deployed)
3. **Bot Running** (`python bot/main.py`)
4. **Payment Products** in database

### ✅ Recommended (For production):

5. **Webhook configured** in YooKassa dashboard
6. **Public HTTPS URL** for webhook endpoint
7. **Monitoring/logging** setup

### ❌ NOT Required:

- ~~Provider Token from @BotFather~~
- ~~Native Telegram payment setup~~

---

## 🚀 Quick Start Checklist

- [ ] YooKassa account created
- [ ] Shop ID and Secret Key in `.env`
- [ ] WebApp URL configured in `.env`
- [ ] WebApp server running (or deployed)
- [ ] Bot started: `python bot/main.py`
- [ ] Test payment completed successfully
- [ ] Webhook URL configured in YooKassa (optional)
- [ ] Webhook receiving notifications (optional)

---

## 🆘 Troubleshooting

### WebApp doesn't open

**Check:**
1. `WEBAPP_URL` is set in `.env`
2. WebApp server is running: `cd webapp && python server.py`
3. URL uses HTTPS (required by Telegram)
4. If using ngrok, tunnel is active

### Payment form doesn't load

**Check:**
1. YooKassa credentials are correct
2. Payment ID is passed in URL
3. Browser console for errors (Telegram Desktop: Ctrl+Shift+I)

### User not notified after payment

**Check:**
1. Bot logs for errors
2. `handle_webapp_data` handler is working
3. Database transaction was created

### Webhook not receiving notifications

**Check:**
1. Webhook URL is publicly accessible
2. HTTPS is configured (webhooks require HTTPS)
3. URL is set in YooKassa dashboard
4. Firewall allows port 8443
5. Bot logs show "Webhook server started"

---

## 📝 Summary

**You have TWO notification systems:**

1. **WebApp Callback** (immediate)
   - User pays in WebApp
   - WebApp sends data to bot
   - Bot notifies user ✅

2. **YooKassa Webhook** (redundant + handles edge cases)
   - YooKassa processes payment
   - YooKassa sends webhook
   - Bot notifies user ✅

**Both work together for maximum reliability!**

---

## 🎉 Ready to Accept Payments!

Your setup:
- ✅ Payments happen inside Telegram
- ✅ Webhooks provide real-time notifications
- ✅ No provider token needed
- ✅ Production-ready

Just configure `.env` and run `python bot/main.py`! 🚀
