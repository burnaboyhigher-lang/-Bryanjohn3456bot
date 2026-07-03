#!/usr/bin/env python3
"""
Telegram Bot @Bryanjohn3456bot
Features: Image Conversion, AI Image Generation, URL Shortening
Deployed on: Railway + GitHub
"""

import os
import io
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlparse

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Image Processing
from PIL import Image
import requests

# URL Shortening
import pyshorteners

# AI Generation
from huggingface_hub import InferenceClient

# Environment
from dotenv import load_dotenv

# ============================================
# CONFIGURATION & SETUP
# ============================================

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")  # Optional for AI generation
PORT = int(os.getenv("PORT", 8080))  # Railway uses PORT env

# Validation
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not set! Please add it to environment variables.")
    raise ValueError("BOT_TOKEN is required")

# Initialize Services
shortener = pyshorteners.Shortener()
hf_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None

# Rate Limiting (Simple in-memory store)
user_usage: Dict[int, Dict[str, int]] = {}
DAILY_LIMIT = 5  # AI generations per day

# ============================================
# HELPER FUNCTIONS
# ============================================

def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded daily AI generation limit."""
    today = datetime.now().date()
    
    if user_id not in user_usage:
        user_usage[user_id] = {"date": today, "count": 0}
    
    if user_usage[user_id]["date"] != today:
        user_usage[user_id] = {"date": today, "count": 0}
    
    if user_usage[user_id]["count"] >= DAILY_LIMIT:
        return False
    
    user_usage[user_id]["count"] += 1
    return True

def format_bytes(size: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

# ============================================
# COMMAND HANDLERS
# ============================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - Show welcome menu."""
    user = update.effective_user
    first_name = user.first_name or "User"
    
    welcome_text = f"""
👋 **Hello {first_name}!**

Welcome to **@Bryanjohn3456bot** - Your All-in-One Utility Assistant!

I can help you with:

🎯 **Available Features:**

🖼️ **Image Conversion**
   - Convert JPG ↔ PNG ↔ WEBP ↔ BMP
   - Resize images (50% or 200%)
   - No quality loss!

🎨 **AI Image Generation**
   - Create images from text descriptions
   - Powered by Stable Diffusion
   - {DAILY_LIMIT} free generations per day

🔗 **URL Shortening**
   - Shorten long URLs instantly
   - Track link length savings

📱 **How to Use:**
   • Send an image → Convert it
   • Send `generate: prompt` → Create AI image
   • Send a URL → Shorten it
   • Use buttons below → Quick actions

📊 **Bot Stats:**
   • Uptime: 24/7
   • Response Time: Fast ⚡
   • Free to use! 🎉

_Select an option below to get started:_
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🖼️ Convert Image", callback_data="convert"),
            InlineKeyboardButton("🎨 Generate Image", callback_data="generate"),
        ],
        [
            InlineKeyboardButton("🔗 Shorten URL", callback_data="shorten"),
            InlineKeyboardButton("📖 Help", callback_data="help"),
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="stats"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = """
📖 **Detailed Help Guide**

---

**🖼️ Image Conversion**
1. Send any image (JPG, PNG, WEBP, BMP)
2. Choose conversion option from buttons
3. Receive converted image instantly

_Supported formats:_ JPG, PNG, WEBP, BMP
_Max file size:_ 10MB

---

**🎨 AI Image Generation**
1. Type: `generate: your description`
2. Example: `generate: a beautiful sunset over mountains`
3. Wait 10-30 seconds for your image

_Tips:_
• Be specific in your description
• Include style (realistic, cartoon, etc.)
• Mention colors and mood

---

**🔗 URL Shortening**
1. Send any URL starting with http:// or https://
2. Get a shortened link instantly
3. Use it anywhere!

---

**📋 Quick Commands**
`/start` - Main menu
`/help` - This help
`/convert` - Start image conversion
`/generate` - Generate AI image
`/shorten` - Shorten a URL
`/stats` - Your usage stats

---

**⚠️ Limits & Policies**
• AI Generation: {DAILY_LIMIT} per day
• Image size: Max 10MB
• Supported formats: JPG, PNG, WEBP, BMP, GIF
• All conversions are lossless

**🔒 Privacy**
• Images are processed temporarily
• No data is stored permanently
• All processing is secure

---

_Need help? Just ask!_ 🤗
"""
    
    await update.message.reply_text(
        help_text.format(DAILY_LIMIT=DAILY_LIMIT),
        parse_mode="Markdown"
    )

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command - Show user statistics."""
    user_id = update.effective_user.id
    
    if user_id in user_usage:
        usage = user_usage[user_id]
        remaining = max(0, DAILY_LIMIT - usage["count"])
        used = usage["count"]
    else:
        remaining = DAILY_LIMIT
        used = 0
    
    stats_text = f"""
📊 **Your Usage Statistics**

🎨 **AI Image Generation**
   • Used today: {used}/{DAILY_LIMIT}
   • Remaining: {remaining}
   • Resets: Tomorrow at 00:00

🖼️ **Image Conversion**
   • Unlimited ✓
   • No daily limit

🔗 **URL Shortening**
   • Unlimited ✓
   • No daily limit

📅 **Date:** {datetime.now().strftime('%B %d, %Y')}
⏰ **Last Reset:** Today at 00:00

---
_Keep creating! 🚀_
"""
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

