import socket
import struct
import time
import threading
from datetime import datetime

# Define MAC addresses for server and client
server_mac = "00:11:22:33:44:55"
client_mac = "66:77:88:99:AA:BB"

# Define the number of frames and frame size
num_frames = 304000
frame_size = 1500
batch_size = 91200  # Process frames in batches


# Convert MAC addresses to binary format
def mac_to_bytes(mac):
    return bytes.fromhex(mac.replace(":", ""))


server_mac_bytes = mac_to_bytes(server_mac)
client_mac_bytes = mac_to_bytes(client_mac)

# Create an Ethernet frame with the specified size
ethertype = b'\x08\x00'  # IPv4 ethertype
payload = b'X' * (frame_size - 14)  # Payload size minus Ethernet header size
frame = client_mac_bytes + server_mac_bytes + ethertype + payload

# Create raw sockets for sending and receiving frames
send_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
send_sock.bind(("eth0", 0))

recv_sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0800))
recv_sock.bind(("eth0", 0))

# Increase socket buffer size
send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 ** 30)
recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 ** 30)

# Set non-blocking mode and timeouts
recv_sock.setblocking(False)
recv_sock.settimeout(1.0)

# Event objects to signal completion
send_complete = threading.Event()
recv_complete = threading.Event()


def send_frames(start_time_str):
    start_time = time.time()
    for i in range(0, num_frames, batch_size):
        for _ in range(batch_size):
            send_sock.send(frame)
    end_time = time.time()
    elapsed_time = end_time - start_time
    total_data_sent = num_frames * frame_size / (1024 * 1024)  # Convert to MB
    speed = total_data_sent / elapsed_time  # MB/s

    report = {
        "Test Start Time": start_time_str,
        "Number of Frames Sent": num_frames,
        "Frame Size (bytes)": frame_size,
        "Total Data Sent (MB)": total_data_sent,
        "Time Taken (seconds)": elapsed_time,
        "Speed (MB/s)": speed
    }

    with open("send_report.txt", "w") as f:
        for key, value in report.items():
            f.write(f"{key}: {value}\n")

    print("Send report generated.")
    send_complete.set()  # Signal that sending is complete


def receive_frames(start_time_str):
    received_frames = 0
    start_time = time.time()
    while not send_complete.is_set() or received_frames < num_frames:
        try:
            data = recv_sock.recv(frame_size)
            if data:
                received_frames += 1
        except socket.timeout:
            continue
    end_time = time.time()
    elapsed_time = end_time - start_time
    total_data_received = received_frames * frame_size / (1024 * 1024)  # Convert to MB
    speed = total_data_received / elapsed_time  # MB/s

    report = {
        "Test Start Time": start_time_str,
        "Number of Frames Received": received_frames,
        "Frame Size (bytes)": frame_size,
        "Total Data Received (MB)": total_data_received,
        "Time Taken (seconds)": elapsed_time,
        "Speed (MB/s)": speed
    }

    with open("receive_report.txt", "w") as f:
        for key, value in report.items():
            f.write(f"{key}: {value}\n")

    print("Receive report generated.")
    recv_complete.set()  # Signal that receiving is complete


def start_test():
    # Capture the start time
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add a delay before starting the transmission and receiving to allow time to start the script on the other end
    time.sleep(10)  # Delay for 10 seconds

    # Create threads for sending and receiving frames
    send_thread = threading.Thread(target=send_frames, args=(start_time_str,))
    recv_thread = threading.Thread(target=receive_frames, args=(start_time_str,))

    # Start the threads
    send_thread.start()
    recv_thread.start()

    # Wait for both threads to complete
    send_thread.join()
    recv_thread.join()

    print("Bi-directional test completed.")


start_test()
