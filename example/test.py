#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 20 10:14:22 2019

@author: slo
"""
from multiprocessing import Process
from regularflow import newAgent, cycleManager

#<------------------------------------ManagerConfig------------------------------------------------------------>
consumerConfigManager1 = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'manager',
                'auto.offset.reset': 'earliest'
                }
producerConfigManager1 = {
                'bootstrap.servers': 'localhost:9092'
                 }

consumerConfigManager0 = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'manager',
                'auto.offset.reset': 'earliest'
                }
producerConfigManager0 = {
                'bootstrap.servers': 'localhost:9092'
                 }

manager1 = newAgent(1, consumerConfigManager1, producerConfigManager1, "cluster0", "manager0", "manager")
manager1._setAgents([1])
cycleManager([manager1], [600])

manager0 = newAgent(0, consumerConfigManager0, producerConfigManager0, "cluster0", "manager0", "manager")
manager0._setAgents([0])
cycleManager([manager0], [600])

#<------------------------------------LightConfig------------------------------------------------------------>
consumerConfigLight0 = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster',
                'auto.offset.reset': 'earliest'
                }
producerConfigLight0 = {
                'bootstrap.servers': 'localhost:9092'
                 }

consumerConfigLight1 = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'cluster0',
                'auto.offset.reset': 'earliest'
                }
producerConfigLight1 = {
                'bootstrap.servers': 'localhost:9092'
                 }

light0 = newAgent(0, consumerConfigLight0, producerConfigLight0,"cluster0", "manager0", "influencer")
light0._setAgents([1])
light0._setForbidenAgents([1])

light1 = newAgent(1, consumerConfigLight1, producerConfigLight1, "cluster0", "manager0", "follower")
light1._setAgents([0])

#<------------------------------------Start------------------------------------------------------------>

if __name__ == '__main__' :
    #pL0 = Process(target=light0._start)
    #pL1 = Process(target=light1._start)
    #pM0 = Process(target=manager0._start)
    pM1 = Process(target=manager1._start)
    #manager0._start()
    #pL0.start()
    #pL1.start()
    #pM0.start()
    pM1.start()
    
    #pL0.join()
    #pL1.join()
    #pM0.join()
    pM1.join()
    
    #light0._save()
    #light1._save()