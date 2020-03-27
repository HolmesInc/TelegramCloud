from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from app import logger
from app.handlers import BaseHandlers, FileSystemHandlers, MediaHandlers
from app.config import TOKEN


def main():
    """Run bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", BaseHandlers.start))
    dp.add_handler(CommandHandler("help", BaseHandlers.help))
    dp.add_handler(CommandHandler("create_directory",
                                  FileSystemHandlers.create_directory,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler("show_photos", FileSystemHandlers.show_photos))
    dp.add_handler(MessageHandler(Filters.photo, MediaHandlers.document))

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
