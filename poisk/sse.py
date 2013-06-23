import tornado.httpserver
import tornado.ioloop
import tornado.wsgi

import datetime

from .app import app

class SSEHandler(tornado.web.RequestHandler):
    _closing_timeout = False
    _live_connections = set()

    def __init__(self, application, request, **kwargs):
        super(SSEHandler, self).__init__(application, request, **kwargs)
        self.stream = request.connection.stream
        self._closed = False

    def initialize(self):
        self.set_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Connection', 'keep-alive')

    @tornado.web.asynchronous
    def get(self):
        self._live_connections.add(self)
        self.flush()

    @classmethod
    def ping_all(cls):
        for handle in cls._live_connections:
            print handle
            handle.ping()

    def on_connection_close(self):
        self._live_connections.remove(self)

    def ping(self):
        data = "ping"
        message = 'data: %s\n\n' % data
        self.write(message)
        self.flush()


def pinger():
    tornado.ioloop.IOLoop.instance().add_timeout(
        datetime.timedelta(seconds=1), pinger)
    SSEHandler.ping_all()

if __name__ == "__main__":
    wsgi_app = tornado.wsgi.WSGIContainer(app)
    tornado_app = tornado.web.Application(
        [
            ('/events', SSEHandler),
            ('.*', tornado.web.FallbackHandler, dict(fallback=wsgi_app)),
        ], debug=True)
    http_server = tornado.httpserver.HTTPServer(tornado_app)
    http_server.listen(8888)
    loop = tornado.ioloop.IOLoop.instance()
    pinger()
    loop.start()
