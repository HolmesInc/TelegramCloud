from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from app import logger
from app.config import TOKEN, ROOT_DIRECTORY
from app.models import Directory
from app.handlers import BaseHandlers, FileSystemHandlers, MediaHandlers


def set_up():
    """ Setting up bot internal services during start up
    """
    root_directory = Directory.objects.get(name=ROOT_DIRECTORY)
    if root_directory:
        pass
    else:
        Directory(name=ROOT_DIRECTORY).save()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    return updater, dp


def main():
    """Run bot."""
    updater, dispatcher = set_up()

    ###########################################################################
    # Commands
    ###########################################################################
    dispatcher.add_handler(CommandHandler("start", BaseHandlers.start))
    dispatcher.add_handler(CommandHandler("help", BaseHandlers.help))
    dispatcher.add_handler(CommandHandler(
        "create",
        FileSystemHandlers.create_directory,
        pass_args=True,
        pass_job_queue=True,
        pass_chat_data=True
    ))
    dispatcher.add_handler(CommandHandler(
        "current",
        FileSystemHandlers.current_directory,
        pass_job_queue=True,
        pass_chat_data=True
    ))
    dispatcher.add_handler(CommandHandler("show", MediaHandlers.show_photo))
    dispatcher.add_handler(CommandHandler("goto", FileSystemHandlers.go_to))
    dispatcher.add_handler(CommandHandler("goback", FileSystemHandlers.go_back))
    ###########################################################################
    # Message handlers
    ###########################################################################
    dispatcher.add_handler(MessageHandler(Filters.photo, MediaHandlers.save_photo))
    ###########################################################################
    # Callback handlers
    ###########################################################################
    dispatcher.add_handler(CallbackQueryHandler(FileSystemHandlers.button))
    ###########################################################################
    # Error handlers
    ###########################################################################
    dispatcher.add_error_handler(BaseHandlers.error)
    ###########################################################################

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    logger.info('TelegramCloud app has started')
    main()
