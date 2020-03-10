#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from confluent_kafka import Consumer, Producer
from confluent_kafka import TopicPartition
from .state import State
from json import dumps
from time import process_time
from .constant import INDEXCAR, INDEXPEDESTRIAN, CLOSE, INDEXLIGHT
import numpy as np

__all__ = ["Communication"]

class Communication():

    def __init__(self, clusterTopic: str, managerTopic: str, displayTopic: str, classType: str, myId: int) :
        self.clusterTopic: str = clusterTopic
        self.managerTopic: str = managerTopic
        self.displayTopic: str = displayTopic
        self.classType: str = classType
        self.myId: int = myId
        self.consumer = None
        self.producer = None
        self.checkPass = 0

#<-------------------------------------- SENDING -------------------------------------------------------------------------->

    def _checkIfFollower(self, id_: int, forbidenList: list) -> bool:
        for follower in forbidenList:
            for key in follower:
                if key == id_:
                    return True
        return False

    def _sendTo(self, data: dict, to: int, topic: str):
        #print("envois ", data ,"to ", to)
        self.producer.poll(0)
        self.producer.produce(topic, dumps(data).encode('utf-8'), callback=self._delivery_report, partition=to)
        self.producer.flush()

    def _setConsumer(self, config: dict):
        self.consumer = Consumer(config)
        if self.classType == "manager":
            tp = TopicPartition(self.managerTopic, self.myId)
        else:
            tp = TopicPartition(self.clusterTopic, self.myId)
        self.consumer.assign([tp])

    def _setProducer(self, config: dict):
        self.producer = Producer(config)

    def _broadcastMyState(self, otherAgents: list, state: State, forbidenList: list):
        ownState = list(state._getOwnState())
        data = {"from": self.myId, "state": ownState, "score": state.score}
        for agent in otherAgents:
            for key in agent:
                if not self._checkIfFollower(key, forbidenList):
                    self._sendTo(data, key, self.clusterTopic)

    def _broadcastInit(self, otherAgents: list):
        data = {"from": -1, "cars": 0, "pedestrian": 0}
        for agent in otherAgents:
            for key in agent:
                    self._sendTo(data, key, self.clusterTopic)

    def _broadcastReverse(self, forbidenAgents: list, state: State):
        light = list(state._getLight())
        data = {"from" : self.myId, "reverse": light}
        for forbidenAgent in forbidenAgents:
            for key in forbidenAgent:
                self._sendTo(data, key, self.clusterTopic)

    def _sendToManager(self, state: State):
        ownState = list(state._getOwnState())
        data = {"from": self.myId, "state" : ownState}
        self._sendTo(data, self.myId, self.managerTopic)

    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        #else :
            #print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def _killConsume(self, jsonData):
        for key in jsonData:
            if (key == "close"  and jsonData[key] == -1):
                return CLOSE

    def _killFollower(self, forbidenAgents: list):
        data = {"from": -1, "close": -1}
        for forbidenAgent in forbidenAgents:
            for key in forbidenAgent:
                self._sendTo(data, key, self.clusterTopic)

    def _killManager(self, forbidenAgents: list):
        data = {"from": -1, "close": -1}
        for forbidenAgent in forbidenAgents:
            for key in forbidenAgent:
                self._sendTo(data, key, self.managerTopic)

    def _killInfluencer(self, fromWho):
        data = {"from": -1, "close": -1}
        self._sendTo(data, fromWho, self.clusterTopic)

    def _killDisplay(self, to):
        data = {"from": -1, "close": -1}
        self._sendTo(data, to, self.displayTopic)

    def _resetState(self, fromWho):
        data = {"from": -1, "cars": -1, "pedestrian": -1}
        self._sendTo(data, fromWho, self.clusterTopic)

    def _resetZeros(self, fromWho):
        data = {"from": -1, "cars": 0, "pedestrian": 0}
        self._sendTo(data, fromWho, self.clusterTopic)

    def _managementDataSending(self, jsonData: dict):
        for key in jsonData:
            if key == "from":
                if (jsonData[key] == -1):
                    fromWho = -1
                else :
                    fromWho = jsonData[key]
            if key == "state":
                nbPedestrian = jsonData[key][INDEXPEDESTRIAN]
                nbCars = jsonData[key][INDEXCAR]
                if nbCars >= 60 or nbPedestrian >= 60:
                    self._resetState(fromWho)
                    break
                if nbCars == -1 or nbPedestrian == -1:
                    self._resetZeros(fromWho)
                    break
                if nbCars >= 4:
                    maxCars = np.random.randint(1, 4)
                else:
                    maxCars = np.random.randint(0, nbCars + 1)
                    if (maxCars == 0 and nbCars > 0):
                        maxCars = 1
                if nbPedestrian >= 4:
                    maxPedestrian = np.random.randint(1, 4)
                else:
                    maxPedestrian = np.random.randint(0, nbPedestrian + 1)
                    if maxPedestrian == 0 and nbPedestrian > 0:
                        maxPedestrian = 1
                if jsonData[key][0] == 0:
                    if nbPedestrian > 0:
                        data = {"from": -1, "cars": nbCars + np.random.randint(0, 4), "pedestrian": nbPedestrian - maxPedestrian}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbPedestrian <= 0:
                        data = {"from": -1, "cars" : nbCars + np.random.randint(0, 4)}
                        self._sendTo(data, fromWho, self.clusterTopic)
                else:
                    if nbCars > 0:
                        data = {"from": -1, "pedestrian" : nbPedestrian + np.random.randint(0, 4), "cars": nbCars - maxCars}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbCars <= 0:
                        data = {"from": -1, "pedestrian" : nbPedestrian + np.random.randint(0, 4)}
                        self._sendTo(data, fromWho, self.clusterTopic)


        return fromWho

    def _sendToDisplay(self, jsonData, index, nbIteration):
        for key in jsonData:
            if key == "from":
                if (jsonData[key] == -1):
                    fromWho = -1
                else:
                    fromWho = jsonData[key]
            if key == "state":
                nbPedestrian = jsonData[key][INDEXPEDESTRIAN]
                nbCars = jsonData[key][INDEXCAR]
                light = jsonData[key][INDEXLIGHT]
        data = {"from": fromWho, "light": light, "nbCars": nbCars, "nbPedestrian": nbPedestrian, "index": index, "nbIteration": nbIteration}
        self._sendTo(data, self.myId, self.displayTopic)

