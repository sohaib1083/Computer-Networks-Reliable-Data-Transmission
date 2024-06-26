#!/usr/bin/env python3

# Package imports
from dotenv import load_dotenv
import random
import socket
import time
import json
import os

# Local imports
from models.TCPPacket import TCPPacket
from models.AuxProcessing import AuxProcessing
from lib.GoBackN import GoBackNSender, SenderWindow

# take environment variables from .env
load_dotenv()

# The SENDER client's hostname or IP address
HOST = str(os.environ['HOST'])

# The port used by the SENDER client
CLIENT_PORT = int(os.environ['RECEIVER_PORT'])

# Port to listen on (non-privileged ports are > 1023)
SERVER_PORT = int(os.environ['SENDER_PORT'])

# Information to receive
BYTES_TO_RECEIVE = int(os.environ['BYTES_TO_RECEIVE'])

# Global TCP Data coverage
TCPData = None

# Global TCP PKT coverage
TCPPkt = None

# Counter for interaction
counter = 0

# Data to send
data = ''

# Data index
data_index = 0

# Timer Conf
TimerStarter = time.process_time()

# Number of clients connected
ClientCount = 0

# Go Back N Sender Client
GoBackN = GoBackNSender()


def SenderClient():

    global TCPData, TCPPkt, counter, data, data_index, TimerStarter, ClientCount

    with open(str(os.environ['DATA_TO_SEND']), mode='rb') as file:
        data = file.read()

    GoBackN.InsertEntry(0, SenderWindow.USABLE)
    for iteration in range(0, (len(data) // int(os.environ['DEFAULT_WINDOW_SIZE'])) + 1):
        GoBackN.InsertEntry(
            1 + iteration*int(os.environ['DEFAULT_WINDOW_SIZE']), SenderWindow.USABLE)

    try:
        with open(str(os.environ['SENDER_LOG_FILENAME']), mode='w') as PKTLogger:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, CLIENT_PORT))

                while True:

                    if (time.process_time() - TimerStarter) >= float(os.environ['IDLE_TIMEOUT']):
                        print(
                            f'[SENDER - {time.process_time()}] Idle timeout')
                        TimerStarter = time.process_time()

                    if ClientCount == 0:

                        PKTLogger.close()
                        s.close()

                    else:
                        if (time.process_time() - TimerStarter) >= float(os.environ['FIXED_TIMEOUT_DELAY']):
                            print(
                                f'[SENDER - {time.process_time()}] Request timed out')
                            PKTLogger.write(
                                f'[SENDING - {time.process_time()}] Counter: {counter} - {TCPPkt.__repr__()}\n{GoBackN.__repr__()}\n\n')
                            counter += 1
                            s.sendall(TCPPkt.EncodeObject())
                            TimerStarter = time.process_time()
                            continue

                        if TCPData == str(b'') or TCPData == None:
                            continue

                        TCPPkt = TCPPacket().CustomConfig(
                            **json.loads(TCPData[2:-1]))

                        PKTLogger.write(
                            f'[RECEIVED - {time.process_time()}] Counter: {counter} - {TCPPkt.__repr__()}\n{GoBackN.__repr__()}\n\n')
                        counter += 1

                        print(
                            f'[SENDER - {time.process_time()}] Received at Sender')

                        if str(os.environ['SENDER_DEBUG']) == 'True':
                            print('In Sender Client', TCPPkt.__dict__)

                        # TCP Handshake, 1st step
                        if TCPPkt.tcp_control_flags['SYN'] == 0x0 and TCPPkt.tcp_control_flags['ACK'] == 0x0 and GoBackN.ReceiveACK(TCPPkt):

                            # TCP Handshake, 2nd step
                            TCPPkt.tcp_control_flags['SYN'] = 0x1
                            TCPPkt.tcp_control_flags['ACK'] = 0x1

                            # The sender should only update the ACK value
                            TCPPkt.sequence_number = AuxProcessing.IntegersToBinary(AuxProcessing.BinaryToIntegers(
                                TCPPkt.sequence_number) + AuxProcessing.BinaryToIntegers(TCPPkt.acknowledgement_number))

                        # The connection has already been established
                        elif TCPPkt.tcp_control_flags['ACK'] == 0x1 and GoBackN.ReceiveACK(TCPPkt):

                            # We have approached the end of the data
                            if data_index + int(os.environ['DEFAULT_WINDOW_SIZE']) >= len(data):

                                window_selected = data[data_index: data_index +
                                                       (len(data) - data_index)]

                                # Set the FIN bit to 1
                                TCPPkt.tcp_control_flags['FIN'] = 0x1

                                # Set the ACK bit to 0
                                TCPPkt.tcp_control_flags['ACK'] = 0x0

                                # Client Counter
                                ClientCount -= 1

                                __temp_store = TCPPkt.acknowledgement_number

                                TCPPkt.sequence_number = AuxProcessing.IntegersToBinary(
                                    AuxProcessing.BinaryToIntegers(TCPPkt.acknowledgement_number) + len(window_selected))

                                TCPPkt.acknowledgement_number = __temp_store

                                data_index = data_index + \
                                    int(os.environ['DEFAULT_WINDOW_SIZE']) + 1
                                
                                try:
                                    print("before: ", type(window_selected))
                                    TCPPkt.data = AuxProcessing.UTF8ToBinary(window_selected.decode('utf-8'))
                                    print("after: ", type(window_selected))
                                except UnicodeDecodeError:
                                    print("Unable to decode the input using UTF-8.")
                                    # Handle the error gracefully, such as skipping this data or logging the error



                            else:

                                window_selected = data[data_index: data_index +
                                                       int(os.environ['DEFAULT_WINDOW_SIZE'])]

                                __temp_store = TCPPkt.acknowledgement_number

                                TCPPkt.sequence_number = AuxProcessing.IntegersToBinary(
                                    AuxProcessing.BinaryToIntegers(TCPPkt.acknowledgement_number) + len(window_selected))

                                TCPPkt.acknowledgement_number = __temp_store

                                data_index = data_index + \
                                    int(os.environ['DEFAULT_WINDOW_SIZE']) + 1
                                
                            try:
                                print("before: ", type(window_selected))
                                TCPPkt.data = AuxProcessing.UTF8ToBinary(window_selected.decode('utf-8'))
                                print("after: ", type(window_selected))
                            except UnicodeDecodeError:
                                print("Unable to decode the input using UTF-8.")
                                # Handle the error gracefully, such as skipping this data or logging the error



                                print("after: ", type(window_selected))

                        time.sleep(random.uniform(0.2, 0.5))

                        PKTLogger.write(
                            f'[SENDING - {time.process_time()}] Counter: {counter} - {TCPPkt.__repr__()}\n{GoBackN.__repr__()}\n\n')
                        counter += 1

                        try:
                            s.sendall(TCPPkt.EncodeObject())
                            GoBackN.SendPkt()
                        except Exception as err:
                            print(
                                f'[SENDER - {time.process_time()}] An error occurred while sending a pkt to the receiver with the data {TCPPkt}: {err}')
                        TimerStarter = time.process_time()

                        TCPData = str(b'')

    except IOError as err:
        print("I/O error({0}): {1}".format(err.errno, err.strerror))


def SenderServer():

    global TCPData, ClientCount

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, SERVER_PORT))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            ClientCount += 1
            while True:
                TCPData = str(conn.recv(BYTES_TO_RECEIVE))
