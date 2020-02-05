import logging
import time

api_root = "https://vault.cca.edu/api"
token = "123a4567-abcd-9876-edcb-4321fedc1234"

# copied from syllabus-notifications, log to both (dated) file & console
format = '%(asctime)s %(name)s %(levelname)s %(message)s'
level = logging.INFO
# DEBUG level is pretty verbose
# https://docs.python.org/3/library/logging.html#levels
logging.basicConfig(
    level=level,
    datefmt='%Y-%m-%d %H:%M:%S',
    format=format,
    filename='data/{today}.log'.format(today=time.strftime('%Y-%m-%d')),
)
formatter = logging.Formatter(format)
logger = logging.getLogger()
# add 2nd handler for console
console = logging.StreamHandler()
console.setLevel(level)
console.setFormatter(formatter)
logger.addHandler(console)
