Author: Kripash Shrestha
File: Readme.txt 
Project: CPE 401 Lab 2

Files:
 client.py
This file is the python file that will run on the client and has a UI that the user can interact with the client to call functions to communicate with the server. 

devices.py 
This file holds the device object that is called by server.py for an object-oriented approach to each device that the server can keep track of. 

server.py 
This file is the python file that will run on the server and is always on a blocking call waiting for a client to send it messages so that it may respond back to the client. 

How the program works: 
On the client side, the user side, the user will be able to start up the program and once done so, the program will inform the user of the IP that the client binds to. Keep in mind that the client is listening to all the IP addresses on the device, but it has a specific hostname IP that will be put in some messages for the server to confirm some actions. The client will then prompt the user to enter a 1-time passphrase that has 32 alphanumeric chars at max to act as the device passphrase. 
After the User has completed the initial phases, the user will me prompted to the CLI menu for the client with 5 options. 

1. Register Device With Server – Sends a message to the server to register the device to the server. 

2. DeRegister Device With Server – Sends a message to the server to deregister the device from the server. 

3. Login Device to System – Sends a message to the server to login the device to the Server. 
Keep in mind that since there was no explicit decision on what to do with a device that was already logged into a system, 
the server will Ack back with 70, every time the device can register, even if it is already registered. 
This also triggers a Query from the server to the client, in which the client will generate a random binary number from 1- 100 to send back as the data. 
You may notice that this may take a while to finish as it waits for all of the python function calls to exit and go back to the main loop.

4. Logoff Device From System – Sends a message to the server to logoff the device from the server. 
Keep in mind that since there was no explicit decision on what to do with a device that was already logged off from the system, 
the server will Ack back and log off the device every time it can, even if it is already logged off. 

5. Exit - The program will unbind the socket from the IP and exit with 0.

I took an object-oriented approach to the problem by making the client an object and server objects and every device that could be registered as an object. This allows for an ease of access to functions, member objects 
and makes the server modifications easier for future projects and additions. 
One problem I had was getting the IP address of the machine on linux. On Windows, it worked and would return the correct IP address. However, when on linux 
the hostname and IP always resolved to localhost/127.0.0.1, and would therefore cause some issues with a client being up on linux. This has no affect on the server itself, 
but it does on the client, since it needs the machine IPs to send with messages. After some research, I figured out that it has to do with the host names 
registered in /etc/hosts. To solve this, I had used a solution from stackoverflow, https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
from user Jamieson Becker with the license: MIT/CC2-BY-SA. 



