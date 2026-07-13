import os
import time

from loguru import logger

project_dir = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir)
)
log_path = os.path.join(project_dir, "tmp", "logs")

if not os.path.exists(log_path):
    os.makedirs(log_path, exist_ok=True)

log_path_error = os.path.join(log_path, f'{time.strftime("%Y-%m-%d")}_error.log')

logger.add(log_path_error, rotation="12:00", retention="5 days", enqueue=True)