# ============================================
# IMAGE CONVERSION HANDLER
# ============================================

async def convert_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /convert command."""
    await update.message.reply_text(
        "🖼️ **Image Conversion Mode Activated**\n\n"
        "Please send me an image to convert.\n\n"
        "I accept:\n"
        "• 📸 Photos (JPEG)\n"
        "• 🎨 PNG images\n"
        "• 🌐 WEBP images\n"
        "• 🖼️ BMP images\n\n"
        "_Send any image and I'll show conversion options._",
        parse_mode="Markdown"
    )

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process received image for conversion."""
    try:
        # Get the image file
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        elif update.message.document:
            doc = update.message.document
            if not doc.mime_type or not doc.mime_type.startswith("image/"):
                await update.message.reply_text(
                    "📄 This doesn't appear to be an image.\n"
                    "Please send a valid image file."
                )
                return
            file = await doc.get_file()
        else:
            return
        
        # Check file size
        if file.file_size > 10 * 1024 * 1024:  # 10MB
            await update.message.reply_text(
                "❌ Image is too large!\n"
                f"Size: {format_bytes(file.file_size)}\n"
                "Maximum allowed: 10 MB"
            )
            return
        
        # Download image
        processing_msg = await update.message.reply_text(
            "⏳ **Processing image...**\n"
            f"Size: {format_bytes(file.file_size)}",
            parse_mode="Markdown"
        )
        
        image_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Store in context
        context.user_data['last_image_bytes'] = image_bytes
        context.user_data['last_image_format'] = image.format or "Unknown"
        context.user_data['last_image_size'] = (image.width, image.height)
        
        # Show conversion options
        keyboard = [
            [
                InlineKeyboardButton("➡️ PNG", callback_data="conv_png"),
                InlineKeyboardButton("➡️ JPG", callback_data="conv_jpg"),
                InlineKeyboardButton("➡️ WEBP", callback_data="conv_webp"),
            ],
            [
                InlineKeyboardButton("➡️ BMP", callback_data="conv_bmp"),
                InlineKeyboardButton("📐 50% Size", callback_data="conv_resize_50"),
                InlineKeyboardButton("📐 200% Size", callback_data="conv_resize_200"),
            ],
            [
                InlineKeyboardButton("🔄 Rotate 90°", callback_data="conv_rotate"),
                InlineKeyboardButton("⬜ Grayscale", callback_data="conv_grayscale"),
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await processing_msg.delete()
        await update.message.reply_text(
            f"🖼️ **Image Ready!**\n\n"
            f"📐 Size: {image.width} × {image.height}\n"
            f"🎨 Format: {image.format or 'Unknown'}\n"
            f"💾 Size: {format_bytes(file.file_size)}\n\n"
            "**Choose conversion option:**",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        await update.message.reply_text(
            f"❌ **Error processing image:**\n{str(e)[:100]}\n\n"
            "Please try again with a different image."
        )

# ============================================
# AI IMAGE GENERATION HANDLER
# ============================================

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /generate command."""
    await update.message.reply_text(
        "🎨 **AI Image Generation Mode**\n\n"
        "Send me a prompt like:\n"
        "`generate: a futuristic city at night`\n\n"
        "**Examples:**\n"
        "• `generate: a cute cat wearing a hat`\n"
        "• `generate: beautiful landscape sunset`\n"
        "• `generate: cyberpunk style portrait`\n\n"
        f"📊 You have {DAILY_LIMIT} free generations per day.\n"
        "_Get creative! ✨_",
        parse_mode="Markdown"
    )

async def handle_generate(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str) -> None:
    """Generate AI image from prompt."""
    user_id = update.effective_user.id
    
    # Check rate limit
    if not check_rate_limit(user_id):
        await update.message.reply_text(
            f"❌ **Daily limit reached!**\n\n"
            f"You've used all {DAILY_LIMIT} generations for today.\n"
            f"Please try again tomorrow. 🌙\n\n"
            f"Use /stats to check your usage."
        )
        return
    
    # Check if HF client is available
    if not hf_client:
        await update.message.reply_text(
            "❌ **AI generation is not available**\n\n"
            "The bot is not configured for AI image generation.\n"
            "Please contact @Bryanjohn3456 for assistance."
        )
        return
    
    # Send processing message
    status_msg = await update.message.reply_text(
        f"🎨 **Generating your image...**\n\n"
        f"📝 Prompt: _{prompt[:100]}_\n"
        f"⏳ Estimated time: 15-30 seconds\n"
        f"📊 Remaining today: {DAILY_LIMIT - user_usage[user_id]['count']}\n\n"
        "_Please wait..._ 🎨",
        parse_mode="Markdown"
    )
    
    try:
        # Generate image
        response = await asyncio.to_thread(
            hf_client.text_to_image,
            prompt=prompt,
            model="stabilityai/stable-diffusion-2-1",
            parameters={
                "negative_prompt": "blurry, bad quality, distorted",
                "num_inference_steps": 30,
            }
        )
        
        # Save to bytes
        img_bytes = io.BytesIO()
        response.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Send generated image
        await update.message.reply_photo(
            photo=img_bytes,
            caption=(
                f"✅ **Image Generated Successfully!**\n\n"
                f"📝 Prompt: _{prompt[:150]}_\n"
                f"📊 Remaining: {DAILY_LIMIT - user_usage[user_id]['count']} today\n"
                f"🎨 Model: Stable Diffusion 2.1\n\n"
                f"_Generate more with_ `/generate` ✨"
            ),
            parse_mode="Markdown"
        )
        
        await status_msg.delete()
        
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        # Refund the user's generation (remove the count)
        if user_id in user_usage and user_usage[user_id]["count"] > 0:
            user_usage[user_id]["count"] -= 1
        
        await status_msg.edit_text(
            f"❌ **Error generating image**\n\n"
            f"Error: {str(e)[:150]}\n\n"
            f"Please try:\n"
            f"• A different prompt\n"
            f"• More specific description\n"
            f"• Use /help for tips\n\n"
            f"_Your generation has been refunded._"
        )

# ============================================
# URL SHORTENING HANDLER
# ============================================

async def shorten_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /shorten command."""
    await update.message.reply_text(
        "🔗 **URL Shortening Mode**\n\n"
        "Send me a URL to shorten.\n\n"
        "**Example:**\n"
        "`https://www.example.com/very/long/url/path`\n\n"
        "I'll give you a short, shareable link! 📏",
        parse_mode="Markdown"
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str) -> None:
    """Shorten a URL."""
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            await update.message.reply_text(
                "❌ **Invalid URL**\n\n"
                "Please send a valid URL starting with:\n"
                "• `http://`\n"
                "• `https://`"
            )
            return
        
        # Shorten
        short_url = shortener.tinyurl.short(url)
        original_len = len(url)
        short_len = len(short_url)
        
        await update.message.reply_text(
            f"✅ **URL Shortened Successfully!**\n\n"
            f"🔗 **Original:**\n`{url[:100]}`\n\n"
            f"📏 **Shortened:**\n`{short_url}`\n\n"
            f"📊 **Statistics:**\n"
            f"• Original length: {original_len} chars\n"
            f"• Shortened length: {short_len} chars\n"
            f"• Saved: **{original_len - short_len} characters** 🎉\n\n"
            f"_Copy and share your short link!_ 📋",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"URL shortening error: {e}")
        await update.message.reply_text(
            f"❌ **Error shortening URL**\n\n"
            f"{str(e)[:100]}\n\n"
            f"Please try again with a different URL."
        )

# ============================================
# CALLBACK QUERY HANDLER
# ============================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callback queries."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_data = context.user_data
    
    # Quick action buttons
    if data == "convert":
        await query.edit_message_text(
            "🖼️ **Image Conversion Mode**\n\n"
            "Send me any image, and I'll show you conversion options!\n\n"
            "_Supported formats: JPG, PNG, WEBP, BMP_"
        )
        return
    
    elif data == "generate":
        await query.edit_message_text(
            "🎨 **AI Image Generation**\n\n"
            "Type your prompt like:\n"
            "`generate: your description here`\n\n"
            f"**You get {DAILY_LIMIT} free generations daily!**\n\n"
            "_Example: generate: a beautiful waterfall in a forest_"
        )
        return
    
    elif data == "shorten":
        await query.edit_message_text(
            "🔗 **URL Shortening**\n\n"
            "Send me any URL starting with:\n"
            "• `http://`\n"
            "• `https://`\n\n"
            "_I'll give you a short, shareable link instantly!_"
        )
        return
    
    elif data == "help":
        await query.edit_message_text(
            "📖 **Quick Help**\n\n"
            "**Commands:**\n"
            "• /start - Main menu\n"
            "• /help - Full help guide\n"
            "• /stats - Your usage stats\n\n"
            "**Features:**\n"
            "• Send image → Convert\n"
            "• Send generate: prompt → AI image\n"
            "• Send URL → Shorten it\n\n"
            "_Type /help for detailed guide_"
        )
        return
    
    elif data == "stats":
        # Reuse stats command
        await stats_command(update, context)
        return
    
    elif data == "cancel":
        await query.edit_message_text(
            "❌ **Operation Cancelled**\n\n"
            "Use /start to begin again or choose from the menu above.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Main Menu", callback_data="main")]
            ])
        )
        return
    
    elif data == "main":
        await start_command(update, context)
        return
    
    # Image conversion actions
    elif data.startswith("conv_"):
        if 'last_image_bytes' not in user_data:
            await query.edit_message_text(
                "❌ **No image found!**\n\n"
                "Please send an image first.\n"
                "_Use /convert to start again_"
            )
            return
        
        await perform_conversion(update, context, data)
        return

