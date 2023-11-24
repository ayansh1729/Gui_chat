#Creating of terminal chat app
#Features can send text,multi-media,private as well as group messages

#Importing Libraries
import socket
import threading
import os

#Creating a socket object in general a tcp socket
server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

#Creating the address where our server will be running 
Ip_addr = '127.0.0.1'
Port = 8080

#This address is a tuple
address = (Ip_addr,Port)

#Bindind the server to the address
server.bind(address)

#Set up the server for listening (max. clients at a time is 10)
server.listen(10)

#<------- From here the main work strats ----------------->
#? Requirements -> 
#When a client will enter he should have know who all are online
#He can send private message which will be visible only to corresponding client for rest it would be  ****
#He can send group message which will be visible to everyone
#The interface would be common

#So one of the requirements is we want list of all the client who are online
#we can use dictionary to keep track of that

client_online ={}

# Broadcasting Method
def broadcast(message, sender_name):
    for client_name, client_obj in client_online.items():
        if client_name != sender_name:
            client_obj[0].send(message.encode())

    
#Handling the commands
def handle_command(conn, command, username):
    # Handle different commands here
    if command.lower() == '/online':
        online_users = ", ".join(client_online.keys())
        response = f"Online users: {online_users}"
        conn.send(response.encode())
    else:
        response = "Unknown command. Type '/online' to see online users."
        conn.send(response.encode())

def send_private(sender_conn, message, sender_name):
    try:
        recipient_username, private_message = message.split(' ', 1)
        # Ensure that recipient_username starts with '@'
        if recipient_username.startswith('@'):
            recipient_username = recipient_username[1:]  # Remove '@' from the beginning
            print(recipient_username)

            recipient_conn = client_online.get(recipient_username)

            if recipient_conn:
                private_message = f"(Private) {sender_name}: {private_message}"
                recipient_conn[0].send(private_message.encode())
                sender_conn.send("Private message sent.".encode())
            else:
                sender_conn.send(f"User '{recipient_username}' is not online.".encode())
        else:
            sender_conn.send("Invalid private message format.".encode())

    except ValueError:
        sender_conn.send("Invalid private message format.".encode())

# Function to handle file transfer
def handle_file_transfer(sender_conn, message, sender_name):
    try:
        _, file_info = message.split('$', 1)
        recipient_username, file_path = file_info.split(' ', 1)
        print("The file path is:", file_path)

        recipient_conn = client_online.get(recipient_username)

        if recipient_conn:
            recipient_conn[0].send(f"file {file_path}".encode())  # Send the raw file path

            sender_conn.send("File path sent to recipient.".encode())

            # Now, sender (client1) will send the file data to the server
            file_data = sender_conn.recv(1024)  # Adjust the buffer size as needed

            while file_data:
                recipient_conn[0].send(file_data)
                file_data = sender_conn.recv(1024)  # Receive the next chunk

            sender_conn.send("File sent.".encode())
        else:
            sender_conn.send(f"User '{recipient_username}' is not online.".encode())

    except ValueError:
        sender_conn.send("Invalid file transfer format.".encode())
    except Exception as e:
        sender_conn.send(f"Error during file transfer: {e}".encode())

# Handling the clients
def handle_client(conn, addr, username):
    try:
        for client_name, client_obj in client_online.items():
            if client_name != username:
                message = f"{username} joined the chat"
                client_conn, _ = client_obj
                client_conn.send(message.encode())

        while True:
            message = conn.recv(1024).decode()
            print(f"Received message from {username}: {message}")

            if message.lower() == 'exit':
                break

            if message.startswith('/'):
                handle_command(conn, message, username)
            elif message.startswith('@'):
                send_private(conn, message, username)
            elif message.startswith('$'):
                handle_file_transfer(conn, message, username)
            else:
                broadcast(f"{username}: {message}", username)

    except Exception as e:
        print(f"Error handling client {username}: {e}")

    finally:
        print(f"{username} disconnected.")
        # Notify other clients about the departure
        for client_name, client_obj in client_online.items():
            if client_name != username:
                message = f"{username} left the chat"
                client_conn, _ = client_obj
                client_conn.send(message.encode())
        # Remove the client from the online list
        del client_online[username]
        conn.close()

#This beacuse we don't want server to stop unless we do
print("The server is up and listening...")
while True:
    #Accept the incoming connection
    conn,addr = server.accept() 
    connection_obj = (conn,addr)
    # print(f"New client connected: {connection_obj}")    

    #Now asking the client for the username with which he wants to enter chatroom
    name_input = "Enter you username: "
    #Then send it to client object
    conn.send(name_input.encode())     

    #Now listen for the response:
    user_name = conn.recv(1024).decode()
    client_online[user_name] = connection_obj
    print(user_name)

    #Now we want to keep the server running and we also want to handle the client so we would use threading here
    #Let's create a function that will handle clients
    client_thread = threading.Thread(target=handle_client,args=(conn, addr, user_name))
    client_thread.start()
