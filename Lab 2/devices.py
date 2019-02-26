import sys


class Device():
  def __init__(self, device_id, device_passphrase, device_mac, device_ip, device_port):
    self.id = device_id
    self.passphrase = device_passphrase
    self.mac = device_mac
    self.ip = device_ip
    self.port = device_port
    self.messages = []
    self.login = False

  def addMessage(self, message):
    self.messages.append(message)

  def debug(self):
    print "~~~~~~~~~~~~~~~~~~~~"
    print "Device ID: ", self.id
    print "Passphrase: ", self.passphrase
    print "Device MAC: ", self.mac
    print "Device IP: ", self.ip
    print "Device PORT: ", self.port
    print "Device Login: ", self.login
    for x in self.messages:
      print "Message: " , x