# Quick Start: Native Payments & Webhooks

## What's New?

✅ **Telegram Native Payments** - Users pay inside Telegram (no external browser)
✅ **Webhook Server** - Real-time payment notifications from YooKassa
✅ **Better UX** - Fully native Telegram payment interface

---

## Setup in 5 Steps

### 1. Get Provider Token from BotFather

```
1. Open @BotFather in Telegram
2. Send: /mybots
3. Select your bot → Payments → YooKassa
4. Enter your YooKassa Shop ID and Secret Key
5. Copy the Provider Token (e.g., 381764678:TEST:12345)
```

### 2. Update .env File

Add this line:
```env
YOOKASSA_PROVIDER_TOKEN=381764678:TEST:12345
```

### 3. (Optional) Configure Webhook

For real-time notifications, add:
```env
WEBHOOK_PORT=8443
WEBHOOK_URL=https://yourdomain.com/webhook/yookassa
```

Then configure the webhook URL in your YooKassa dashboard:
https://yookassa.ru → Settings → Notifications

### 4. Run the Bot

```bash
python bot/main.py
```

You should see:
```
Bot initialized successfully
Webhook server started on http://0.0.0.0:8443
Webhook endpoint: http://0.0.0.0:8443/webhook/yookassa
```

### 5. Test Payment

In Telegram:
```
1. Send: /pay
2. Select a product
3. You'll see a Telegram invoice (native UI!)
4. Use test card: 5555 5555 5555 4444
5. Expiry: 12/25, CVC: 123
6. Pay → Receive confirmation ✅
```

---

## Files Changed

**New Files:**
- `bot/handlers/payment_native.py` - Native payment handlers
- `bot/webhook/webhook_server.py` - Webhook endpoint
- `bot/webhook/__init__.py` - Package init
- `docs/NATIVE_PAYMENTS_SETUP.md` - Full documentation

**Modified Files:**
- `bot/config.py` - Added webhook settings
- `bot/main.py` - Integrated webhook server

---

## Commands

- `/pay` - Start payment
- `/check_payment` - Check pending payments
- `/my_payments` - View payment history

---

## Need Help?

Read the full guide: `docs/NATIVE_PAYMENTS_SETUP.md`

---

## What Happens When User Pays?

```
1. User sends /pay
2. Bot sends Telegram invoice
3. User enters card in Telegram
4. Telegram processes payment
5. User gets confirmation ✅
6. YooKassa sends webhook to your server
7. Bot updates database & notifies user
```

Both Telegram and webhook confirm the payment simultaneously!

---

## Testing Without Webhook

You can use native payments **without** webhooks:
- User gets confirmation immediately after paying
- Webhook adds redundancy and handles edge cases

To skip webhook setup:
- Just get the Provider Token
- Start the bot
- The webhook server will still start but won't receive notifications (which is fine for testing)

---

**That's it! Start accepting payments in Telegram! 🚀**
