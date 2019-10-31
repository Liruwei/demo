plisttemplate = '''
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>items</key>
	<array>
		<dict>
			<key>assets</key>
				<array>
				<dict>
					<key>kind</key>
					<string>software-package</string>
					<key>url</key>
					<string>{softwarepackage}</string>
				</dict>
				<dict>
					<key>kind</key>
					<string>full-size-image</string>
					<key>needs-shine</key>
					<true/>
					<key>url</key>
					<string>{fullsizeimage}</string>
				</dict>
				<dict>
					<key>kind</key>
					<string>display-image</string>
					<key>needs-shine</key>
					<true/>
					<key>url</key>
					<string>{displayimage}</string>
				</dict>
			</array>
			<key>metadata</key>
			<dict>
				<key>bundle-identifier</key>
				<string>{bundleidentifier}</string>
				<key>bundle-version</key>
				<string>{bundleversion}</string>
				<key>kind</key>
				<string>software</string>
				<key>title</key>
				<string>{title}</string>
			</dict>
		</dict>
	</array>
</dict>
</plist>
'''


from flask import Flask, Response, request
app = Flask(__name__)

def args(name):
	return request.args.get(name)

@app.route('/items-services-file')
def createplist():
    data = plisttemplate.format(
    	softwarepackage=args('ipa'),
    	fullsizeimage=args('image'),
    	displayimage=args('icon'),
    	bundleidentifier=args('identifier'),
    	bundleversion=args('version'),
    	title=args('title'))
    headers = {"Content-Disposition": 'attachment;filename=install.plist'}
    return Response(data, mimetype="application/octet-stream", headers=headers)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=False)


