from app import logger
from app import models
from app.config import ROOT_DIRECTORY
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
                        f'Unexpected amount of arguments. Command /create_directory requires {amount_of_args} '
                        f'arguments to be passed'
                    )
            return apply

        return decorator

    @staticmethod
    def set_root_directory(function):
        """ Set up ROOT_DIRECTORY, if chat_data doesn't contain one
        """
        def decorator(update, context, *args, **kwargs):
            current_directory = context.chat_data.get('current_directory')
            if current_directory:
                pass
            else:
                context.chat_data['current_directory'] = ROOT_DIRECTORY
            function(update, context, *args, **kwargs)
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
    @PreProcessors.set_root_directory
    def create_directory(update, context, name):
        """ Create new directory in the current one

        :param update: Telegram chat data
        :param context: Telegram chat data
        :param name: name of a directory to be created
        """
        name = name[0]
        # check if directory exists
        if models.Directory.objects.get(name=name):
            update.message.reply_text(f'The directory "{name}" already exists')
        else:
            # create new directory
            new_directory = models.Directory(name=name)
            new_directory.save()
            # add new directory as a sub directory to current_directory
            current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
            current_directory.update(add_to_set__contains_directories=new_directory)  # , upsert=True
            current_directory.save()
            update.message.reply_text(f'The directory "{name}" is successfully created')

    @staticmethod
    @PreProcessors.set_root_directory
    def current_directory(update, context):
        """ Send current directory, that user located in now
        """
        current_directory = context.chat_data.get('current_directory')
        update.message.reply_text(f"Current directory is {current_directory}")

    @staticmethod
    @PreProcessors.set_root_directory
    def show_photos(update, context):
        """ Send all photos from current directory
        """
        directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
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
    @PreProcessors.set_root_directory
    def save_photo(update, context):
        """ Add given photo to current directory
        """
        # create new record about the file in the DB
        photo = models.File(telegram_id=update.message.message_id)
        photo.save()
        # attach new file to current directory
        directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
        directory.update(add_to_set__contains_files=photo)
        directory.save()
        update.message.reply_text('Your file is saved')
