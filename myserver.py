#!/usr/bin/env python3

import socket
import os
import sys
import struct

def out_band_deframe(files):
    extracted_files, extracted_contents = [], []

    if not os.path.exists(files):                              
        os.write(2, ("Framed file %s does not exist\n" % files).encode())
        exit()

    with open(files, 'rb') as file:
        while True:
            raw_length = file.read(8)
            if not raw_length:
                break 
            filename_length = struct.unpack("Q", raw_length)[0]

            filename = file.read(filename_length).decode()
            content_size = struct.unpack("Q", file.read(8))[0]

            content = file.read(content_size)

            with open(filename, 'wb') as f:
                f.write(content)
                extracted_files.append(filename)
                extracted_contents.append(content)

    return extracted_files, extracted_contents

def receiver(connection):
    folder = "transferred-files"
    os.makedirs(folder, exist_ok=True)
    filename = connection.recv(1024).decode()
    file_path = os.path.join(folder, filename)

    if os.path.isfile(file_path):
        os.remove(file_path)

    with open(file_path, 'wb') as file:
        while True:
            data = connection.recv(1024)
            if not data:
                break
            file.write(data)

    extracted_files, extracted_contents = out_band_deframe(file_path)
    os.remove(file_path)

    return extracted_files, extracted_contents

def ack(connection, ack_message):
    ack_message = ack_message.encode()
    connection.sendall(ack_message)

def reap_zombies():
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            print(f"Child process {pid} terminated")
        except OSError:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 50000))
    sock.listen(5)  # Maximum 5 pending connections

    print("Server is listening...")

    while True:
        reap_zombies()
        connection, address = sock.accept()
        print(f"Connection from {address}")

        incoming = connection.recv(1024).decode()
        print(f"Receiving file: {incoming}")

        received_filename, received_contents = receiver(connection)
        if received_filename and received_contents:
            print("File has been successfully received.")

        ack_message = "Acknowledged"
        ack(connection, ack_message)
        print("Acknowledgement sent")

        connection.shutdown(socket.SHUT_WR)
        connection.close()

if __name__ == "__main__":
    main()
