# 🌐 Staging Website Deployment Guide

## Quick Start: Use Ngrok (Recommended for Testing)

### Step 1: Run with Public URL

Stop your current server (Ctrl+C), then run:

```bash
python run_public.py
```

You'll see output like:
```
✅ Your AI Agent is now PUBLIC at:
   https://abc123.ngrok.io

📝 Copy this URL and paste it in WordPress > AI Chat > API Endpoint
```

### Step 2: Update WordPress Plugin

1. Go to your staging site: **https://dev.rozebiohealth.com/wp-admin**
2. Navigate to: **AI Chat** (in sidebar)
3. Change **API Endpoint** from:
   ```
   http://localhost:8002
   ```
   To your ngrok URL:
   ```
   https://abc123.ngrok.io
   ```
4. Click **Save Changes**

### Step 3: Test on Staging

1. Visit: **https://dev.rozebiohealth.com**
2. The chat widget should appear!
3. Test a few questions

---

## ✅ Done! Your AI Agent is Live on Staging

**Important Notes:**
- Ngrok free URLs expire when you restart
- For permanent deployment, use Option 2 or 3 below

---

## Option 2: Railway Deployment (Permanent - Free Tier)

### Perfect for Production

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login:**
   ```bash
   railway login
   ```

3. **Deploy:**
   ```bash
   cd ai-whatsapp-commerce-bot
   railway init
   railway up
   ```

4. **Get Your URL:**
   ```bash
   railway domain
   ```
   
   You'll get: `https://your-app.railway.app`

5. **Update WordPress:**
   - Set API Endpoint to: `https://your-app.railway.app`

**Cost:** FREE for up to 500 hours/month

---

## Option 3: VPS Deployment (Most Control)

If you have a server (DigitalOcean, AWS, etc.):

### Step 1: Upload Code

```bash
scp -r ai-whatsapp-commerce-bot user@your-server:/var/www/
```

### Step 2: Install Dependencies

```bash
ssh user@your-server
cd /var/www/ai-whatsapp-commerce-bot
pip install -r requirements.txt
```

### Step 3: Run with systemd

Create `/etc/systemd/system/roze-ai.service`:

```ini
[Unit]
Description=Roze AI Chat Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/ai-whatsapp-commerce-bot
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8002
Restart=always

[Install]
WantedBy=multi-user.target
```

Start:
```bash
sudo systemctl start roze-ai
sudo systemctl enable roze-ai
```

### Step 4: Configure Nginx (Optional)

Add to your nginx config:

```nginx
location /ai/ {
    proxy_pass http://localhost:8002/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

Then use: `https://dev.rozebiohealth.com/ai/`

---

## 🔒 Security Checklist

- [ ] Use HTTPS (ngrok/Railway do this automatically)
- [ ] Add API authentication (future enhancement)
- [ ] Monitor server resources
- [ ] Set up error logging
- [ ] Configure backup for databases

---

## 🐛 Troubleshooting

### Widget Not Showing?
**Check:**
1. Is backend running? Test: `https://your-url/test`
2. Is API endpoint correct in WordPress?
3. Check browser console (F12) for errors

### CORS Errors?
The backend already allows all origins. If you still see errors:
- Ensure you're using HTTPS (not HTTP mixed with HTTPS)

### Chat Not Responding?
- Check backend logs
- Test directly: `https://your-url/api/test-chat`

---

## 📊 Monitoring Your Deployment

### Check if Backend is Running

```bash
curl https://your-url/
```

Should return:
```json
{"status":"active","service":"AI WhatsApp Commerce Bot (Live Only)"}
```

### View Logs (Railway)

```bash
railway logs
```

### Analytics

Visit: `https://your-url/admin` → View conversation stats

---

## 🚀 Recommended Flow

1. **Development:** Use `localhost:8002` (current setup)
2. **Staging:** Use `ngrok` or Railway (this guide)
3. **Production:** Use Railway (paid) or VPS with SSL

---

## 💡 Pro Tips

1. **Get a stable ngrok URL:**
   - Sign up at https://ngrok.com (free)
   - Get auth token
   - Add to `.env`:
     ```
     NGROK_AUTH_TOKEN=your_token_here
     ```

2. **Test before deploying:**
   - Always test locally first
   - Then test on staging
   - Finally push to production

3. **Monitor performance:**
   - Check `/api/analytics/stats` regularly
   - Adjust cache settings if needed

---

## 🎯 Your Next Steps

1. ✅ Run `python run_public.py`
2. ✅ Copy the ngrok URL
3. ✅ Update WordPress plugin settings
4. ✅ Test on https://dev.rozebiohealth.com
5. ✅ Show it to your team!

**Questions?** Check the main README or contact support.
