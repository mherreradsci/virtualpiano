#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 22:35:46 2021

@author: mherrera
"""

import pygame

class ScreenTools:
    def __init__(self):
        pygame.init()
        self.infos = pygame.display.Info()
    
    def current_widht(self):
        return self.infos.current_w

    def current_height(self):
        return self.infos.current_h

    def screen_size(self):
        return (self.infos.current_w, self.infos.current_h)
