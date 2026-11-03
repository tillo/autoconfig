#!/usr/bin/python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import time
from xml.sax.saxutils import escape


hostName = ""
hostPort = 80


class MyServer(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.close()

    def do_GET(self):
        self.send_response(200)
        if self.path.startswith('/mail/config-v1.1.xml'):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'autoconfig.xml')
            with open(path) as f:
                template = f.read()
            self.send_header('Content-type', 'text/xml')
            self.end_headers()
            context = {
                'hostname':             self.headers['Host'].replace('autoconfig.', ''),
                'display_name':         os.environ.get('DISPLAY_NAME', ''),
                'display_short_name':   os.environ.get('DISPLAY_SHORT_NAME', ''),
                'mail_hostname':        os.environ.get('MAIL_HOSTNAME', ''),
            }
            content = template.format(**{k: escape(v, {'"': '&quot;'}) for k, v in context.items()})
            self.wfile.write(content.encode('utf-8'))
        else:
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('Autoconfig server (https://developer.mozilla.org/en-US/docs/Mozilla/Thunderbird/Autoconfiguration)\r\n'.encode('utf-8'))


def run():
    myServer = HTTPServer((hostName, hostPort), MyServer)
    print(time.asctime(), "Server started - %s:%s" % (hostName, hostPort))

    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass

    myServer.server_close()
    print(time.asctime(), "Server stopped - %s:%s" % (hostName, hostPort))


if __name__ == '__main__':
    run()
