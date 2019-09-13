#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:39:42 2019

@author: slo
"""

import tensorflow as tf
from .constant import SIZELAYERONE

__all__ = ["Qfunction"]

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