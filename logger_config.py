import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(
        "app.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    
    return logger
