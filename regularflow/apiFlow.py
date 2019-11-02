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

__all__ = ["newAgent", "cycleManager", "startAgent", "startDemo"]

       
def newAgent(myId:int, consumerConfig: dict, producerConfig: dict, clusterTopic: str, managerTopic: str, displayTopic: str, classType: str) :
    qfunction:object = Qfunction()
    state: object = State()
    toolbox: object = Toolbox(qfunction)
    communication: object = Communication(clusterTopic, managerTopic, displayTopic, classType, myId)
    dataset: object = Dataset(communication, state, toolbox)
    agent: object = Agent(dataset, state, toolbox, qfunction, communication, myId, classType)
    agent.communication._setProducer(producerConfig)
    agent.communication._setConsumer(consumerConfig)
    return agent

def cycleManager(agents: list, nbs: list) :
    for i in range(len(agents)) : 
        agents[i].nbIteration = nbs[i]


def startAgent(agent: object):
    agent._start()

def startDemo(agent: object):
    agent._startDemo()