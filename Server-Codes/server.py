import socket
import sys
import os
import threading
import struct
import ssl

# Initialize socket stuff
TCP_IP = "127.0.0.1"  # Localhost
TCP_PORT = 9790  # Random choice
BUFFER_SIZE = 2048  # Standard size
AUTH_USERNAME = "username" # Can be changed
AUTH_PASSWORD = "12345"    # Can be changed

def authenticate(conn):
    # Send username prompt
    conn.send("Username: ".encode())
    # Receives username and removes any space using strip function
    username = conn.recv(BUFFER_SIZE).decode().strip()
    # Send password prompt
    conn.send("Password: ".encode())
    # Receives password and removes any space using strip function
    password = conn.recv(BUFFER_SIZE).decode().strip()
    # Authenticates with the username and password sent from the client
    if username == AUTH_USERNAME and password == AUTH_PASSWORD:
        conn.send("Authenticated".encode())
        return True
    else:
        conn.send("Authentication failed".encode())
        return False

def upld(conn):
    # Receive file name length and file name h short integer
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size).decode()
    # Receive file size
    file_size = struct.unpack("i", conn.recv(4))[0]
    # Receive file content
    # opens the file in binary write mode ("wb"), used to store the content received from the client.
    with open(file_name, "wb") as f:
        bytes_received = 0
        while bytes_received < file_size:
            data = conn.recv(BUFFER_SIZE)
            # if statement checks whether it has reached the end of file
            if not data:
                break
            f.write(data)
            bytes_received += len(data)
    print("Received file:", file_name)

def list_files(conn):
    # Get list of files in the directory
    listing = os.listdir(os.getcwd())
    # Send number of files
    conn.send(struct.pack("i", len(listing)))
    # Send file names and sizes
    for file_name in listing:
        conn.send(struct.pack("i", len(file_name)))
        conn.send(file_name.encode())
        conn.send(struct.pack("q", os.path.getsize(file_name)))
        # Wait for acknowledgment
        conn.recv(BUFFER_SIZE)
    # Send total directory size q-->64 bit signed integer(long int)
    total_directory_size = sum(os.path.getsize(file_name) for file_name in listing)
    conn.send(struct.pack("q", total_directory_size))
    # Wait for acknowledgment
    conn.recv(BUFFER_SIZE)

def dwld(conn):
    # Receive file name length and file name
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    #print("1",file_name_size)
    file_name = conn.recv(file_name_size).decode()
    #print("2",file_name)
    # Check if file exists
    if os.path.isfile(file_name):
        # Send file size
        conn.send(struct.pack("i", os.path.getsize(file_name)))
        # Wait for acknowledgment
        conn.recv(BUFFER_SIZE)
        # Send file content
        # opens the file in binary read mode ,with statement is used to properly close the file
        with open(file_name, "rb") as f:
            # while loop iterates indefinitely, reads chunks of data from the file 
            while True:
                data = f.read(BUFFER_SIZE)
                # if statement checks whether it has reached the end of the file
                if not data:
                    break
                conn.send(data)
        print("Sent file:", file_name)
    else:
        # Send error code if file doesn't exist
        conn.send(struct.pack("i", -1))

def quit(conn):
    # h is a short integer
    #file_size_quit = struct.unpack("h", conn.recv(2))[0]
    #print("1",file_name_size)
    #quit_name = conn.recv(file_size_quit).decode()
    # Closes the connection
    #if os.path.isfile(quit_name):
    conn.close()
    print("Connection closed.")
        

def handle_client(conn, addr):
    print("Connected to the client through the address:", addr)
    authenticated = authenticate(conn)
    if not authenticated:
        conn.close()
        return
    
    while True:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            break
        command = data.decode()
        if command == "UPLD":
            upld(conn)
        elif command == "LIST":
            list_files(conn)
        elif command == "DWLD":
            dwld(conn)
        elif command == "QUIT":
            quit(conn)
            break
        else:
            print("Invalid command")
    print("Connection closed by client:", addr)

# Create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(10)  # Allow up to 10 connections in the queue
print(f"Server is listening on {TCP_IP}:{TCP_PORT}")

#ssl geneartion and handshake connection
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain("server.crt", "server.key")
ssl_context.load_verify_locations("client.crt")  # Path to client certificate
ssl_context.verify_mode = ssl.CERT_REQUIRED

# We use threading library to handle multiple clients simultaneously 
while True:
    conn, addr = s.accept()
    client_thread = threading.Thread(target=handle_client, args=(conn, addr))
    client_thread.start()
