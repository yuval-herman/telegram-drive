#!/usr/bin/env python
import logging

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from receivingFiles import file_conversation
from browseFiles import file_browsing
from sqlDB import *

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if not user:
        return
    await update.message.reply_html(f"Hi {user.mention_html()}!\n" +
                                    "Here is how to use this bot, to show help at any time send /help.")
    await help(update, context)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    if not user:
        return
    await update.message.reply_html(
        "Send any file as a document to save it.\n"
        "Send a text message to search all your files.\n"
        "Send /list to view all your folders and retrieve a file.\n"
    )


async def search_commend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    await update.message.reply_text('Send me the name of the file you want to search for.')


async def search_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    file_list = search_file_for_user(user.id, update.message.text)
    if len(file_list) == 0:
        await update.message.reply_text(f"Didn't find anything with '{update.message.text}' in it🤷.")
    keyboard = [
        [InlineKeyboardButton(
            get_dir_full_path(user.id, file[2])+file[0], callback_data=file[1])] for file in file_list
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Click on a file to get it', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    if not query.data.isdigit():
        await query.answer('This button is not active anymore')
        return
    await query.answer()
    file_id = get_telegramID_by_id(int(query.data))
    await query.edit_message_reply_markup(None)
    await query.edit_message_text('Working on it...\nDepending on the file size this might take a while')
    await query.message.reply_document(file_id)
    await query.message.delete()


async def bad_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "I can't process files not sent as documents.\n" +
        "If you are trying to upload an image file, make sure the 'Compress images' flag is unchecked")


def main() -> None:
    with open('token.txt', 'r') as token_file:
        application = Application.builder().token(token_file.read()).build()

    application.add_handler(file_conversation)
    application.add_handler(file_browsing)

    application.add_handler(MessageHandler(
        filters.ATTACHMENT & ~filters.Document.ALL, bad_data))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler('search', search_commend))
    application.add_handler(CommandHandler('help', help))

    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(MessageHandler(
        filters.TEXT and ~filters.COMMAND, search_file))
    application.run_polling()


if __name__ == "__main__":
    main()
