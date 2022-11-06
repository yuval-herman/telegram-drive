import json
from enum import Enum, auto
from typing import TypedDict, cast

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      Update)
from telegram.ext import (CallbackQueryHandler, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

from sqlDB import *


class Browse_conversation(Enum):
    choose_dir = auto()
    rename = auto()


class UserData(TypedDict):
    dir_id: Union[int, None]            # current dir id
    curr_message: Union[Message, None]  # last message sent from the bot
    file_id: Union[int, None]           # used for rename and delete
    old_name: str                       # used for rename


def files_dirs_keyboard(user_id: int, parent_dir: Union[int, None], extras: List[str] = []):
    dir_files_names = get_dir_names_under_dir(user_id, parent_dir)
    dir_files_names.extend(get_file_names_under_dir(user_id, parent_dir))
    keyboard = [
        [InlineKeyboardButton(
            btn, callback_data=btn)] for btn in extras
    ]
    keyboard.extend([
        [InlineKeyboardButton(file, callback_data=file),
         InlineKeyboardButton('rename', callback_data=json.dumps(['rename', file]))] for file in dir_files_names
    ])
    return InlineKeyboardMarkup(keyboard), keyboard


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return ConversationHandler.END
    user_data = cast(UserData, context.user_data)
    user_data['dir_id'] = None
    keyboard, key_list = files_dirs_keyboard(
        update.effective_user.id, None, ['cancel'])
    if len(key_list) == 0:
        await update.effective_user.send_message(
            "You haven't added any files yet.\nSend me any file to start saving files.")
        return ConversationHandler.END

    user_data['curr_message'] = await update.effective_user.send_message(
        "Click on a Directory to see it's files", reply_markup=keyboard)
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

    try:
        action, file = json.loads(message_text)
        if action == 'rename':
            await user_data['curr_message'].edit_text(f"Send {file}'s new name")
            user_data['file_id'] = get_fileID_by_name(
                update.effective_user.id, user_data['dir_id'], file)
            file = file[:-1]
            if not user_data['file_id']:
                user_data['dir_id'] = (get_child_dir(
                    user_data['dir_id'], file, update.effective_user.id) or [None])[0]
            user_data['old_name'] = file
            return Browse_conversation.rename
    except json.decoder.JSONDecodeError:
        pass

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
        await user_data['curr_message'].edit_text(
            get_dir_full_path(update.effective_user.id, directory[0]),
            reply_markup=files_dirs_keyboard(
                update.effective_user.id, directory[0], ['cancel', '../'])[0])
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


async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return ConversationHandler.END
    user_data = cast(UserData, context.user_data)
    if user_data['file_id']:
        change_file_name(update.message.text, user_data['file_id'])
    elif user_data['dir_id']:
        change_dir_name(update.message.text, user_data['dir_id'])
    if user_data['curr_message']:
        await user_data['curr_message'].edit_text(f"""change successful!\n
            {user_data["old_name"]} -> {update.message.text}""")
    else:
        await update.effective_user.send_message(f"""change successful!\n
            {user_data["old_name"]} -> {update.message.text}""")
    await update.message.delete()
    return ConversationHandler.END


file_browsing = ConversationHandler(
    entry_points=[CommandHandler('list', list)],  # type: ignore
    states={
        Browse_conversation.choose_dir: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose),
            CallbackQueryHandler(choose)
        ],
        Browse_conversation.rename: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, rename),
        ]
    },  # type: ignore
    fallbacks=[CommandHandler('cancel', cancel)],  # type: ignore
    conversation_timeout=60


)
