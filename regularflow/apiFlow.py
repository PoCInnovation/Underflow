#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from .utils_regularflow import (Qfunction,
                                State,
                                Toolbox,
                                Dataset,
                                Communication,
                                Agent)

__all__ = ["newAgent", "cycleManager"]
       
def newAgent(myId:int, consumerConfig: dict, producerConfig: dict, clusterTopic: str, managerTopic: str, classType: str) :
    qfunction:object = Qfunction()
    state: object = State()
    toolbox: object = Toolbox(qfunction)
    communication: object = Communication(clusterTopic, managerTopic, classType, myId)
    dataset: object = Dataset(communication, state, toolbox)
    agent: object = Agent(dataset, state, toolbox, qfunction, communication, myId, classType)
    agent.communication._setProducer(producerConfig)
    agent.communication._setConsumer(consumerConfig)
    return agent

def cycleManager(agents: list, nbs: list) :
    for i in range(agents) : 
        agents[i].nbIteration = nbs[i]
        