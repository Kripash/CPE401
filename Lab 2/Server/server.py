import sys
import socket
import SocketServer
from devices import Device
import time
import hashlib

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
server_port = int(sys.argv[1])


class UDPServer():
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

  def actAsThread(self):
    while True:
      print "\n~~~~~~~~~~~~~~~~~~~~"
      self.data, self.addr = self.sock.recvfrom(1024)
      print "Received from: ", self.addr
      print "Received Message: ", self.data
      self.parse(self.data, self.addr)
      print "~~~~~~~~~~~~~~~~~~~~"

  def parse(self, data, addr):
    self.recordActivity("Receieved: " + data)
    message = []
    code = str(-1)
    message = (data.split("\t"))
    if (message[0] == "REGISTER"):
      if(len(message) == 6):
        code = self.registerDevice(message, data)
        if (code != "-1"):
          self.ackClient("REGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr,
                       message[3], message[4])
      else:
        self.recordError("Malformed Message!")
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
    elif (message[0] == "LOGIN"):
      if (len(message) == 5):
        code = self.loginDevice(message, data)
        self.ackClient("LOGIN", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr,
                     message[3], message[4])
        if(code == "70"):
          self.queryDevice(str(message[1]), "0", str(time.time()), addr)
      else:
        self.recordError("Malformed Message!")
    elif (message[0] == "LOGOFF"):
      if (len(message) == 2):
        code = self.logoffDevice(message, data)
        self.ackClient("LOGOFF", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, "null",
                     "null")
      else:
        self.recordError("Malformed Message!")
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

  def deregisterDevice(self, message):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.ip == message[4] and x.mac == message[3]):
          self.devices.remove(x)
          return "20"
        elif (x.ip != message[4] or x.mac != message[3]):
          return "30"
    return "21"

  def loginDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.passphrase == message[2]):
          x.addMessage(data)
          x.login = True
          return "70"
    return "31"

  def queryDevice(self, device_id, code, time, addr):
    message = ("QUERY\t" + code + "\t" + device_id + "\t" + time)
    self.sock.sendto(message, addr)

  def handleData(self, Dcode, device_id, length, message, data):
    for x in self.devices:
      if (x.id == device_id):
        x.addMessage(data)
        return "50"
    return "51"

  def logoffDevice(self, message, data):
    for x in self.devices:
      if (x.id == message[1]):
        if (x.ip == self.addr[0]):
          self.recordActivity("Data received at: " + str(time.time()))
          x.addMessage(data)
          x.login = False
          return "80"
    return "31"

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

  def recordActivity(self, activity):
    file = open('Activity.log', 'a+')
    file.write(activity + " \n")
    file.close()

  def recordError(self, activity):
    file = open('Error.log', 'a+')
    file.write(activity + " \n")
    file.close()


def main():
  UDP_Server = UDPServer("0.0.0.0", server_port)
  UDP_Server.actAsThread()


if __name__ == '__main__':
  main()
