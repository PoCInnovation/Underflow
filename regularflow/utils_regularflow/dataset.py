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
        self.stateClass = state
        self.toolbox = toolbox
        self.state = []
        self.action = []
        self.reward = []
        self.nextState = []
        self.index = 0

    def _influencerDataProcess(self, jsonData: dict, otherAgents: list, forbidenAgents: list, eps: float) :
        self.communication._updateEnv(jsonData, otherAgents, self.stateClass, forbidenAgents)
        if len(self.nextState) == (len(self.state) - 1) :
            tmpNextState = self.stateClass._getState()
            self.nextState.append(tmpNextState)
        tmpState = self.stateClass._getState() #STATE GLOBAL
        tmpAction = self.toolbox._take_action(eps, self.stateClass)
        if (np.array_equal(self.stateClass.saveLight, self.stateClass.light) == False) :
            self.communication._broadcastReverse(forbidenAgents, self.stateClass) #SENDTOFORBIDEN TAKE INVERSE ACTION (TO INVERSE)
        
        if (np.array_equal(self.stateClass.saveCars, self.stateClass.nCars) == False or np.array_equal(self.stateClass.savePedestrian, self.stateClass.nPedestrian) == False) :
            tmpReward = self.stateClass._getGlobalScore() #update save
            self.communication._broadcastMyState(otherAgents, self.stateClass, forbidenAgents) #SEND TO ALL MY OTHER AGENT MY STATE (TO EXTERN)
        else:
            tmpReward = self.stateClass._getGlobalScore()
        self.stateClass._setSave([self.stateClass._getnCars()], [self.stateClass._getnPedestrian()], list(self.stateClass._getLight()))
        self.action.append(tmpAction)
        if len(self.reward) == (len(self.state) - 1):
            self.reward.append(tmpReward)
        self.state.append(tmpState)
        if len(self.state) == 33 and len(self.nextState) == 32: #101 100
            if eps < 0.2:
                return
            state = self.state[0:-1]
            action = self.action[0:-1]
            self._train(np.array(state), np.expand_dims(self.reward, 1), np.array(self.nextState), np.array(action), self.toolbox)
            self.state.clear()
            self.action.clear()
            self.reward.clear()
            self.nextState.clear()
            self.index += 1
            if (self.index >= 10):
                if eps > 0.2:
                    eps = float(eps - 0.1)
                if eps <= 0.2:
                    eps = float(0.9)
                self.index = 0
        return eps       
                
    def _train(self, states, rewards, next_states, actions, toolbox) :
        qtarget: list = toolbox._qtarget(rewards, 0.9, next_states)
        toolbox.qfunction.model.fit(states, qtarget * actions, epochs=2)
            #print("state", states)
            #print("nextState", next_states)
            #print("action", actions)
            #print("reward", rewards)