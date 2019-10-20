#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 11:38:21 2019

@author: slo
"""

from regularflow import newAgent, cycleManager

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'manager',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent = newAgent(2, consumerConfig, producerConfig, "cluster0", "manager0", "manager")
agent._setAgents([2])
cycleManager([agent], [1000])
agent._start()
