import serial
import sys
from xmodem import XMODEM
import os
from parse import parse
import time
import io
from tqdm import tqdm
from rumboot.OpFactory import OpFactory
import threading
import serial
import serial.rfc2217
import socket
import select

class redirector(threading.Thread):
    alive = False
    fatal = False

    def configure(self, server, serial, socket):
        self.serial = serial
        self.socket = socket
        self.server = server

    def cleanup(self, fatal):
        self.socket.close()
        self.fatal = fatal
        self.alive = False
        if not fatal:
            print("Client disconnected")
            self.server.serve_once()
        else:
            print("Something bad happened. Stopping daemon")

    def run(self):
        self.alive = True
        self.fatal = False
        self.socket.setblocking(0)

        fromserial = bytearray(b"")
        fromsocket = bytearray(b"")
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 2)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        try:
            while True:
                ready_to_read, ready_to_write, in_error = select.select(
                    [self.socket, self.serial.fileno()],
                    [self.socket, self.serial.fileno()],
                    [self.socket, self.serial.fileno()],
                    1)


                for sock in ready_to_read:       
                    if sock == self.serial.fileno():
                        fromserial = fromserial + bytearray(self.serial.read(self.serial.inWaiting()))
                        if self.socket in ready_to_write:
                            sent = self.socket.send(fromserial)
                            del fromserial[0:sent]

                    if sock == self.socket:
                        tmp = self.socket.recv(1024)
                        if len(tmp) == 0:
                            self.cleanup(False)
                            return
                        fromsocket = fromsocket + bytearray(tmp)
                        if self.serial.fileno() in ready_to_write:
                            ret = self.serial.write(fromsocket)
                            del fromsocket[0:ret]

                for sock in in_error:
                    if sock == self.serial.fileno():
                        print("Something bad with serial port")
                        self.cleanup(True)
                        return
                    if sock == self.socket:
                        print("Disconnect?")
                        self.cleanup(False)               
                        return
        except BrokenPipeError:
            self.cleanup(False)
            return
        except ConnectionResetError:
            self.cleanup(False)
            return
        except Exception:
            self.cleanup(False)
            raise

class server:
    client_queue = [ ]
    worker = None

    def __init__(self, sport, baud, tcplisten):
        print("Starting server", sport, baud, tcplisten)
        self.serial = serial.Serial(sport, baud, timeout=5)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr, port = tcplisten.split(":")
        self.sock.bind((addr, int(port)))

    def set_reset_seq(self, rst):
        self.rst = rst

    def serve_once(self):
        if self.worker != None:
            if self.worker.alive:
                return #We're busy here

        try:
            client = self.client_queue.pop(0)
            self.worker = redirector()
            self.worker.configure(self, self.serial, client["connection"])
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            self.rst.resetToHost()
            self.worker.start()
            print("Now serving client: ", client["dns"])
        except(IndexError):
            self.worker = None
            self.rst.power(0) # Power off board

    def queue_client(self, connection, client_address):
        dns = socket.gethostbyaddr(client_address[0])
        print("Incoming connection: ", dns)
        client = { }
        client["connection"] = connection
        client["address"] = client_address
        client["dns"] = dns
        self.client_queue.append(client)
        pos = len(self.client_queue)
        if self.worker != None:
            pos = pos + 1

        text = "Urumboot-daemon: You are client number %d in queue, please stand by\n\n\n" % pos
        connection.sendall(text.encode())

        if self.worker == None:
            self.serve_once()

    def loop(self):
        self.rst.power(0) # Power off board
        try:
            self.sock.listen()
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 2)

            while True:
                print('waiting for a connection')
                connection, client_address = self.sock.accept()
                self.queue_client(connection, client_address)
        finally:
            print('Cleaning up...')
            self.sock.close()
