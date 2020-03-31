from app import logger
from app import models
from app.config import ROOT_DIRECTORY, CANCEL_BUTTON, DIRECTORY_ACTIONS
from telegram.error import BadRequest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from functools import reduce


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
                        f'Unexpected amount of arguments.\nCommand "{update.message.text}" requires {amount_of_args} '
                        f'arguments to be passed.\nCheck "/help" command if you have any issues'
                    )
            return apply

        return decorator

    @staticmethod
    def set_root_directory(function):
        """ Set up ROOT_DIRECTORY, if chat_data doesn't contain one
        """
        def decorator(update, context, *args, **kwargs):
            current_directory = context.chat_data.get('current_directory')
            if not current_directory:
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
        update.message.reply_text('Welcome to Telegram Cloud bot. I will help you to store an manage your photos. '
                                  'Now you are in a root directory. '
                                  'You can upload your photos here, or create you on directories to '
                                  'store your files im more manageable way')

    @staticmethod
    def help(update, context):
        logger.info('Incoming help request')
        update.message.reply_text(
            'Commands description:\n'
            '/create <Directory Name> - Creates a new directory in the current one. '
            'Directory name should be without whitespaces;\n'
            '/delete - Display list of subdirectories, located in the current directory, to delete one;\n'
            '/current - Display the name of current directory;\n'
            '/dirs - Display subdirectories of the current directory;\n'
            '/goto - Display list of subdirectories, located in the current directory, to be redirected to;\n'
            '/back - Redirect user to parent directory of the current one;\n'
            '/show - Display files, stored in the current directory.'
        )


