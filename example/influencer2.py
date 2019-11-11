#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 11:32:01 2019

@author: Roloman
"""

from regularflow import newAgent, startDemo, startAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }


agent = newAgent(2, consumerConfig, producerConfig,"cluster0", "manager0", "display", "influencer")
agent._setAgents([0, 1, 3])
agent._setForbidenAgents([3])
#agent._restore("/home/roloman/projet-perso/regularflow/example/saves/save_influencer2")
startAgent(agent)
agent._save()