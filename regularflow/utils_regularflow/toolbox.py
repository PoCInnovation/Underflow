#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:39:59 2019

@author: slo
"""

import torch
from .qfunction import Qfunction
from torch.optim import RMSprop
from.state import State
import numpy as np
import math as math
from time import process_time
import random

EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 200
STEPS_DONE = 0

__all__ = ["Toolbox"]

class Toolbox() :

    def __init__(self, qfunction: Qfunction):
        self.qfunction: Qfunction = qfunction
        self.optimizer: RMSprop = RMSprop(qfunction.parameters())

    def _qtarget(self, reward, gamma, next_step):
        next_state = self.qfunction(next_step).max(1)[0].unsqueeze(1)
        reward = reward.unsqueeze(1)
        return reward + (gamma * next_state)

    def _one_hot(self, a, num_classes):
        return np.squeeze(np.eye(num_classes)[a.reshape(-1)])

    def _take_action(self, state: State):
        global STEPS_DONE
        sample = random.random()
        eps_threshold = EPS_END + (EPS_START - EPS_END) * math.exp(-1. * STEPS_DONE / EPS_DECAY)
        STEPS_DONE += 1
        if (eps_threshold <= 0.06):
            eps_threshold = EPS_START
            STEPS_DONE = 0
        stateAction = torch.from_numpy(state._getState()).unsqueeze(0).float()
        print(f"Step done : {STEPS_DONE}\nstate : {state._getState()}\n eps : {eps_threshold}\n\n")
        if sample < 0:
            action = np.random.randint(0, 2)
            newLight = list(self._one_hot(np.array(action), 2))
        else:
            print("model")
            with torch.no_grad():
                action = self.qfunction(stateAction).max(1)[1].view(1, 1)
                print(self.qfunction(stateAction))
                newLight = list(self._one_hot(action, 2))
        state._setState(light=newLight)
        if newLight[0] == 0:
            state.clockCars = process_time()
        else:
            state.clockPedestrian = process_time()
        return newLight

    def _progbar(self, curr, total, full_progbar):
        frac = curr / total
        filled_progbar = round(frac * full_progbar)
        print('\r', '#' * filled_progbar + '-' * (full_progbar - filled_progbar), '[{:>7.2%}]'.format(frac), end='')