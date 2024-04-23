#! /usr/bin/env python3

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
        extractArchiveOutBand(tempArchive)
        print("Archive extracted, closing connection!")
    
    finally:
        client_socket.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: myclient.py <file1> <file2> ...", file=sys.stderr)
        sys.exit(1)
    
    server_address = ('127.0.0.1', 50001)
    files = sys.argv[1:]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(server_address)
            print(f"Connected to {server_address}")
            send_framed_data(sock, files)
            print("File(s) sent successfully")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
