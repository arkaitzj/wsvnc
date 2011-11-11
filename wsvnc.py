import os,json

import paste.urlparser

import gevent
from gevent import select
from geventwebsocket.handler import WebSocketHandler
from rfb import RFBClient

def main():
    '''Set up zmq context and greenlets for all the servers, then launch the web
    browser and run the data producer'''

    ws_server = gevent.pywsgi.WSGIServer(
        ('', 9999), WSVncApp(),
        handler_class=WebSocketHandler)
    # http server: serves up static files
    http_server = gevent.pywsgi.WSGIServer(
        ('', 8000),
        paste.urlparser.StaticURLParser(os.path.abspath(os.path.dirname(__file__))+"/public"))
    # Start the server greenlets
    http_server.start()
    ws_server.serve_forever()

    
class WSVncApp(object):
    '''WS <-> VNC'''

    def __init__(self):
        self.posx = None
        self.posy = None

    def __call__(self, environ, start_response):
        ws = environ['wsgi.websocket']
        transport = gevent.socket.create_connection(("localhost",5900))
        vnc = RFBClient(transport)
        (name, width, height) = vnc.get_info()
        buff = json.dumps({"type":"s", "name":name, "width":width, "height":height})
        buff = chr(len(buff)) + buff
        ws.send(buff)
        counter = 0
        while True:
            fds = select.select([ws,vnc],[],[])[0]
            if vnc in fds:
                (msg,data) = vnc.receive()
                if msg == 0:
                    for rectangle in data:
                        buff = '{ "type":"fu","rectangle":{"x":'+str(rectangle["x"])+',"y":'+str(rectangle["y"])+',"width":'+str(rectangle["width"])+',"height":'+str(rectangle["height"])+',"encoding":"'+str(rectangle["encoding"])+'", "datalen":'+str(len(rectangle['data']))+'} }'
                        buff = chr(len(buff)) + buff + rectangle['data']
                        ws.send(buff)
                        counter += 1
                elif msg == 2:
                    buff = '{"type":"bell"}'
                    buff = chr(buff) + buff
                    ws.send(buff)
            if ws in fds:
                raw = ws.receive()
                msg = json.loads(raw)
                msgtype = msg['type']
                if   msgtype == 'fuq':
                    vnc.framebuffer_update_request(msg['x'],msg['y'], msg['width'], msg['height'], msg.get('incremental',0))
                elif msgtype == 'pe':
                    if msg['event'].find('mousedown') != -1:
                        vnc.mouse(int(msg['x']),int(msg['y']),1)
                    else:
                        vnc.mouse(int(msg['x']),int(msg['y']))
                else:
                    print msg['type']

if __name__ == '__main__':
    main()
