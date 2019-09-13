#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 09:23:52 2019

@author: _Rollo
"""

from .utils_regularflow import (Qfunction,
                                State,
                                Toolbox,
                                Dataset,
                                Communication,
                                Agent)

__all__ = ["newAgent"]
       
def newAgent(myId:int, consumerConfig: dict, producerConfig: dict, clusterTopic: str, managerTopic: str, classType: str) :
    qfunction:object = Qfunction()
    state: object = State()
    toolbox: object = Toolbox(qfunction)
    dataset: object = Dataset()
    communication: object = Communication(clusterTopic, managerTopic, classType, myId)
    agent: object = Agent(dataset, state, toolbox, qfunction, communication, myId, classType)
    agent.communication._setProducer(producerConfig)
    agent.communication._setConsumer(consumerConfig)
    return agent
