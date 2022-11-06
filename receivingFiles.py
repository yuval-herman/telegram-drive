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
    last_file_id: Union[int, None]      # last received file from user
    dir_id: Union[int, None]            # current dir id
    dir_parent_id: Union[int, None]     # current dir parent id
    curr_message: Union[Message, None]  # last message sent from the bot


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

    # initialize user data for conversation
    user_data['last_file_id'] = file_id
    user_data['dir_id'] = None
    user_data['dir_parent_id'] = None
    user_data['curr_message'] = None

    options = ['cancel']

    options.extend(get_root_dir_names(user.id) or [])
    keyboard = [
        [InlineKeyboardButton(
            option, callback_data=option)] for option in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_data['curr_message'] = (
        await update.message.reply_text(f'I got your file, {file_name}!\n' +
                                        'where would you like to save it?', reply_markup=reply_markup))
    try:
        await update.message.delete()
    except AttributeError:
        pass
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
        return ConversationHandler.END

    if not user_data['curr_message']:
        user_data['curr_message'] = await update.effective_user.send_message('Thinking...')

    if message_text == 'upload here':
        if not user_data['dir_id']:
            await user_data['curr_message'].edit_text("can't upload to the root directory.\n" +
                                                      "create a directory first by sending any name and upload your file there.")
            return
        change_file_dir(
            user_data['last_file_id'], user_data['dir_id'])
        await user_data['curr_message'].edit_text("uploaded successfully", reply_markup=InlineKeyboardMarkup([]))

        try:
            await update.message.delete()
        except AttributeError:
            pass
        return ConversationHandler.END
    if message_text == 'cancel':
        await user_data['curr_message'].edit_text("Alright, I'm just gonna forget you did that👀", reply_markup=InlineKeyboardMarkup([]))
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
            MessageHandler(filters.TEXT, choose),
            CallbackQueryHandler(choose)
        ],
    },  # type: ignore
    fallbacks=[],
)
