from app import logger
from app import models


class PreProcessors:
    @staticmethod
    def validate_args(amount_of_args):
        def decorator(function):
            def apply(update, context):
                if len(context.args) == amount_of_args:
                    return function(update, context, context.args[0:amount_of_args])
                else:
                    update.message.reply_text(f'Unexpected amount of arguments. Command /{function.__name__} '
                                              f'requires {amount_of_args} arguments to be passed')
            return apply

        return decorator


class BaseHandlers:
    @staticmethod
    def error(update, context):
        """Log Errors caused by Updates."""
        logger.warning(f'Update {update} \n caused error {context.error}')

    @staticmethod
    def start(update, context):
        logger.info('New user joined')
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
        context.bot.forward_message(chat_id=update.effective_chat.id,
                                    from_chat_id=update.effective_chat.id,
                                    message_id=44)


class MediaHandlers:
    @staticmethod
    def document(update, context):
        update.message.reply_text('Saved')
