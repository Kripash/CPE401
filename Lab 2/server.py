import sys
import socket
import SocketServer

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
server_port = int(sys.argv[1])
#print("Your Computer Name is:" + hostname)
#print("Your Computer IP Address is:" + IPAddr)

class UCHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    remote = self.client_address
    data, skt = self.request
    print("Received Message: ", data)
    print("Received from: ", remote)
    skt.sendto("Why did you say " + data + " ?", remote)

def main():
  UDP_server = ("0.0.0.0", server_port)
  myserver = SocketServer.UDPServer(UDP_server, UCHandler)
  myserver.serve_forever()

if __name__ == '__main__':
  main()


#import socket
#UDP_IP = "192.168.56.1"
#UDP_PORT = 5006
#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
#sock.bind((UDP_IP, UDP_PORT))

#print("Server IP: ", UDP_IP)
#print("Server Port: ", UDP_PORT)

#while True:
#  data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
#  print("received message: ", data)
#  print("from :", addr)
#  sock.sendto("Why did you say " + data +" ?" , addr)
