#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 11:34:42 2019

@author: slo
"""

from regularflow import newAgent, startDemo, startAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster0',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent = newAgent(3, consumerConfig, producerConfig, "cluster0", "manager0","display", "follower")
agent._setAgents([0, 1, 2])
startAgent(agent)