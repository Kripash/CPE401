import sys
#File: devices.py
#Author: Kripash Shrestha
#Project: Lab 4

#This file represents the devices that will be connecting and registering with the server.
#Every device has a :
# id
# mac address
# ip
# device passphrase
# port to reach the device
# messages that it has sent to server
# login boolean to indicate login


class Device():
  #constructor for the device
  def __init__(self, device_id, device_passphrase, device_mac, device_ip):
    self.id = device_id
    self.passphrase = device_passphrase
    self.mac = device_mac
    self.ip = device_ip
    self.messages = []
    self.login = False
    self.sock = None
    self.udp_port = None

  #append a message to the list everytime the client sends a message to the server
  def addMessage(self, message):
    self.messages.append(message)

  #print the data from the device to the terminal
  def debug(self):
    print "~~~~~~~~~~~~~~~~~~~~"
    print "Device ID: ", self.id
    print "Passphrase: ", self.passphrase
    print "Device MAC: ", self.mac
    print "Device IP: ", self.ip
    print "Device PORT: ", self.udp_port
    print "Device Login: ", self.login
    for x in self.messages:
      print "Message: " , x
