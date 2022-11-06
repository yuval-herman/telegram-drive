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
    dir_list = get_dir_names_under_dir(user.id, None)
    if len(dir_list) == 0:
        await user.send_message("You haven't added any files yet.\nSend me any file to start saving files.")
        return ConversationHandler.END
    keyboard = [
        [InlineKeyboardButton(
            dir, callback_data=dir)] for dir in ['cancel', *dir_list]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    user_data['curr_message'] = await user.send_message(
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

    if message_text == 'cancel':
        return await cancel(update, context)
    if message_text == '../' and user_data['dir_id']:
        directory = get_parent_dir(
            user_data['dir_id'], update.effective_user.id)
        if not directory:
            await user_data['curr_message'].delete()
            return await list(update, context)
    else:
        directory = get_child_dir(user_data['dir_id'],
                                  message_text[:-1], update.effective_user.id)
    if directory:
        user_data['dir_id'] = directory[0]
        dir_files_names = get_dir_names_under_dir(
            update.effective_user.id, directory[0])
        dir_files_names.extend(get_file_names_under_dir(
            update.effective_user.id, directory[0]))
        keyboard = [
            [InlineKeyboardButton(
                dir, callback_data=dir)] for dir in ['cancel', '../', *dir_files_names] or []
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


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return ConversationHandler.END
    await update.effective_user.send_message('Wait what were we talking about again?😴')
    try:
        await cast(UserData, context.user_data)['curr_message'] \
            .delete()  # type: ignore
        await update.message.delete()
    except Exception:
        pass
    return ConversationHandler.END

file_browsing = ConversationHandler(
    entry_points=[CommandHandler('list', list)],  # type: ignore
    states={
        Browse_conversation.choose_dir: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose),
            CallbackQueryHandler(choose)
        ],
    },  # type: ignore
    fallbacks=[CommandHandler('cancel', cancel)],  # type: ignore
    conversation_timeout=60
)