class FileSystemHandlers:
    @staticmethod
    def __create_subdirectories_keyboard(current_directory: object, action: str) -> list:
        """ NOTE: this method assumes, that <current_directory> contains subdirectories and there is no
            need for additional validation

        :param current_directory: Directory instance
        :param action: type of action, that should be performed over directory
        :return: list with directories
        """
        def __reducer(result: list, directory: object):
            """ Divides array of subdirectories, stored at directory.contains_directories to list of two
                items lists to have well readable inline keyboard
            Example: [Dir1, Dir2, Dir3, Dir4, Dir5] -> __reducer() -> [[Dir1, Dir2], [Dir3, Dir4], [Dir5]]

            :param result: list of two items lists
            :param directory: Directory instance
            :return: [[Dir1, Dir2], [Dir3, Dir4], [Dir5]]
            """
            if len(result[-1]) == 2:
                result.append([])
            result[-1].append(InlineKeyboardButton(directory.name, callback_data=f"{action},{directory.name}"))

            return result

        keyboard = reduce(__reducer, current_directory.contains_directories, [[]])
        keyboard.append([InlineKeyboardButton(CANCEL_BUTTON, callback_data=f"{action},{CANCEL_BUTTON}")])

        return keyboard

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
        if models.Directory.exists(name):
            update.message.reply_text(f"The directory '{name}' already exists")
        else:
            # create new directory
            new_directory = models.Directory(name=name)
            new_directory.save()
            # add new directory as a sub directory to current_directory
            current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
            current_directory.update(add_to_set__contains_directories=new_directory)
            current_directory.save()
            update.message.reply_text(
                f"The directory '{name}' is successfully created and saved in {current_directory.name} directory"
            )

    @staticmethod
    @PreProcessors.set_root_directory
    def remove_directory(update, context):
        """ Remove selected subdirectory

        :param update: Telegram chat data
        :param context: Telegram chat data
        """
        current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))

        if current_directory.contains_directories:

            keyboard = FileSystemHandlers.__create_subdirectories_keyboard(
                current_directory, DIRECTORY_ACTIONS['delete']
            )

            update.message.reply_text(
                'Choose the folder, that you want to delete',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            update.message.reply_text(
                f"There are no subdirectories in the directory {context.chat_data.get('current_directory')}"
            )

    @staticmethod
    @PreProcessors.set_root_directory
    def show_subdirectories(update, context):
        """ Show subdirectories of current directory

        :param update: Telegram chat data
        :param context: Telegram chat data
        """
        current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
        if current_directory.contains_directories:
            subdirectories = reduce(
                lambda res, directory: f"{res} {directory.name}",
                current_directory.contains_directories,
                ""
            )

            update.message.reply_text(
                f"Current directory {context.chat_data.get('current_directory')} "
                f"contains the following subdirectories: {subdirectories}"
            )
        else:
            update.message.reply_text(
                f"There are no subdirectories in the directory {context.chat_data.get('current_directory')}"
            )

    @staticmethod
    @PreProcessors.set_root_directory
    def current_directory(update, context):
        """ Send current directory, that user located in now
        """
        current_directory = context.chat_data.get('current_directory')
        update.message.reply_text(f"Current directory is {current_directory}")

    @staticmethod
    @PreProcessors.set_root_directory
    def go_to_directory(update, context):
        """ Create a buttons template. Buttons are names of subdirectories, that current directory contains.
            By clicking on one of buttons user will be redirected to selected directory
        """
        current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
        if current_directory.contains_directories:

            keyboard = FileSystemHandlers.__create_subdirectories_keyboard(
                current_directory, DIRECTORY_ACTIONS['goto']
            )

            update.message.reply_text(
                'Choose the folder, that you want go to',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            update.message.reply_text(
                f"There are no subdirectories in the directory {context.chat_data.get('current_directory')}"
            )

    @staticmethod
    @PreProcessors.set_root_directory
    def return_to_parent_directory(update, context):
        """ Moving user back to parent directory of current directory
        """
        current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
        parent_directory = models.Directory.objects.get(contains_directories=current_directory)

        def __handle_successfully_switched():
            context.chat_data['current_directory'] = parent_directory.name
            update.message.reply_text(f"You now switched to directory {parent_directory.name}")

        def __handle_dir_with_no_parents():
            if current_directory.name != ROOT_DIRECTORY:
                context.chat_data['current_directory'] = ROOT_DIRECTORY
                logger.error(f"Unexpected accident: directory {current_directory.name} "
                             f"doesn't have a parent directory. User were redirected to root directory")

            update.message.reply_text(f"You now in the root directory")

        if parent_directory:
            __handle_successfully_switched()

        else:
            __handle_dir_with_no_parents()

    @staticmethod
    @PreProcessors.set_root_directory
    def process_keyboard(update, context):
        """ A callback for go_to_directory() and remove_directory() methods, that perform directory change to
            selected one
        """
        query = update.callback_query
        action, directory = query.data.split(',')
        current_directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))

        def _goto_handler(directory_name):
            if current_directory.has_subdirectory(directory_name):
                context.chat_data['current_directory'] = directory_name
                query.answer()
                query.edit_message_text(text=f"You now switched to directory {directory_name}")

            else:
                context.chat_data['current_directory'] = ROOT_DIRECTORY
                logger.error(f"Unexpected accident: <directory.has_subdirectory> returned False for directory "
                             f"{directory_name}. current_directory={current_directory}, action={action}, "
                             f"directory={directory_name}. User were redirected to root directory")

                query.edit_message_text(f"Wow, you've broke me somehow..\nSo i switched you to root directory")

        def _delete_handler(directory_name):
            if current_directory.has_subdirectory(directory_name):
                subdirectory = models.Directory.objects.get(name=directory_name)
                subdirectory.delete()

                query.edit_message_text(
                    f"The directory '{directory_name}' and it's files are successfully deleted from current "
                    f"{current_directory.name} directory"
                )
            else:
                query.edit_message_text(f"Seems, the directory '{directory_name}' is already deleted")

        if directory == CANCEL_BUTTON:
            query.edit_message_text(text=f"Operation were canceled")
        else:
            action_map = {
                DIRECTORY_ACTIONS['goto']: _goto_handler,
                DIRECTORY_ACTIONS['delete']: _delete_handler,
            }

            handler = action_map[action]
            handler(directory)


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
        update.message.reply_text(f'Your file now live in directory {directory.name}')

    @staticmethod
    @PreProcessors.set_root_directory
    def show_photo(update, context):
        """ Send all photos from current directory
        """
        directory = models.Directory.objects.get(name=context.chat_data.get('current_directory'))
        if not directory.contains_files:
            update.message.reply_text('There are no photos stored in current directory')
        else:
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
