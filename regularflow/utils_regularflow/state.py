#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:38:43 2019

@author: slo
"""

import numpy as np
from time import process_time

__all__ = ["State"]


class State():

    def __init__(self):
        self.nbOtherAgents = 0
        self.light: list = np.array([1, 0])
        self.nCars: list = np.array([0])
        self.nPedestrian: list = np.array([0])
        self.saveCars: list = np.array([0])
        self.savePedestrian: list = np.array([0])
        self.saveLight: list = np.array([0.,1.])
        self.ownState = np.concatenate((self.light, self.nCars, self.nPedestrian))
        self.otherAgentState: list = np.zeros([self.nbOtherAgents, np.size(self.ownState)])
        self.state = np.concatenate((self.light, self.nCars, self.nPedestrian, self.otherAgentState.flat))
        self.otherAgentScore: list = np.zeros([self.nbOtherAgents, 1])
        self.clockCars = 0
        self.clockPedestrian = 0
        self.score = 0
        
    def _update(self):
        self.light = np.array(self.light)
        self.nCars = np.array(self.nCars)
        self.nPedestrian = np.array(self.nPedestrian)
        self.state = np.concatenate((self.light, self.nCars, self.nPedestrian, self.otherAgentState.flat))
        self.ownState = np.concatenate((self.light, self.nCars, self.nPedestrian))
        
    def _setState(self, light: list = None, nCars: list = None, nPedestrian: list = None):
        self.light = light or self.light
        self.nCars = nCars or self.nCars
        self.nPedestrian = nPedestrian or self.nPedestrian
        self._update()
       
    def _setOtherAgentState(self, index: int, state: list):
        self.otherAgentState[index] = np.array(state)
        self._update()
        
    def _setOtherAgentScore(self, index: int, score: int):
        self.otherAgentScore[index] = score

    def _setSave(self, saveCars: list = None, savePedestrian: list = None, saveLight: list = None):
        self.saveCars = saveCars or self.saveCars
        self.savePedestrian = savePedestrian or self.savePedestrian
        self.saveLight = saveLight or self.saveLight
        self.saveLight = np.array(self.saveLight)
        self.saveCars = np.array(self.saveCars)
        self.savePedestrian = np.array(self.savePedestrian)
    
    def _setNbOtherAgents(self, nb: int):
        self.nbOtherAgents += nb
        self.otherAgentScore: list = np.zeros([self.nbOtherAgents, 1])
        self.otherAgentState: list = np.zeros([self.nbOtherAgents, np.size(self.ownState)])
        self._update()
    
    def _getState(self):
        return np.array(self.state).astype('float64')

    def _getOwnState(self):
        return np.array(self.ownState).astype('float64')

    def _getLight(self):
        return self.light

    def _getnCars(self):
        return self.nCars[0]

    def _getnPedestrian(self):
        return self.nPedestrian[0]

    def _getSaveCars(self):
        return self.saveCars[0]

    def _getSavePedestrian(self):
        return self.savePedestrian[0]

    def _getOtherAgentScore(self):
        return np.sum(self.otherAgentScore)
    
    def _getScore(self):
        actual = self._getnCars() + self._getnPedestrian() 
        ancien = self._getSaveCars() + self._getSavePedestrian()
        if actual < 0:
            return -5
        if ancien < 0:
            ancien = 0
        score = ancien - actual
        if score > 0:
            score += 5
        if self._getnCars() < 5 and self._getnPedestrian() < 5 and score > 0:
            score += 5
        #self._setSave(saveCars=[self._getnCars()])
        #self._setSave(savePedestrian=[self._getnPedestrian()])
        if self.light[0] == 0 and (self._getnCars() > 0):
            score += ((process_time() - self.clockCars) * -1)
        elif self.light[0] == 1 and (self._getnPedestrian() > 0):
            score += ((process_time() - self.clockPedestrian) * -1)
        self.score = float(score)
        return float(score)

    #revoir le system de score si il y a beaucoup de voiture sur l'autre agent il faut passer au rouge pour augmenter son score
    def _getGlobalScore(self):
        globalScore: int = self._getScore()
        globalScore += self._getOtherAgentScore()
        return globalScore