from enum import Enum, auto
from typing import TypedDict, cast

from telegram import (InlineKeyboardButton, Message, InlineKeyboardMarkup,
                      Update)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler,
                          filters, CallbackQueryHandler, CommandHandler)

from sqlDB import *


class Browse_conversation(Enum):
    choose_dir = auto()


class UserData(TypedDict):
    dir_id: Union[int, None]            # current dir id
    curr_message: Union[Message, None]  # last message sent from the bot


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return ConversationHandler.END
    user_data = cast(UserData, context.user_data)
    user_data['dir_id'] = None
    dir_list = get_user_top_dirs(user.id)
    if len(dir_list) == 0:
        await update.message.reply_text("You haven't added any files yet.\nSend me any file to start saving files.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(
            dir[3], callback_data=dir[3])] for dir in dir_list
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    user_data['curr_message'] = await update.message.reply_text(
        "Click on a Directory to see it's files", reply_markup=reply_markup)
    return Browse_conversation.choose_dir


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called until user chooses a directory for upload or cancels the conversation"""
    if not update.effective_user:
        return ConversationHandler.END

    query = update.callback_query
    if query:
        await query.answer()
        message_text = query.data
    else:
        message_text = update.message.text
    user_data = cast(UserData, context.user_data)
    if not user_data['curr_message']:
        user_data['curr_message'] = await update.effective_user.send_message('Thinking...')
    directory = get_dir(user_data['dir_id'],
                        message_text, update.effective_user.id)
    if directory:
        user_data['dir_id'] = directory[0]
        dir_files_names = get_dir_names_under_dir(
            update.effective_user.id, directory[0])
        dir_files_names.extend(get_file_names_under_dir(
            update.effective_user.id, directory[0]))
        keyboard = [
            [InlineKeyboardButton(
                dir, callback_data=dir)] for dir in dir_files_names or []
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await user_data['curr_message'].edit_text(get_dir_full_path(update.effective_user.id, directory[0]), reply_markup=reply_markup)
        return
    elif user_data['dir_id']:
        file_id = get_telegramID_by_name(
            update.effective_user.id, user_data['dir_id'], message_text)
        if file_id:
            await user_data['curr_message'].edit_text('Sending the file, give me a moment...')
            await update.effective_user.send_document(file_id)
            await user_data['curr_message'].delete()
            return ConversationHandler.END

    await user_data['curr_message'].edit_text('There is no such file or directory')
    return ConversationHandler.END


file_browsing = ConversationHandler(
    entry_points=[CommandHandler('list', list)],  # type: ignore
    states={
        Browse_conversation.choose_dir: [
            MessageHandler(filters.TEXT, choose),
            CallbackQueryHandler(choose)
        ],
    },  # type: ignore
    fallbacks=[],
)
