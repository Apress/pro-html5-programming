#!/usr/bin/env python

import asyncore
import socket
import struct
import time
import hashlib

class WebSocketConnection(asyncore.dispatcher_with_send):

    def __init__(self, conn, server):
        asyncore.dispatcher_with_send.__init__(self, conn)

        self.server = server
        self.server.sessions.append(self)
        self.readystate = "connecting"
        self.buffer = ""

    def handle_read(self):
        data = self.recv(1024)
        self.buffer += data
        if self.readystate == "connecting":
            self.parse_connecting()
        elif self.readystate == "open":
            self.parse_frametype()

    def handle_close(self):
        self.server.sessions.remove(self)
        self.close()

    def parse_connecting(self):
        header_end = self.buffer.find("\r\n\r\n")
        if header_end == -1:
            return
        else:
            header = self.buffer[:header_end]
            # remove header and four bytes of line endings from buffer
            self.buffer = self.buffer[header_end+4:]
            header_lines = header.split("\r\n")
            headers = {}

            # validate HTTP request and construct location
            method, path, protocol = header_lines[0].split(" ")
            if method != "GET" or protocol != "HTTP/1.1" or path[0] != "/":
                self.terminate()
                return

            # parse headers
            for line in header_lines[1:]:
                key, value = line.split(": ")
                headers[key] = value

            headers["Location"] = "ws://" + headers["Host"] + path

            self.readystate = "open"
            self.handler = self.server.handlers.get(path, None)(self)

            if "Sec-WebSocket-Key1" in headers.keys():
                self.send_server_handshake_76(headers)
            else:
                self.send_server_handshake_75(headers)

    def terminate(self):
        self.ready_state = "closed"
        self.close()

    def send_server_handshake_76(self, headers):
        """
        Send the WebSocket Protocol v.76 handshake response
        """

        key1 = headers["Sec-WebSocket-Key1"]
        key2 = headers["Sec-WebSocket-Key2"]
        # read additional 8 bytes from buffer
        key3, self.buffer = self.buffer[:8], self.buffer[8:]

        response_token = self.calculate_key(key1, key2, key3)

        # write out response headers
        self.send_bytes("HTTP/1.1 101 Web Socket Protocol Handshake\r\n")
        self.send_bytes("Upgrade: WebSocket\r\n")
        self.send_bytes("Connection: Upgrade\r\n")
        self.send_bytes("Sec-WebSocket-Origin: %s\r\n" % headers["Origin"])
        self.send_bytes("Sec-WebSocket-Location: %s\r\n" % headers["Location"])

        if "Sec-WebSocket-Protocol" in headers:
            protocol = headers["Sec-WebSocket-Protocol"]
            self.send_bytes("Sec-WebSocket-Protocol: %s\r\n" % protocol)

        self.send_bytes("\r\n")
        # write out hashed response token
        self.send_bytes(response_token)

    def calculate_key(self, key1, key2, key3):
        # parse keys 1 and 2 by extracting numerical characters
        num1 = int("".join([digit for digit in list(key1) if digit.isdigit()]))
        spaces1 = len([char for char in list(key1) if char == " "])
        num2 = int("".join([digit for digit in list(key2) if digit.isdigit()]))
        spaces2 = len([char for char in list(key2) if char == " "])

        combined = struct.pack(">II", num1/spaces1, num2/spaces2) + key3
        # md5 sum the combined bytes
        return hashlib.md5(combined).digest()

    def send_server_handshake_75(self, headers):
        """
        Send the WebSocket Protocol v.75 handshake response
        """

        self.send_bytes("HTTP/1.1 101 Web Socket Protocol Handshake\r\n")
        self.send_bytes("Upgrade: WebSocket\r\n")
        self.send_bytes("Connection: Upgrade\r\n")
        self.send_bytes("WebSocket-Origin: %s\r\n" % headers["Origin"])
        self.send_bytes("WebSocket-Location: %s\r\n" % headers["Location"])

        if "Protocol" in headers:
            self.send_bytes("WebSocket-Protocol: %s\r\n" % headers["Protocol"])

        self.send_bytes("\r\n")

    def parse_frametype(self):
        while len(self.buffer):
            type_byte = self.buffer[0]
            if type_byte == "\x00":
                if not self.parse_textframe():
                    return

    def parse_textframe(self):
        terminator_index = self.buffer.find("\xFF")
        if terminator_index != -1:
            frame = self.buffer[1:terminator_index]
            self.buffer = self.buffer[terminator_index+1:]
            s = frame.decode("UTF8")
            self.handler.dispatch(s)
            return True
        else:
            # incomplete frame
            return false

    def send(self, s):
        if self.readystate == "open":
            self.send_bytes("\x00")
            self.send_bytes(s.encode("UTF8"))
            self.send_bytes("\xFF")

    def send_bytes(self, bytes):
        asyncore.dispatcher_with_send.send(self, bytes)


class EchoHandler(object):
    """
    The EchoHandler repeats each incoming string to the same Web Socket.
    """

    def __init__(self, conn):
        self.conn = conn

    def dispatch(self, data):
        self.conn.send("echo: " + data)


class WebSocketServer(asyncore.dispatcher):

    def __init__(self, port=80, handlers=None):
        asyncore.dispatcher.__init__(self)
        self.handlers = handlers
        self.sessions = []
        self.port = port
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("", port))
        self.listen(5)

    def handle_accept(self):
        conn, addr = self.accept()
        session = WebSocketConnection(conn, self)

if __name__ == "__main__":
    print "Starting WebSocket Server"
    WebSocketServer(port=8080, handlers={"/echo": EchoHandler})
    asyncore.loop()
