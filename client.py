import socket
import threading
import os

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message.startswith('file'):
                _, file_path = message.split(' ', 1)
                receive_file(client_socket, file_path)
            else:
                print(message)
        except ConnectionError:
            print("Connection to server lost.")
            break

def send_messages(client_socket):
    while True:
        try:
            message = input("> ")
            if message.lower() == 'exit':
                client_socket.close()
            elif message.startswith('$'):
                client_socket.send(message.encode())
                confirmation = client_socket.recv(1024).decode()
                if confirmation.startswith('file'):
                    _, filename = confirmation.split(' ', 1)
                    send_file(client_socket, filename)
                else:
                    print(confirmation)
            else:
                client_socket.send(message.encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            break



def send_file(client_socket,filename):
    try:
        with open(filename, 'rb') as file:
            file_data = file.read(1024)
            while file_data:
                client_socket.send(file_data)
                file_data = file.read(1024)

        print(f"File '{filename}' sent.")
    except Exception as e:
        print(f"Error sending file: {e}")

def receive_file(client_socket, file_path):
    try:
        with open(os.path.basename(file_path), 'wb') as file:
            file_data = client_socket.recv(1024)
            while file_data:
                file.write(file_data)
                file_data = client_socket.recv(1024)

        print(f"File received: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"Error receiving file: {e}")

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = '127.0.0.1'
    server_port = 8080

    try:
        client.connect((server_ip, server_port))
    except Exception as e:
        print(f"Error connecting to the server: {e}")
        return

    # printing the message
    message = client.recv(1024).decode()
    print(message, end="")
    username = input()
    client.send(username.encode())

    # Start a thread to receive messages from the server
    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    try:
        send_messages(client)
    except KeyboardInterrupt:
        print("Client disconnected.")
    finally:
        client.close()

if __name__ == "__main__":
    main()
