#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  *
  * Copyright (c) 2019 _rollo Commit <slohan.stcroix@gmail.com>
  *
"""

# 1 =  colones
# 0 =  ligne
#socre unique + score globale
#score globale = cars + pedestrian des autre agent 
#l'opposé de la fonction logarithme neperien

from time import sleep
import tensorflow as tf
import numpy as np
from threading import Thread, RLock
from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka import TopicPartition
from json import dumps
from json import loads


CLOSE = -99
INDEXCAR = 2 # mandatory
INDEXPEDESTRIAN = 3 # mandatory
SIZESTATE = 4  # optional
NBAGENT = 2 # optional
SIZELAYERONE = NBAGENT * SIZESTATE 
VERROU = RLock()
#UN BROKER PAR ZONE

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class Qfunction(tf.keras.Model) :
    def __init__(self) :
        super(Qfunction, self).__init__(name='Qfunction')
        self.layerOne: object = tf.keras.layers.Dense(SIZELAYERONE, activation='relu', name='l1')
        self.hidenLayer: object = tf.keras.layers.Dense(256, activation='relu', name='hl')
        self.hidenLayerTwo: object = tf.keras.layers.Dense(128, activation='relu', name='hl')
        self.out: object = tf.keras.layers.Dense(2, activation='linear', name='out')
        
    def call(self, env) :
        layerOne: list = self.layerOne(env)
        hidenLayer: list = self.hidenLayer(layerOne)
        hidenLayerTwo: list = self.hidenLayerTwo(hidenLayer)
        out: list = self.out(hidenLayerTwo)
        return out
    
class Toolbox() :
    
    def __init__(self, qfunction, clusterTopic, managerTopic) :
        self.clusterTopic = clusterTopic
        self.managerTopic = managerTopic
        self.qfunction: object = qfunction
        self.optimizer:object = tf.keras.optimizers.Adam(learning_rate=0.1)
        self.mse: object = tf.keras.losses.MeanSquaredError(name="Mean Squared Errror")
        self.loss: object = tf.keras.metrics.Mean(name="Metric loss")
        
    def _qtarget(self, reward, gamma, next_step):
        return reward + (gamma * np.expand_dims(np.max(self.qfunction(next_step), 1), 1))
    
    def _one_hot(self, a, num_classes):
        return np.squeeze(np.eye(num_classes)[a.reshape(-1)])
    
class State() :
    
    def __init__(self, qfunction) :
        self.nbOtherAgents = 0
        self.qfunction: object = qfunction
        self.light: list = np.array([1,0])
        self.nCars: list = np.array([0])
        self.nPedestrian: list = np.array([0])
        self.saveCars: list = np.array([0])
        self.savePedestrian: list = np.array([0])
        self.saveLight: list = np.array([0.,1.])
        self.ownState = np.concatenate((self.light, self.nCars, self.nPedestrian))
        self.otherAgentState: list = np.zeros([self.nbOtherAgents, np.size(self.ownState)])
        self.state = np.concatenate((self.light, self.nCars, self.nPedestrian, self.otherAgentState.flat))
        self.otherAgentScore: list = np.zeros([self.nbOtherAgents, 1])
        
    def _update(self) :
        self.light = np.array(self.light)
        self.nCars = np.array(self.nCars)
        self.nPedestrian = np.array(self.nPedestrian)
        self.state = np.concatenate((self.light, self.nCars, self.nPedestrian, self.otherAgentState.flat))
        self.ownState = np.concatenate((self.light, self.nCars, self.nPedestrian))
        
    def _setState(self, light:list=None, nCars:list=None, nPedestrian:list=None) :
        self.light = light or self.light
        self.nCars = nCars or self.nCars
        self.nPedestrian = nPedestrian or self.nPedestrian
        self._update()
       
    def _setOtherAgentState(self, index: int, state: list) :
        self.otherAgentState[index] = np.array(state)
        self._update()
        
    def _setOtherAgentScore(self, index: int, score: int) :
        self.otherAgentScore[index] = score

    def _setSave(self, saveCars:list=None, savePedestrian:list=None, saveLight:list = None) :
        self.saveCars = saveCars or self.saveCars
        self.savePedestrian = savePedestrian or self.savePedestrian
        self.saveLight = saveLight or self.saveLight
        self.saveLight = np.array(self.saveLight)
        self.saveCars = np.array(self.saveCars)
        self.savePedestrian = np.array(self.savePedestrian)
    
    def _setNbOtherAgents(self, nb:int) :
        self.nbOtherAgents += nb
        self.otherAgentScore: list = np.zeros([self.nbOtherAgents, 1])
        self.otherAgentState: list = np.zeros([self.nbOtherAgents, np.size(self.ownState)])
        self._update()
    
    def _getState(self):
        return np.array(self.state).astype("float64")
    def _getOwnState(self):
        return np.array(self.ownState).astype("float64")
    def _getLight(self) :
        return self.light
    def _getnCars(self) :
        return self.nCars[0]
    def _getnPedestrian(self):
        return self.nPedestrian[0]
    def _getSaveCars(self) :
        return self.saveCars[0]
    def _getSavePedestrian(self):
        return self.savePedestrian[0]
    def _getOtherAgentScore(self) :
        return np.sum(self.otherAgentScore)
    
class Dataset() :

    #regarder si sa optimize bien la loss
    def train(self, states, rewards, next_states, actions, toolbox) :
        with tf.GradientTape() as Gt :
            prediction:list = toolbox.qfunction(states)
            qtarget:list = toolbox._qtarget(rewards, 0.9, next_states)
            loss = toolbox.mse(qtarget * actions, prediction * actions) 
            gradients:list = Gt.gradient(loss, toolbox.qfunction.trainable_variables)
            toolbox.optimizer.apply_gradients(zip(gradients, toolbox.qfunction.trainable_variables))

class Agent() :
    def __init__(self, dataset, state, toolbox, qfunction, myId, classType) :
        self.dataset = dataset
        self.state = state 
        self.toolbox = toolbox
        self.qfunction = qfunction
        self.myId:int = myId
        self.consumer = None
        self.producer = None
        self.queue: int = 0
        self.forbidenQueue: int = 0
        self.otherAgents: list = []
        self.forbidenAgents: list = []
        self.classType = classType
        
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
        
    def _setConsumer(self, config:dict, topic: str) :
        self.consumer = Consumer(config)
        tp = TopicPartition(topic , self.myId)
        self.consumer.assign([tp])
    
    def _setProducer(self, config:dict) :
        self.producer = Producer(config)
        
    def _getQueueNumber(self, _id: int) :
        otherAgents: list = self.otherAgents
        for dictData in otherAgents :
            for key in dictData : 
                if key == _id:
                    return dictData[key]

    def _getScore(self) :
        actual = self.state._getnCars() + self.state._getnPedestrian() 
        ancien = self.state._getSaveCars() + self.state._getSavePedestrian()
        score = ancien - actual
        self.state._setSave(saveCars=[self.state._getnCars()])
        self.state._setSave(savePedestrian=[self.state._getnPedestrian()])
        return score

    #revoir le system de score si il y a beaucoup de voiture sur l'autre agent il faut passer au rouge pour augmenter son score
    def _getGlobalScore(self) :
        globalScore: int = self._getScore()
        globalScore += self.state._getOtherAgentScore()
        return globalScore
    

        
    def _take_action(self, eps):
        if np.random.uniform(0, 1) < eps:
            action = np.random.randint(0, 2)
            newLight = list(self.toolbox._one_hot(np.array(action), 2))
        else:
            action = self.qfunction(np.expand_dims(self.state._getState(), 0).astype("float64"))
            newLight = list(self.toolbox._one_hot(np.argmax(action), 2))
        self.state._setState(light=newLight)
        return  newLight
            
    def _fromOtherAgent(self, key, jsonData, fromWho) :
        if key == "state" :
            self.state._setOtherAgentState(fromWho, jsonData[key])
        if key == "score" :
            self.state._setOtherAgentScore(fromWho, jsonData[key])
        if key == "reverse" :
            self.state._setState(light=list(jsonData[key][::-1]))
            
    def _fromExtern(self, key, jsonData) :
        if key == "cars" :
            self.state._setState(nCars=[jsonData[key]])
        if key == "pedestrian" :
            self.state._setState(nPedestrian=[jsonData[key]])

    def _updateEnv(self, jsonData) :
        fromWho = -2 
        for key in jsonData :
            if key == "from" :
                if (jsonData[key] == -1):
                    fromWho = -1
                else : 
                    fromWho = self._getQueueNumber(jsonData[key])
            if fromWho == -1 :
                self._fromExtern(key, jsonData)
            elif fromWho >= 0 :
                self._fromOtherAgent(key, jsonData, fromWho)
        if fromWho == -1:
            self._sendToManager(self.toolbox.managerTopic) #send state to manager
        fromWho = -2
        
    def _delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
        if err is not None :
            print('Message delivery failed: {}'.format(err))
        else :
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))
            
    def _sendTo(self, data: dict, to: int, topic: str) :
        print("envois ", data ,"to ", to)
        self.producer.poll(0)
        self.producer.produce(topic, dumps(data).encode('utf-8'), callback=self._delivery_report, partition=to)
        self.producer.flush()
        
    def _checkIfFollower(self, id_: int) :
        forbidenList = self.forbidenAgents
        for follower in forbidenList :
            for key in follower :
                if key == id_:
                    return True
        return False
    
    def _broadcastMyState(self, topic: str) :
        ownState = list(self.state._getOwnState())
        score = int(self._getScore())
        data = {"from": self.myId, "state" : ownState, "score": score}
        for agent in self.otherAgents :
            for key in agent :
                if (self._checkIfFollower(key) == False) :
                    self._sendTo(data, key, topic)
                    
    def _broadcastInit(self) :
        data = {"from": -1, "cars" : 0, "pedestrian": 0}
        for agent in self.otherAgents :
            for key in agent :
                    self._sendTo(data, key, self.toolbox.clusterTopic)       
                    
    def _broadcastReverse(self, topic: str):
        light = list(self.state._getLight())
        data = {"from" : self.myId, "reverse": light}
        for forbidenAgent in self.forbidenAgents :
            for key in forbidenAgent :
                self._sendTo(data, key, topic)
                
    def _sendToManager(self, topic: str) :
        ownState = list(self.state._getOwnState()) 
        data = {"from": self.myId, "state" : ownState}   
        self._sendTo(data, self.myId, topic)

    def _followerCycleLife(self) :
        saveState = np.array([0])
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            jsonData = loads(msg.value().decode('utf-8'))
            if (self._killConsume(jsonData) == CLOSE):
                self.consumer.close()
                break
            print(jsonData, self.state.state)
            self._updateEnv(jsonData)
            if (np.array_equal(saveState, self.state._getState()) == False) :
                self._broadcastMyState(self.toolbox.clusterTopic)
            saveState = self.state._getState()
            
    def _killConsume(self, jsonData) : 
        for key in jsonData : 
            if (key == "close"  and jsonData[key] == -1) :
                return CLOSE

    def _managementCycleLife(self) :
        sleep(5)
        self._broadcastInit()
        i = 0
        while True:
            fromWho = -2
            msg = self.consumer.poll(1.0)
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
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                        elif np.random.uniform(0, 1) < 1 and jsonData[key][INDEXPEDESTRIAN] <= 0:
                            data = {"from": -1, "cars" : jsonData[key][INDEXCAR] + 1}
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                        elif jsonData[key][INDEXPEDESTRIAN] > 0 :
                            data = {"from": -1, "pedestrian": jsonData[key][INDEXPEDESTRIAN] - 1}
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                    else :
                        if np.random.uniform(0, 1) < 1 and jsonData[key][INDEXCAR] > 0:
                            data = {"from": -1, "pedestrian" : jsonData[key][INDEXPEDESTRIAN] + 1, "cars": jsonData[key][INDEXCAR] - 1}
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                        elif np.random.uniform(0, 1) < 1 and jsonData[key][INDEXCAR] <= 0: 
                            data = {"from": -1, "pedestrian" : jsonData[key][INDEXPEDESTRIAN] + 1}
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                        elif jsonData[key][INDEXCAR] > 0 :
                            data = {"from": -1, "cars": jsonData[key][INDEXCAR] - 1}
                            self._sendTo(data, fromWho, self.toolbox.clusterTopic)
            if i > 900 :
                self.consumer.close()
                data = {"from": -1, "close": -1}
                self._sendTo(data, fromWho, self.toolbox.clusterTopic)
                break
            i += 1

    def _initDataset(self) :
        eps = 1
        state = []
        action = []
        reward = []
        nextState = []
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error: {}".format(msg.error()))
                continue
            jsonData = loads(msg.value().decode('utf-8'))
            if (self._killConsume(jsonData) == CLOSE):
                self.consumer.close()
                break
            print(jsonData, self.state.state)
            if len(nextState) == (len(state) - 1) :
                tmpNextState = self.state._getState()
                nextState.append(tmpNextState)
            self._updateEnv(jsonData)
            tmpState = self.state._getState() #STATE GLOBAL
            tmpAction = self._take_action(eps)
            if (np.array_equal(self.state.saveLight, self.state.light) == False) :
                self._broadcastReverse(self.toolbox.clusterTopic) #SENDTOFORBIDEN TAKE INVERSE ACTION (TO INVERSE)
            tmpReward = self._getGlobalScore()
            if (np.array_equal(self.state.saveCars, self.state.nCars) == False or np.array_equal(self.state.savePedestrian, self.state.nPedestrian) == False) :
                self._broadcastMyState(self.toolbox.clusterTopic) #SEND TO ALL MY OTHER AGENT MY STATE (TO EXTERN)
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
     
def newAgent(myId:int, consumerConfig: dict, producerConfig: dict, clusterTopic: str, managerTopic: str, classType: str) :
    qfunction = Qfunction()
    state = State(qfunction)
    toolbox = Toolbox(qfunction, clusterTopic, managerTopic)
    dataset = Dataset()
    agent = Agent(dataset, state, toolbox, qfunction, myId, classType)
    if (classType == "manager") :
        agent._setConsumer(consumerConfig, managerTopic)
    else:
        agent._setConsumer(consumerConfig, clusterTopic)
    agent._setProducer(producerConfig)
    return agent


consumerConfig = {
                'bootstrap.servers': 'localhost:9092',
                'group.id': 'manager',
                'auto.offset.reset': 'earliest'
                }
producerConfig = {
                'bootstrap.servers': 'localhost:9092'
                 }

agent = newAgent(0, consumerConfig, producerConfig, "cluster0", "manager0", "manager")
agent._setAgents([0])
agent._start()