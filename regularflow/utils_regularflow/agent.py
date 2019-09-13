#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 09:23:52 2019

@author: _Rollo
"""

from time import sleep
import numpy as np
from json import loads
from .constant import INDEXCAR, INDEXPEDESTRIAN, CLOSE

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
            for key in jsonData :
                if key == "from" :
                    if (jsonData[key] == -1):
                        fromWho = -1
                    else : 
                        fromWho = jsonData[key]
        
                if key == "state" :
                    if (jsonData[key][0] == 0) :
                        if np.random.uniform(0, 1) < 1 and jsonData[key][INDEXPEDESTRIAN] > 0 :
                            data = {"from": -1, "cars" : jsonData[key][INDEXCAR] + 1, "pedestrian": jsonData[key][INDEXPEDESTRIAN] - 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                        elif np.random.uniform(0, 1) < 1 and jsonData[key][INDEXPEDESTRIAN] <= 0:
                            data = {"from": -1, "cars" : jsonData[key][INDEXCAR] + 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                        elif jsonData[key][INDEXPEDESTRIAN] > 0 :
                            data = {"from": -1, "pedestrian": jsonData[key][INDEXPEDESTRIAN] - 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                    else :
                        if np.random.uniform(0, 1) < 1 and jsonData[key][INDEXCAR] > 0:
                            data = {"from": -1, "pedestrian" : jsonData[key][INDEXPEDESTRIAN] + 1, "cars": jsonData[key][INDEXCAR] - 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                        elif np.random.uniform(0, 1) < 1 and jsonData[key][INDEXCAR] <= 0: 
                            data = {"from": -1, "pedestrian" : jsonData[key][INDEXPEDESTRIAN] + 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                        elif jsonData[key][INDEXCAR] > 0 :
                            data = {"from": -1, "cars": jsonData[key][INDEXCAR] - 1}
                            self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
            if i > 900 :
                self.communication.consumer.close()
                data = {"from": -1, "close": -1}
                self.communication._sendTo(data, fromWho, self.communication.clusterTopic)
                break
            i += 1

    def _initDataset(self) :
        eps = 1
        state = []
        action = []
        reward = []
        nextState = []
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
            if len(nextState) == (len(state) - 1) :
                tmpNextState = self.state._getState()
                nextState.append(tmpNextState)
            self.communication._updateEnv(jsonData, self.otherAgents, self.state)
            tmpState = self.state._getState() #STATE GLOBAL
            tmpAction = self.toolbox._take_action(eps, self.state)
            if (np.array_equal(self.state.saveLight, self.state.light) == False) :
                self.communication._broadcastReverse(self.forbidenAgents, self.state) #SENDTOFORBIDEN TAKE INVERSE ACTION (TO INVERSE)
            tmpReward = self.state._getGlobalScore()
            if (np.array_equal(self.state.saveCars, self.state.nCars) == False or np.array_equal(self.state.savePedestrian, self.state.nPedestrian) == False) :
                self.communication._broadcastMyState(self.otherAgents, self.state, self.forbidenAgents) #SEND TO ALL MY OTHER AGENT MY STATE (TO EXTERN)
            self.state._setSave([self.state._getnCars()], [self.state._getnPedestrian()], list(self.state._getLight()))
            state.append(tmpState)
            action.append(tmpAction)
            reward.append(tmpReward)
            if len(state) == 4 and len(nextState) == 3:
                state = state[0:-1]
                action = action[0:-1]
                reward = reward[0:-1]
                self.dataset.train(np.array(state), np.expand_dims(reward, 1), np.array(nextState), np.array(action), self.toolbox)
                state.clear()
                action.clear()
                reward.clear()
                nextState.clear()
                if eps > 0.3 :
                    eps -= 0.1                 
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
        