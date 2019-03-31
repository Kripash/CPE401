#File: client.py
#Author: Kripash Shrestha
#Project: Lab 2
import sys
import socket
import uuid
import hashlib
import time
import random
import thread
import threading

threads_exit = False

#grab host name to get ip of device
USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
UDP_PORT = int(sys.argv[3])
hostname = socket.gethostname()

screenlock = threading.Semaphore(value = 1)


#Function: getClientIP
#Gets the IP of the client, none of the described methods in the slides worked, and returned localhost/127.0.0.1
#So I looked at some resources to get the IP. If a socket cannot connect to a random IP, it will return the Ip as local host
#because then that means, no other IP exists, otherwise it will return an IP registered on the host.
#Part of this code was retrieved and modified from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
#from user Jamieson Becker with the license:
#MIT/CC2-BY-SA
def getClientIP():
  ip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    ip_sock.connect(("1.1.1.1", 10000))
    CLIENT_IP = ip_sock.getsockname()[0]
  except:
    CLIENT_IP = "127.0.0.1"

  ip_sock.close()
  return CLIENT_IP


#Client object to handle the client
class TCPClient():
  #constructor for the object, intializes the lists, server ip, ports, binds the sockets and informs the client of the
  #retrieved ip using hostname.
  def __init__(self, user_id, server_ip, my_ip, tcp_port):
    self.user_selection = -1
    self.user_id = user_id
    self.server_ip = server_ip
    self.list_of_client_addresses = []

    self.udp_read_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
      self.write_sock.connect((server_ip, tcp_port))
    except Exception, errtxt:
      print "Could not connect to server, Exiting!"
      sys.exit(0)

    self.thread = None
    #self.client_port = int(self.write_sock.getsockname()[1])
    self.my_ip = my_ip
    self.tcp_port = int(tcp_port)
    self.TCP_server = (server_ip, tcp_port)
    print self.TCP_server
    self.message = "default message"
    self.data_received = False
    self.data = "default message"
    self.mac = hex(uuid.getnode())
    file = open('error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()
    self.passphrase = "default passphrase is too long for sending messages"
    print "Your IP is: " +  self.my_ip
    print "Client Sucessfully Initialized!"


  def setupThread(self):
    try:
      self.thread = threading.Thread(target = self.readSocket,args = (self.data, ))
      self.thread.start()
    except Exception, errtxt:
      print "Could not start new thread"

    # Function: sendMessageToServer
    # Send a message to server and wait for response, if there is no response within 3 timeouts, then report the
    # error and log it that the server could not be contacted.
  def sendMessageToServer(self):
    self.sendMessage()
    if (not self.data_received):
      print "No Reply from Server, Trying Again!"
      self.sendMessage()
      if (not self.data_received):
        print "No Reply from Server, Trying Again!"
        self.sendMessage()
        if (not self.data_received):
          print "No Reply from Server, Server Cannot be Contacted!"
          file = open('Error.log', 'a+')
          file.write(self.message + "\n")
          file.write("No Reply from Server, Server Cannot be Contacted!\n")
          file.close()


  # Function: sendMessage
  # record the activity of sending a message and then wait for the Ack.
  def sendMessage(self):
    #self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #self.write_sock.connect((self.TCP_server))
    self.recordActivity(self.message)
    try :
      self.write_sock.send(self.message)
    except Exception, errtxt:
      print "Could not send message"
    self.data_received = False
    #self.write_sock.close()
    self.waitForAck()

  # Function: waitForAck
  # Set the socket timeout to 10 seconds and wait for a response with a blocking call
  # if none occurs, report no reply received.
  def waitForAck(self):
    self.write_sock.settimeout(10)
    try:
      data = self.write_sock.recv(1024)
      self.data_received = True
    except socket.timeout:
      self.data_received = False
    if self.data_received:
      self.recordActivity(data)
      self.data = data
      print "Received reply from server: ", self.data
      # print "Reply received from: ", addr
      self.handleAck(data)
    elif (not self.data_received):
      self.data = "No reply received!"

  # Function: handleAck
  # since there are no proper responses to ack for this project, the function splits the message by tabs and
  # checks to see if the hashed message matches the message it sent, if not then it reports an error in the log.
  # No functionality to resend message yet as it was not mentioned.
  def handleAck(self, data):
    message = []
    message = (data.split("\t"))
    if (not (hashlib.sha256(self.message).hexdigest() == message[4])):
      file = open('Error.log', 'a+')
      file.write("Message hash does not match original message hash!\n")
      file.close()

    if(message[0] == "DATA" and message[1] == "01"):
      client_addr = (message[5], (message[6], int(message[7])))
      found = False
      for index, x in enumerate(self.list_of_client_addresses):
        if (x[0] == client_addr[0] and x[1] != client_addr[1]):
          self.list_of_client_addresses[index] = client_addr
          found = True
        elif (x[0] == client_addr[0] and x[1] == client_addr[1]):
          print "Device Already Queried!"
          found = True

      if found == False:
        self.list_of_client_addresses.append(client_addr)


  # Function: actAsThread
  # Acts as main thread by asking the user for the passphrase for client and then calls a function
  # based on the user selection for register, deregister, login, logoff or exit system.
  def actAsThread(self):
    self.passphrase = raw_input("Please input 1 time passphrase (32 alphanumeric chars max): ")
    while (len(self.passphrase) > 32 or len(self.passphrase) <= 0):
      self.passphrase = raw_input(
        "Invalid amount of characters in password! Please input 1 time passphrase (32 alphanumeric chars max): ")

    while True:
      self.userSelection()
      if (self.user_selection == 1):
        self.registerDevice()
      elif (self.user_selection == 2):
        self.deregisterDevice()
      elif (self.user_selection == 3):
        self.loginToSystem()
      elif (self.user_selection == 4):
        self.logOffFromSystem()
      elif (self.user_selection == 5):
        device_id = raw_input("Input Device ID you would like to Query to Server: ")
        self.queryServer(device_id, "01")
      elif (self.user_selection == 6):
        print "Query Client"
      elif (self.user_selection == 7):
        threads_exit = True
        print "Exiting Program!"
        self.udp_read_sock.close()
        self.write_sock.close()
        sys.exit(0)
      else:
        print "Invalid Choice!"

  def readSocket(self, c):
    return 0
    #while (threads_exit == False):
      #self.read_sock.listen(5)
      #sock, addr = self.read_sock.accept()
      #data = sock.recv(1024)
      #screenlock.acquire()
      #print " "
      #print "~~~~~~~~~~~~~~~~~~~"
      #print "Received from: ", addr
      #print "Received Message: ", data
      #print "~~~~~~~~~~~~~~~~~~~~"
      #print " "
      #screenlock.release()

    #sys.exit(0)

    # Function: userSelection
    # The Usuer selection menu that allows the user to interact with client for client functions
  def userSelection(self):
    screenlock.acquire()
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "CLI Menu for Client"
    print "1. Register Device with Server"
    print "2. DeRegister Device with Server"
    print "3. Login Device to System"
    print "4. Logoff Device from System"
    print "5. Query Server"
    print "6. Query Another Client/Device"
    print "7. Exit"
    screenlock.release()

    # select an action 1-5 for client action
    self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))
    while ((self.user_selection <= 0) or (self.user_selection >= 8)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))
    print " "



  #Function: registerDevice
  #Creates the string message to register the device and calls sendMessageToServer to send the message to the server.
  def registerDevice(self):
    self.message = "REGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\n"
    self.sendMessageToServer()

  #Function: deRegisterDevice
  #Creates the string message to deregister the device and calls sendMessageToServer to send the message to the server.
  def deregisterDevice(self):
    self.message = "DEREGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\n"
    self.sendMessageToServer()

  #Function: loginToSystem
  #Creates the string message to login the device to the server and calls sendMessageToServer
  #to send the message to the server. If the response comes back as a sucessful login, the function calls
  #for waitforQuery to wait for the query from the server.
  def loginToSystem(self):
    try:
      self.udp_read_sock.bind(('', 0))
    except:
      print "Device Already Logged In!"
    self.message = "LOGIN\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + self.my_ip + "\t" + str((self.udp_read_sock.getsockname())[1])
    self.sendMessageToServer()
    message = []
    message = (self.data.split("\t"))
    if(self.data_received and message[1] == "70"):
      self.waitForQuery()

  #Function: waitForQuery
  #Set the socket timeout to 10 seconds and waits for a query response. If none occurs it is reported.
  #If a query is received, the function receives a message, it makes sure that it is a query and that
  #it is for the right device before sending the data.
  def waitForQuery(self):
    self.write_sock.settimeout(10)
    try:
      data = self.write_sock.recv(1024)
      self.data_received = True
    except socket.timeout:
      self.data_received = False
    if self.data_received:
      self.data = data
      print "Received Query from server: ", self.data
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

  #Function: dataToServer
  #In response to the query, the client will record the activity. The client then makes sure the query code is 0 for
  #since none were given to us and i made up my own. If the query code is 0, the function will randomly create a
  #binary string from 1 - 100 and send it to the server and record the activity and wait for the ack.
  def dataToServer(self, data, message):
    self.recordActivity(data)
    if(message[1] == "01"):
      data = bin(random.randint(1, 101))[2:]
      length = len(str(data))
      self.message = "DATA\t" + "01\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(length) + "\t" + str(data)
      self.recordActivity(self.message)
      self.sendMessageToServer()
      print "Please wait for device to return to user menu (10-15 seconds)"
      self.waitForAck()
    else:
      self.recordActivity("Incorrect Query code")


  #Function: logOffFromDevice
  #Creates the string message to logoff the device from the server and calls sendMessageToServer to send the message
  #to the server.
  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    self.sendMessageToServer()

  def queryServer(self, device_id, qcode):
    self.message = "QUERY\t" + str(qcode) + "\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(device_id)
    self.sendMessageToServer()

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
  #Call the getClientIP function to get the IP address of the Client
  CLIENT_IP = getClientIP()
  TCP_client = TCPClient(sys.argv[1], sys.argv[2], CLIENT_IP, int(sys.argv[3]))
  TCP_client.setupThread()
  TCP_client.actAsThread()


if __name__ == '__main__':
  main()


#python client2.py 1 104.238.183.139 5006
#python client2.py 1 192.168.1.8 5006
