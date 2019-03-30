#File: client.py
#Author: Kripash Shrestha
#Project: Lab 2
import sys
import socket
import uuid
import hashlib
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

    self.read_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.read_sock.bind((my_ip, 5015))

    self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #self.write_sock.connect((server_ip, tcp_port))
    self.thread = None
    #self.client_port = int(self.write_sock.getsockname()[1])
    self.my_ip = my_ip
    self.tcp_port = int(tcp_port)
    self.TCP_server = (my_ip, tcp_port)
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
    #if (not self.data_received):
    #  print "No Reply from Server, Trying Again!"
    #  self.sendMessage()
    #  if (not self.data_received):
    #    print "No Reply from Server, Trying Again!"
    #    self.sendMessage()
    #    if (not self.data_received):
    #      print "No Reply from Server, Server Cannot be Contacted!"
    #      file = open('Error.log', 'a+')
    #      file.write(self.message + "\n")
    #      file.write("No Reply from Server, Server Cannot be Contacted!\n")
    #      file.close()


  # Function: sendMessage
  # record the activity of sending a message and then wait for the Ack.
  def sendMessage(self):
    self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.write_sock.connect((self.TCP_server))
    self.recordActivity(self.message)
    try :
      self.write_sock.send(self.message)
    except Exception, errtxt:
      print "Could not send message"
    print "sent message"
    self.data_received = False
    self.write_sock.close()
    #self.waitForAck()


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
        threads_exit = True
        print "Exiting Program!"
        self.read_sock.close()
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
    print "5. Exit"
    screenlock.release()

    # select an action 1-5 for client action
    self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))
    while ((self.user_selection <= 0) or (self.user_selection >= 6)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 5): "))
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
    self.message = "LOGIN\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + self.my_ip + "\t" + str(self.client_port)
    #self.sendMessageToServer()
    #message = []
    #message = (self.data.split("\t"))
    #if(self.data_received and message[1] == "70"):
    #  self.waitForQuery()

  #Function: logOffFromDevice
  #Creates the string message to logoff the device from the server and calls sendMessageToServer to send the message
  #to the server.
  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    #self.sendMessageToServer()


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
#python client2.py 1 192.168.1.10 5006
