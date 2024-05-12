import logging
from concurrent.futures import ThreadPoolExecutor
from flask import request

logger = logging.getLogger('async_logger')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('async_app.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

executor = ThreadPoolExecutor(max_workers=2)

def log_message(message):
    logger.info(message)

def setup_logging(app):
    @app.before_request
    def log_request_info():
        executor.submit(log_message, f"IP: {request.remote_addr}, URL: {request.url}")
