#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: _Rollo
"""

from collections import namedtuple
import random
import numpy as np
import torch.nn.functional as F
import torch
from .communication import Communication
from .state import State
from .toolbox import Toolbox

__all__ = ["Dataset"]

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

BATCH_SIZE = 128
GAMMA = 0.999
FIRST = True

class Memory(object):

    def __init__(self, capacity: int):
        self.capacity: int = capacity
        self.memory: list = []
        self.position: int = 0

    def push(self, *args: list):
        """push a transition"""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = Transition(*args)
        self.position = (self.position + 1) % self.capacity

    def batch(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

class Dataset() :

    def __init__(self, communication: Communication, state: State, toolbox: Toolbox, memory: Memory):
        self.communication = communication
        self.stateClass = state
        self.toolbox = toolbox
        self.tState = []
        self.tAction = []
        self.tNext_State = []
        self.tReward = []
        self.memory = memory

    def _resend(self, forbidenAgents: list, otherAgents: list):
        global FIRST
        if (np.array_equal(self.stateClass.saveLight, self.stateClass.light) == False or FIRST == True):
            self.communication._broadcastReverse(forbidenAgents, self.stateClass)  # SENDTOFORBIDEN TAKE INVERSE ACTION (TO INVERSE)

        if (np.array_equal(self.stateClass.saveCars, self.stateClass.nCars) == False or np.array_equal(self.stateClass.savePedestrian, self.stateClass.nPedestrian) == False or FIRST == True):
            #reward = self.stateClass._getGlobalScore()  # update save
            self.communication._broadcastMyState(otherAgents, self.stateClass, forbidenAgents)  # SEND TO ALL MY OTHER AGENT MY STATE (TO EXTERN)
        FIRST = False
        #else:
            #reward = self.stateClass._getGlobalScore()
       # return reward

    def _influencerDataProcess(self, jsonData: dict, otherAgents: list, forbidenAgents: list, eps: float):
        self.communication._updateEnv(jsonData, otherAgents, self.stateClass, forbidenAgents)
        if len(self.tState) != 0:
            self.tNext_State = self.stateClass._getState()
            self.tReward =  self.stateClass._getGlobalScore()
            self.memory.push(self.tState, self.tAction, self.tNext_State, self.tReward)
            self.tState = []
            self.tAction = []
            self.tNext_State = []
            self.tReward = []
            self._optimize()
        self.tState = self.stateClass._getState() #STATE GLOBAL
        #self.stateClass._setSave(saveLight=list(self.stateClass._getLight()))
        self.tAction = self.toolbox._take_action(self.stateClass)
        self._resend(forbidenAgents, otherAgents)
        self.communication._checkFromAndSendManager(jsonData, self.stateClass)
        self.stateClass._setSave([self.stateClass._getnCars()], [self.stateClass._getnPedestrian()], list(self.stateClass._getLight()))
        return eps       

    def _optimize(self):
        if len(self.memory) < BATCH_SIZE:
            return
        transitions = self.memory.batch(BATCH_SIZE)
        batch = Transition(*zip(*transitions))
        state = torch.Tensor(batch.state)
        next_state = torch.Tensor(batch.next_state)
        action = torch.Tensor(batch.action).long()
        reward = torch.Tensor(batch.reward).long()
        predictions: list = self.toolbox.qfunction(state)
        prediction = (predictions * action).gather(1, action)[:, 1].view(-1, 1)
        qtarget: list = self.toolbox._qtarget(reward, GAMMA, next_state)
        loss = F.smooth_l1_loss(prediction, qtarget)
        #print(f"state-{state}\naction-{action}\nnext-state-{next_state}\nreward-{reward}-prediction-{prediction}-predic{predictions}-qtarget-{qtarget}")
        print(f"predition : {prediction}\nreward : {reward.sum()}")
        self.toolbox.optimizer.zero_grad()
        loss.backward()
        for param in self.toolbox.qfunction.parameters():
            param.grad.data.clamp_(-1, 1)
        self.toolbox.optimizer.step()
        print(f"loss : {loss}")

    def _train(self, states, rewards, next_states, actions, toolbox):
        rd_states = []
        rd_rewards = []
        rd_next_states = []
        rd_actions = []
        while (len(states) != 0):
            i = np.random.randint(0, len(states))
            rd_states.append(states[i])
            rd_rewards.append(rewards[i])
            rd_next_states.append(next_states[i])
            rd_actions.append(actions[i])
            states = np.delete(states, i, 0)
            rewards = np.delete(rewards, i, 0)
            next_states = np.delete(next_states, i, 0)
            actions = np.delete(actions, i, 0)

        qtarget: list = toolbox._qtarget(np.array(rd_rewards), 0.9, np.array(rd_next_states))
        toolbox.qfunction.model.fit(np.array(rd_states), qtarget * np.array(rd_actions), epochs=2)
            #print("state", states)
            #print("nextState", next_states)
            #print("action", actions)
            #print("reward", rewards)