async def perform_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """Perform actual image conversion."""
    query = update.callback_query
    user_data = context.user_data
    
    try:
        # Load image
        image_bytes = user_data['last_image_bytes']
        image = Image.open(io.BytesIO(image_bytes))
        
        # Determine action
        output_format = None
        action_type = None
        
        # Format conversions
        if action == "conv_png":
            output_format = "PNG"
            action_type = f"Converting to PNG"
        elif action == "conv_jpg":
            output_format = "JPEG"
            action_type = f"Converting to JPEG"
        elif action == "conv_webp":
            output_format = "WEBP"
            action_type = f"Converting to WEBP"
        elif action == "conv_bmp":
            output_format = "BMP"
            action_type = f"Converting to BMP"
        
        # Resize operations
        elif action == "conv_resize_50":
            width, height = image.size
            image = image.resize((width // 2, height // 2))
            output_format = image.format or "PNG"
            action_type = f"Resizing to 50%"
        elif action == "conv_resize_200":
            width, height = image.size
            image = image.resize((width * 2, height * 2))
            output_format = image.format or "PNG"
            action_type = f"Resizing to 200%"
        
        # Other operations
        elif action == "conv_rotate":
            image = image.rotate(90, expand=True)
            output_format = image.format or "PNG"
            action_type = f"Rotating 90°"
        elif action == "conv_grayscale":
            image = image.convert("L")
            output_format = image.format or "PNG"
            action_type = f"Converting to Grayscale"
        
        else:
            await query.edit_message_text("❌ Unknown conversion action.")
            return
        
        # Update status
        await query.edit_message_text(f"⏳ **{action_type}...**\n\n_Please wait..._")
        
        # Save converted image
        output_buffer = io.BytesIO()
        image.save(output_buffer, format=output_format)
        output_buffer.seek(0)
        
        # Get file size
        file_size = len(output_buffer.getvalue())
        
        # Send converted image
        await query.message.reply_document(
            document=output_buffer,
            filename=f"converted.{output_format.lower()}",
            caption=(
                f"✅ **Conversion Complete!**\n\n"
                f"🎯 Operation: {action_type}\n"
                f"📐 New Size: {image.width} × {image.height}\n"
                f"💾 File Size: {format_bytes(file_size)}\n"
                f"🎨 Format: {output_format}\n\n"
                f"_Send another image to convert more!_"
            ),
            parse_mode="Markdown"
        )
        
        await query.edit_message_text("✅ **Done!** Image converted successfully.")
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await query.edit_message_text(
            f"❌ **Conversion Error**\n\n"
            f"{str(e)[:150]}\n\n"
            f"Please try again with a different image."
        )

# ============================================
# MESSAGE HANDLER (Main dispatcher)
# ============================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Main message handler - dispatches to appropriate functions."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    # Check for generate: prompt
    if text.lower().startswith("generate:"):
        prompt = text[9:].strip()
        if not prompt:
            await update.message.reply_text(
                "❌ Please provide a description!\n"
                "Example: `generate: a cat in space`",
                parse_mode="Markdown"
            )
            return
        await handle_generate(update, context, prompt)
        return
    
    # Check for URL
    if text.startswith(("http://", "https://")):
        await handle_url(update, context, text)
        return
    
    # If none of the above, help
    await update.message.reply_text(
        "🤔 **I didn't understand that.**\n\n"
        "**Try these:**\n"
        "• `generate: your prompt` - AI Image\n"
        "• Send a URL - Shorten it\n"
        "• Send an image - Convert it\n"
        "• /start - Main menu\n"
        "• /help - Help guide\n\n"
        "_What would you like to do?_"
    )

# ============================================
# MAIN APPLICATION
# ============================================

def main() -> None:
    """Initialize and run the bot."""
    logger.info("🚀 Starting @Bryanjohn3456bot...")
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("convert", convert_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("shorten", shorten_command))
    
    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, process_image))
    application.add_handler(MessageHandler(
        filters.Document.IMAGE | filters.Document.ALL,
        process_image
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))
    
    # Add callback handler for buttons
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Start the bot
    logger.info("✅ Bot is ready! Waiting for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
