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
        self.nbIteration: int = 10
        
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

    def _managementCycleLife(self, timeSleep: float) :
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
            #print(jsonData)
            #self.toolbox._progbar(i, self.nbIteration, 30)
            print(i)
            sleep(timeSleep)
            fromWho = self.communication._managementDataSending(jsonData)
            if i > self.nbIteration and self.nbIteration != -1:
                print("KILL INFLUENCER MANAGER")
                self.communication.consumer.close()
                self.communication._killInfluencer(fromWho)
                break
            if (self.communication._killConsume(jsonData) == CLOSE):
                self.communication.consumer.close()
                print("KILL FOLLOWER MANAGER")
                break
            i += 1


    def _managementCycleLifeDemo(self, timeSleep: float) :
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
            #print(jsonData)
            #self.toolbox._progbar(i, self.nbIteration, 30)
            print(i)
            sleep(timeSleep)
            fromWho = self.communication._managementDataSending(jsonData)
            #self.communication._sendToDisplay(jsonData, i, self.nbIteration)
            if i > self.nbIteration and self.nbIteration != -1:
                print("KILL INFLUENCER MANAGER")
                self.communication.consumer.close()
                self.communication._killInfluencer(fromWho)
                self.communication._killDisplay(self.myId)
                break
            if (self.communication._killConsume(jsonData) == CLOSE):
                self.communication.consumer.close()
                self.communication._killDisplay(self.myId)
                print("KILL FOLLOWER MANAGER")
                break
            i += 1

    def _followerCycleLife(self) :
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
            #print(self.state.ownState, self.state.score)
            self.communication._updateEnv(jsonData, self.otherAgents, self.state, self.forbidenAgents)
            if ((np.array_equal(self.state.saveCars, self.state.nCars) == False) or (np.array_equal(self.state.savePedestrian, self.state.nPedestrian) == False)) :
                self.state._getGlobalScore()
                self.communication._broadcastMyState(self.otherAgents, self.state, self.forbidenAgents)
            else:
                self.state._getGlobalScore()
            self.state._setSave([self.state._getnCars()], [self.state._getnPedestrian()], list(self.state._getLight()))
            
    def _initDataset(self, type: str, eps: float = 1.0):
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
                self.communication._killManager(self.forbidenAgents)
                self.communication._killFollower(self.forbidenAgents)
                break
            #print(self.state.ownState, self.state.score, eps)
            if type == "demo":
                self.dataset._influencerDataProcess(jsonData, self.otherAgents, self.forbidenAgents, eps)
            else:
                eps = self.dataset._influencerDataProcess(jsonData, self.otherAgents, self.forbidenAgents, eps)

    def _start(self, timeSleep: float = 1.0) :
        if (self.classType == "influencer"):
            self._initDataset("train", 0.9)
            return
        if (self.classType == "follower"):
            self._followerCycleLife()
            return
        if (self.classType == "manager"):
            self._managementCycleLife(timeSleep)
            return
        print("Error() : Unknow classType : ", self.classType)

    def _startDemo(self, timeSleep: float = 1.0):
        if (self.classType == "influencer"):
            self._initDataset("demo", 0.1)
            return
        if (self.classType == "follower"):
            self._followerCycleLife()
            return
        if (self.classType == "manager"):
            self._managementCycleLifeDemo(timeSleep)
            return

    def _save(self) :
        #self.qfunction.save_weights("./saves/save_" + self.classType + str(self.myId), save_format='tf')
        self.qfunction._saveModel("./saves/save_" + self.classType + str(self.myId))
    
    def _restore(self, path: str):
        self.qfunction._loadModel(path)