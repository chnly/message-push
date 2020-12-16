from loguru import logger as logger
import logging
import sys
try:
    from . import utils
except ImportError:
    import utils

__all__ = [
    "loggers",
    "loggers_handler"
]


def load_config():
    fmt = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | " \
          "<level>{level: <8}</level> | " \
          "<cyan>{thread.name}</cyan>:" \
          "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> " \
          "- <level>{message}</level>"
    # 去除默认配置，否则会输出两遍
    logger.remove()
    if utils.config['log']['console']['enable']:
        level = utils.config['log']['console']['level']
        # 向控制台stderr输出
        logger.add(sys.stderr, format=fmt, level=level,
                   colorize=True)
    if utils.config['log']['file']['enable']:
        # 向文件输出，文件夹不存在时，会自动创建文件夹
        # error日志保存到error.log中，单文件最大1M，保存7天
        logger.add("log/error.log", filter=lambda record: record["level"].name == "ERROR",
                   rotation="1 MB", retention="1 week",
                   enqueue=True)

        # debug日志保存到debug.log中，单文件最大1M，保存7天
        logger.add("log/debug.log", filter=lambda record: record["level"].name == "DEBUG",
                   rotation="1 MB", retention="1 week",
                   enqueue=True)
        # info日志保存到info.log中，单文件最大1M，保存7天
        logger.add("log/info.log", filter=lambda record: record["level"].name == "INFO",
                   rotation="1 MB", retention="1 week",
                   enqueue=True)

    return logger


def log_handler():
    # TODO 将flask日志映射到loguru上
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            global loggers
            # Retrieve context where the logging call occurred, this happens to be in the 6th frame upward
            logger_opt = loggers.opt(depth=6, exception=record.exc_info)
            logger_opt.log(record.levelno, record.getMessage())

    handler = InterceptHandler()
    handler.setLevel(0)
    return handler


loggers = load_config()
loggers_handler = log_handler()

if __name__ == '__main__':
    loggers.info('use loguru log')
    loggers.warning('use loguru log')
    loggers.error('use loguru log')
    loggers.critical('use loguru log')
