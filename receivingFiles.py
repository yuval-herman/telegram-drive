from enum import Enum, auto

from telegram import (Document, KeyboardButton, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update, error)
from telegram.ext import (ContextTypes, ConversationHandler, MessageHandler,
                          filters)

from sqlDB import *


class File_conversation(Enum):
    choose_dir = auto()


async def file_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save file to DB"""
    if not update.effective_user:
        return
    received_file = update.message.effective_attachment
    file_name = 'unknown file'
    if context.user_data is None:
        context.user_data = {}
    if isinstance(received_file, Document):
        file_name = f'{received_file.file_name} {received_file.mime_type} file'
        file_id = insert_file(received_file.file_name, received_file.file_id,
                              update.effective_user.id)
        context.user_data['last_file_id'] = file_id
        context.user_data['dir_parent_id'] = None
    options = ['cancel']
    options.extend(get_root_dir_names(update.effective_user.id) or [])
    keyboard = [
        [KeyboardButton(
            option, callback_data=option)] for option in (options)
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)
    context.user_data['curr_message'] = (
        await update.message.reply_text(f'Got your {file_name}!\nwhere would you like to save it?', reply_markup=reply_markup))
    await update.message.delete()
    return File_conversation.choose_dir


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save file to DB"""
    if not update.effective_user or not context.user_data:
        return ConversationHandler.END
    if 'last_file_id' not in context.user_data:
        await update.message.reply_text('some error occurred... sorry🙇')
        context.user_data.clear()
        return ConversationHandler.END
    if update.message.text == 'upload here':
        if 'dir_id' not in context.user_data:
            try:
                await context.user_data['curr_message'].edit_text("can't upload to the root directory.\n" +
                                                                  "create a directory first by sending any name and upload your file there.")
            except error.BadRequest:
                context.user_data['curr_message'] = await update.message.reply_text("can't upload to the root directory.\n" +
                                                                                    "create a directory first by sending any name and upload your file there.")
            return
        change_file_dir(
            context.user_data['last_file_id'], context.user_data['dir_id'])
        try:
            await context.user_data['curr_message'].edit_text("uploaded successfully", reply_markup=ReplyKeyboardRemove())
        except error.BadRequest:
            context.user_data['curr_message'] = await update.message.reply_text("uploaded successfully", reply_markup=ReplyKeyboardRemove())

        await update.message.delete()
        context.user_data.clear()
        return ConversationHandler.END
    if update.message.text == 'cancel':
        try:
            await context.user_data['curr_message'].edit_text("Alright, I'm just gonna forget you did that👀")
        except error.BadRequest:
            context.user_data['curr_message'] = await update.message.reply_text("Alright, I'm just gonna forget you did that👀")
        context.user_data.clear()
        return ConversationHandler.END

    options = ['upload here', 'cancel']
    options.extend(get_dir_names_under_dir(
        update.effective_user.id, context.user_data.get('dir_id')) or [])
    keyboard = [
        [KeyboardButton(
            option, callback_data=option)] for option in (options)
    ]

    reply_markup = ReplyKeyboardMarkup(keyboard)
    directory = get_dir_tree(
        context.user_data.get('dir_id'), update.message.text, update.effective_user.id)
    if directory:
        try:
            await context.user_data['curr_message'].edit_text(str(directory[3]), reply_markup=reply_markup)
        except error.BadRequest:
            context.user_data['curr_message'] = await update.message.reply_text(str(directory[3]), reply_markup=reply_markup)
        await update.message.delete()
        context.user_data['dir_id'] = directory[0]
        return
    await update.message.delete()
    await context.user_data['curr_message'].edit_text(f"created new directory '{update.message.text}'")
    context.user_data['dir_id'] = (insert_dir(
        context.user_data.get('dir_id'), update.effective_user.id, update.message.text))


file_conversation = ConversationHandler(
    entry_points=[MessageHandler(
        filters.ATTACHMENT, file_received)],
    states={
        File_conversation.choose_dir: [
            MessageHandler(filters.TEXT, choose),
        ],
    },
    fallbacks=[],
)
