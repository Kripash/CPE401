LAB 2 
The project Description can be found at: https://www.cse.unr.edu/~mgunes/cpe401/lab2.htm

Overview
In this assignment, we will develop a simple proxy for IoT devices that will allow them to communicate with.

The code that you develop in this part will serve as a basis for the subsequent programming assignments. You must create a pair of programs (client and server). The server (a PC) will act as a central repository where clients (a Raspberry PI) will post and access messages. All communications will happen through the server. Clients establish a UDP connection to interact with the server.

The server code should be started with a parameter of port-number. Similarly, client code should be started with parameters of user-ID, server-IP, and server-port (all separated with spaces).

Message Formats
Following are the application level messages sent from/to the server using UDP sockets (note that message fields are seperated by tab '\t'):

REGISTER device-ID pass-phrase MAC IP port
This command is used to register a device with device-ID and MAC address in the server. The IP address and port number are for the UDP communication. The server will build a database/table of all registered devices and allow devices to search for others using device-ID or MAC. If the client does not get a ACK reply to a REGISTER message after 10 sec then it should retry two more times and if all fail assume the server is unavailable and record the event in the error.log.

ACK code device-ID time hash parameter(s)
This command acknowledges a successfully request. code indicates what is being acknowledged and parameters include any useful information. For instance, after a REGISTER request, if there is no conflict, a reply of code 00 is sent to indicate successful registration. If the user is already registered, a reply of code 01 is sent to indicate previous registration for this device-ID along with a count of any messages waiting for the device. code 02 indicates an updated IP registration. code 12 indicates reused IP address. code 13 indicates reused MAC address. We will extend the list of ACK codes. device-ID confirms the recepient of the acknowledgement. time indicates when the original message that triggered an ACK was received. hash is SHA-256 hash of the original message leading to an ACK.

DEREGISTER device-ID pass-phrase MAC IP port
This command is used to remove a registration from the proxy server. If successful, server should reply with a ACK 20 device-ID time hash to indicate device is successfully removed from the list or ACK 21 device-ID time hash to indicate the MAC or device-ID was not registered anyway. Otherwise, it should notify the client with a ACK 30 device-ID time hash MAC IP message to indicate it was registered to another MAC or IP address.

LOGIN device-ID pass-phrase IP port
This command indicates the device-ID is logging in to the system (sent from device to server). The server should assure the pass-phrase of the packet matches the recorded one before logging in the device. A successful logoff will be replied with ACK 70 device-ID time hash. If device is not registered then the server should send a reply of ACK 31 device-ID time hash.

LOGOFF device-ID
This command indicates the device-ID is leaving the system (sent from device to server). The server should assure the source-IP of the packet matches the device-ID before logging off the device. A successful logoff will be replied with ACK 80 device-ID time hash. If device is not registered then the server should send a reply of ACK 31 device-ID time hash.

DATA Dcode device-ID time length message
This packet carries data from client to server. After successful delivery of the data, the server keeps a log of delivery time in Activity.log file. The server acknowledges reception of a DATA by ACK 50 device-ID time hash reply. If the device-ID does not exist in the system, it will send a ACK 51 device-ID time hash. Dcode is the data type sent from the device.

QUERY code device-ID time parameter(s)
This command from server queries the device for a particular data. The reply is a DATA message. Dcode is the data sought from the device.

Assumptions/Notes:
Report all major actions as the program communicates with other server/users in a file named Activity.log.

We assume device-IDs to be at most 32 alphanumeric characters.

When a malformed message is received report it in a log file named Error.log.

You may utilize localhost (127.0.0.1 or actual IP address) to test your program by running multiple users on the same machine but within different folders (with different port numbers).

If testing on multiple machines, be sure that the machines are not behind a NAT.

Deliverables:
You must submit all the source code in Python with sufficient comments to help understand the code.

You must include in your submission a file named Readme.txt that includes your name and a brief description of your submission, including the name of each file submitted along with a one line description of what is in the file.

If your code is not complete, tell us what works and what doesn't in Readme.txt file. If you are submitting code that does not compile, please tell us that as well. If you borrow code from someone else, you are required to tell us about it (this must also be documented in the code itself).

Finally, feel free to include a description of any problems you had or anything else you think might be helpful to us.

Grading:
You should work individually.

Your assignment will be tested to make sure it works properly.

Your grade will depend on the functionality and the code quality. Hence, please pay careful attention to clean, modular and extensible design as you implement the project.

There will be bonus grades for extra functionality (such as a well designed GUI) not required by the project (optional and at the discretion of the instructor).

There will be bonus for students that point to major issues or add to the program structure.

Remarks:
This document will evolve as we discuss the project and determine communication protocols and messaging formats.

Don't wait till the last minute to start this phase!

Last updated on Feb 20, 2019
