
import BaseHTTPServer
import SimpleHTTPServer

class StreamHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    pass

if __name__ == "__main__":
    SimpleHTTPServer.test(HandlerClass=StreamHTTPRequestHandler,
                          ServerClass=BaseHTTPServer.HTTPServer)
