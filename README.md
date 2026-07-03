# @Bryanjohn3456bot - Telegram Utility Bot

A multi-functional Telegram bot with Image Conversion, AI Image Generation, and URL Shortening.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖼️ Image Conversion | Convert between JPG, PNG, WEBP, BMP |
| 🎨 AI Image Generation | Generate images from text using Stable Diffusion |
| 🔗 URL Shortening | Shorten long URLs instantly |
| 📊 Stats Tracking | Track daily usage and limits |

## 🚀 Deployment on Railway

1. **Fork this repository** on GitHub
2. **Create bot** with @BotFather on Telegram
3. **Deploy** on Railway:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository
4. **Add Environment Variables**:
   - `BOT_TOKEN`: Your bot token from @BotFather
   - `HF_TOKEN`: (Optional) Hugging Face token for AI generation
5. **Deploy!** Railway handles everything

## 🔧 Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/telegram-bot.git
cd telegram-bot

# Install dependencies
pip install -r requirements.txt

# Create .env file with BOT_TOKEN
echo "BOT_TOKEN=your_token_here" > .env

# Run bot
python bot.py
