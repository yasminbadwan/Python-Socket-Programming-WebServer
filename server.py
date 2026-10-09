import socket

TCP_PORT = 8090
UDP_PORT = 8090
BUFFER_SIZE = 1024  # maximum size of a UDP packet in bytes


def run_server():
    # Create TCP socket for START and END messages
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_sock.bind(('', TCP_PORT))
    tcp_sock.listen(1)
    print("Server is listening on TCP port", TCP_PORT)

    # Create UDP socket for receiving numbers
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', UDP_PORT))
    print("Server is listening on UDP port", UDP_PORT)

    while True:
        print("\nWaiting for a TCP client...")
        conn, addr = tcp_sock.accept()
        print("New TCP connection from:", addr)

        # Receive START message over TCP
        start_msg = conn.recv(1024).decode('utf-8').strip()
        print("Received over TCP:", start_msg)

        if start_msg != "START":
            # If the first message is not START, close this client
            print("First message was not 'START'. Closing connection.")
            conn.close()
            continue

        print("START received. Now listening for UDP numbers...")

        # Set timeout for UDP socket (to stop when client finishes)
        udp_sock.settimeout(2.0)

        count = 0          # number of UDP packets received
        out_of_order = 0   # how many times the order was wrong
        last_number = -1   # last number received

        while True:
            try:
                # Receive one UDP packet
                data, client_addr = udp_sock.recvfrom(BUFFER_SIZE)
                text = data.decode('utf-8').strip()

                if text == "":
                    # Ignore empty packets
                    continue

                # Convert text to integer
                try:
                    n = int(text)
                except ValueError:
                    # Ignore invalid data
                    print("Received non-integer UDP data:", text)
                    continue

                # Increase packet counter
                count += 1

                # Check if the sequence is broken
                if last_number != -1 and n != last_number + 1:
                    out_of_order += 1

                last_number = n

            except socket.timeout:
                # No UDP packets for a while, stop receiving
                print("No UDP packets for some time. Stopping UDP receiving.")
                break

        # Receive END message over TCP
        end_msg = conn.recv(1024).decode('utf-8').strip()
        print("Received over TCP:", end_msg)

        # Print results
        print("\n=== RESULTS ===")
        print("Total UDP packets received:", count)
        print("Last number received:", last_number)
        print("Out-of-order events:", out_of_order)
        print("===============\n")

        conn.close()
        print("TCP connection closed.")


if __name__ == "__main__":
    run_server()
