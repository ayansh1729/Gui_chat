import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QCoreApplication
import socket
import threading
import struct

class ClientApp(QWidget):
    def __init__(self, client_socket):
        super().__init__()

        self.client_socket = client_socket
        self.receive_thread = None  # Keep track of the receive thread

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('File Transfer Chat Application')

        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)

        self.message_input = QLineEdit(self)
        self.send_button = QPushButton('Send', self)
        self.send_button.clicked.connect(self.send_message)

        self.file_button = QPushButton('Send File', self)
        self.file_button.clicked.connect(self.choose_file)

        layout = QVBoxLayout()
        layout.addWidget(self.chat_display)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        layout.addWidget(self.file_button)

        self.setLayout(layout)

        # Start a thread to receive messages from the server
        self.receive_thread = ReceiveThread(self.client_socket)
        self.receive_thread.message_received.connect(self.display_message)
        self.receive_thread.connection_lost.connect(self.connection_lost_handler)
        self.receive_thread.start()

    def display_message(self, message):
        self.chat_display.append(message)

    def send_message(self):
        message = self.message_input.text()
        if message:
            if message.startswith('$'):
                recipient, filename = message.split(' ', 1)
                recipient = recipient[1:]
                self.send_file(filename, recipient)
            else:
                self.client_socket.send(message.encode())
            self.message_input.clear()

    def choose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filename, _ = QFileDialog.getOpenFileName(self, "Choose File to Send", "", "All Files (*);;Text Files (*.txt)", options=options)
        if filename:
            self.send_file(filename)

    def send_file(self, filename, recipient=None):
        try:
            with open(filename, 'rb') as file:
                file_content = file.read()
        except FileNotFoundError:
            self.chat_display.append(f"File '{filename}' not found.")
            return

        try:
            if recipient:
                self.client_socket.send(f"${recipient} {filename}".encode())
            else:
                self.client_socket.send(filename.encode())

            # Send recipient's name
            recipient_length = len(recipient) if recipient else 0
            self.client_socket.send(struct.pack('>I', recipient_length))
            if recipient:
                self.client_socket.send(recipient.encode())

            # Send file name
            filename_length = len(filename)
            self.client_socket.send(struct.pack('>I', filename_length))
            self.client_socket.send(filename.encode())

            # Send file content
            content_length = len(file_content)
            self.client_socket.send(struct.pack('>I', content_length))
            self.client_socket.send(file_content)

        except ConnectionError:
            self.connection_lost_handler()

    def connection_lost_handler(self):
        print("Connection to server lost.")
        # Perform any cleanup or user notification here
        self.close()

    def closeEvent(self, event):
    # Signal the receive thread to stop before closing the application
        if self.receive_thread:
            self.receive_thread.stop()
            self.receive_thread.wait()
        self.client_socket.close()
        event.accept()


class ReceiveThread(QThread):
    message_received = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket

    def run(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if not message:
                    self.connection_lost.emit()  # Emit the signal when the server connection is lost
                    break
                if message.startswith('file'):
                    self.receive_file()
                else:
                    self.message_received.emit(message)
            except ConnectionError:
                self.connection_lost.emit()  # Emit the signal when the server connection is lost
                break

        # Cleanup when the thread exits
        self.client_socket.close()

    def receive_file(self):
        try:
            # Receive recipient's name
            recipient_length = struct.unpack('>I', self.client_socket.recv(4))[0]
            recipient = self.client_socket.recv(recipient_length).decode()

            # Receive file name
            filename_length = struct.unpack('>I', self.client_socket.recv(4))[0]
            filename = self.client_socket.recv(filename_length).decode()

            # Receive file content
            content_length = struct.unpack('>I', self.client_socket.recv(4))[0]
            file_content = b""
            while len(file_content) < content_length:
                file_content += self.client_socket.recv(1024)

            try:
                with open(filename, 'wb') as file:
                    file.write(file_content)
                print(f"File received: {filename} from {recipient}")
            except Exception as e:
                print(f"Error saving file: {e}")
        except ConnectionError:
            self.connection_lost.emit()  # Emit the signal when the server connection is lost

    def stop(self):
        self.terminate()


def main():
    app = QApplication(sys.argv)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = '127.0.0.1'
    server_port = 8080

    try:
        client_socket.connect((server_ip, server_port))
    except Exception as e:
        print(f"Error connecting to the server: {e}")
        return

    # printing the message
    message = client_socket.recv(1024).decode()
    print(message, end="")
    username = input()
    client_socket.send(username.encode())

    window = ClientApp(client_socket)
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
