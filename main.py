import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# Telegram Bot Token
TOKEN = os.getenv("TOKEN") 

# Genius API Token
GENIUS_API_TOKEN = os.getenv("GENIUS_API_TOKEN")

# Your Channel and Group Details
CHANNEL_ID = -1002682987275
GROUP_ID = -1002375756524
CHANNEL_LINK = "https://t.me/latest_animes_world"
GROUP_LINK = "https://t.me/All_anime_chat"

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to check user membership
async def is_member(user_id, context):
    try:
        chat_member_channel = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        chat_member_group = await context.bot.get_chat_member(GROUP_ID, user_id)

        # Check if the user is at least a member in both the channel and the group
        return chat_member_channel.status in ["member", "administrator", "creator"] and \
               chat_member_group.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

# Function to get lyrics from Genius
def get_lyrics(song_name):
    base_url = "https://api.genius.com"
    search_url = f"{base_url}/search"
    
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    params = {"q": song_name}

    response = requests.get(search_url, headers=headers, params=params)
    if response.status_code != 200:
        return "❌ Error: Unable to connect to Genius API."

    data = response.json()
    hits = data["response"]["hits"]

    if not hits:
        return "❌ Lyrics not found."

    song_url = hits[0]["result"]["url"]  # First result
    return f"🎵 Lyrics found! Click below:\n{song_url}"

# /start command handler with inline buttons
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if await is_member(user_id, context):
        await update.message.reply_text("✅ You are verified! Send me a song name, and I'll fetch the lyrics for you!")
        return

    # Inline keyboard for join verification
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("💬 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("✅ I've Joined", callback_data="verify_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔒 *To use this bot, you must join our official channel and group.*\n\n"
        f"📢 *Join the Channel:* [Click Here]({CHANNEL_LINK})\n"
        f"💬 *Join the Group:* [Click Here]({GROUP_LINK})\n\n"
        "After joining, tap *'I've Joined'* below.",
        parse_mode="Markdown",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

# Callback handler for "I've Joined" button
async def verify_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if await is_member(user_id, context):
        await query.message.edit_text("✅ You are verified! Send me a song name, and I'll fetch the lyrics for you!")
    else:
        await query.answer("❌ You haven't joined both the channel and group yet!", show_alert=True)

async def fetch_lyrics(update: Update, context: CallbackContext):
    # Ignore messages in groups
    if update.message.chat.type in ["group", "supergroup"]:
        return

    user_id = update.message.from_user.id

    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("💬 Join Group", url=GROUP_LINK)],
            [InlineKeyboardButton("✅ I've Joined", callback_data="verify_join")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "❌ *You must join both the channel and group to use this bot!*\n\n"
            f"📢 *Join the Channel:* [Click Here]({CHANNEL_LINK})\n"
            f"💬 *Join the Group:* [Click Here]({GROUP_LINK})\n\n"
            "After joining, tap *'I've Joined'* below.",
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return

    song_name = update.message.text
    await update.message.reply_text("🔍 Searching for lyrics...")

    lyrics = get_lyrics(song_name)
    await update.message.reply_text(lyrics)

# Main function
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_lyrics))
    app.add_handler(CallbackQueryHandler(verify_join, pattern="verify_join"))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
