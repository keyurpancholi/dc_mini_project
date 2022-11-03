
from multiprocessing.sharedctypes import Synchronized
from timeit import default_timer as timer
from dateutil import parser
import threading
import datetime
import socket
import json
import time
import datetime
from colorama import Fore, Style

from server import print_messages
name = ''

cid = ''
hasToken = False
isCritical = False
reqQ = []

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
            print_messages(payload, slave_client)
            continue
        Synchronized_time = parser.parse(payload['time'])

        print("Synchronized time at the client is: " +
              str(Synchronized_time),
              end="\n\n")


def acquireToken(slave_client):
    print('Sent token request')
    data = {
        'type': 'broadcast_request',
        'cid': cid
    }
    payload = json.dumps(data)
    slave_client.send(payload.encode())


def waitUntilLock():
    print('Waiting for lock')
    while True:
        if hasToken == True:
            break
    # time.sleep(.5)


def handleRequests(slave_client):
    global hasToken
    if len(reqQ):
        nextCid = reqQ.pop(0)
        data = {
            'type': 'token_release',
            'cid': nextCid,
            'reqQ': reqQ
        }
        payload = json.dumps(data)
        hasToken = False
        slave_client.send(payload.encode())


def sendMessage(slave_client):
    global isCritical, hasToken, cid
    while True:
        # print("Send Message", end='\n')
        message = input()
        data = {
            'type': 'message',
            'message': message,
            'name': cid
        }
        if not hasToken:
            acquireToken(slave_client)
            waitUntilLock()
            hasToken = True
            print('Lock acquired')
            isCritical = True
        print('now sending message')
        payload = json.dumps(data)
        slave_client.send(payload.encode())
        chatFile = open("chat.txt", "a")
        chatFile.write(f"{cid}: {message} {datetime.datetime.now()} \n")
        chatFile.close()
        isCritical = False
        handleRequests(slave_client)


def print_messages(data, slave_client):
    global name, hasToken, isCritical, cid, reqQ
    if data['type'] == 'connect':
        name = data['name']
        print(f"{name} connected")
        if data['clientCount'] == 1:
            hasToken = True
            print(cid, 'has token')
    if data['type'] == 'message':
        _name = data['name']
        message = data['message']
        print(Fore.GREEN + f"{_name}: {message}")
        print(Style.RESET_ALL)

    if data['type'] == 'broadcast_request' and hasToken:
        if not isCritical:
            data = {
                'type': 'token_release',
                'cid': data['cid'],
                'reqQ': reqQ
            }
            payload = json.dumps(data)
            slave_client.send(payload.encode())
            hasToken = False

        if isCritical:
            reqQ.append(data['cid'])

    if data['type'] == 'token_release' and data['cid'] == cid:
        reqQ = data['reqQ']
        hasToken = True
        # function used to Synchronize client process time


def initiateSlaveClient(port=8080):

    global name, cid
    slave_client = socket.socket()
    name = input("Enter name => ")

    # connect to the clock server on local computer
    slave_client.connect(('127.0.0.1', port))
    data = {
        'type': 'connect',
        'name': name
    }
    cid = name
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
