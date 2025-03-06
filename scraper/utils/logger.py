import logging
import os

log_dir = "/var/log/app"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# handle sqlachemy logs
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.WARNING)
sqlalchemy_logger.propagate = False  # prevent from propagating to root logger
sqlalchemy_logger.handlers.clear()

# hand;e pyvips logs
pyvips_logger = logging.getLogger("pyvips")
pyvips_logger.setLevel(logging.WARNING)
pyvips_logger.propagate = False
pyvips_logger.handlers.clear()

logger = logging.getLogger(__name__)

error_log_path = os.path.join(log_dir, "error.log")
error_file_handler = logging.FileHandler(error_log_path, mode="w")
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logger.addHandler(error_file_handler)
