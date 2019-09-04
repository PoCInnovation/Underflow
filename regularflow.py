#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 18 17:12:11 2020

@author: _Rollo
"""

# 1 =  colones
# 0 =  ligne
#socre unique + score globale
#score globale = cars + pedestrian des autre agent 
#l'opposé de la fonction logarithme neperien

import time
import tensorflow as tf
import numpy as np
from threading import Thread, RLock

VERROU = RLock()
BADREWARD = -5
GOODREWARD = 5

def threaded(fn):
    def wrapper(*args, **kwargs):
        thread = Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class Qfunction(tf.keras.Model) :
    def __init__(self) :
        super(Qfunction, self).__init__(name='Qfunction')
        self.layerOne: object = tf.keras.layers.Dense(8, activation='relu', name='l1')
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
    
    def __init__(self, qfunction) :
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
        self.qfunction: object = qfunction
        self.light = [1,0]
        self.nCars = [0]
        self.nPedestrian = [0]
        self.saveCars = [0]
        self.savePedestrian = [0]
        self.agentState = []
        self.forbidenAgents:list = []
        self.otherAgents:list = []
        self.state = list(self.light) + list(self.nCars) + list(self.nPedestrian) + list(self.agentState)
        self.ownState = list(self.light) + list(self.nCars) + list(self.nPedestrian)
        
    def _update(self):
        agentStates:list = []
        for agent in self.otherAgents :
            agentStates += list(agent.state._getOwnState())
        self.agentState = list(agentStates)
        agentStates.clear()
        self.state = list(self.light) + list(self.nCars) + list(self.nPedestrian) + list(self.agentState)
        self.ownState = list(self.light) + list(self.nCars) + list(self.nPedestrian)
        
    def _setState(self, light:list=None, nCars:list=None, nPedestrian:list=None, otherAgents:list=None, forbidenAgents:list=None) :
        self.light = light or self.light
        self.nCars = nCars or self.nCars
        self.nPedestrian = nPedestrian or self.nPedestrian
        self.otherAgents = otherAgents or self.otherAgents
        self.forbidenAgents = forbidenAgents or self.forbidenAgents
        self._update()        
    def _setSave(self, saveCars:list=None, savePedestrian:list=None) :
        self.saveCars = saveCars or self.saveCars
        self.savePedestrian = savePedestrian or self.savePedestrian
        
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
    def _getForbidenAgents(self):
        return self.forbidenAgents
    def _getOtherAgents(self) :
        return self.otherAgents
    def _getSaveCars(self) :
        return self.saveCars[0]
    def _getSavePedestrian(self):
        return self.savePedestrian[0]
    
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
    def __init__(self, dataset, state, toolbox, qfunction, myId) :
        self.dataset = dataset
        self.state = state 
        self.toolbox = toolbox
        self.qfunction = qfunction
        self.myId:int = myId
        
    def _setAgents(self, agents:list) :
        newAgents:list = self.state._getOtherAgents()
        for agent in agents :
            newAgents.append(agent)
        self.state._setState(otherAgents=newAgents)      
    
    def _setForbidenAgents(self, forbidenIds:list) :
        forbidenAgents:list = []
        agents:list = self.state._getOtherAgents()
        newForbidenAgents:list = self.state._getForbidenAgents()
        for id_a in forbidenIds :
            for agent in agents :
                if id_a == agent.myId:
                    forbidenAgents.append(agent)
        for forbidenAgent in forbidenAgents :
            newForbidenAgents.append(forbidenAgent)
        self.state._setState(forbidenAgents=newForbidenAgents)
        #self._take_action(1)
                    
    def _getForbidenAgents(self) :
        return self.state._getForbidenAgents
    def _getAgents(self) :
        return self.state._getOtherAgents                
    #def _getStateWithUpdate(self):
     #   self._updateAgentStates()
      #  return self.state._getState()
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
        otherAgents: list = self.state._getOtherAgents()
        for otherAgent in otherAgents :
                globalScore += agent._getScore()
        return globalScore
    
    def _take_action(self, eps):
        #self._updateAgentStates()
        #print(np.shape(self.state.state))
        forbidenAgents: list = self.state._getForbidenAgents()
        if np.random.uniform(0, 1) < eps:
            action = np.random.randint(0, 2)
            newLight = list(self.toolbox._one_hot(np.array(action), 2))
        else:
            action = self.qfunction(np.expand_dims(self.state._getState(), 0).astype("float64"))
            newLight = list(self.toolbox._one_hot(np.argmax(action), 2))
        self.state._setState(light=newLight)
        for forbidenAgent in forbidenAgents :
            forbidenAgent.state._setState(light=list(self.state.light[::-1]))
            #print(forbidenAgent.state._getLight(), "=", self.state._getLight())
        #self._updateAgentStates()
        return  newLight
    
    @threaded
    def _initDataset(self) :
        eps = 1
        state = []
        action = []
        reward = []
        nextState = []
        i = 0
        while( i < 100):
            #print(self.myId)
    
                if np.random.uniform(0, 1) < 0.5 and self.state._getLight() == [0,1] :
                    self.state._setState(nCars=[self.state._getnCars() + 1])
                if np.random.uniform(0, 1) < 0.3 and self.state._getLight() == [1,0] :
                    self.state._setState(nPedestrian=[self.state._getnPedestrian() + 1])
                if self.state._getLight() == [1,0]:
                    if self.state._getnCars() != 0 :
                        self.state._setState(nCars=[self.state._getnCars() - 1])
                if self.state._getLight() == [0,1]:
                    if self.state._getnPedestrian() != 0 :
                        self.state._setState(nPedestrian=[self.state._getnPedestrian() - 1])

                if (np.random.uniform(0, 1) < 1) and len(self.state._getForbidenAgents()) > 0:       
                     tmpState = self.state._getState()
                     tmpAction = self._take_action(eps)
                     tmpReward = self._getGlobalScore()
                     tmpNextState = self.state._getState()
                     state.append(tmpState)
                     action.append(tmpAction)
                     reward.append(tmpReward)
                     nextState.append(tmpNextState)
                     print(self.myId, str(tmpState) , str(tmpAction), str(tmpReward))
                     if i % 5 == 0 and i != 0 :
                         self.dataset.train(np.array(state), np.expand_dims(reward, 1), np.array(nextState), np.array(action), self.toolbox)
                         state.clear()
                         action.clear()
                         reward.clear()
                         nextState.clear()
                         if eps > 0.3 :
                             eps -= 0.1
                i += 1
     
def newAgent(myId:int) :
    qfunction = Qfunction()
    state = State(qfunction)
    toolbox = Toolbox(qfunction)
    dataset = Dataset()
    agent = Agent(dataset, state, toolbox, qfunction, myId)
    return agent


    
agent = newAgent(0)
agent_two = newAgent(1)
agent._setAgents([agent_two])
agent._setForbidenAgents([1])
handle1 = agent._initDataset()
handle2 = agent_two._initDataset()
handle1.join()
handle2.join()




np.array([0,0,0]).astype("float64")