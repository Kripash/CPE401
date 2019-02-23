import sys
import socket
import SocketServer

# from socket import *

USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
CLIENT_IP = "0.0.0.0"
UDP_PORT = int(sys.argv[3])


# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
# sock.bind((CLIENT_IP, UDP_PORT))

# sock.sendto(MESSAGE, (SERVER_IP, UDP_PORT))

# while True:
#  data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
#  print "received message: ", data
#  print "from :" , addr


class UDPClient():
  def __init__(self, user_id, server_ip, my_ip, udp_port):
    self.user_id = user_id
    self.server_ip = server_ip
    self.my_ip = my_ip
    self.udp_port = udp_port
    self.UDP_server = (my_ip, udp_port)
    self.message = "default message"
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((my_ip, udp_port))
    self.data_received = False
    self.data = "default message"
    # self.debug()
    print("Client Sucessfully Initialized!")

  def debug(self):
    print("User ID: ", self.user_id)
    print("Server IP: ", self.server_ip)
    print("My IP: ", self.my_ip)
    print("UDP Port: ", self.udp_port)
    print("Message: ", self.message)
    print("Data Received: ", self.data_received)
    print("Data: ", self.data)

  def sendMessageToServer(self):
    self.message = raw_input("Message to send to server: ")
    self.sock.sendto(self.message, (self.server_ip, self.udp_port))
    self.data_received = False
    self.waitForMessage()

  def waitForMessage(self):
    self.sock.settimeout(10)
    try:
      data, addr = self.sock.recvfrom(1024)
      self.data_received = True
    except socket.timeout:
      self.data_received = False
    if self.data_received:
      print("Received reply from server: ", self.data)
      print("Reply received from: ", addr)
      self.data = data
    elif(not self.data_received):
      print("No Reply from Server, Try Again!")
      self.data = "No reply received!"

  def actAsThread(self):
    while True:
      self.sendMessageToServer()
      # self.debug()


def main():
  UDP_client = UDPClient(sys.argv[1], sys.argv[2], "0.0.0.0", int(sys.argv[3]))
  UDP_client.actAsThread()


if __name__ == '__main__':
  main()

