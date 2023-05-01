#!/usr/bin/python3
import time
import json
import logging
import os

import obd
from obd import OBDStatus
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

from pids import *
import os

mqttBroker = os.environ.get('MQTT_HOST', "localhost")
client = mqtt.Client()


def payload2json(payload):
    return json.dumps(payload)

def newval(r):
    try:
        # COUNTER += 1
        # print("recived mreading")
        #not the best but r is an obd response type so this makes it none
        if str(r) == "None":
            return
        payload = {'value': '{0.magnitude}'.format(r.value), 'name': r.command.name, 'time': r.time, 'units': '{0.units}'.format(r.value) }

        payload = { **payload, **pids[r.command.name] }

        topic = '/obd/{0}'.format(r.command.name)

        # client.reconnect()
        client.publish(topic, payload2json(payload))

        # if COUNTER % 100 == 0:
        #     update_rate = COUNTER - previous_counter
        #     previous_counter = COUNTER
        #     print(update_rate)
        #     if COUNTER == 100_000:
        #         COUNTER = 0
            

    except:
        logging.exception('MQTT publish failed')
        pass
    
    
def connect_obd(port = None):
    connection = obd.Async(port)
    for pid in pids:
        connection.watch(obd.commands[pid], callback=newval) # keep track of the RPM
    print("starting connection")
    connection.start() # start the async update loop
    return connection
    

def main(port):
    connection = connect_obd(port)
    client.connect(mqttBroker)

    while True:

        if connection is None or connection.status() != OBDStatus.CAR_CONNECTED:
            connection = connect_obd(port)
            print(f"waiting for connection")
            time.sleep(5)
            
        time.sleep(5)
        topic = '/obd_status/connection'
        payload = {'status': connection.status(), 'protocol_name': connection.protocol_name()}

        logging.info(topic, payload)

        client.reconnect()
        client.publish(topic, payload2json(payload))

        logging.info(topic, payload)
        topic = '/obd_status/pids'
        payload = list(pids.keys())

        client.reconnect()
        client.publish(topic, payload2json(payload))
        response = connection.query(obd.commands.ELM_VOLTAGE)
        # saftey cut off so that it only send messages when turned on 
        if str(response.value) != "None":
            print(float(str(response.value).split(" ")[0]))
            if float(str(response.value).split(" ")[0]) <= 13:
                print("closing connection")
                connection.close()



if __name__ == '__main__':
    client.connect('localhost')

    # obd.logger.setLevel(obd.logging.disable)
    # obd.logging.disable()
    main(port="/dev/ttyUSB0")