#<-------------------------------------- LISTENING -------------------------------------------------------------------------->

    def _getQueueNumber(self, _id: int, otherAgents: list):
        for dictData in otherAgents:
            for key in dictData:
                if key == _id:
                    return dictData[key]

    def _fromOtherAgent(self, key: str, jsonData: dict, fromWho: int, state: State):
        if key == "state":
            state._setOtherAgentState(fromWho, jsonData[key])
        if key == "reverse":
            state._setState(light=list(jsonData[key][::-1]))
            if (state.light[0] == 0):
                state.clockCars = process_time()
            else:
                state.clockPedestrian = process_time()

    def _updateMyFollowerScore(self, jsonData, index: int, forbidenList: list, state: State):
        for key in jsonData:
            if key == "from":
                if jsonData[key] == -1: #manager don't send score
                    return
                else:
                    fromWho = jsonData[key]
            if self._checkIfFollower(fromWho, forbidenList):
                if key == "score":
                    state._setOtherAgentScore(index, jsonData[key])

    def _dump(self, state: State):
        self.checkPass = 0
        light = state._getLight()
        if (light[0] == 1):
            print("Vert -> ", end="")
        else:
            print("Rouge -> ", end="")
        print("Cars:", state._getnCars(), " Pedestrian:", state._getnPedestrian())

    def _fromExtern(self, key: str, jsonData: dict, state: State):
        self.checkPass += 1
        if key == "cars":
            state._setState(nCars=[jsonData[key]])
        if key == "pedestrian":
            state._setState(nPedestrian=[jsonData[key]])
        #if self.checkPass == 3:
            #self._dump(state)

    def _updateEnv(self, jsonData: dict, otherAgents: list, state: State, forbidenList: list):
        fromWho = -2
        for key in jsonData:
            if key == "from":
                if jsonData[key] == -1:
                    fromWho = -1
                else:
                    fromWho = self._getQueueNumber(jsonData[key], otherAgents)
            if fromWho == -1:
                self._fromExtern(key, jsonData, state)
            elif fromWho >= 0:
                self._fromOtherAgent(key, jsonData, fromWho, state)
        #if fromWho == -1:
         #   self._sendToManager(state) #send state to manager
        self._updateMyFollowerScore(jsonData, fromWho, forbidenList, state)
        #print(jsonData," ", state._getLight())
        fromWho = -2

    def _checkFromAndSendManager(self, jsonData, state: State):
        for key in jsonData:
            if key == "from":
                if jsonData[key] == -1:
                    self._sendToManager(state)
