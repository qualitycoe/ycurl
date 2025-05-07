import logging


def setup_logging(level=logging.INFO):
    logging.basicConfig(format="🧾 [%(levelname)s] %(message)s", level=level)
