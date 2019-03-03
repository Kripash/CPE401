import sys
import socket
import uuid
import hashlib
import random
import time

USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
CLIENT_IP = "0.0.0.0"
UDP_PORT = int(sys.argv[3])
hostname = socket.gethostname()

class UDPClient():
  def __init__(self, user_id, server_ip, my_ip, udp_port):
    self.user_selection = -1
    self.user_id = user_id
    self.server_ip = server_ip
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind(('', 0))
    self.client_port = int(self.sock.getsockname()[1])
    self.my_ip = my_ip
    self.udp_port = int(udp_port)
    self.UDP_server = (my_ip, udp_port)
    self.message = "default message"
    self.data_received = False
    self.data = "default message"
    self.mac = hex(uuid.getnode())
    file = open('error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()
    self.passphrase = "default passphrase is too long for sending messages"
    # self.debug()
    print "Your IP is: " +  self.my_ip
    print "Client Sucessfully Initialized!"


  def debug(self):
    print "User ID: ", self.user_id
    print "Server IP: ", self.server_ip
    print "My IP: ", self.my_ip
    print "UDP Port: ", self.client_port
    print "Message: ", self.message
    print "Data Received: ", self.data_received
    print "Data: ", self.data


  def sendMessageToServer(self):
    self.sendMessage()
    if(not self.data_received):
      print "No Reply from Server, Trying Again!"
      self.sendMessage()
      if (not self.data_received):
        print "No Reply from Server, Trying Again!"
        self.sendMessage()
        if(not self.data_received):
          print "No Reply from Server, Server Cannot be Contacted!"
          file = open('Error.log', 'a+')
          file.write(self.message + "\n")
          file.write("No Reply from Server, Server Cannot be Contacted!\n")
          file.close()

  def sendMessage(self):
    self.recordActivity(self.message)
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
      self.recordActivity(data)
      self.data = data
      print "Received reply from server: ", self.data
      #print "Reply received from: ", addr
      self.handleAck(data)
    elif(not self.data_received):
      self.data = "No reply received!"


  def userSelection(self):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
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
    self.passphrase = raw_input("Please input 1 time passphrase (32 alphanumeric chars max): ")
    while(len(self.passphrase) > 32 or len(self.passphrase) <= 0):
      self.passphrase = raw_input("Invalid amount of characters in password! Please input 1 time passphrase (32 alphanumeric chars max): ")


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
        self.sock.close()
        sys.exit(0)
      else:
        print "Invalid Choice!"

  def handleAck(self, data):
    message = []
    message = (data.split("\t"))
    if(not(hashlib.sha256(self.message).hexdigest() == message [4])):
      file = open('Error.log', 'a+')
      file.write("Message hash does not match original message hash!\n")
      file.close()

  def registerDevice(self):
    self.message = "REGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()

  def deregisterDevice(self):
    self.message = "DEREGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()

  def loginToSystem(self):
    self.message = "LOGIN\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()
    message = []
    message = (self.data.split("\t"))
    if(self.data_received and message[1] == "70"):
      self.waitForQuery()

  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    self.sendMessageToServer()

  def dataToServer(self, data, message):
    self.recordActivity(data)
    if(message[1] == "0"):
      data = bin(random.randint(1, 101))[2:]
      length = len(str(data))
      self.message = "DATA\t" + "Binary As String\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(length) + "\t" + str(data)
      self.recordActivity(self.message)
      self.sendMessageToServer()
      self.waitForAck()
    else:
      self.recordActivity("Incorrect Query code")

  def waitForQuery(self):
    self.sock.settimeout(10)
    try:
      data, addr = self.sock.recvfrom(1024)
      self.data_received = True
    except socket.timeout:
      self.data_received = False
    if self.data_received:
      self.data = data
      print "Received Query from server: ", self.data
      #print "Query received from: ", addr
      message = []
      message = (data.split("\t"))
      if(message[0] == "QUERY" and message[2] == str(self.user_id)):
        self.dataToServer(data, message)
      elif(message[0] != "QUERY"):
        self.recordActivity("Not a Query")
      elif(message[2] != str(self.user_id)):
        self.recordActivity("Query for wrong device")
    elif (not self.data_received):
      self.data = "No Query received!"

  def recordActivity(self, activity):
    file = open('Activity.log', 'a+')
    file.write(activity + " \n")
    file.close()

def main():
  if(len(sys.argv[1]) > 32):
    print "ERROR: USER ID Too Long, should be at most 32 alphanumeric characters."
    sys.exit(0)
  UDP_client = UDPClient(sys.argv[1], sys.argv[2], socket.gethostbyname(hostname), int(sys.argv[3]))
  UDP_client.actAsThread()


if __name__ == '__main__':
  main()

