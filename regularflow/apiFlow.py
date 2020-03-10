#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Slo alias Slohan SAINTE-CROIX
"""

from .utils_regularflow import (Qfunction,
                                State,
                                Toolbox,
                                Dataset,
                                Communication,
                                Agent,
                                Memory)

__all__ = ["newAgent", "cycleManager", "startAgent", "startDemo"]

       
def newAgent(myId: int, consumerConfig: dict, producerConfig: dict, clusterTopic: str, managerTopic: str, displayTopic: str, classType: str):
    qfunction: Qfunction = Qfunction()
    state: State = State()
    toolbox: Toolbox = Toolbox(qfunction)
    communication: Communication = Communication(clusterTopic, managerTopic, displayTopic, classType, myId)
    memory: Memory = Memory(10000)
    dataset: Dataset = Dataset(communication, state, toolbox, memory)
    agent: Agent = Agent(dataset, state, toolbox, qfunction, communication, myId, classType)
    agent.communication._setProducer(producerConfig)
    agent.communication._setConsumer(consumerConfig)
    print(f"Agent n°{myId} initialized with success !\n\tI'm a {classType}.\n\tHere is my configuration :\n\tpro-{producerConfig}\n\tcons-{consumerConfig}\n")
    return agent

def cycleManager(agents: list, nbs: list) :
    for i in range(len(agents)):
        agents[i].nbIteration = nbs[i]

def startAgent(agent: Agent):
    print(f"Agent n°{agent.myId} ready to start in training mode !\n")
    agent._start()

def startDemo(agent: Agent):
    print(f"Agent n°{agent.myId} ready to start in demo mode !\n")
    agent._startDemo()