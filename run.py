from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
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


def main():
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # internal services set-up
    set_up()
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", BaseHandlers.start))
    dp.add_handler(CommandHandler("help", BaseHandlers.help))
    dp.add_handler(CommandHandler(
        "create_directory",
        FileSystemHandlers.create_directory,
        pass_args=True,
        pass_job_queue=True,
        pass_chat_data=True
    ))
    dp.add_handler(CommandHandler(
        "current_directory",
        FileSystemHandlers.current_directory,
        pass_job_queue=True,
        pass_chat_data=True
    ))
    dp.add_handler(CommandHandler("show_photos", FileSystemHandlers.show_photos))
    dp.add_handler(MessageHandler(Filters.photo, MediaHandlers.save_photo))

    # log all errors
    dp.add_error_handler(BaseHandlers.error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    logger.info('TelegramCloud app has started')
    main()
