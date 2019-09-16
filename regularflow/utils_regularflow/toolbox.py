#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:39:59 2019

@author: slo
"""

import tensorflow as tf
import numpy as np
from time import process_time

__all__ = ["Toolbox"]

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
    
    def _take_action(self, eps: int, state: object):
        if np.random.uniform(0, 1) < eps:
            action = np.random.randint(0, 2)
            newLight = list(self._one_hot(np.array(action), 2))
        else:
            action = self.qfunction(np.expand_dims(state._getState(), 0).astype("float64"))
            newLight = list(self._one_hot(np.argmax(action), 2))
        state._setState(light=newLight)
        if (newLight[0] == 0) :
            state.clockCars = process_time()
        else:
            state.clockPedestrian = process_time()
        return  newLight
    