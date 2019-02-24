import sys
import socket
import SocketServer

# from socket import *

USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
CLIENT_IP = "0.0.0.0"
UDP_PORT = int(sys.argv[3])
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)


# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
# sock.bind((CLIENT_IP, UDP_PORT))

# sock.sendto(MESSAGE, (SERVER_IP, UDP_PORT))

# while True:
#  data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
#  print "received message: ", data
#  print "from :" , addr


class UDPClient():
  def __init__(self, user_id, server_ip, my_ip, udp_port):
    self.user_selection = -1
    self.user_id = user_id
    self.server_ip = server_ip
    self.my_ip = my_ip
    self.udp_port = int(udp_port)
    self.UDP_server = (my_ip, udp_port)
    self.message = "default message"
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #self.sock.bind((self.my_ip, self.udp_port))
    self.data_received = False
    self.data = "default message"
    # self.debug()
    print "Client Sucessfully Initialized!"


  def debug(self):
    print "User ID: ", self.user_id
    print "Server IP: ", self.server_ip
    print "My IP: ", self.my_ip
    print "UDP Port: ", self.udp_port
    print "Message: ", self.message
    print "Data Received: ", self.data_received
    print "Data: ", self.data


  def sendMessageToServer(self):
    self.message = raw_input("Message to send to server: ")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((self.my_ip, self.udp_port))
    self.sock.sendto(self.message, (self.server_ip, self.udp_port))
    self.data_received = False
    self.waitForAck()
    self.sock.close()


  def waitForAck(self):
    self.sock.settimeout(10)
    try:
      data, addr = self.sock.recvfrom(1024)
      self.data_received = True
    except socket.timeout:
      self.data_received = False
    if self.data_received:
      self.data = data
      print "Received reply from server: ", self.data
      print "Reply received from: ", addr
    elif(not self.data_received):
      print "No Reply from Server, Try Again!"
      self.data = "No reply received!"


  def userSelection(self):
    print "~~~~~~~~~~~~~~~~~~~"
    print "CLI Menu for Client"
    print "1. Register Device with Server"
    print "2. DeRegister Device with Server"
    print "3. Login Device to System"
    print "4. Logoff Device from System"
    print "5. Exit"

    self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))
    while((self.user_selection <= 0) or (self.user_selection >= 6)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))


  def actAsThread(self):
    while True:
      self.userSelection()
      if(self.user_selection == 1):
        self.registerDevice()
      elif(self.user_selection == 2):
        self.deregisterDevice()
      elif(self.user_selection == 3):
        self.loginToSystem()
      elif(self.user_selection == 4):
        self.logOffFromSystem()
      elif (self.user_selection == 5):
        print "Exiting Program!"
        sys.exit(0)
      else:
        print "Invalid Choice!"


  def registerDevice(self):
    print "in register device"
    self.sendMessageToServer()

  def deregisterDevice(self):
    print "in deregister device"

  def loginToSystem(self):
    print "in login to system"

  def logOffFromSystem(self):
    print "in log off from system"


def main():
  UDP_client = UDPClient(sys.argv[1], sys.argv[2], "0.0.0.0", int(sys.argv[3]))
  UDP_client.actAsThread()


if __name__ == '__main__':
  main()

