
from dateutil import parser
from threading import *
import threading
import datetime
import socket
import json
import time
import random


client_data = {}


''' nested thread function used to receive
	clock time from a connected client '''


def startReceivingClockTime(connector, address, data):

    # while True:
    # receive clock time
    # data = connector.recv(1024).decode()
    # data = json.loads(data)
    # print("type=", data)

    if data['type'] != 'time':
        print_messages(data)
        return

    print("time recieved")
    clock_time = parser.parse(data['time'])
    clock_time_diff = datetime.datetime.now() - \
        clock_time

    client_data[address] = {
        "clock_time": clock_time,
        "time_difference": clock_time_diff,
        "connector": connector
    }

    print("Client Data updated with: " + str(address),
          end="\n\n")
    # time.sleep(5)


''' master thread function used to open portal for
	accepting clients over given port '''


def startConnecting(master_server):

    # fetch clock time at slaves / clients
    while True:
        # accepting a client / slave clock client
        master_slave_connector, addr = master_server.accept()
        slave_address = str(addr[0]) + ":" + str(addr[1])

        print(slave_address + " got connected successfully")

        # current_thread = threading.Thread(
        #     target=startReceivingClockTime,
        #     args=(master_slave_connector,
        #           slave_address, ))

        receive_messages = threading.Thread(target=receiveData,
                                            args=(master_slave_connector,
                                                  slave_address, ))
        receive_messages.start()
        data = {
            'type': 'time',
            'time': str(
                datetime.datetime.now())
        }
        startReceivingClockTime(master_slave_connector, slave_address, data)

        # current_thread.start()

# subroutine function used to fetch average clock difference


def getAverageClockDiff():

    current_client_data = client_data.copy()

    time_difference_list = list(client['time_difference']
                                for client_addr, client
                                in client_data.items())

    sum_of_clock_difference = sum(time_difference_list,
                                  datetime.timedelta(0, 0))

    average_clock_difference = sum_of_clock_difference \
        / len(client_data)

    return average_clock_difference


''' master sync thread function used to generate
	cycles of clock synchronization in the network '''


def synchronizeAllClocks():

    while True:

        # print("New synchronization cycle started.")
        # print("Number of clients to be synchronized: " +
        #       str(len(client_data)))

        if len(client_data) > 0:

            average_clock_difference = getAverageClockDiff()

            for client_addr, client in client_data.items():
                try:
                    synchronized_time = \
                        datetime.datetime.now() + \
                        average_clock_difference

                    data = {
                        'type': 'time',
                        'time': str(synchronized_time)
                    }
                    payload = json.dumps(data)

                    client['connector'].send(payload.encode())
                    # client['connector'].send(str(
                    #     synchronized_time).encode())

                except Exception as e:
                    print(e)
                    print("Something went wrong while " +
                          "sending synchronized time " +
                          "through " + str(client_addr))

        else:
            print("No client data." +
                  " Synchronization not applicable.")

            print("\n")

        time.sleep(5)


def print_messages(data):
    print('data=', data)
    if data['type'] == 'connect':
        name = data['name']
        print(f"{name} connected")
        for client_addr, client in client_data.items():
            payload = {
                'type': 'connect',
                'name': name,
                'clientCount': len(client_data)
            }
            data = json.dumps(payload)
            client['connector'].send(data.encode())
    elif data.get('type') == 'message':
        _name = data['name']
        message = data['message']

        # print(f"{_name}: {message}")
        payload = {
            'type': 'message',
            'message': message,
            'name': _name
        }
        print(payload)
        for client_addr, client in client_data.items():
            data = json.dumps(payload)
            client['connector'].send(data.encode())


# function used to initiate the Clock Server / Master Node

def receiveData(connector, slave_address):
    while True:
        data = connector.recv(1024).decode()
        data = json.loads(data.encode().decode())
        if data['type'] == 'time':
            startReceivingClockTime(connector, slave_address, data)
        elif data['type'] == 'broadcast_request' or data['type'] == 'token_release':

            for client_addr, client in client_data.items():
                payload = json.dumps(data)
                client['connector'].send(payload.encode())

        else:
            print_messages(data)


def initiateClockServer(port=8080):

    master_server = socket.socket()
    master_server.setsockopt(socket.SOL_SOCKET,
                             socket.SO_REUSEADDR, 1)

    print("Socket at master node created successfully\n")

    master_server.bind(('', port))

    # Start listening to requests
    master_server.listen(10)
    print("Clock server started...\n")

    # start making connections
    print("Starting to make connections...\n")
    master_thread = threading.Thread(
        target=startConnecting,
        args=(master_server, ))
    master_thread.start()

    # start synchronization
    print("Starting synchronization parallelly...\n")
    sync_thread = threading.Thread(
        target=synchronizeAllClocks,
        args=())
    sync_thread.daemon = True
    sync_thread.start()

    # receive_messages = threading.Thread(
    #     target=receiveData,
    #     args=(master_server,))
    # receive_messages.start()


master_q = [dict({"t": "init"})]
master = 2
killedThreads = []
activeThreads = []


def killServerThread(c):
    global killedThreads, activeThreads
    time.sleep(2)
    if len(killedThreads) == 5:
        print("Only One server left")
        return
    killedThreads.append(master)
    activeThreads = []
    master_q.append({
        "t": "kill_thread",
        "id": master
    })
    time.sleep(10)
    killServerThread(c)


def serverThread(id, c):
    isDead = False
    selfLock = threading.Lock()
    while not isDead:
        selfLock.acquire()
        data = master_q[-1]
        selfLock.release()

        if data['t'] == 'init':
            time.sleep(1)
            continue

        if data['t'] == 'kill_thread' and data['id'] == id:
            print("Killed", id)
            isDead = True
            selfLock.acquire()
            selfLock.release()
            chosen = id
            while chosen in killedThreads:
                chosen = random.randint(1, 6)
            print(f"\nServer {id} has gone down")
            print(f"Server {chosen} has detected the failure")
            master_q.append({
                "t": 'polling',
                "initiator": chosen
            })
            print(
                f"Server {chosen} has started election algorithm with the servers greater than itself")
            break

        if data['t'] == 'polling' and data['initiator'] <= id:
            global master
            if not id in activeThreads:
                selfLock.acquire()
                activeThreads.append(id)
                selfLock.release()
                if data['initiator'] == id:
                    time.sleep(3)
                    print("Response recieved from = ", activeThreads)
                    newMasterThread = max(activeThreads)
                    selfLock.acquire()
                    if newMasterThread == id:
                        print(
                            f"Server {id} became the master as it received no response from other servers\n")
                    master_q.append({
                        "t": "new_master",
                        "chosen": newMasterThread,
                    })
                    print(f"{newMasterThread} is the new master\n")
                    master = newMasterThread
                    selfLock.release()
                    time.sleep(1)
                    selfLock.acquire()
                    master_q.append({
                        "t": 'init'
                    })
                    selfLock.release()

        time.sleep(1)


def initServer():
    print("")
    c = threading.Condition()
    for i in range(1, 7):
        server_thread = threading.Thread(
            target=serverThread,
            args=(i, c,))
        server_thread.start()
        print(f'Server {i} started')
    time.sleep(2)
    killer_thread = threading.Thread(
        target=killServerThread,
        args=(c,))
    killer_thread.start()


# Driver function
if __name__ == '__main__':

    # Trigger the Clock Server
    # initServer()
    chatFile = open("chat.txt", "w")
    initiateClockServer(port=8080)
