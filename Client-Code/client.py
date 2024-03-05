import socket
import struct,threading
import sys
import os
import ssl

# Initialize socket stuff
TCP_IP = "127.0.0.1"  # Only a local server
TCP_PORT = 9790  # Just a random choice
BUFFER_SIZE = 2048  # Standard size

# Function to connect with the server 
def conn():
    # Connect to the server
    print("Connecting to the server....")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# Creates a new socket object named s AF_INET-->IPV4 and Sock_STREAM-TCP socket
    try:
        s.connect((TCP_IP, TCP_PORT)) # tries to connect to the server using the connect method 
        print("Connection successful\nEnter the authentication details to verify your identity")
        return s
    except Exception as e:
        print("Connection failed:", e)# If an exception occurs it moves to this block and prints Connection failed along with exception name
        return None

def authenticate(s):# Takes the socket object s as an argument
    try:
        # Receive authentication prompt
        print(s.recv(BUFFER_SIZE).decode())
        # Send username
        username = input("Enter username: ")
        #sends the username through socket s
        s.send(username.encode())
        # Receive password prompt
        print(s.recv(BUFFER_SIZE).decode())
        # Send password
        password = input("Enter password: ")
        s.send(password.encode())
        # Receive authentication result
        auth_result = s.recv(BUFFER_SIZE).decode()
        # Checks for the authentication message sent by the server 
        if auth_result == "Authenticated":
            print("Authentication successful.")
            print("SSL implemented successfully")
            return True
        else:
            print("Authentication failed.")
            return False
        # Checks for an exception if there is any prints error with exception details
    except Exception as e:
        print("Error during authentication:", e)
        return False


def upld(s, file_name):
    # Send upload command which is in bytes format
    s.send(b"UPLD")
    # Send file name size here "h" stands for short integer format specifier and file name
    s.send(struct.pack("h", len(file_name)))
    s.send(file_name.encode())
    # Send file size
    file_size = os.path.getsize(file_name)
    # sends the file size in integer format
    s.send(struct.pack("i", file_size))
    # Send file content
    # opens the file in binary read mode ,with statement is used to properly close the file
    with open(file_name, "rb") as f:
        # while loop iterates indefinitely, reads chunks of data from the file 
        while True:
            data = f.read(BUFFER_SIZE)
            # if statement checks whether it has reached the end of file
            if not data:
                break
            s.send(data)
    print("Upload complete.")

def list_files(s):
    # Send list command
    s.send(b"LIST")
    # Receive and print file listing
    number_of_files = struct.unpack("i", s.recv(4))[0]
    # loop iterates over each file and prints it size
    for _ in range(number_of_files):
        file_name_size = struct.unpack("i", s.recv(4))[0]
        file_name = s.recv(file_name_size).decode()
        file_size = struct.unpack("q", s.recv(8))[0]
        print(f"{file_name} - {file_size} bytes")
        # Send acknowledgment
        s.send(b"1")
    # Receive and print total directory size q-->64 bit signed integer(long int)
    total_directory_size = struct.unpack("q", s.recv(8))[0]
    print(f"Total directory size: {total_directory_size} bytes")
    # Send acknowledgment
    s.send(b"1")

def dwld(s, file_name):
    # Send download command
    s.send(b"DWLD")
    # Send file name size and file name
    s.send(struct.pack("h", len(file_name)))
    s.send(file_name.encode())
    # Receive file size
    file_size = struct.unpack("i", s.recv(4))[0]
    # Checks if the size of the file is -1 then it prints file does not exist
    if file_size == -1:
        print("File does not exist.")
        return
    s.send(b'BUFFER_SIZE')
    # Receive file content
    # Opens the file in binary write mode ("wb"), used to store the content received from the server
    with open(file_name, "wb") as f:
        bytes_received = 0
        while bytes_received < file_size:
            data = s.recv(BUFFER_SIZE)
            # if statement checks whether it has reached the end of the file
            if not data:
                break
            f.write(data)
            bytes_received += len(data)
    print("Download complete.")

def quit(s):
    # Sends quit command which is byte encoded
    s.send(b"QUIT")
    # Closes the connection
    s.close()
    print("Connection closed.")

print("\n\nWelcome to our FTP client.\n\nCall any one of the following functions:\nCONN           : For establishing connection with the server\nUPLD file_path : For Uploading the file\nLIST           : For Listing files in the present Directory\nDWLD file_path : For Downloading the file\nQUIT           : For quiting out from the server ")

while True:
    # Listen for a command
    prompt = input("\nEnter a command: ")
    if prompt[:4].upper() == "CONN":
        s = conn()
        if s:
            authenticated = authenticate(s)
    elif prompt[:4].upper() == "UPLD":
        if authenticated:
            upld(s, prompt[5:])
    elif prompt[:4].upper() == "LIST":
        if authenticated:
            list_files(s)
    elif prompt[:4].upper() == "DWLD":
        if authenticated:
            dwld(s, prompt[5:])
    elif prompt[:4].upper() == "QUIT":
        if authenticated:
            quit(s)
            break
    else:
        print("Command not recognized; please try again with a valid command as mentioned above.")
# We use threading to handle multiple clients
upload_thread = threading.Thread(target =authenticate ,args = (s,)).start()