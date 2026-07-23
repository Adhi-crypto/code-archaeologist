import sys
from loguru import logger

def setup_logging(debug: bool = False):
    logger.remove()
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )
    return logger