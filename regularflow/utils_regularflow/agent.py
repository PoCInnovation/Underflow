#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from time import sleep
import numpy as np
from json import loads
from .constant import CLOSE, SIZELAYERONE

__all__ = ["Agent"]

class Agent() :
    def __init__(self, dataset: object, state: object, toolbox: object, qfunction: object, communication: object, myId: int, classType: str) :
        self.dataset: object = dataset
        self.state: object = state 
        self.toolbox: object = toolbox
        self.qfunction: object = qfunction
        self.communication: object = communication
        self.myId: int = myId
        self.queue: int = 0
        self.forbidenQueue: int = 0
        self.otherAgents: list = []
        self.forbidenAgents: list = []
        self.classType: str = classType
        self.nbIteration: int = 500
        
    def _setAgents(self, agents:list) :
        newAgents: list = list(self.otherAgents)
        nbOtherAgents: int = 0
        for agentId in agents :
            newAgents.append({agentId:self.queue})
            nbOtherAgents += 1
            self.queue += 1
        self.state._setNbOtherAgents(nbOtherAgents)  
        self.otherAgents = list(newAgents)      
    
    def _setForbidenAgents(self, forbidenIds:list) :
        otherAgents:list = list(self.otherAgents)
        newForbidenAgents:list = list(self.forbidenAgents)
        for _id in forbidenIds :
            for dictData in otherAgents :
                for key in dictData :
                    if key == _id :
                        newForbidenAgents.append({_id : self.forbidenQueue})
                        self.forbidenQueue += 1
        self.forbidenAgents = list(newForbidenAgents)

    def _managementCycleLife(self) :
        sleep(5)
        self.communication._broadcastInit(self.otherAgents)
        i = 0
        while True:
            fromWho = -2
            msg = self.communication.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            jsonData = loads(msg.value().decode('utf-8'))
            print(jsonData)
            sleep(1)
            self.communication._managementDataSending(jsonData)
            if i > self.nbIteration :
                self.communication.consumer.close()
                data = {"from": -1, "close": -1}
                self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                break
            i += 1

    def _followerCycleLife(self) :
        saveState = np.array([0])
        while True:
            msg = self.communication.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            jsonData = loads(msg.value().decode('utf-8'))
            if (self.communication._killConsume(jsonData) == CLOSE):
                self.communication.consumer.close()
                break
            print(jsonData, self.state.state)
            self.communication._updateEnv(jsonData, self.otherAgents, self.state)
            if (np.array_equal(saveState, self.state._getState()) == False) :
                self.communication._broadcastMyState(self.otherAgents, self.state, self.forbidenAgents)
            saveState = self.state._getState()
            
    def _initDataset(self) :
        
        while True:
            msg = self.communication.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            jsonData = loads(msg.value().decode('utf-8'))
            if (self.communication._killConsume(jsonData) == CLOSE):
                self.communication.consumer.close()
                break
            print(jsonData, self.state.state)
            self.dataset._influencerDataProcess(jsonData, self.otherAgents, self.forbidenAgents)

    def _start(self) :
        if (self.classType == "influencer"):
            self._initDataset()
            return
        if (self.classType == "follower"):
            self._followerCycleLife()
            return
        if (self.classType == "manager"):
            self._managementCycleLife()
            return
        print("Error() : Unknow classType : ", self.classType)
        
    def _save(self) :
        self.qfunction.save_weights("./saves/save_" + self.classType + str(self.myId), save_format='tf')
    
    def _retore(self, path: str) :
        self.qfunction(np.zeros([1, SIZELAYERONE]))
        self.qfunction.load_weights(path)