#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

import tensorflow as tf
import numpy as np

__all__ = ["Dataset"]

class Dataset() :

    def __init__(self, communication: object, state: object, toolbox:object) :
        self.communication = communication
        self.state = state
        self.toolbox = toolbox

    def _influencerDataProcess(self, jsonData: dict, otherAgents: list, forbidenAgents: list) :
        eps = 1
        state = []
        action = []
        reward = []
        nextState = []
        if len(nextState) == (len(state) - 1) :
            tmpNextState = self.state._getState()
            nextState.append(tmpNextState)
        self.communication._updateEnv(jsonData, otherAgents, self.state)
        tmpState = self.state._getState() #STATE GLOBAL
        tmpAction = self.toolbox._take_action(eps, self.state)
        if (np.array_equal(self.state.saveLight, self.state.light) == False) :
            self.communication._broadcastReverse(forbidenAgents, self.state) #SENDTOFORBIDEN TAKE INVERSE ACTION (TO INVERSE)
        tmpReward = self.state._getGlobalScore()
        if (np.array_equal(self.state.saveCars, self.state.nCars) == False or np.array_equal(self.state.savePedestrian, self.state.nPedestrian) == False) :
            self.communication._broadcastMyState(otherAgents, self.state, forbidenAgents) #SEND TO ALL MY OTHER AGENT MY STATE (TO EXTERN)
        self.state._setSave([self.state._getnCars()], [self.state._getnPedestrian()], list(self.state._getLight()))
        state.append(tmpState)
        action.append(tmpAction)
        reward.append(tmpReward)
        if len(state) == 101 and len(nextState) == 100:
            state = state[0:-1]
            action = action[0:-1]
            reward = reward[0:-1]
            self._train(np.array(state), np.expand_dims(reward, 1), np.array(nextState), np.array(action), self.toolbox)
            state.clear()
            action.clear()
            reward.clear()
            nextState.clear()
            if eps > 0.3 :
                eps -= 0.1 
                
    def _train(self, states, rewards, next_states, actions, toolbox) :
        with tf.GradientTape() as Gt :
            prediction:list = toolbox.qfunction(states)
            qtarget:list = toolbox._qtarget(rewards, 0.9, next_states)
            loss = toolbox.mse(qtarget * actions, prediction * actions) 
            gradients:list = Gt.gradient(loss, toolbox.qfunction.trainable_variables)
            toolbox.optimizer.apply_gradients(zip(gradients, toolbox.qfunction.trainable_variables))