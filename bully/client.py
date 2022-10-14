
from multiprocessing.sharedctypes import Synchronized
from timeit import default_timer as timer
from dateutil import parser
import threading
import datetime
import socket
import json
import time

from server import print_messages
name = ''

# client thread function used to send time at client side


def startSendingTime(slave_client):

    while True:
        # provide server with clock time at the client
        data = {
            'type': 'time',
            'time': str(
                datetime.datetime.now())
        }
        payload = json.dumps(data)
        slave_client.send(payload.encode())

        print("Recent time sent successfully",
              end="\n\n")

        time.sleep(5)


# client thread function used to receive synchronized time
def startReceivingTime(slave_client):

    while True:
        # receive data from the server
        # Synchronized_time = parser.parse(
        #     slave_client.recv(1024).decode())
        payload = slave_client.recv(1024).decode()
        payload = json.loads(payload)  # data loaded
        if payload.get('type') != 'time':
            print_messages(payload)
            continue
        Synchronized_time = parser.parse(payload['time'])

        print("Synchronized time at the client is: " +
              str(Synchronized_time),
              end="\n\n")


def sendMessage(slave_client):
    while True:
        # print("Send Message", end='\n')
        message = input()
        data = {
            'type': 'message',
            'message': message,
            'name': name
        }
        payload = json.dumps(data)
        slave_client.send(payload.encode())


def print_messages(data):
    global name
    if data['type'] == 'connect':
        name = data['name']
        print(f"{name} connected")
    if data['type'] == 'message':
        _name = data['name']
        message = data['message']
        print(f"{_name}: {message}")


# function used to Synchronize client process time


def initiateSlaveClient(port=8080):

    global name
    slave_client = socket.socket()
    name = input("Enter name => ")

    # connect to the clock server on local computer
    slave_client.connect(('127.0.0.1', port))
    data = {
        'type': 'connect',
        'name': name
    }
    data = json.dumps(data)
    slave_client.send(data.encode())
    print("Send message =>", end='\r')

    # start sending time to server
    print("Starting to receive time from server\n")
    send_time_thread = threading.Thread(
        target=startSendingTime,
        args=(slave_client, ))
    send_time_thread.start()

    # start receiving synchronized from server
    print("Starting to receiving " +
          "synchronized time from server\n")
    receive_time_thread = threading.Thread(
        target=startReceivingTime,
        args=(slave_client, ))

    send_messages = threading.Thread(
        target=sendMessage,
        args=(slave_client, ))
    receive_time_thread.start()
    send_messages.start()


# Driver function
if __name__ == '__main__':

    # initialize the Slave / Client
    initiateSlaveClient(port=8080)
