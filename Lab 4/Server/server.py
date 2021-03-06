#File: server.py
#Author: Kripash Shrestha
#Project: Lab 4

import sys
import socket
import os 
import SocketServer
from devices import Device
import time
import hashlib
import thread
import threading
import dropbox

data_lock = threading.Lock()

#server port to bind for the server
#hostname = socket.gethostname()
#IPAddr = socket.gethostbyname(hostname)
server_port = int(sys.argv[1])


#Function: getClientIP
#Gets the IP of the client, none of the described methods in the slides worked, and returned localhost/127.0.0.1
#So I looked at some resources to get the IP. If a socket cannot connect to a random IP, it will return the Ip as local host
#because then that means, no other IP exists, otherwise it will return an IP registered on the host.
#Part of this code was retrieved and modified from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
#from user Jamieson Becker with the license:
#MIT/CC2-BY-SA
def getServerIP():
  ip_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    ip_sock.connect(("1.1.1.1", 10000))
    SERVER_IP = ip_sock.getsockname()[0]
  except:
    SERVER_IP = "127.0.0.1"

  ip_sock.close()
  return SERVER_IP


class TCPServer():
  #constructor to set up the socket on the server and list of devices
  def __init__(self, my_ip, tcp_port):
    print my_ip, " ", tcp_port
    self.read_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.read_sock.bind((my_ip, tcp_port))

    self.sock = None
    self.addr = None
    
    self.devices = []
    self.data = []

    self.recent_data = "null"

    file = open('Error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()

    #self.dropbox_key = "0-oGatugSJAAAAAAAAAACRyxcHGxKpBUlGGDQYTvFmYkb7ILcgk_56PjKUN49Dh1"
    self.dropbox_key = raw_input("Please Input DropBox Account Token (to access cloud account): ")
    self.dbx = dropbox.Dropbox(self.dropbox_key)
    self.dbx.users_get_current_account()
    self.analyze_thread = None
    self.dbx.files_upload("Server Set up", "/cpe_lab_4/server.txt", dropbox.files.WriteMode.overwrite)
    self.total_temp = 0
    self.total_login = 0

    print "Server set up!"

    

  #main thread of the function, which will listen to incoming datagrams on the socket and parse them.
  #sets up the analyze_thread so that the server can query the cloud for the files in the dropbox cloud and anaylze the temperature data in there
  def actAsThread(self):
    try:
      self.analyze_thread = threading.Thread(target=self.analyzeCloudData, args=(None,))
      self.analyze_thread.daemon = True
      self.analyze_thread.start()
    except Exception, errtxt:
      print "Could not start client data analysis thread thread!"
    self.readSocket()

  #Function: analyzeCloudData 
  #The thread wakes up every 30 seconds
  #the server retrieves data from all files besides the one it created on the cloud 
  #the server then checks to make sure that the file that exists has been recently changed and the device that changed it is logged in and exists in the database of the server 
  #if the requirements are met, the server records the temperature data that the client IoT put up there
  #after all of the files are read and processed, the client will record the total devices logged in and recorded in the cloud and the average temperature of all the devices 
  #that loggined in and recorded to the cloud 
  def analyzeCloudData(self, null):
    while(True):
      time.sleep(30)
      for entry in self.dbx.files_list_folder('/cpe_lab_4').entries:
        if(entry.name != "server.txt"):
          device_id = (entry.name.rsplit('.', 1)[0])[-1:]
          for x in self.devices:
            if x.id == device_id and x.login == True:
              md, res = self.dbx.files_download("/cpe_lab_4/" + entry.name)
              data = res.content
              self.total_temp = self.total_temp + float(data) 
              self.total_login = self.total_login + 1
      time_string = str(time.time())
      if(self.total_login > 0):
        self.recordActivity("Total Devices Logged in: " + str(self.total_login) + " at time " + time_string)
        self.recordActivity("Average Temperature of Devices Logged in: " +  str(self.total_temp / self.total_login) + " at time " + time_string)
      else:
        self.recordActivity("No Devices Logged in at time " + time_string)      
      self.total_temp = 0
      self.total_login = 0
        

  #readSocket
  #The function acts as the main thread, waiting for clients to open up connections with the socket and creating a
  #new thread and socket to direct them to that client
  def readSocket(self):
    self.read_sock.listen(1000)
    while True:
      self.sock, self.addr = self.read_sock.accept()
      try :
        new_client = threading.Thread(target = self.newClient ,args = (self.sock, self.addr))
        new_client.start()
      except Exception, errtxt:
        print "Could not start client thread for:", self.addr

  #newClient
  #new client thread that will listen to incoming data per client and then parse the data to do the data handling
  def newClient(self, sock, addr):  
    while True:
      data = sock.recv(1024)
      if not data:
        break
      print "Message Received: " + data
      self.parse(data, sock, addr)
    print "Client has closed connection!"
    sock.close()
    

  #Parse
  # Parse the message received and then based on the command of the message, call the function to appropriately
  # deal with each server datagram and then send the proper Ack back.
  # The parsing is based on the command message.
  def parse(self, data, sock, addr):
    data_lock.acquire()
    self.recordActivity("Receieved: " + data)
    message = []
    code = str(-1)
    message = (data.split("\t"))
    if (message[0] == "REGISTER"):
      if(len(message) == 4):
        code = self.registerDevice(message, data, addr)
        self.ackClient(sock,"REGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, message[3])   
      else:
        self.recordError("Malformed Message: " + data)
    # If the command is deregister and the len of message is 6, go ahead and parse it and send the ack, other wise record it as an error
    elif (message[0] == "DEREGISTER"):
      if (len(message) == 4):
        mac = None 
        ip = None
        code = self.deregisterDevice(message, addr)
        if (code == "30"):
          for x in self.devices:
            if (x.id == message[1]):
              mac = x.mac
              ip = x.ip
        self.ackClient(sock, "DEREGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, message[3])
      else:
        self.recordError("Malformed Message: " + data) 
    #If the command is login and the len of message is 5, go ahead and parse it and send the ack, other wise
    #record it as an error
    elif (message[0] == "LOGIN"):
      if (len(message) == 5):
        code = self.loginDevice(message, data)
        self.ackClient(sock, "LOGIN", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, message[3])
        if(code == "70"):
          time.sleep(1)
          self.queryDevice(str(message[1]), "01", str(time.time()), sock)
      else:
        self.recordError("Malformed Message: " + data)
    # If the command is logoff and the len of message is 2, go ahead and parse it and send the ack, other wise record it as an error
    elif (message[0] == "LOGOFF"):
      if (len(message) == 2):
        code = self.logoffDevice(message, data)
        self.ackClient(sock, "LOGOFF", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, None)
      else:
        self.recordError("Malformed Message: " + data)
    # If the command is data and the len of message is 6, go ahead and parse it and send the ack, other wise record it as an error
    elif (message[0] == "DATA"):
      if(len(message) == 6):
        time.sleep(0.5)
        code = self.dataReceived(message, data)
        self.ackClient(sock, "DATA", code, str(message[2]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, None)
      else:
        self.recordError("Malformed Message: " + data)
    #If the command is QUERY and the length is 4, look for the device ID and respond with the proper ACK
    elif (message[0] == "QUERY"):
      if(len(message) == 5):
        self.queryReceived(message, data, sock)
      else:
        self.recordError("Malformed Message: " + data)

    data_lock.release()
    print "Number of Registered Devices: ", len(self.devices)
    #for x in self.devices:
    #  x.debug()
    print "\n"

  #Loop through the list of devices and if the device already exists, and the IP is different, update it
  #and add the message to the device list and return 02. If there is nothing left to update, add the message to
  #the device list and return 01. If the device conflicts with mac returns 13 and if with IP, return 12. If the device
  #does not exist, add it to the list and return 00.
  def registerDevice(self, message, data, addr):
    for x in self.devices: 
      if (x.id == message[1] and x.mac == message[3]):
        if (x.ip != addr[0] and x.passphrase == message[2]):
          x.ip = addr[0]
          x.addMessage(data)
          return "02"
        else:
          x.addMessage(data)
          return "01"
      elif (x.ip == addr[0] and (not (x.id == message[1] and x.mac == message[3]))):
        return "12"
      elif (x.mac == message[3] and x.id != message[1]):
        return "13"

    temp = Device(message[1], message[2], message[3], addr[0])
    temp.addMessage(data)
    self.devices.append(temp)
    return "00"

  #Function: deregisterDevice
  #Loop through the list of devices and if it exists and the mac address and ip matches, remove it from the list and
  #return 20, otherwise if the device doesn't match the ip or mac, return 30 and don't remove it. If the device is not
  #registered, return 21.
  def deregisterDevice(self, message, addr):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.mac == message[3]):
          self.devices.remove(x)
          return "20"
        elif (x.mac != message[3]):
          return "30"
    return "21"

  #Function: loginDevice
  #Loop through the list of devices and if it exists, and the passphrase matches, add the message to the device
  #and login by setting the bool as true and return 70. Otherwise, if the device does not exist, return 31.
  def loginDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.passphrase == message[2]):
          x.ip = message[3]
          x.udp_port = message[4]
          x.addMessage(data)
          x.login = True
          return "70"
    return "31"

  #Function: queryDevice:
  #Query the client for data after every login.
  def queryDevice(self, device_id, code, time, sock):
    message = ("QUERY\t" + code + "\t" + device_id + "\t" + time)
    sock.send(message)
    self.recordActivity("Sent: " + message)

  #Function: dataReceived
  #Once the query response comes back, make sure the device ID exists and matches, and if it does, return 50,
  # otherwise return 51 since there are no other restrictions for this yet.
  def dataReceived(self, message, data):
    for x in self.devices:
      if(x.id == message[2]):
        x.addMessage(data)
        return "50"
    return "51"

  #Function: logoffDevice
  #Loop through the devices and if the Id matches the message and the IP matches, record the activity,
  #add the message to the device and logoff the device by setting the bool to false and return 80. Otherwise,
  #if the device does not exist, return 31.
  def logoffDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.login == True):
          self.recordActivity("Data received at: " + str(time.time()))
          x.addMessage(data)
          x.login = False
          return "80"
        elif(x.login == False):
          self.recordActivity("Data received at: " + str(time.time()))
          x.addMessage(data)
          x.login = False
          return "32"
    return "31"

  #queryReceived
  #The function will parse the query and check to see that the queried device id exists
  #If the does, it will send the data back with code 01, if the queried device id exists but is not logged in
  #The function responds with 12, other wise if the queried device id is not registered, the function responds with 11
  def queryReceived(self, message, data, sock):
    for x in self.devices:
      if(x.id == message[2]):
        x.addMessage(data)
      if(x.id == message[4]):
        if(x.login == True):
          self.sendData("01", message[2], x.ip, x.udp_port, message[4], sock)
          return "01"
        elif(x.login == False):
          self.sendData("12", message[2], x.ip, x.udp_port, message[4], sock)
          return "12"

    self.sendData("11", message[2], None, None, message[4], sock)
    return "11"
      
  #sendData
  #The function sends the proper DATA response to the device that queried the device id
  def sendData(self, code, device_id, device_ip, device_port, queried_id, sock):
    if(code == "01"):
      message = "DATA\t" + code + "\t" + device_id + "\t" + str(time.time()) + "\t" + "0\t" + str(queried_id) + "\t" + str(device_ip) + "\t" + str(device_port) 
      length = len(message)
      message = "DATA\t" + code + "\t" + device_id + "\t" + str(time.time()) + "\t" +  str(length) + "\t" + str(queried_id) + "\t" + str(device_ip) + "\t" + str(device_port) 
      self.recordActivity(message)
      sock.send(message)
    else:
      message = "DATA\t" + code + "\t" + device_id + "\t" + str(time.time()) + "\t" + "0\t" + str(queried_id) 
      length = len(message) 
      message = "DATA\t" + code + "\t" + device_id + "\t" + str(time.time()) + "\t" + str(length) + "\t" + str(queried_id)
      self.recordActivity(message)
      sock.send(message)


  #Function: ackClient
  #acknowledge the client with the proper resposne and format based on the command and parameters passed in.
  #commands are based on the client's datagrams/messages sent and the ack's that the client is expecting.
  #Since deregister is the only one with a unique ACk based on the ack code, it has a custom one for the mac and ip
  #address values that the device is expecting.
  def ackClient(self, sock, command, code, device_id, time, hashed_message, addr, mac):
    if (command == "DEREGISTER"):
      if (code == "30"):
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message + "\t" + mac
        sock.send(message)
        self.recordActivity("Sent: " + message)
      else:
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
        sock.send(message)
        self.recordActivity("Sent: " + message)
    elif(command == "LOGIN" and code == "70"):
      message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message + "\t" + self.dropbox_key
      sock.send(message)
      self.recordActivity("Sent: " + message)
    else:
      message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
      sock.send(message)
      self.recordActivity("Sent: " + message)
    


  #Function: recordActivity
  #open the Activity.log file, record the activity and close the file.
  def recordActivity(self, activity):
    file = open('Activity.log', 'a+')
    file.write(activity + " \n")
    file.close()

  #Function: recordError
  #open the Error.log file, record the activity and close the file.
  def recordError(self, activity):
    file = open('Error.log', 'a+')
    file.write(activity + " \n")
    file.close()

#Create the object and call the main thread function of the object
def main():
  #Open up the server on all IPs on the device.
  SERVER_IP = getServerIP()
  TCP_Server = TCPServer(SERVER_IP, server_port)
  TCP_Server.actAsThread()


if __name__ == '__main__':
  main()
