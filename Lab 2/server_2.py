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

  def actAsThread(self):
    while True:
      print "\n~~~~~~~~~~~~~~~~~~~~"
      data, addr = self.sock.recvfrom(1024)
      print "Received from: ", addr
      print "Received Message: ", data
      self.parse(data, addr)
      print "~~~~~~~~~~~~~~~~~~~~"
      # self.sock.sendto("Why did you say " + data + " ?", addr)

  def parse(self, data, addr):
    message = []
    code = str(-1)
    message = (data.split("\t"))
    if (message[0] == "REGISTER"):
      code = self.registerDevice(message, data)
      if (code != "-1"):
        self.ackClient("REGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, message[3], message[4])
    elif (message[0] == "DEREGISTER"):
      mac = "NULL"
      ip = "NULL"
      code = self.deregisterDevice(message)
      if(code == "30"):
        for x in self.devices:
          if(x.id == message[1]):
            mac = x.mac
            ip = x.ip
      self.ackClient("DEREGISTER", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, mac, ip)
    elif(message[0] == "LOGIN"):
      code = self.loginDevice(message)
      self.ackClient("LOGIN", code, str(message[1]), str(time.time()), hashlib.sha256(data).hexdigest(), addr, message[3], message[4])

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
        if (x.ip == message[4] and x.mac == message [3]):
          self.devices.remove(x)
          return "20"
        elif(x.ip != message[4] or x.mac != message[3]):
          return "30"

    return "21"

  def loginDevice(self, message):
    for x in self.devices:
      if(x.id == message[1]):
        if(x.passphrase == message[2]):
          x.login = True
          return "70"
    return "31"


  def ackClient(self, command, code, device_id, time, hashed_message, addr, mac, ip):
    if(command == "REGISTER"):
      message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
      self.sock.sendto(message, addr)
    elif(command == "DEREGISTER"):
      if(code == "30"):
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message + "\t" + mac + "\t" + ip
      else:
        message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
      self.sock.sendto(message, addr)
    elif(command == "LOGIN"):
      message = message = "ACK\t" + code + "\t" + device_id + "\t" + time + "\t" + hashed_message
      self.sock.sendto(message, addr)

def main():
  UDP_Server = UDPServer("0.0.0.0", server_port)
  UDP_Server.actAsThread()


if __name__ == '__main__':
  main()
