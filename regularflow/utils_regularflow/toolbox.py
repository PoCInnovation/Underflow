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

gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus :
    tf.config.experimental.set_memory_growth(gpu, True)
    break

class Toolbox() :
    
    def __init__(self, qfunction) :
        self.qfunction: object = qfunction
        self.optimizer:object = tf.keras.optimizers.Adam(learning_rate=0.1)
        self.mse: object = tf.keras.losses.MeanSquaredError(name="Mean Squared Errror")
        self.loss: object = tf.keras.metrics.Mean(name="Metric loss")
        
    def _qtarget(self, reward, gamma, next_step):
        return reward + (gamma * np.expand_dims(np.max(self.qfunction.model.predict(next_step), 1), 1))
    
    def _one_hot(self, a, num_classes):
        return np.squeeze(np.eye(num_classes)[a.reshape(-1)])
    
    def _take_action(self, eps: int, state: object):
        if np.random.uniform(0, 1) < eps:
            action = np.random.randint(0, 2)
            newLight = list(self._one_hot(np.array(action), 2))
        else:
            if (eps < 0.2) :
                action = self.qfunction.model(np.expand_dims(state._getState(), 0))
            else:
                action = self.qfunction.model.predict(np.expand_dims(state._getState(), 0))
            newLight = list(self._one_hot(np.argmax(action), 2))
        state._setState(light=newLight)
        if (newLight[0] == 0) :
            state.clockCars = process_time()
        else:
            state.clockPedestrian = process_time()
        return  newLight

    def _progbar(self, curr, total, full_progbar):
        frac = curr / total
        filled_progbar = round(frac * full_progbar)
        print('\r', '#' * filled_progbar + '-' * (full_progbar - filled_progbar), '[{:>7.2%}]'.format(frac), end='')