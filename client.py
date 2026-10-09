import socket
import time

SERVER_IP = "127.0.0.1"
TCP_PORT = 8090
UDP_PORT = 8090

# Start with a small number for testing (e.g., 1000)
# Later set this to 1000000 for the full project
MAX_NUMBER = 1000000


def run_client():
    # Create TCP socket
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((SERVER_IP, TCP_PORT))
    print("Connected to server.")

    # Send START
    tcp_sock.sendall(b"START\n")
    print("Sent START.")

    # Create UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send numbers over UDP
    for i in range(MAX_NUMBER + 1):
        msg = (str(i) + "\n").encode()   # convert number to bytes
        udp_sock.sendto(msg, (SERVER_IP, UDP_PORT))

        if i % 100 == 0:
            print("Sent number:", i)

    print("Finished sending all numbers.")

    # Send END
    tcp_sock.sendall(b"END\n")
    print("Sent END.")

    # Close sockets
    udp_sock.close()
    tcp_sock.close()
    print("Client finished.")


# Make sure the client runs when we execute this file
run_client()
