#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 14:00:26 2019

@author: slo
"""

from regularflow import newAgent 

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }


agent = newAgent(0, consumerConfig, producerConfig,"cluster0", "manager0", "influencer")
agent._setAgents([1])
agent._setForbidenAgents([1])
agent._start()
agent._save()