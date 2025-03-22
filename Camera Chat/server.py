from vidstream import CameraClient, StreamingServer
import threading
import time

serverIP = input("Enter Server IP: ")
serverPort = int(input("Enter Server Port: "))
clientIP = input("Enter Client IP: ")
clientPort = int(input("Enter Client Port: "))

# Initialize the streaming server and client
receiving = StreamingServer(serverIP, serverPort)
sending = CameraClient(clientIP, clientPort)

# Start server in a separate daemon thread
t1 = threading.Thread(target=receiving.start_server, daemon=True)
t1.start()

time.sleep(2)  # Allow the server to initialize

# Start client in a separate daemon thread
t2 = threading.Thread(target=sending.start_stream, daemon=True)
t2.start()

# Wait for user input to stop the program
input("Press ENTER to stop...\n")

# Stop the server and client
receiving.stop_server()
sending.stop_stream()
