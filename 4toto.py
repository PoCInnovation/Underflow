#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 19:03:44 2019

@author: slo
"""

from confluent_kafka import Producer
from json import dumps
p = Producer({'bootstrap.servers': 'localhost:9092'})

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


some_data_source = [{"from": -1, "cars": 50}]
for data in some_data_source:
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    # Asynchronously produce a message, the delivery report callback
    # will be triggered from poll() above, or flush() below, when the message has
    # been successfully delivered or failed permanently.
    p.produce('cluster0', dumps(data).encode('utf-8'), callback=delivery_report, partition=1)

# Wait for any outstanding messages to be delivered and delivery report
# callbacks to be triggered.
p.flush()

"""for data in some_data_source:
    for d in data: 
        print(d, data[d])"""