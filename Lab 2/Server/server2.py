import sys
import socket
import SocketServer
from devices import Device
import time
import hashlib
import thread
import threading

data_lock = threading.Lock()
write_sock_lock = threading.Lock()

#grab host name and ip of device
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
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

    self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.write_sock.bind((my_ip, 0))

    self.devices = []
    self.data = []
    self.recent_data = "null"
    self.addr = 0
    file = open('error.log', 'a+')
    file.close()
    file = open('Activity.log', 'a+')
    file.close()

  #main thread of the function, which will listen to incoming datagrams on the socket and parse them.
  def actAsThread(self):
    try:
      write_thread = threading.Thread(target = self.writeSocket,args = (self.recent_data, ))
      write_thread.start()
    except Exception, errtxt:
      print "Could not start new thread"
    #thread.start_new_thread(self.writeSocket, (self.recent_data,))
    self.readSocket()

  def readSocket(self):
    self.read_sock.listen(1)
    #sock, self.addr = self.read_sock.accept()
    print "set up listen"
    while True:
      print "\n~~~~~~~~~~~~~~~~~~~~"
      print "waiting for data"
      sock, self.addr = self.read_sock.accept()
      print "ready to accept data"
      self.recent_data = sock.recv(1024)
      print "Received Message: ", self.recent_data
      data_lock.acquire()
      self.data.append(self.recent_data)
      print "Received from: ", self.addr
      self.changeClient(self.addr[0], self.addr[1])
      #print "Received Message: ", self.recent_data
      #self.parse(self.data, self.addr)
      data_lock.release()
      print "~~~~~~~~~~~~~~~~~~~~"


  def writeSocket(self, c):
    return 0
  #  while True:
      #print "\n~~~~~~~~~~~~~~~~~~~~"
  #    if(len(self.data) != 0):
        #print len(self.data)
  #      data_lock.acquire()
  #      write_sock_lock.acquire()
        #print "write lock acquired"
  #      self.write_sock.send(self.data[0])
  #      self.data.pop(0)
        #print "sent data"
        #print self.send(self.recent_data)
  #      write_sock_lock.release()
  #      data_lock.release()
        #print "write lock released"

  def changeClient(self, ip_address, port):
    print ip_address, " ", port
    #write_sock_lock.acquire()
    #self.write_sock.close()
    #print "change lock"
    #self.write_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #print ip_address
    #self.write_sock.connect((ip_address, 5015))
    #print "about to release lock"
    #write_sock_lock.release()
    print "changed socket"

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
