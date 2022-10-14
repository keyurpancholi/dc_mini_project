
from concurrent.futures import thread
from email import message
from dateutil import parser
import threading
import datetime
import socket
import json
import time


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

        print("New synchronization cycle started.")
        print("Number of clients to be synchronized: " +
              str(len(client_data)))

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

        print("\n\n")

        time.sleep(5)


def print_messages(data):
    if data['type'] == 'connect':
        name = data['name']
        print(f"{name} connected")
    if data['type'] == 'message':
        _name = data['name']
        message = data['message']

        # print(f"{_name}: {message}")
        payload = {
            'type': 'message',
            'message': message,
            'name': _name
        }
        for client_addr, client in client_data.items():
            data = json.dumps(payload)
            client['connector'].send(data.encode())


# function used to initiate the Clock Server / Master Node

def receiveData(connector, slave_address):
    while True:
        data = connector.recv(1024).decode()
        data = json.loads(data)
        if data['type'] == 'time':
            startReceivingClockTime(connector, slave_address, data)
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

    receive_messages = threading.Thread(
        target=receiveData,
        args=(master_server))
    receive_messages.start()


# Driver function
if __name__ == '__main__':

    # Trigger the Clock Server
    initiateClockServer(port=8080)
