#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 00:43:58 2021

@author: mherrera
"""
import numpy as np


class KeyboardMap:
    def __init__(self):
        self.prev_map = np.empty(0, dtype=bool)

    def get_kayboard_map(self,
                         virtual_keyboard,
                         fingertips_pos,
                         fingers_height,
                         center_point_distance,
                         keyboard_n_key):

        curr_map = np.full((keyboard_n_key, 1), False, dtype=bool)
        on_map = np.full((keyboard_n_key, 1), False, dtype=bool)
        off_map = np.full((keyboard_n_key, 1), False, dtype=bool)
        # obtain the current map pressed piano keys
        for fingertip_pos, dist in zip(fingertips_pos, fingers_height):
            # print('fpos: Hand:{} tip:{} x:{} y:{}'.format(
            #     fingertip_pos[0],
            #     fingertip_pos[1],
            #     fingertip_pos[2],
            #     fingertip_pos[3]))

            if virtual_keyboard.intersect((fingertip_pos[2],
                                           fingertip_pos[3])):
                # Aquí deberia hacer un mapa de las teclas presionadas
                key = virtual_keyboard.find_key(fingertip_pos[2],
                                                fingertip_pos[3])
                # print('keyboard_piano:key:{}'.format(key))
                if key >= 0 and key < keyboard_n_key:
                    try:
                        # TODO: devería evaluar para todos los dedos
                        if dist > center_point_distance:
                            curr_map[key] = True
                    except Exception:
                        print('key:{}'.format(key))
                        raise

        if np.all((curr_map == False)) and \
            np.all((self.prev_map == False)):
            # print('all zero')
            None
        else:
            # print('Current Map:{}'.format(np_curr_map))
            # print('Previ   Map:{}'.format(np_prev_map))

            xor_map = np.bitwise_xor(self.prev_map, curr_map)
            # print('--- XOR Map:{}'.format(xor_map))
            # xnor_map = np.bitwise_not(xor_map)
            # print('--- XNOR Map:{}'.format(xnor_map))

            on_map = np.logical_and(xor_map, curr_map)
            off_map = np.logical_and(xor_map, self.prev_map)

            # print('on      Map:{}'.format(on_map))
            # print('off     Map:{}\n'.format(off_map))

            self.prev_map = curr_map
        return on_map, off_map
