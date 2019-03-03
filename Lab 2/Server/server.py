#File: server.py
#Author: Kripash Shrestha
#Project: Lab 2

import sys
import socket
import SocketServer
from devices import Device
import time
import hashlib

#grab host name and ip of device
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
server_port = int(sys.argv[1])


class UDPServer():
  #constructor to set up the socket on the server and list of devices
  def __init__(self, my_ip, udp_port):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.bind((my_ip, udp_port))
    self.devices = []
    self.data = "null"
    self.addr = 0
    file = open('error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()

  #main thread of the function, which will listen to incoming datagrams on the socket and parse them.
  def actAsThread(self):
    while True:
      print "\n~~~~~~~~~~~~~~~~~~~~"
      self.data, self.addr = self.sock.recvfrom(1024)
      print "Received from: ", self.addr
      print "Received Message: ", self.data
      self.parse(self.data, self.addr)
      print "~~~~~~~~~~~~~~~~~~~~"

  #Parse the message received and then based on the command of the message, call the function to appropriately
  #deal with each server datagram and then send the proper Ack back.
  def parse(self, data, addr):
    self.recordActivity("Receieved: " + data)
    message = []
    code = str(-1)
    #parse the message and split it based on tabs
    message = (data.split("\t"))
    #If the command is register and the len of message is 6, go ahead and parse it and send the ack, other wise
    #record it as an error
    if (message[0] == "REGISTER"):
      if(len(message) == 6):
        code = self.registerDevice(message, data)
        if (code != "-1"):
          self.ackClient("REGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr,
                       message[3], message[4])
      else:
        self.recordError("Malformed Message!")
    # If the command is deregister and the len of message is 6, go ahead and parse it and send the ack, other wise
    # record it as an error
    elif (message[0] == "DEREGISTER"):
      if (len(message) == 6):
        mac = "NULL"
        ip = "NULL"
        code = self.deregisterDevice(message)
        if (code == "30"):
          for x in self.devices:
            if (x.id == message[1]):
              mac = x.mac
              ip = x.ip
        self.ackClient("DEREGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, mac,
                     ip)
      else:
        self.recordError("Malformed Message!")
    #If the command is login and the len of message is 5, go ahead and parse it and send the ack, other wise
    #record it as an error
    elif (message[0] == "LOGIN"):
      if (len(message) == 5):
        code = self.loginDevice(message, data)
        self.ackClient("LOGIN", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr,
                     message[3], message[4])
        if(code == "70"):
          self.queryDevice(str(message[1]), "0", str(time.time()), addr)
      else:
        self.recordError("Malformed Message!")
    # If the command is logoff and the len of message is 2, go ahead and parse it and send the ack, other wise
    # record it as an error
    elif (message[0] == "LOGOFF"):
      if (len(message) == 2):
        code = self.logoffDevice(message, data)
        self.ackClient("LOGOFF", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, "null",
                     "null")
      else:
        self.recordError("Malformed Message!")
    # If the command is data and the len of message is 6, go ahead and parse it and send the ack, other wise
    # record it as an error
    elif (message[0] == "DATA"):
      if (len(message) == 6):
        code = self.handleData(message[1], message[2], message[4], message[5], data)
        self.ackClient("DATA", code, str(message[2]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, "null",
                     "null")
      else:
        self.recordError("Malformed Message!")
    print "Number of Registered Devices: ", len(self.devices)
    for x in self.devices:
      x.debug()

  #Function: registerDevice
  #Loop through the list of devices and if the device already exists, and the IP is different, update it
  #and add the message to the device list and return 02. If there is nothing left to update, add the message to
  #the device list and return 01. If the device conflicts with mac returns 12 and if with IP, return 13. If the device
  #does not exist, add it to the list and return 00.
  def registerDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1] and x.mac == message[3]):
        if (x.ip != message[4] and x.passphrase == message[2]):
          x.ip = message[4]
          x.addMessage(data)
          return "02"
        else:
          x.addMessage(data)
          return "01"
      elif (x.ip == message[5] and (not (x.id == message[1] and x.mac == message[3]))):
        return "12"
      elif (x.mac == message[3] and x.id != message[1]):
        return "13"
      else:
        return "-1"

    temp = Device(message[1], message[2], message[3], message[4], message[5])
    temp.addMessage(data)
    self.devices.append(temp)
    # self.devices[0].debug()
    return "00"

  #Function: deregisterDevice
  #Loop through the list of devices and if it exists and the mac address and ip matches, remove it from the list and
  #return 20, otherwise if the device doesn't match the ip or mac, return 30 and don't remove it. If the device is not
  #registered, return 21.
  def deregisterDevice(self, message):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.ip == message[4] and x.mac == message[3]):
          self.devices.remove(x)
          return "20"
        elif (x.ip != message[4] or x.mac != message[3]):
          return "30"
    return "21"

  #Function: loginDevice
  #Loop through the list of devices and if it exists, and the passphrase matches, add the message to the device
  #and login by setting the bool as true and return 70. Otherwise, if the device does not exist, return 31.
  def loginDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.passphrase == message[2]):
          x.addMessage(data)
          x.login = True
          return "70"
    return "31"

  #Function: queryDevice:
  #Query the client for data after every login.
  def queryDevice(self, device_id, code, time, addr):
    message = ("QUERY\t" + code + "\t" + device_id + "\t" + time)
    self.sock.sendto(message, addr)

  #Function: handleData
  #Once the query response comes back, make sure the device ID exists and matches, and if it does, return 50,
  # otherwise return 51 since there are no other restrictions for this yet.
  def handleData(self, Dcode, device_id, length, message, data):
    for x in self.devices:
      if (x.id == device_id):
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
        if (x.ip == self.addr[0]):
          self.recordActivity("Data received at: " + str(time.time()))
          x.addMessage(data)
          x.login = False
          return "80"
    return "31"

  #Function: ackClient
  #acknowledge the client with the proper resposne and format based on the command and parameters passed in.
  #commands are based on the client's datagrams/messages sent and the ack's that the client is expecting.
  #Since deregister is the only one with a unique ACk based on the ack code, it has a custom one for the mac and ip
  #address values that the device is expecting.
  def ackClient(self, command, code, device_id, time, hashed_message, addr, mac, ip):
    if (command == "DEREGISTER"):
      if (code == "30"):
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message + "\t" + mac + "\t" + ip
        self.recordActivity("Sent: " + message)
      else:
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
        self.sock.sendto(message, addr)
        self.recordActivity("Sent: " + message)
    else:
      message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
      self.sock.sendto(message, addr)
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
  UDP_Server = UDPServer("0.0.0.0", server_port)
  UDP_Server.actAsThread()


if __name__ == '__main__':
  main()
