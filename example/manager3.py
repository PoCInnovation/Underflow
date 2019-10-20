#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 11:39:35 2019

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

agent = newAgent(3, consumerConfig, producerConfig, "cluster0", "manager0", "manager")
agent._setAgents([3])
cycleManager([agent], [1000])
agent._start()
