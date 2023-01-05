
import os
import sys
import time
import json
import shutil
import platform
import multiprocessing
from APIFramework import APIFramework, APIFrameworkWithFrontEnd, queue
from browserhelper import EGH

if __name__ == '__main__':
    multiprocessing.freeze_support()

    browserhelper_app = EGH()
    browserhelper_app.find_config("browserhelper_local.ini")
    browserhelper_app.start()




