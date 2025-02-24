import logging

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logging.getLogger('sqlalchemy.engine').addHandler(logging.StreamHandler())
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

logger = logging.getLogger(__name__)
