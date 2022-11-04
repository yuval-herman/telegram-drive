#!/usr/bin/env python
import logging

from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from receivingFiles import file_conversation
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
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    file_list = get_user_files(user.id)
    if len(file_list) == 0:
        await update.message.reply_text("You haven't added any files yet.\nSend me any file to start saving files.")
    keyboard = [
        [InlineKeyboardButton(
            file[0], callback_data=file[1])] for file in file_list
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Click on a file to get it', reply_markup=reply_markup)


async def dirs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    file_list = get_user_files(user.id)
    if len(file_list) == 0:
        await update.message.reply_text("You haven't added any files yet.\nSend me any file to start saving files.")
    keyboard = [
        [InlineKeyboardButton(
            file[0], callback_data=file[1])] for file in file_list
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Click on a file to get it', reply_markup=reply_markup)


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
            file[0], callback_data=file[1])] for file in file_list
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Click on a file to get it', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    await query.answer()
    file_id = get_telegramID_by_id(int(query.data))
    await query.edit_message_reply_markup(None)
    await query.edit_message_text('Working on it...\nDepending on the file size this might take a while')
    await query.message.reply_document(file_id)
    await query.message.delete()


def main() -> None:
    with open('token.txt', 'r') as token_file:
        application = Application.builder().token(token_file.read()).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler('list', list))
    application.add_handler(CommandHandler('dirs', dirs))
    application.add_handler(CommandHandler('search', search_commend))

    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(file_conversation)

    application.add_handler(MessageHandler(
        filters.TEXT and ~filters.COMMAND, search_file))
    application.run_polling()


if __name__ == "__main__":
    main()
