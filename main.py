import logging

from aiohttp import web
from app.UploadApp import UploadApp

# can be move out to config file
SERVER_IP = "0.0.0.0"
SERVER_PORT = "3000"
LOGGING_LEVEL = logging.DEBUG
LOGGING_FILE = "logs/uploader-log.log"


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print("Hi, {0}".format(name))  # Press Ctrl+F8 to toggle the breakpoint.


app = UploadApp()
if __name__ == '__main__':
    print_hi('Launch Server')

    logging.basicConfig(level = LOGGING_LEVEL, filename = LOGGING_FILE)
    logging.debug('This will get logged')

    web.run_app(app, host=SERVER_IP, port=SERVER_PORT)

