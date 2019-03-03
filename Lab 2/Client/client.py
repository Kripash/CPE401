#File: client.py
#Author: Kripash Shrestha
#Project: Lab 2
import sys
import socket
import uuid
import hashlib
import random
import time

#grab host name to get ip of device
USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
CLIENT_IP = "0.0.0.0"
UDP_PORT = int(sys.argv[3])
hostname = socket.gethostname()

class UDPClient():
  #constructor for the object, intializes the lists, server ip, ports, binds the sockets and informs the client of the
  #retrieved ip using hostname.
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

  #Function: debug
  #Prints the data of the object for debugging purposes.
  def debug(self):
    print "User ID: ", self.user_id
    print "Server IP: ", self.server_ip
    print "My IP: ", self.my_ip
    print "UDP Port: ", self.client_port
    print "Message: ", self.message
    print "Data Received: ", self.data_received
    print "Data: ", self.data

  #Function: sendMessageToServer
  #Send a message to server and wait for response, if there is no response within 3 timeouts, then report the
  #error and log it that the server could not be contacted.
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

  #Function: sendMessage
  #record the activity of sendding a message and then wait for the Ack.
  def sendMessage(self):
    self.recordActivity(self.message)
    self.sock.sendto(self.message, (self.server_ip, self.udp_port))
    self.data_received = False
    self.waitForAck()

  #Function: waitForAck
  #Set the socket timeout to 10 seconds and wait for a response with a blocking call
  #if none occurs, report no reply received.
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

  #Function: userSelection
  #The Usuer selection menu that allows the user to interact with client for client functions
  def userSelection(self):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "CLI Menu for Client"
    print "1. Register Device with Server"
    print "2. DeRegister Device with Server"
    print "3. Login Device to System"
    print "4. Logoff Device from System"
    print "5. Exit"

    #select an action 1-5 for client action
    self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))
    while((self.user_selection <= 0) or (self.user_selection >= 6)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))


  #Function: actAsThread
  #Acts as main thread by asking the user for the passphrase for client and then calls a function
  #based on the user selection for register, deregister, login, logoff or exit system.
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

  #Function: handleAck
  #since there are no proper responses to ack for this project, the function splits the message by tabs and
  #checks to see if the hashed message matches the message it sent, if not then it reports an error in the log.
  #No functionality to resend message yet as it was not mentioned.
  def handleAck(self, data):
    message = []
    message = (data.split("\t"))
    if(not(hashlib.sha256(self.message).hexdigest() == message [4])):
      file = open('Error.log', 'a+')
      file.write("Message hash does not match original message hash!\n")
      file.close()

  #Function: registerDevice
  #Creates the string message to register the device and calls sendMessageToServer to send the message to the server.
  def registerDevice(self):
    self.message = "REGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()

  #Function: deRegisterDevice
  #Creates the string message to deregister the device and calls sendMessageToServer to send the message to the server.
  def deregisterDevice(self):
    self.message = "DEREGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()

  #Function: loginToSystem
  #Creates the string message to login the device to the server and calls sendMessageToServer
  #to send the message to the server. If the response comes back as a sucessful login, the function calls
  #for waitforQuery to wait for the query from the server.
  def loginToSystem(self):
    self.message = "LOGIN\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + self.my_ip + "\t" + str(self.client_port)
    self.sendMessageToServer()
    message = []
    message = (self.data.split("\t"))
    if(self.data_received and message[1] == "70"):
      self.waitForQuery()

  #Function: logOffFromDevice
  #Creates the string message to logoff the device from the server and calls sendMessageToServer to send the message
  #to the server.
  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    self.sendMessageToServer()

  #Function: dataToServer
  #In response to the query, the client will record the activity. The client then makes sure the query code is 0 for
  #since none were given to us and i made up my own. If the query code is 0, the function will randomly create a
  #binary string from 1 - 100 and send it to the server and record the activity and wait for the ack.
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

  #Function: waitForQuery
  #Set the socket timeout to 10 seconds and waits for a query response. If none occurs it is reported.
  #If a query is received, the function receives a message, it makes sure that it is a query and that
  #it is for the right device before sending the data.
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

  #Function: recordActivity
  #open the Activity.log file, record the activity and close the file.
  def recordActivity(self, activity):
    file = open('Activity.log', 'a+')
    file.write(activity + " \n")
    file.close()

#Create the object and call the main thread function of the object
def main():
  #If the userID is invalid, the client exits.
  if(len(sys.argv[1]) > 32):
    print "ERROR: USER ID Too Long, should be at most 32 alphanumeric characters."
    sys.exit(0)
  #Create the udp client object and call the "main thread" function
  UDP_client = UDPClient(sys.argv[1], sys.argv[2], socket.gethostbyname(hostname), int(sys.argv[3]))
  UDP_client.actAsThread()


if __name__ == '__main__':
  main()

