#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 19:06:16 2021
Original:
    https://github.com/LearnTechWithUs/Stereo-Vision/blob/master/README.md
    LearnTechWithUs: Stephane Vujasinovicand Frederic Uhrweiller
@author: mherrera
"""

import os
import time
import cv2

APP_HOME = os.getenv('APP_HOME')

if APP_HOME is None:
    print('set de APP_HOME OS Environment variable')
else:
    print('APP_HOME:[{}]'.format(APP_HOME))

    print('Starting the Calibration. Press and maintain the space bar '
          'to exit the script\n')
    print('Push (s) to save the image you want and push (n) to see next '
          'frame without saving the image')
    print('Push (q) to exit')

    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

    # The left and rigth point of view must be in cameras perpective,
    # like human eyes
    CamL = cv2.VideoCapture(2)
    CamR = cv2.VideoCapture(0)
    time.sleep(0.5)

    id_image = 0
    found_corners = False
    while True:

        retL, frameL = CamL.read()
        retR, frameR = CamR.read()

        if (retL is False or retL is False):
            print("Can't read from input (01)")
            break

        cv2.imshow('imgL', frameL)
        cv2.imshow('imgR', frameR)

        grayR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)
        grayL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)

        # Find the chess board corners
        # Define the number of chess corners (here 9 by 6) we are
        # looking for with the right Camera
        retL, cornersL = cv2.findChessboardCorners(grayL, (9, 6), None)
        retR, cornersR = cv2.findChessboardCorners(
            grayR, (9, 6), None)  # Same with the left camera

        # If found, add object points, image points (after refining them)
        if (retL is True and retR is True):
            corners2R = cv2.cornerSubPix(
                grayR, cornersR, (11, 11), (-1, -1),
                criteria)  # Refining the Position
            corners2L = cv2.cornerSubPix(
                grayL, cornersL, (11, 11), (-1, -1),
                criteria)

            # Draw and display the corners
            cv2.drawChessboardCorners(grayR, (9, 6), corners2R, retR)
            cv2.drawChessboardCorners(grayL, (9, 6), corners2L, retL)
            cv2.imshow('VideoR', grayR)
            cv2.imshow('VideoL', grayL)

            # Push "s" to save the images and "n" if you don't want to
            key = cv2.waitKey(0) & 0xFF
            if key == ord('s'):
                # str_id_image= str(id_image)
                id_image += 1

                target_left_filename = os.path.join(
                    APP_HOME,
                    './images/stereoR/img-{:04d}.png'.format(id_image))

                print('target_left_filename: [{}]'.
                      format(target_left_filename))

                target_right_filename = os.path.join(
                    APP_HOME,
                    './images/stereoL/img-{:04d}.png'.format(id_image))

                print('Images {:04d} saved on \n{}'.format(
                    id_image, os.path.join(APP_HOME, 'images')))
                cv2.imwrite(target_left_filename,  frameL)
                cv2.imwrite(target_right_filename,  frameR)
            else:
                print('Images not saved, last saved:{}'.format(id_image))
        else:
            print("Can't find corners")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the Cameras
    CamR.release()
    CamL.release()
    cv2.destroyAllWindows()
