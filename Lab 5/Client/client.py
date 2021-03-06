#File: client.py
#Author: Kripash Shrestha
#Project: Lab 5
import sys
import socket
import uuid
import hashlib
import time
import random
import thread
import threading
import dropbox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import binascii
from Crypto.PublicKey import RSA
from Crypto.Util import asn1
from base64 import b64decode

threads_exit = False

#grab host name to get ip of device
USER_ID = sys.argv[1]
SERVER_IP = sys.argv[2]
UDP_PORT = int(sys.argv[3])
hostname = socket.gethostname()

data_lock = threading.Lock()
thread_lock = threading.Lock()
io_lock = threading.Lock()


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
    self.udp_received = []
    self.device_query = []

    self.logged_in = False
    self.write_thread = None
    self.read_thread = None
    self.heart_thread = None
    self.kill_threads = False

    self.udp_read_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.udp_write_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.udp_data = None
    self.udp_addr = None

    self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.email = None
    self.email_password = None

    self.key = RSA.generate(2048)
    self.privKeyBin = self.key.exportKey('DER')
    self.pubKeyBin = self.key.publickey().exportKey('DER')
    self.privKey = RSA.importKey(self.privKeyBin)
    self.pubKey = RSA.importKey(self.pubKeyBin)

    self.server_pub_key = None

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

    self.message = "default message"
    self.data_received = False
    self.data = "default message"
    self.mac = hex(uuid.getnode())
    file = open('Error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()
    self.passphrase = "default passphrase is too long for sending messages"

    self.dropbox_key = None
    self.dbx = None
    self.auth = False
    self.cloud_thread = None

    print "Your IP is: " +  self.my_ip
    print "Client Sucessfully Initialized!"

  #setupThread, sets up the threads for
  #heartBeat: 5 min sleep cycle and wakes up to broadcast message to all devices it knows of
  #read: udp read thread
  #write: udp write_thread
  #pushToCloud: will push data of the cpu temp to the cloud every 30 seconds
  def setupThread(self):
    try:
      self.read_thread = threading.Thread(target=self.readUDPSocket, args=(None,))
      self.read_thread.daemon = True
      self.read_thread.start()
    except Exception, errtxt:
      print "Could not start client readUDPSocket thread!"

    try:
      self.write_thread = threading.Thread(target=self.writeUDPSocket, args=(None,))
      self.write_thread.daemon = True
      self.write_thread.start()
    except Exception, errtxt:
      print "Could not start client writeUDPSocket thread!"

    try:
      self.heart_thread = threading.Thread(target=self.heartBeat, args=(None,))
      self.heart_thread.daemon = True
      self.heart_thread.start()
    except Exception, errtxt:
      print "Could not start heart beat thread!"

    try:
      self.cloud_thread = threading.Thread(target=self.pushToCloud, args=(None,))
      self.cloud_thread.daemon = True
      self.cloud_thread.start()
    except Exception, errtxt:
      print "Could not start cloud thread!"


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
          io_lock.acquire()
          file = open('Error.log', 'a+')
          file.write(self.message + "\n")
          file.write("No Reply from Server, Server Cannot be Contacted!\n")
          file.close()
          io_lock.release()

  def binaryToHex(self, bin_val):
    return binascii.hexlify(bin_val)


  def hexToBinary(self, hex_val):
    return binascii.unhexlify(hex_val)


  # Function: sendMessage
  # record the activity of sending a message and then wait for the Ack.
  def sendMessage(self):
    self.recordActivity("Sent:     " + self.message)
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
      self.recordActivity("Received:     " + data)
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
    if ((not (hashlib.sha256(self.message).hexdigest() == message[4])) and message[0] == "ACK"):
      io_lock.acquire()
      print "Opening Error Log"
      file = open('Error.log', 'a+')
      file.write("Message hash does not match original message hash: " + data + "\n")
      file.close()
      io_lock.release()

    if message[1] == "00":
      self.server_pub_key = message[4]
      self.recordActivity("Received server public key: " +  message[5])

    if message[1] == "70":
      self.logged_in = True
      self.dropbox_key = message[5]

    if message[1] == "80" or message[1] == "32":
      self.logged_in = False

    if(message[0] == "DATA" and message[1] == "01"):
      client_addr = (message[5], (message[6], int(message[7])))
      found = False
      for index, x in enumerate(self.list_of_client_addresses):
        if (x[0] == client_addr[0] and x[1] != client_addr[1]):
          self.list_of_client_addresses[index] = client_addr
          found = True
        elif (x[0] == client_addr[0] and x[1] == client_addr[1]):
          found = True

      if found == False:
        self.list_of_client_addresses.append(client_addr)


  # Function: actAsThread
  # Acts as main thread by asking the user for the passphrase for client and then calls a function
  # based on the user selection for register, deregister, login, logoff, query server, or query device or exit system.
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
        while(device_id == self.user_id):
          device_id = raw_input("Invalid!Input Device ID (that is not yours) you would like to Query to Server: ")
        self.queryServer(device_id, "01")
      elif (self.user_selection == 6):
        query_id = raw_input("Input Device ID you would like to Query to: ")
        while (query_id == self.user_id):
          query_id = raw_input("Input Device ID (that is not yours) you would like to Query to: ")
        self.device_query.append(query_id)
      elif (self.user_selection == 7):
        print "Exiting Program and Cleaning Up Threads!"
        print "Waiting for Heart Beat Thread to awake and close (5 minute cycle)"
        self.logged_in = False
        self.kill_threads = True
        self.udp_read_sock.close()
        self.udp_write_sock.close()
        self.write_sock.close()
        sys.exit(0)
      else:
        print "Invalid Choice!"

  def sendEmail(self):
    if(self.email is None and self.email_password is None):
      self.email = raw_input("Please input email account(refreshed upon program close): ")
      self.email_password = raw_input("Please input email password(refreshed upon program close): ")
    email_rec = raw_input("Please input email recipient: ")

    #msg = "test"
    #emsg = self.pubKey.encrypt(msg, 'x')[0]
    #dmsg = self.privKey.decrypt(emsg)

    msg = MIMEMultipart()
    msg['From'] = str(self.email)
    msg['To'] = str(email_rec)
    msg['Subject'] = "Device " + str(self.user_id) + " cloud log file"
    header = str(self.user_id) + "\n" + str(self.binaryToHex(self.pubKeyBin)) + "\n" 
    body = "/cpe_lab_5/device" + str(self.user_id) + ".txt" + " " + str(self.dropbox_key)
    #print body
    body_encrypted = self.privKey.encrypt(body, 'x')[0]
    #print header + body_encrypted
    #print self.privKey.decrypt(body_encrypted)
    msg.attach(MIMEText(header + body_encrypted, 'plain'))
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    try:
      s.login(self.email, self.email_password)
    except Exception, errtxt:
      print "Could not sign into email, check security settings on account!"
      sys.exit(0)
    s.sendmail(self.email, email_rec, str(msg))
    self.recordActivity("Sent Email to: " + str(email_rec) + "with message: " + str(body_encrypted))
    s.quit()


 
  #readUDPSocket
  #waits for the device to be logged in the server, after the device is logged in the function will sleep for 1 second
  #then it will wait for the mutex lock to be available before reading to a socket for 2 seconds, if there is data
  #to be read, the function records it and acks it. The function releases the mutex at the end.
  def readUDPSocket(self, null):
    while True:
      if(self.kill_threads == True):
        return 0
      data_received = False
      while self.logged_in:
        time.sleep(1)
        thread_lock.acquire()
        if(self.kill_threads == True):
          return 0
        try:
          self.udp_read_sock.settimeout(2)
        except:
          data_received = False
        try:
          self.udp_data, self.udp_addr = self.udp_read_sock.recvfrom(1024)
          data_received = True
        except:
          data_received = False
        if data_received == True:
          #print "UDP Data: ", self.udp_data
          self.udp_received.append((self.udp_data, self.udp_addr))
          self.recordActivity("Received:     " + self.udp_data)
          self.ackUDP(self.udp_data, self.udp_addr)
        thread_lock.release()

  #Function: ackUDP
  #Function acks the message from the UDP client and logs it into the Activity log and acks the device that
  #sent the device and then exits
  def ackUDP(self, data, addr):
    message = (data.split("\t"))
    data_message = "Message Received!"
    if(message[0] == "QUERY" and message[1] == "01"):
      message = "DATA\t" + "01\t" + str(self.user_id) + "\t" + str(len(data_message)) + "\t" + data_message
      self.recordActivity("Sent:     " + message)
      self.udp_read_sock.sendto(message, addr)
    elif(message[0] == "STATUS"):
      message = "ACK\t" + "40\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + hashlib.sha256(data).hexdigest()
      self.recordActivity("Sent:     " + message)
      self.udp_read_sock.sendto(message, addr)
    elif(message[0] == "DATA"):
      message = "ACK\t" + "50\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + hashlib.sha256(data).hexdigest()
      self.recordActivity("Sent:     " + message)

  #writeUDPSocket
  #Waits for the queue to be set and exist so that the query can be properly set. Acquires the thread mutex.
  #The function pops up the device at the front of the queue and then sends a query to that client device
  # the function records the activity and releases the mutex
  def writeUDPSocket(self, null):
    while True:
      if(self.kill_threads == True):
        return 0
      if(len(self.device_query) > 0):
        time.sleep(1)
        thread_lock.acquire()
        if(self.kill_threads == True):
          return 0
        device_id = self.device_query[0]
        self.device_query.pop(0)
        for x in self.list_of_client_addresses:
          #print x
          if x[0] == device_id:
            message = "QUERY\t" + "01\t" + str(device_id) + "\t" + str(time.time())
            #print self.udp_read_sock.getsockname()
            self.udp_read_sock.sendto(message, x[1])
            self.recordActivity("Sent:     " + message)
        thread_lock.release()

  #heartBeat
  #The function sleeps for 300 seconds and if wakes up
  #If it is logged in , the function acquires the lock before transmitting the heartbeat to all of the devices that
  #eexist in the device id list that it holds
  #The function then records the activity and releases the mutex lock
  def heartBeat(self, null):
    while True:
      if(self.kill_threads == True):
        return 0
      time.sleep(300)
      if(self.kill_threads == True):
        return 0
      if(self.logged_in):
        thread_lock.acquire()
        if(self.kill_threads == True):
          return 0
        heart_beat = "This is my Heart Beat!"
        message = "STATUS\t" + "02\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(len(heart_beat)) + "\t" + heart_beat
        for x in self.list_of_client_addresses:
          self.udp_read_sock.sendto(message, x[1])
          self.recordActivity("HeartBeat Sent:     " + message)
        thread_lock.release()


  #Function:pushToCloud
  #The thread wakes up every 30 seconds
  #the thread will then check to see if the device is logged in to the server
  #If the device is logged into the server, the device will continue to authenticate itself to the dropbox cloud
  #the device will then get the CPU temperature of the device and record it to the cloud under the folder /cpe_lab_5/device(device_id).txt
  #The client IoT device will record the activity into the
  def pushToCloud(self, null):
    while True:
      if(self.kill_threads == True):
        return 0
      time.sleep(30)
      if(self.kill_threads == True):
        return 0
      if(self.logged_in):
        if(not self.auth):
          self.dbx = dropbox.Dropbox(self.dropbox_key)
          self.dbx.users_get_current_account()
        temp_file = open("/sys/class/thermal/thermal_zone0/temp")
        temp = float(temp_file.read())
        temp_c = temp/1000
        self.dbx.files_upload(str(temp_c), "/cpe_lab_5/device" + str(self.user_id) + ".txt", dropbox.files.WriteMode.overwrite)
        self.recordActivity("Wrote to Cloud at file /cpe_lab_5/device" + str(self.user_id) + ".txt with temperature " + str(temp_c))



  # Function: userSelection
  # The Usuer selection menu that allows the user to interact with client for client functions
  def userSelection(self):
    print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    print "CLI Menu for Client"
    print "1. Register Device with Server"
    print "2. DeRegister Device with Server"
    print "3. Login Device to System"
    print "4. Logoff Device from System"
    print "5. Query Server"
    print "6. Query Another Client/Device"
    #print "7. Send Email With Token"
    #print "8. Read Friend Cloud File From Email"
    print "7. Exit"

    # select an action 1-7 for client action
    self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))
    while ((self.user_selection <= 0) or (self.user_selection >= 8)):
      print "Error: Menu Option Invalid! "
      self.user_selection = int(raw_input("Please Select an Action (1 - 7): "))
    print " "

  #Function: registerDevice
  #Creates the string message to register the device and calls sendMessageToServer to send the message to the server.
  def registerDevice(self):
    self.message = "REGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac) + "\t" + str(self.binaryToHex(self.pubKeyBin))
    self.sendMessageToServer()

  #Function: deRegisterDevice
  #Creates the string message to deregister the device and calls sendMessageToServer to send the message to the server.
  def deregisterDevice(self):
    self.message = "DEREGISTER\t" + str(self.user_id) + "\t" + self.passphrase + "\t" + str(self.mac)
    self.sendMessageToServer()

  #Function: loginToSystem
  #Creates the string message to login the device to the server and calls sendMessageToServer
  #to send the message to the server. If the response comes back as a sucessful login, the function calls
  #for waitforQuery to wait for the query from the server.
  def loginToSystem(self):
    if(self.logged_in == False):
      try:
        self.udp_read_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
    self.data_received = False
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
    elif (self.data_received == False):
      self.data = "No Query received!"

  #Function: dataToServer
  #In response to the query, the client will record the activity. The client then makes sure the query code is 0 for
  #since none were given to us and i made up my own. If the query code is 0, the function will randomly create a
  #binary string from 1 - 100 and send it to the server and record the activity and wait for the ack.
  def dataToServer(self, data, message):
    self.recordActivity("Received:     " + data)
    if(message[1] == "01"):
      data = bin(random.randint(1, 101))[2:]
      length = len(str(data))
      self.message = "DATA\t" + "01\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(length) + "\t" + str(data)
      self.recordActivity("Sent:     " + self.message)
      self.sendMessageToServer()
      print "Please wait for device to return to user menu (10-15 seconds)"
      self.waitForAck()
    else:
      self.recordActivity("Incorrect Query code")


  #Function: logOffFromDevice
  #Creates the string message to logoff the device from the server and calls sendMessageToServer to send the message
  #to the server. The function will also close the udp_sockets so that the devices it will not be receiving any data.
  def logOffFromSystem(self):
    self.message = "LOGOFF\t" + str(self.user_id)
    self.sendMessageToServer()
    data_lock.acquire()
    self.logged_in = False
    self.udp_read_sock.close()
    self.udp_write_sock.close()
    data_lock.release()

  #queryServer
  #send a message to query the server for the specific device id
  def queryServer(self, device_id, qcode):
    self.message = "QUERY\t" + str(qcode) + "\t" + str(self.user_id) + "\t" + str(time.time()) + "\t" + str(device_id)
    self.sendMessageToServer()

  #Function: recordActivity
  #open the Activity.log file, record the activity and close the file.
  def recordActivity(self, activity):
    io_lock.acquire()
    file = open('Activity.log', 'a+')
    file.write(activity + " \n")
    file.close()
    io_lock.release()


#Create the object and call the main thread function of the object
def main():
  #If the userID is invalid, the client exits.
  if(len(sys.argv[1]) > 32):
    print "ERROR: USER ID Too Long, should be at most 32 alphanumeric characters."
    sys.exit(0)
  #Call the getClientIP function to get the IP address of the Client and set up the threads
  CLIENT_IP = getClientIP()
  TCP_client = TCPClient(sys.argv[1], sys.argv[2], CLIENT_IP, int(sys.argv[3]))
  TCP_client.setupThread()
  TCP_client.actAsThread()


if __name__ == '__main__':
  main()


#python client2.py 1 104.238.183.139 5006
#python client2.py 1 192.168.1.8 5006
