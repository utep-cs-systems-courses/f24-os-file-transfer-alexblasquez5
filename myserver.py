#!/usr/bin/python3

import socket
import sys
import os
import struct

def frame_data(files):
    framed_data = b""
    for file_name in files:
        if not os.path.exists(file_name):
            print(f"File {file_name} does not exist", file=sys.stderr)
            return None
        
        with open(file_name, "rb") as f:
            content = f.read()
        
        file_name_encoded = file_name.encode()
        file_name_length = struct.pack("Q", len(file_name_encoded))
        content_size = struct.pack("Q", len(content))

        framed_data += file_name_length + file_name_encoded + content_size + content
    
    return framed_data

def send_framed_data(connection, files):
    framed_data = frame_data(files)
    if framed_data:
        connection.sendall(framed_data)
        connection.sendall(b'EOF')

def receive_framed_data(connection):
    framed_data = b""
    while True:
        data = connection.recv(1024)
        if not data:
            break
        framed_data += data
        if b'EOF' in data:
            break
    return framed_data

def extract_data(framed_data):
    extracted_files = []
    extracted_contents = []

    while len(framed_data) >= 8:
        file_name_length = struct.unpack("Q", framed_data[:8])[0]
        if len(framed_data) < 8 + file_name_length + 8:
            break

        file_name = framed_data[8:8 + file_name_length].decode()
        content_size = struct.unpack("Q", framed_data[8 + file_name_length:8 + file_name_length + 8])[0]
        if len(framed_data) < 8 + file_name_length + 8 + content_size:
            break

        content = framed_data[8 + file_name_length + 8:8 + file_name_length + 8 + content_size]

        extracted_files.append(file_name)
        extracted_contents.append(content)

        framed_data = framed_data[8 + file_name_length + 8 + content_size:]

    return extracted_files, extracted_contents

def write_files(files, contents):
    for file_name, content in zip(files, contents):
        with open(file_name, 'wb') as f:
            f.write(content)

def handleClient(client_socket, client_address):
    targetDir = "/home/alexblasquez5/f24-os-file-transfer-alexblasquez5"  # Update with your target directory
    
    print(f"Child: pid = {os.getpid()} connected to client at {client_address}")

    try:
        dataReceived = bytearray()

        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            dataReceived.extend(data)
            if b'EOF' in data:
                break

        tempArchive = os.path.join(targetDir, "receivedArchive.tar")
        with open(tempArchive, 'wb') as file:
            file.write(dataReceived)
        
        os.chdir(targetDir)
        files, contents = extract_data(dataReceived)
        write_files(files, contents)
        print("Files extracted, closing connection!")
    
    finally:
        client_socket.close()

def main():
    listen_port = 50001
    server_address = ('', listen_port)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listen_sock:
        listen_sock.bind(server_address)
        listen_sock.listen(1)

        print(f"Server is listening on port {listen_port}")

        while True:
            print("Waiting for a connection...")
            connection, client_address = listen_sock.accept()

            try:
                print(f"Connection from {client_address}")
                handleClient(connection, client_address)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                connection.close()

if __name__ == "__main__":
    main()
