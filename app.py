from flask import Flask, request, send_file, jsonify
from flasgger import Swagger
from ftplib import FTP
from io import BytesIO
import base64
import binascii
import os

# _ftphost = '0.0.0.0'
# _ftphost = '118.24.99.49'
_ftphost = 'localhost'
_downloadUrl = 'http://192.168.60.38:1314/api/v1/download/'
_itemsServicesUrl = 'https://liruwei.cn/download-manifest-file'

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def encode(val):
    return binascii.b2a_hex(val.encode()).decode()
def decode(val):
    return binascii.a2b_hex(val.encode()).decode()

def base64encode(val):
    print(val)
    return base64.b64encode(val.encode('utf-8')).decode('utf-8')
def base64decode(val):
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
        elif checkfilexml(newPath) and line == 'app.plist':
            cb(newPath)

def existFile(ftp, file):
    try:
        filePath = '/{}'.format(file)
        return ftp.size(filePath) > 0
    except Exception as e:
        return False

def connectftp():
    host = _ftphost
    ftp = FTP()
    ftp.connect(host=host, port=21, timeout=5)
    ftp.login(user='anonymous',passwd=' ')
    return ftp

def fetchftp():    
    files = []
    ftp = connectftp()
    readallavailablefiles(ftp, '', files.append)    
    res = []
    for file in files:
        appPlist = AppPlist()
        ftp.retrbinary('RETR {}'.format(file), appPlist.put)
        keys = ['appName', 'bundleIdentifier', 'version', 'build','buildDateTime', 'userName', 'ipaPath']
        item = dict(zip(keys, [appPlist.key(k) for k in keys]))

        if item['build'] is None:
            item['build'] = '1'

        if 'ipaPath' in item and existFile(ftp, item['ipaPath']):
            res.append(item)

        for val in res:
            args = (_itemsServicesUrl, encode(_downloadUrl + base64encode(item['ipaPath'])), encode(item['bundleIdentifier']), encode(item['version']), encode(item['appName']))
            val['ipaPath'] = '{}?ipa={}&identifier={}&version={}&title={}'.format(*args)

    ftp.quit()
    return res


## Class

class AppPlist(object):
    def __init__(self):
        self.bytes = None
    
    def put(self, data):
        self.bytes = data

    def key(self, keyStr) -> str:
        tree = ET.fromstring(self.bytes.decode())
        root = tree.find('dict')
        keys = [x.text for x in root.findall('key')]
        vals = [x.text for x in root.findall('string')]
        if keyStr in keys:
            return vals[keys.index(keyStr)]
        else:
            return None


## Flask


app = Flask(__name__)


template = {
  "swagger": "2.0",
  "info": {
    "title": "My API",
    "version": "1.0.0"
  },
  "host": "192.168.60.38:1314",  # overrides localhost:500
  "basePath": "/",  # base bash for blueprint registration
  "operationId": "getmyData"
}

swagger = Swagger(app, template=template)


@app.route('/api/v1/apps')
def apps():
    """ IPA列表
    Fetch ipa list from ftp
    ---
    tags: 
      - FTP
    parameters:
      - name: page
        description: Current page
        in: query
        type: string
        default: 1
      - name: per_page
        description: The number of page
        in: query
        type: string
        default: 20
    definitions:
      IPAItem:
        type: object
        properties:
          appName:
            type: string
            description: Display Name
          bundleIdentifier:
            type: string
            description: Bundle Identifier
          version:
            type: string
            description: Version
          build:
            type: string
            description: Build
          buildDateTime:
            type: string
            description: Build time
          userName:
            type: string
            description: The user who build this app
          ipaPath:
            type: string
            description: Ipa path in ftp

    responses:
      200:
        schema: 
          $ref: '#/definitions/IPAItem'
        description: The list of ipa in ftp
        examples:
          data: [
            {
                'appName' : '',
                'bundleIdentifier' : '',
                'version' : '',
                'build' : '',
                'buildDateTime' : '',
                'userName' : '',
                'ipaPath' : ''
            }
          ]
    """
    try:
        data = fetchftp()

        page = request.args.get('page')
        per_page = request.args.get('per_page')
        if page is not None and per_page is not None:
            limit = int(per_page)
            offset = (int(page) - 1) * limit
            data = data[ offset : offset+limit ]
        else:
            data = data[ 0 : 20 ]
        return {'data' : data, 'code': 200}
    except Exception as e:
        return {'code' : 500, 'msg' : str(e)}

@app.route('/api/v1/download/<string:file_download_path>')
def appsdownload(file_download_path):
    """ 下载IPA
    ---
    tags:
      - FTP
    parameters:
      - name: file_download_path
        description: IPA encryption path
        in: path
        type: string
        required: true
    responses:
      200:
        description: Download ipa
    """
    try:
        ftp = connectftp()
        f = BytesIO()
        ftp.retrbinary('RETR ' + base64decode(file_download_path), f.write)
        f.seek(0)
        ftp.quit()
        return send_file(f, as_attachment=True, attachment_filename='app.ipa')
    except Exception as e:
        return {'code' : 500, 'msg' : str(e)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1314, debug=True)






