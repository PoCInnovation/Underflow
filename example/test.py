#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 10:14:22 2019

@author: slo
"""
import multiprocessing as mp
from regularflow import newAgent, cycleManager, startAgent

consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster0',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent1 = newAgent(1, consumerConfig, producerConfig, "cluster0", "manager0", "follower")
agent1._setAgents([0, 2, 3])

agent0 = newAgent(0, consumerConfig, producerConfig,"cluster0", "manager0", "influencer")
agent0._setAgents([1, 2, 3])
agent0._setForbidenAgents([1])

agent2 = newAgent(2, consumerConfig, producerConfig,"cluster0", "manager0", "influencer")
agent2._setAgents([0, 1, 3])
agent2._setForbidenAgents([3])

agent3 = newAgent(3, consumerConfig, producerConfig, "cluster0", "manager0", "follower")
agent3._setAgents([0, 1, 2])

#<------------------------------------Start------------------------------------------------------------>

if __name__ == '__main__':
    pool = mp.Pool(mp.cpu_count())

    pool.apply_async(startAgent(agent0))
    pool.apply_async(startAgent(agent1))
    pool.apply_async(startAgent(agent2))
    pool.apply_async(startAgent(agent3))
    pool.join()
    #pool.apply_async(light1._start)
    pool.close()