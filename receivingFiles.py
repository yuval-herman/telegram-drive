from enum import Enum, auto
from typing import TypedDict, cast

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      Message, Update)
from telegram.ext import (CallbackQueryHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

from sqlDB import *


class File_conversation(Enum):
    choose_dir = auto()


class UserData(TypedDict):
    last_file_id: Union[List[int], None]      # last received file from user
    dir_id: Union[int, None]            # current dir id
    dir_parent_id: Union[int, None]     # current dir parent id
    curr_message: Union[Message, None]  # last message sent from the bot
    mid_conversation: bool


async def file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when receiving a document"""
    if not update.effective_user:
        return ConversationHandler.END

    user = update.effective_user
    user_data = cast(UserData, context.user_data)
    received_file = update.message.document
    file_name = received_file.file_name
    file_id = insert_file(file_name, received_file.file_id,
                          user.id)

    if user_data.get('mid_conversation') and isinstance(user_data['last_file_id'], list):
        user_data['last_file_id'].append(file_id)
    else:
        user_data['last_file_id'] = [file_id]

    user_data['dir_id'] = None
    user_data['dir_parent_id'] = None

    options = ['cancel']

    options.extend(get_root_dir_names(user.id) or [])
    keyboard = [
        [InlineKeyboardButton(
            option, callback_data=option)] for option in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    reply_msg = f'I got your file, {file_name}!\n' + \
        'where would you like to save it?'
    if len(user_data['last_file_id']) > 1:
        reply_msg = f'I got {len(user_data["last_file_id"])} files!\n Where would you like to save them?'
        await user_data['curr_message'].delete()  # type: ignore
    user_data['curr_message'] = await update.message.reply_text(reply_msg, reply_markup=reply_markup)
    try:
        await update.message.delete()
    except AttributeError:
        pass
    user_data['mid_conversation'] = True
    return File_conversation.choose_dir


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
    if not user_data['last_file_id']:
        await update.message.reply_text('critical error occurred.\n please try again later')
        user_data['mid_conversation'] = False
        return ConversationHandler.END

    if not user_data['curr_message']:
        user_data['curr_message'] = await update.effective_user.send_message('Thinking...')

    if message_text == 'upload here':
        if not user_data['dir_id']:
            await user_data['curr_message'].edit_text("can't upload to the root directory.\n" +
                                                      "create a directory first by sending any name and upload your file there.")
            return
        for file in user_data['last_file_id']:
            change_file_dir(
                file, user_data['dir_id'])
        await user_data['curr_message'].edit_text("uploaded successfully", reply_markup=InlineKeyboardMarkup([]))

        try:
            await update.message.delete()
        except AttributeError:
            pass
        user_data['mid_conversation'] = False
        return ConversationHandler.END
    if message_text == 'cancel':
        await user_data['curr_message'].edit_text("Alright, I'm just gonna forget you did that👀", reply_markup=InlineKeyboardMarkup([]))
        user_data['mid_conversation'] = False
        return ConversationHandler.END

    directory = get_dir(user_data.get('dir_id'),
                        message_text, update.effective_user.id)
    if directory:
        # generate reply options
        options = ['upload here', 'cancel']
        options.extend(get_dir_names_under_dir(
            update.effective_user.id, user_data.get('dir_id')) or [])
        keyboard = [[InlineKeyboardButton(
            option, callback_data=option)] for option in options]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await user_data['curr_message'].edit_text(directory[3], reply_markup=reply_markup)
        try:
            await update.message.delete()
        except AttributeError:
            pass
        user_data['dir_id'] = directory[0]
        return
    try:
        await update.message.delete()
    except AttributeError:
        pass
    options = ['upload here', 'cancel']
    keyboard = [[InlineKeyboardButton(
        option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await user_data['curr_message'].edit_text(f"created new directory '{message_text}'", reply_markup=reply_markup)
    user_data['dir_id'] = (insert_dir(user_data.get(
        'dir_id'), update.effective_user.id, message_text))


file_conversation = ConversationHandler(
    entry_points=[MessageHandler(
        filters.Document.ALL, file_received)],  # type: ignore
    states={
        File_conversation.choose_dir: [
            MessageHandler(filters.Document.ALL, file_received),
            MessageHandler(filters.TEXT, choose),
            CallbackQueryHandler(choose)
        ],
    },  # type: ignore
    fallbacks=[], conversation_timeout=60
)
