from app import logger
from app import models
from telegram.error import BadRequest


class PreProcessors:
    @staticmethod
    def validate_args(amount_of_args):
        def decorator(function):
            def apply(update, context):
                if len(context.args) == amount_of_args:
                    return function(
                        update, context, context.args[0:amount_of_args]
                    )
                else:
                    update.message.reply_text(
                        f'Unexpected amount of arguments. Command /{function.__name__} requires {amount_of_args} '
                        f'arguments to be passed'
                    )
            return apply

        return decorator


class BaseHandlers:
    @staticmethod
    def error(update, context):
        """Log Errors caused by Updates."""
        logger.warning(f'{context.error}')

    @staticmethod
    def start(update, context):
        logger.info('New user joined')
        # custom_keyboard = [['top-left', 'top-right'],
        #                    ['bottom-left', 'bottom-right']]
        # reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        # context.bot.send_message(chat_id=update.effective_chat.id,
        #                  text="Custom Keyboard Test",
        #                  reply_markup=reply_markup)
        update.message.reply_text('Hi! Use /set <seconds> to set a timer')

    @staticmethod
    def help(update, context):
        logger.info('Incoming help request')
        update.message.reply_text('Commands description:')
        update.message.reply_text('/create_directory <Directory Name> - Creates a new directory in the current one')
        update.message.reply_text('/current_directory - Shows the name of current directory')
        update.message.reply_text('Help is going to be implemented (or not :) )')


class FileSystemHandlers:
    @staticmethod
    @PreProcessors.validate_args(1)
    def create_directory(update, context, name):
        name = name[0]
        directory = models.Directory(name=name)
        directory.save()
        update.message.reply_text(f'The directory "{name}" is successfully created')

    @staticmethod
    def current_directory(update, context):
        update.message.reply_text('To be implemented)')

    @staticmethod
    def show_photos(update, context):
        directory = models.Directory.objects.first()  # ADD SELECTION OF DIRECTORY
        for photo in directory.contains_files:
            try:
                context.bot.forward_message(
                    chat_id=update.effective_chat.id,
                    from_chat_id=update.effective_chat.id,
                    message_id=models.File.prepare_telegram_id(photo.telegram_id)
                )
            except BadRequest as bad_request:
                no_message = 'Message to forward not found'
                if str(bad_request) == no_message:
                    continue
                else:
                    raise


class MediaHandlers:
    @staticmethod
    def document(update, context):
        photo = models.File(telegram_id=update.message.message_id)
        photo.save()
        directory = models.Directory.objects.first()  # ADD SELECTION OF DIRECTORY
        directory.contains_files.append(photo)
        directory.save()
        update.message.reply_text('Saved')
