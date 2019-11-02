#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:39:42 2019

@author: slo
"""

import tensorflow as tf
from .constant import SIZELAYERONE


__all__ = ["Qfunction"]

class Qfunction() :
    def __init__(self) :
        self.model = tf.keras.models.Sequential([
            tf.keras.layers.InputLayer(input_shape=(SIZELAYERONE), dtype='float64'),
            tf.keras.layers.Dense(128, activation='relu', dtype='float64'),
            tf.keras.layers.Dropout(0.2, dtype='float64'),
            tf.keras.layers.Dense(2, activation='linear', dtype='float64')
        ])
        self.model.compile(optimizer='adam',
                    loss='MSE',
                    metrics=['accuracy'])
    def _saveModel(self, path: str):
        tf.saved_model.save(self.model, path)

    def _loadModel(self, path: str):
        self.model = tf.saved_model.load(path)