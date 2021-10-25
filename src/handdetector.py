#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 00:03:20 2021

Se asume que la relación entre lista de manos detectadas y los landmark
tienen una relación de posición. Se detecta que no existe una relación entre
hand.index y el primer campo del landmark (asumido como tip_id).

@author: mherrera
"""

import mediapipe as mp
import cv2


class HandDetector():

    # WRIST = 0
    # THUMB_CMC = 1  # Carpometacarpal Joint (CMC)
    # THUMB_MCP = 2  # Metacarpophalangeal Joint (MP)
    # THUMB_IP = 3   # Interphalangeal Joint (IP)
    # THUMB_TIP = 4  # Finger Tip

    # INDEX_MCP = 5
    # INDEX_PIP = 6
    # INDEX_DIP = 7  # Distal Interphalangeal Joint (DIP)
    # INDEX_TIP = 8

    # MIDDLE_MCP = 9
    # MIDDLE_PIP = 10
    # MIDDLE_DIP = 11
    # MIDDLE_TIP = 12

    # RING_MCP = 13
    # RING_PIP = 14
    # RING_DIP = 15
    # RING_TIP = 16

    # SMALL_MCP = 17
    # SMALL_PIP = 18
    # SMALL_DIP = 19
    # SMALL_TIP = 20

    # fingerTips = {THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, SMALL_TIP}
    __img_width = 640
    __img_height = 480

    def __init__(self, staticImageMode=False, maxHands=2, detectionCon=0.5,
                 trackCon=0.5, img_width=__img_width, img_height=__img_height):

        self.mode = staticImageMode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon)
        self.mpDraw = mp.solutions.drawing_utils

        self.results = []

        self.fingerTips = [self.mpHands.HandLandmark.THUMB_TIP,
                           self.mpHands.HandLandmark.INDEX_FINGER_TIP,
                           self.mpHands.HandLandmark.MIDDLE_FINGER_TIP,
                           self.mpHands.HandLandmark.RING_FINGER_TIP,
                           self.mpHands.HandLandmark.PINKY_TIP
                           ]

    def setImageDims(self, width, height):
        self.__image_width = width
        self.__image_height = height

    def findHands(self, img):

        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        img.flags.writeable = False
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img.flags.writeable = True

        self.results = self.hands.process(imgRGB)

        # print(results.multi_hand_landmark)
        found = False
        if self.results.multi_handedness:
            # print('{}:multi_handedness:\n{}'.format(
            #     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            #     self.results.multi_handedness))
            found = True
        return found

    def drawHands(self, img):
        # if self.results.multi_handedness:
        #     print('multi_handedness:\n{}'.format(
        #         self.results.multi_handedness))

        if self.results.multi_hand_landmarks:
            for handLandmarks in self.results.multi_hand_landmarks:
                self.mpDraw.draw_landmarks(
                    img, handLandmarks, self.mpHands.HAND_CONNECTIONS)
        # return imgRGB

    # # TODO: No es necesario pasar la img, solo por w+h???
    # def getJoints(self, img, handNo=0, draw=False):
    #     lmList = []
    #     if self.results.multi_hand_landmarks:
    #         myHand = self.results.multi_hand_landmarks[handNo]
    #         for id, lm in enumerate(myHand.landmark):
    #             # print(id, lm)
    #             h, w, _ = img.shape
    #             cx, cy = int(lm.x*w), int(lm.y*h)
    #             # print(id, cx, cy)
    #             lmList.append([id, cx, cy])
    #             if draw:
    #                 cv2.circle(img, (cx,cy), 7, (255,0,255), cv2.FILLED)
    #     return lmList

    # def drawJoints(self, img):
    #     if self.results.multi_hand_landmarks:
    #         for handLandmarks in self.results.multi_hand_landmarks:
    #             self.mpDraw.draw_landmarks(
    #                 img, handLandmarks,
    #                 self.mpHands.HAND_CONNECTIONS)

    def drawTips(self, img):
        if self.results.multi_hand_landmarks:
            for id, handLandmarks in enumerate(
                    self.results.multi_hand_landmarks):
                # print('handLandmarks=id:{}'.format(id))
                for indx_tips in self.fingerTips:
                    cx = handLandmarks.landmark[indx_tips].x * \
                        self.__img_width
                    cy = handLandmarks.landmark[indx_tips].y * \
                        self.__img_height
                    cv2.circle(img, (int(cx), int(cy)),
                               7, (255, 0, 0), cv2.FILLED)

                # self.mpHands.HandLandmark.INDEX_FINGER_TIP].x

    # TODO: Obtener la referencia W y H una sola vez sin pasar la img
    def getFingerTipsPos(self):
        fingertips = []
        if self.results.multi_hand_landmarks:
            for hand_id, handLandmarks in enumerate(
                    self.results.multi_hand_landmarks):
                # print('handLandmarks=id:{}'.format(id))
                for indx_tips in self.fingerTips:
                    tip_id = indx_tips
                    cx = handLandmarks.landmark[indx_tips].x * \
                        self.__img_width
                    cy = handLandmarks.landmark[indx_tips].y * \
                        self.__img_height
                    fingertips.append([hand_id, tip_id, cx, cy])

        hands = []
        if self.results.multi_handedness:
            for handedness in self.results.multi_handedness:
                # print('handedness.classification:\nindex: {}\nscore: {}\nlabel: {}'.\
                #       format(
                #           handedness.classification[0].index,
                #           handedness.classification[0].score,
                #           handedness.classification[0].label
                #     )
                # )
                hands.append(handedness.classification[0])

        return [hands, fingertips]

    # TODO: Obtener la referencia W y H una sola vez sin pasar la img
    def getIndexFingerTipPos(self):
        indexTips = []
        if self.results.multi_hand_landmarks:
            for handLandmarks in self.results.multi_hand_landmarks:
                x = handLandmarks.landmark[
                    self.mpHands.HandLandmark.INDEX_FINGER_TIP].x * \
                    self.__img_width
                y = handLandmarks.landmark[
                    self.mpHands.HandLandmark.INDEX_FINGER_TIP].y * \
                    self.__img_height
                z = handLandmarks.landmark[
                    self.mpHands.HandLandmark.INDEX_FINGER_TIP].z * \
                    1  # self.__img_width

                indexTips.append((x, y, z))

        hands = []
        if self.results.multi_handedness:
            for handedness in self.results.multi_handedness:
                # print('handedness.classification:\nindex: {}\nscore: {}\nlabel: {}'.\
                #       format(
                #           handedness.classification[0].index,
                #           handedness.classification[0].score,
                #           handedness.classification[0].label
                #     )
                # )
                hands.append(handedness.classification[0])

        return hands, indexTips
