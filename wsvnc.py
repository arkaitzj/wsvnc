import os

import paste.urlparser

import gevent
from gevent import select
from geventwebsocket.handler import WebSocketHandler

def main():
    '''Set up zmq context and greenlets for all the servers, then launch the web
    browser and run the data producer'''

    ws_server = gevent.pywsgi.WSGIServer(
        ('', 9999), WSVncApp(),
        handler_class=WebSocketHandler)
    # http server: serves up static files
    http_server = gevent.pywsgi.WSGIServer(
        ('', 8000),
        paste.urlparser.StaticURLParser(os.path.dirname(__file__)))
    # Start the server greenlets
    http_server.start()
    ws_server.serve_forever()

    
class WSVncApp(object):
    '''WS <-> VNC'''

    def __init__(self):
        pass

    def __call__(self, environ, start_response):
        ws = environ['wsgi.websocket']
        vnc = None
        while True:
            fds = select.select([ws,vnc],[],[])
            if vnc in fds:
                msg = vnc.receive()
                ws.send(msg)
            if ws in fds:
                msg = ws.receive()
                vnc.send(msg)

if __name__ == '__main__':
    main()
