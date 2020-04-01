from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from app import logger
from app.config import TOKEN
from app.handlers import BaseHandlers, FileSystemHandlers, MediaHandlers


def set_up():
    """ Setting up bot internal services during start up
    """
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    return updater, dp


def main():
    """ Main function that runs bot
    """
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
        "delete",
        FileSystemHandlers.remove_directory,
        pass_args=True
    ))
    dispatcher.add_handler(CommandHandler(
        "current",
        FileSystemHandlers.current_directory,
        pass_job_queue=True,
        pass_chat_data=True
    ))
    dispatcher.add_handler(CommandHandler(
        "dirs",
        FileSystemHandlers.show_subdirectories
    ))
    dispatcher.add_handler(CommandHandler("show", MediaHandlers.show_photo))
    dispatcher.add_handler(CommandHandler("goto", FileSystemHandlers.go_to_directory))
    dispatcher.add_handler(CommandHandler("back", FileSystemHandlers.return_to_parent_directory))
    ###########################################################################
    # Message handlers
    ###########################################################################
    dispatcher.add_handler(MessageHandler(Filters.photo, MediaHandlers.save_photo))
    ###########################################################################
    # Callback handlers
    ###########################################################################
    dispatcher.add_handler(CallbackQueryHandler(FileSystemHandlers.process_keyboard))
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
