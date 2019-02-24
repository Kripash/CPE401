import sys
import socket
import SocketServer

server_port = int(sys.argv[1])


class UDPServer():
  def __init__(self, my_ip, udp_port):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((my_ip, udp_port))
    self.messages = []
    self.user_ids = []
    self.clients = []

  def actAsThread(self):
    while True:
      data, addr = self.sock.recvfrom(1024)
      print "Received from: ", addr
      print "Received Message: ", data
      self.sock.sendto("Why did you say " + data + " ?", addr)


def main():
  UDP_Server = UDPServer("0.0.0.0", server_port)
  UDP_Server.actAsThread()


if __name__ == '__main__':
  main()
