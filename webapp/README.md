# Payment WebApp - Vercel Deployment Guide

This folder contains a static payment form that integrates with your Telegram bot and YooKassa payments.

## 🎯 What This Does

When users click "Pay" in your Telegram bot:
1. Bot creates a payment in YooKassa
2. Bot sends a WebApp button linking to this payment form (hosted on Vercel)
3. User pays inside Telegram (never leaves the app)
4. JavaScript sends payment result back to bot
5. Bot notifies user of success/failure

## 📁 Files Included

- `index.html` - Main payment form (Vercel serves this by default)
- `payment.html` - Legacy file for local testing (same as index.html)
- `vercel.json` - Vercel configuration
- `.vercelignore` - Files to exclude from deployment
- `server.py` - Flask server for local testing only (NOT deployed to Vercel)

## 🚀 Deploy to Vercel

### Option 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Navigate to webapp folder:**
   ```bash
   cd webapp
   ```

3. **Login to Vercel:**
   ```bash
   vercel login
   ```

4. **Deploy:**
   ```bash
   vercel
   ```

   Follow the prompts:
   - Set up and deploy? **Y**
   - Which scope? Select your account
   - Link to existing project? **N**
   - What's your project's name? **nutritionist-payment** (or your choice)
   - In which directory is your code located? **./** (just press Enter)
   - Want to override settings? **N**

5. **Get your URL:**
   - Vercel will give you a URL like: `https://nutritionist-payment.vercel.app`
   - Copy this URL!

6. **Deploy to production:**
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via Vercel Dashboard

1. **Push to GitHub:**
   ```bash
   cd ..
   git add webapp/
   git commit -m "Add Vercel webapp"
   git push
   ```

2. **Connect to Vercel:**
   - Go to https://vercel.com
   - Click "Add New Project"
   - Import your GitHub repository
   - **Root Directory:** Select `webapp`
   - **Framework Preset:** Other
   - Click "Deploy"

3. **Get your URL:**
   - Vercel will give you a URL like: `https://nutritionist-payment.vercel.app`

## ⚙️ Configure Your Bot

After deployment, update your bot's `.env` file:

```env
# Replace with your actual Vercel URL
WEBAPP_URL=https://nutritionist-payment.vercel.app
```

**Important:** Use the production URL (without `.vercel.app` preview suffix if you have a custom domain).

## 🧪 Test Your Deployment

1. **Check if webapp is live:**
   ```bash
   curl https://your-app.vercel.app
   ```

   You should see the HTML content.

2. **Test in Telegram:**
   - Start your bot
   - Send `/pay` command
   - Click a product
   - Click "💳 Оплатить"
   - WebApp should open inside Telegram

3. **Test payment:**
   - Use YooKassa test card: `5555 5555 5555 4444`
   - Expiry: `12/25`
   - CVC: `123`

## 🔧 How Bot Passes Data to WebApp

Your bot should construct the WebApp URL like this:

```python
webapp_url = f"{Config.WEBAPP_URL}?payment_id={confirmation_token}&product_name={product.name}&amount={product.price}&currency=RUB&return_url=https://t.me/{bot_username}"
```

**URL Parameters:**
- `payment_id` - YooKassa confirmation token (required)
- `product_name` - Name of product/service (required)
- `amount` - Price amount (required)
- `currency` - Currency code (optional, defaults to RUB)
- `product_description` - Description (optional)
- `return_url` - Telegram bot deep link (optional, defaults to placeholder)

## 🔄 Update Deployment

When you make changes:

```bash
cd webapp
vercel --prod
```

Vercel will deploy the new version instantly!

## 🌐 Custom Domain (Optional)

1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update `WEBAPP_URL` in your bot's `.env`

## ❌ Troubleshooting

### WebApp doesn't open
- ✅ Check `WEBAPP_URL` is set correctly in `.env`
- ✅ Ensure bot is passing `payment_id` parameter
- ✅ URL must use HTTPS (Vercel does this automatically)

### Payment form doesn't load
- ✅ Check browser console for errors (Telegram Desktop: Ctrl+Shift+I)
- ✅ Verify YooKassa credentials in bot's `.env`
- ✅ Ensure `payment_id` is valid confirmation token from YooKassa

### Payment succeeds but bot doesn't get notification
- ✅ Check bot has `handle_webapp_data` handler registered
- ✅ Check bot logs for errors
- ✅ Verify database transaction was created

### "Mixed Content" error
- ✅ Vercel uses HTTPS by default - this shouldn't happen
- ✅ If using custom domain, ensure SSL is configured

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│  VERCEL (Static CDN)                                │
│  https://your-app.vercel.app                        │
│                                                     │
│  Files deployed:                                    │
│  ✓ index.html (payment form)                       │
│  ✓ vercel.json (config)                            │
│                                                     │
│  Files ignored:                                     │
│  ✗ server.py (not needed)                          │
└─────────────────────────────────────────────────────┘
                        ↓
            User opens WebApp in Telegram
                        ↓
              User enters card details
                        ↓
          YooKassa processes payment
                        ↓
        JavaScript calls tg.sendData()
                        ↓
┌─────────────────────────────────────────────────────┐
│  YOUR BOT SERVER                                    │
│  (DigitalOcean / Railway / Heroku / Your VPS)      │
│                                                     │
│  ✓ Receives web_app_data from Telegram             │
│  ✓ Updates database                                │
│  ✓ Sends confirmation to user                      │
└─────────────────────────────────────────────────────┘
```

## 💰 Costs

**Vercel Free Tier includes:**
- ✅ 100GB bandwidth/month
- ✅ Unlimited static sites
- ✅ HTTPS/SSL certificates
- ✅ Custom domains

This is **more than enough** for a payment form that only loads when users pay!

## 🔒 Security Notes

- ✅ All payment processing happens on YooKassa servers (PCI compliant)
- ✅ Your webapp only displays the payment form - no sensitive data stored
- ✅ HTTPS enforced by Vercel automatically
- ✅ Security headers configured in `vercel.json`
- ⚠️ Never commit `.env` files with real credentials

## 📝 Local Development

For local testing without Vercel:

```bash
cd webapp
python server.py
```

Then use ngrok to expose:
```bash
ngrok http 8080
```

Update `.env`:
```env
WEBAPP_URL=https://abc123.ngrok-free.app
```

**Note:** This is only for testing! Production should use Vercel.

## ✅ Deployment Checklist

- [ ] Deployed webapp to Vercel
- [ ] Got production URL from Vercel
- [ ] Updated `WEBAPP_URL` in bot's `.env`
- [ ] Restarted bot with new `.env`
- [ ] Tested payment flow end-to-end
- [ ] Verified bot receives `web_app_data`
- [ ] Checked payment confirmation message works

## 🆘 Support

If you encounter issues:
1. Check Vercel deployment logs in dashboard
2. Check bot logs for errors
3. Test with YooKassa test cards
4. Verify all environment variables are set

---

**Your payment system is now fully deployed!** 🎉

Users can pay directly inside Telegram, and you don't need any provider tokens!
