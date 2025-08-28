import logging
import os

from colorama import Fore, Style
from datetime import datetime
from platformdirs import user_data_dir

APP_NAME = "vocab_sprint"

# generate unique log file name for each run
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE_NAME = f"log_{TIMESTAMP}.log"

# log directory
# Windows: C:\Users\<user>\AppData\Local\{APP_NAME}\Logs
# macOS: ~/Library/Logs/{APP_NAME}/Logs
# Linux: ~/.local/share/logs

class ColoredFormatter(logging.Formatter):
    """
    Custom colored formatter for logging.
    """
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.WHITE,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        # get original format
        log_message = super().format(record)
        
        # add color based on log level
        color = self.COLORS.get(record.levelname, Fore.WHITE)
        return f"{color}{log_message}{Style.RESET_ALL}"

class Logger:
    def __init__(self, module_name: str, level=logging.DEBUG):
        self.log_dir = user_data_dir("logs", APP_NAME)
        self.logger = logging.getLogger(module_name)

        # set default level to info
        self.logger.setLevel(level)

        # check if logger already has handler
        if self.logger.handlers:
            return

        # create a console handler
        console_handler = logging.StreamHandler()
        
        # create a file handler
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        file_handler = logging.FileHandler(f"{self.log_dir}/{LOG_FILE_NAME}", mode="a", encoding='utf-8')

        # create a formatter
        formatter = logging.Formatter(
            "[%(asctime)s] | [%(name)s] | [%(levelname)s] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # create colored formatter for console
        colored_formatter = ColoredFormatter(
            "[%(asctime)s] | [%(name)s] | [%(levelname)s] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # add formatter to console handler
        console_handler.setFormatter(colored_formatter)
        # add formatter to file handler
        file_handler.setFormatter(formatter)

        # add console handler to logger
        self.logger.addHandler(console_handler)
        # add file handler to logger
        self.logger.addHandler(file_handler)
    
    def DEBUG(self, message):
        self.logger.debug(message)

    def INFO(self, message):
        self.logger.info(message)

    def WARN(self, message):
        self.logger.warning(message)

    def ERROR(self, message):
        self.logger.error(message)

    def CRITICAL(self, message):
        self.logger.critical(message)

    def get_level(self):
        return self.logger.level

    def set_level(self, level):
        self.logger.setLevel(level)

    def get_name(self):
        return self.logger.name
    
    def set_name(self, name):
        self.logger.name = name

    def get_logger(self):
        return self.logger
    
    def set_logger(self, logger):
        self.logger = logger


# # test logger
# logger = Logger("test_logger")
# logger.DEBUG("This is a debug message")
# logger.INFO("This is an info message")
# logger.WARN("This is a warning message")
# logger.ERROR("This is an error message")
# logger.CRITICAL("This is a critical message")