from ftplib import FTP
from pathlib import Path
from flask import Flask, Response, request, send_from_directory
from threading import Thread, Event
from queue import Queue, Empty
from io import BytesIO
from credentials import *
import os
import base64

def encode(val):
    return base64.b64encode(val.encode('utf-8')).decode('utf-8')

def decode(val):
    return base64.b64decode(val.encode('utf-8')).decode('utf-8')

def checkfiledir(ftp,file_name):
    try:
        rec = ftp.cwd(file_name )  
        ftp.cwd("..") 
        return 'Dir'
    except Exception as e:
        return "File"

def checkfilexml(file):
    end = os.path.splitext(file)[-1]
    return end == ".xml" or  end == '.plist'

def readalllines(ftp, path):
    lines = []
    ftp.cwd(path)
    ftp.retrlines("NLST", lines.append)
    return lines

def readallavailablefiles(ftp, path, cb):
    for line in readalllines(ftp, path):
        newPath = path + '/' +line
        if checkfiledir(ftp ,newPath) == 'Dir':
            readallavailablefiles(ftp, newPath, cb)
        elif checkfilexml(newPath):
            cb(newPath)

def connectftp():
    host = "localhost" 
    ftp = FTP(host)
    ftp.login("test", "test")
    return ftp

def fetchftp():    
    files = []
    ftp = connectftp()
    readallavailablefiles(ftp, '', files.append)
    res = []
    for file in files:
        res.append({ 'value': encode(file)})
    ftp.quit()
    return res




## Class

class FTPDownloader(object):
    def __init__(self, ftp, timeout=0.01):
        self.ftp = ftp
        self.timeout = timeout

    def getBytes(self, filename):
        print("getBytes")
        self.ftp.retrbinary("RETR {}".format(filename) , self.bytes.put)
        self.bytes.join()   # wait for all blocks in the queue to be marked as processed
        self.finished.set() # mark streaming as finished

    def sendBytes(self):
        while not self.finished.is_set():
            try:
                yield self.bytes.get(timeout=self.timeout)
                self.bytes.task_done()
            except Empty:
                self.finished.wait(self.timeout)
        self.worker.join()

    def download(self, filename):
        self.bytes = Queue()
        self.finished = Event()
        self.worker = Thread(target=self.getBytes, args=(filename,))
        self.worker.start()
        return self.sendBytes()





## Flask


app = Flask(__name__)
@app.route('/api/v1/app/list')
def apps():
    try:
        data = fetchftp()
        return {'data' : data, 'code': 200}
    except Exception as e:
        return {'code' : 500, 'msg' : str(e)}

@app.route('/api/v1/app/download/<string:app_path>')
def app_download(app_path):
    try:
        ftp = connectftp()
        filepath = decode(app_path)
        down = FTPDownloader(ftp)
        headers = {"Content-Disposition": 'attachment;filename=%s.plist' % (app_path)}
        return Response(down.download(filepath), mimetype="application/octet-stream", headers=headers)
    except Exception as e:
        return {'code' : 500, 'msg' : str(e)}

@app.route('/api/v1/app')
def ipa():
     directory = os.getcwd()
     headers = {"Content-Disposition": "attachment;filename=jenkind_test.ipa"}
     return send_from_directory(directory, 'jenkind_test.ipa', as_attachment=True)


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=1314, debug=True)





