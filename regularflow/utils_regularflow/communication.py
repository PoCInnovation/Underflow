#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from confluent_kafka import Consumer, Producer
from confluent_kafka import TopicPartition
from json import dumps
from time import process_time
from .constant import INDEXCAR, INDEXPEDESTRIAN, CLOSE
import numpy as np

__all__ = ["Communication"]

class Communication() :
    
    def __init__(self, clusterTopic, managerTopic, classType, myId) :
        self.clusterTopic = clusterTopic
        self.managerTopic = managerTopic
        self.classType = classType
        self.myId = myId
        self.consumer = None
        self.producer = None
        
#<-------------------------------------- SENDING -------------------------------------------------------------------------->      
        
    def _checkIfFollower(self, id_: int, forbidenList: list) :
        for follower in forbidenList :
            for key in follower :
                if key == id_:
                    return True
        return False
    
    def _sendTo(self, data: dict, to: int, topic: str) :
        print("envois ", data ,"to ", to)
        self.producer.poll(0)
        self.producer.produce(topic, dumps(data).encode('utf-8'), callback=self._delivery_report, partition=to)
        self.producer.flush()
        
    def _setConsumer(self, config:dict) :
        self.consumer = Consumer(config)
        if (self.classType == "manager") :
            tp = TopicPartition(self.managerTopic , self.myId)
        else:
            tp = TopicPartition(self.clusterTopic , self.myId)
        self.consumer.assign([tp])
    
    def _setProducer(self, config:dict) :
        self.producer = Producer(config)
        
    def _broadcastMyState(self, otherAgents: list, state: object, forbidenList: list) :
        ownState = list(state._getOwnState())
        score = float(state._getScore())
        data = {"from": self.myId, "state" : ownState, "score": score}
        for agent in otherAgents :
            for key in agent :
                if (self._checkIfFollower(key, forbidenList) == False) :
                    self._sendTo(data, key, self.clusterTopic)
                    
    def _broadcastInit(self, otherAgents: list) :
        data = {"from": -1, "cars" : 0, "pedestrian": 0}
        for agent in otherAgents :
            for key in agent :
                    self._sendTo(data, key, self.clusterTopic)       
                    
    def _broadcastReverse(self, forbidenAgents: list, state: object):
        light = list(state._getLight())
        data = {"from" : self.myId, "reverse": light}
        for forbidenAgent in forbidenAgents :
            for key in forbidenAgent :
                self._sendTo(data, key, self.clusterTopic)
                
    def _sendToManager(self, state: object) :
        ownState = list(state._getOwnState()) 
        data = {"from": self.myId, "state" : ownState}   
        self._sendTo(data, self.myId, self.managerTopic)
        
    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
        if err is not None :
            print('Message delivery failed: {}'.format(err))
        else :
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def _killConsume(self, jsonData) : 
        for key in jsonData : 
            if (key == "close"  and jsonData[key] == -1) :
                return CLOSE
            
    def _managementDataSending(self, jsonData: dict) :
        for key in jsonData :
            if key == "from" :
                if (jsonData[key] == -1):
                    fromWho = -1
                else : 
                    fromWho = jsonData[key]
            if key == "state" :
                nbPedestrian = jsonData[key][INDEXPEDESTRIAN]
                nbCars = jsonData[key][INDEXCAR]
                if (nbCars >= 4) :
                    maxCars = np.random.randint(1, 4)
                else : 
                    maxCars = np.random.randint(0, nbCars + 1)
                    if (maxCars == 0 and nbCars > 0) :
                        maxCars = 1
                if (nbPedestrian >= 4) :
                    maxPedestrian = np.random.randint(1, 4)
                else : 
                    maxPedestrian = np.random.randint(0, nbPedestrian + 1)
                    if (maxPedestrian == 0 and nbPedestrian > 0):
                        maxPedestrian = 1
                if (jsonData[key][0] == 0) :
                    if nbPedestrian > 0 :
                        data = {"from": -1, "cars" : nbCars + np.random.randint(0, 4), "pedestrian": nbPedestrian - maxPedestrian}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbPedestrian <= 0:
                        data = {"from": -1, "cars" : nbCars + np.random.randint(0, 4)}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbPedestrian > 0 :
                        data = {"from": -1, "pedestrian": nbPedestrian - maxPedestrian}
                        self._sendTo(data, fromWho, self.clusterTopic)
                else :
                    if nbCars > 0:
                        data = {"from": -1, "pedestrian" : nbPedestrian + np.random.randint(0, 4), "cars": nbCars - maxCars}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbCars <= 0: 
                        data = {"from": -1, "pedestrian" : nbPedestrian + np.random.randint(0, 4)}
                        self._sendTo(data, fromWho, self.clusterTopic)
                    elif nbCars > 0 :
                        data = {"from": -1, "cars": nbCars - maxCars}
                        self._sendTo(data, fromWho, self.clusterTopic) 
                        
                    
        return fromWho    
                        
#<-------------------------------------- LISTENING -------------------------------------------------------------------------->
                
    def _getQueueNumber(self, _id: int, otherAgents: list) :
        for dictData in otherAgents :
            for key in dictData : 
                if key == _id:
                    return dictData[key]        
        
    def _fromOtherAgent(self, key: str, jsonData: dict, fromWho: int, state: object) :
        if key == "state" :
            state._setOtherAgentState(fromWho, jsonData[key])
        if key == "score" :
            state._setOtherAgentScore(fromWho, jsonData[key])
        if key == "reverse" :
            state._setState(light=list(jsonData[key][::-1]))
            if (state.light[0] == 0) :
                state.clockCars = process_time()
            else:
                state.clockPedestrian = process_time()
            
    def _fromExtern(self, key: str, jsonData: dict, state: object) :
        if key == "cars" :
            state._setState(nCars=[jsonData[key]])
        if key == "pedestrian" :
            state._setState(nPedestrian=[jsonData[key]])

    def _updateEnv(self, jsonData: dict, otherAgents: list, state: object) :
        fromWho = -2 
        for key in jsonData :
            if key == "from" :
                if (jsonData[key] == -1):
                    fromWho = -1
                else : 
                    fromWho = self._getQueueNumber(jsonData[key], otherAgents)
            if fromWho == -1 :
                self._fromExtern(key, jsonData, state)
            elif fromWho >= 0 :
                self._fromOtherAgent(key, jsonData, fromWho, state)
        if fromWho == -1 :
            self._sendToManager(state) #send state to manager
        fromWho = -2
        