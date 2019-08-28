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

import tensorflow as tf
import numpy as np

BADREWARD = -5
GOODREWARD = 5

class Qfunction(tf.keras.Model) :
    def __init__(self) :
        super(Qfunction, self).__init__(name='Qfunction')
        self.layerOne: object = tf.keras.layers.Dense(5, activation='relu', name='l1')
        self.hidenLayer: object = tf.keras.layers.Dense(25, activation='relu', name='hl')
        self.out: object = tf.keras.layers.Dense(3, activation='linear', name='out')
        
    def call(self, env) :
        layerOne: list = self.layerOne(env)
        hidenLayer: list = self.hidenLayer(layerOne)
        out: list = self.out(hidenLayer)
        return out
    
class Toolbox() :
    
    def __init__(self, qfunction) :
        self.qfunction: object = qfunction
        self.optimizer:object = tf.keras.optimizers.Adam(learning_rate=0.1)
        self.mse = tf.keras.losses.MeanSquaredError(name="Mean Squared Errror")
        self.loss = tf.keras.metrics.Mean(name="Metric loss")
        
    def _qtarget(self, reward, gamma, next_step):
        return reward + (gamma * np.expand_dims(np.max(self.qfunction(next_step), 1), 1))
    
class State() :
    
    def __init__(self, qfunction) :
        self.qfunction: object = qfunction
        self.light = [0,0,1]
        self.nCars = [0]
        self.nPedestrian = [0]
        self.agentState = []
        self.state = self.light + self.nCars + self.nPedestrian + self.agentState
        
    def _update(self):
        self.state = self.light + self.nCars + self.nPedestrian + self.agentState
        
    def _setState(self, light:list=None, nCars:list=None, nPedestrian:list=None, agentState:list=None) :
        self.light = light or self.light
        self.nCars = nCars or self.nCars
        self.nPedestrian = nPedestrian or self.nPedestrian
        self.agentState = agentState or self.agentState
        self._update()
        
    def _getState(self):
        return self.state
    
    def _one_hot(self, a, num_classes):
        return np.squeeze(np.eye(num_classes)[a.reshape(-1)])
    
    def _take_action(self, eps):
        if np.random.uniform(0, 1) < eps:
            action = np.random.randint(0, 3)
            newLight = list(self._one_hot(np.array(action), 3))
        else:
            action = self.qfunction(np.expand_dims(self.state, 0).astype("float64"))
            newLight = list(self._one_hot(np.argmax(action), 3))
        self._setState(light=newLight)
        return  newLight
    
class Dataset() :
    def train(states, rewards, next_states, actions, toolbox) :
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
        self.forbidenAgents:list = []
        self.otherAgents:list = []
        
    def _setAgents(self, agent) :
        self.otherAgents.append(agent)
        
    def _getAgents(self) :
        return self.otherAgents 
    
    def _setForbidenAgents(self, forbidenIds:list) :
        for id_a in forbidenIds :
            for agent in self.otherAgents :
                if id_a == agent.myId:
                    self.forbidenAgents.append(agent.state._getState())
                    
    def _getForbidenAgents(self) :
        return self.forbidenAgents
                    
    def _updateAgentStates(self) :
        agentStates:list = []
        for agent in self.otherAgents :
            agentStates += agent.state._getState()
        self.state._setState(agentState=agentStates)
        
    def _getScore(self) :
        return self.state.nCars[0] + self.state.nPedestrian[0]
        
    def _getGlobalScore(self) :
        globalScore = self._getScore()
        for agent in self.otherAgents :
            if agent.state.light == self.state.light :
                return BADREWARD
            else :
                globalScore += agent._getScore()
        if (globalScore == 0):
            return GOODREWARD
        return 1/globalScore * np.exp(np.size(self.otherAgents))
    
def newAgent(myId:int) :
    qfunction = Qfunction()
    state = State(qfunction)
    toolbox = Toolbox(qfunction)
    dataset = Dataset()
    agent = Agent(dataset, state, toolbox, qfunction, myId)
    return agent
    
agent = newAgent(258905)
agent_two = newAgent(258906)
agent_three = newAgent(258907)
agent._setAgents(agent_two)
agent._setAgents(agent_three)
agent_two.state._setState(light=[1,0,0])
agent_three.state._setState(light=[1,0,0])
agent_three.state._setState(nCars=[5])
agent_two.state._setState(nCars=[5])
agent_two.state._setState(nPedestrian=[5])
agent._updateAgentStates()
agent._setForbidenAgents([258906, 258907])
print(agent._getGlobalScore())
