from vidstream import AudioSender
from vidstream import AudioReceiver

import threading
import socket

receiver_IP = input("Receiver IP :   ")
sender_IP = input("Sender IP :   ")

receiver = AudioReceiver(receiver_IP , 9999)
receive_thread = threading.Thread(target = receiver.start_server)

sender = AudioSender(sender_IP , 5555)
sender_thread = threading.Thread(target = sender.start_stream)

receive_thread.start()
sender_thread.start()

