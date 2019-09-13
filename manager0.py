#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 13:58:14 2019

@author: slo
"""
from regularflow import newAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'manager',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent = newAgent(0, consumerConfig, producerConfig, "cluster0", "manager0", "manager")
agent._setAgents([0])
agent._start()