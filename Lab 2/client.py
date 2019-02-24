import sys
import socket
import uuid
import time
import hashlib
import SocketServer


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
    self.mac = hex(uuid.getnode())
    self.passphrase = "default passphrase is too long for sending messages"
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
    #self.message = raw_input("Message to send to server: ")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((self.my_ip, self.udp_port))
    self.sendMessage()
    if(not self.data_received):
      print "No Reply from Server, Trying Again!"
      self.sendMessage()
      if (not self.data_received):
        print "No Reply from Server, Trying Again!"
        self.sendMessage()
        if(not self.data_received):
          print "No Reply from Server, Server Cannot be Contacted!"
          #record in error.log
    self.sock.close()

  def sendMessage(self):
    self.sock.sendto(self.message, (self.server_ip, self.udp_port))
    self.data_received = False
    self.waitForAck()


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
      self.handleAck(data)
    elif(not self.data_received):
      self.data = "No reply received!"


  def userSelection(self):
    print "~~~~~~~~~~~~~~~~~~~"
    print "CLI Menu for Client"
    print "1. Register Device with Server"
    print "2. DeRegister Device with Server"
    print "3. Login Device to System"
    print "4. Logoff Device from System"
    print "5. Logoff Device from System"
    print "6. Logoff Device from Sy" \
          "stem"
    print "7. Exit"

    self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))
    while((self.user_selection <= 0) or (self.user_selection >= 8)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))


  def actAsThread(self):
    self.passphrase = raw_input("Please input 1 time passphrase (32 alphanumeric chars max): ")
    while(len(self.passphrase) > 32):
      self.passphrase = raw_input("Passphase Too Long! Please input 1 time passphrase (32 alphanumeric chars max): ")

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
        self.dataToServer()
      elif (self.user_selection == 6):
        self.queryServer()
      elif (self.user_selection == 7):
        print "Exiting Program!"
        sys.exit(0)
      else:
        print "Invalid Choice!"

  def handleAck(self, data):
    message = []
    message = (data.split("\t"))
    #if(message[2] == "00"):
    print "Ack Code: ", message[1]
    if(hashlib.sha256(self.message).hexdigest() == message [4]):
      print "Message Hashes Match!"

  def registerDevice(self):
    self.message = "REGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.udp_port)
    self.sendMessageToServer()

  def deregisterDevice(self):
    self.message = "DEREGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.udp_port)
    self.sendMessageToServer()

  def loginToSystem(self):
    self.message = "LOGIN\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + self.my_ip + "\t" + str(self.udp_port)
    self.sendMessageToServer()

  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    self.sendMessageToServer()

  def dataToServer(self):
    print "in dataToServer"

  def queryServer(self):
    print "in query Server"


def main():
  UDP_client = UDPClient(sys.argv[1], sys.argv[2], "192.168.1.10", int(sys.argv[3]))
  UDP_client.actAsThread()


if __name__ == '__main__':
  main()

