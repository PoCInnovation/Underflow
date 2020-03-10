#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 13 10:39:42 2019

@author: slo
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from .constant import SIZELAYERONE


__all__ = ["Qfunction"]

class Qfunction(nn.Module):
    def __init__(self):
        super(Qfunction, self).__init__()
        self.fc1 = nn.Linear(SIZELAYERONE, 128)
        self.fc2 = nn.Linear(128, 64)
        self.out = nn.Linear(64, 2)

    def forward(self, x) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        out = self.out(x)
        return out
