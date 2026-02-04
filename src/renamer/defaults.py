# Define your programmatic "hardcoded" default config here
DEFAULT_LOGGING_DICT = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simpleFormatter": {
            "format": "%(asctime)s  %(name)s  %(levelname)7s: %(message)s",
            "datefmt": "",  # Corresponds to datefmt=
        },
    },
    "handlers": {
        "consoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simpleFormatter",
            "stream": "ext://sys.stdout",  # Corresponds to args=(sys.stdout,)
        },
    },
    "loggers": {
        "": {  # The empty string represents the root logger
            "level": "DEBUG",
            "handlers": ["consoleHandler"],
        },
    },
}