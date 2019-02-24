import sys
import socket
import SocketServer
from devices import Device
import time
import hashlib

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
server_port = int(sys.argv[1])


class UDPServer():
  def __init__(self, my_ip, udp_port):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((my_ip, udp_port))
    self.devices = []

  def actAsThread(self):
    while True:
      data, addr = self.sock.recvfrom(1024)
      print "Received from: ", addr
      print "Received Message: ", data
      self.parse(data, addr)
      # self.sock.sendto("Why did you say " + data + " ?", addr)

  def parse(self, data, addr):
    message = []
    code = -1
    message = (data.split("\t"))
    if (message[0] == "REGISTER"):
      code = self.registerDevice(message, data)
      print "Number of Registered Devices: ", len(self.devices)
      self.ackClient("0" + str(code), str(time.time()), hashlib.sha256(data).hexdigest(), addr)

  def registerDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1] or x.mac == message[3]):
        return 1

    temp = Device(message[1], message[2], message[3], message[4], message[5])
    temp.addMessage(data)
    self.devices.append(temp)
    # self.devices[0].debug()
    return 0

  def ackClient(self, code, time, hashed_message, addr):
    message = "ACK\t" + code + "\t" + time + "\t" + hashed_message
    self.sock.sendto(message, addr)


def main():
  UDP_Server = UDPServer("0.0.0.0", server_port)
  UDP_Server.actAsThread()


if __name__ == '__main__':
  main()
