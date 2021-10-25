#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 15:27:37 2021
Proyecto de Integracion: Virtual Piano Keyboard

Fuentes:
    OpenCV
    https://opencv.org/

    Clayton Darwin
    https://www.youtube.com/watch?v=sW4CVI51jDY

    Nicolai Høirup Nielsen  (The Coding Lib)
    https://github.com/niconielsen32/ComputerVision/tree/master/StereoVisionDepthEstimation
    https://www.youtube.com/watch?v=t3LOey68Xpg -


    Kaustubh Sadekar - Satya Mallick
    https://learnopencv.com/making-a-low-cost-stereo-camera-using-opencv/#steps-to-create-the-stereo-camera-setup

    Fernando Souza
    https://medium.com/vacatronics/3-ways-to-calibrate-your-camera-using-opencv-and-python-395528a51615

    Daniel Lee
    https://erget.wordpress.com/2014/02/28/calibrating-a-stereo-pair-with-python/
    https://erget.wordpress.com/2014/02/01/calibrating-a-stereo-camera-with-opencv/


    LearnTechWithUs
    https://github.com/LearnTechWithUs/Stereo-Vision/issues/10

    Najam R. Syed
    https://nrsyed.com/2018/07/05/multithreading-with-opencv-python-to-improve-video-processing-performance/

    Murtaza's Workshop - Robotics and AI
    https://www.youtube.com/watch?v=NZde8Xt78Iw

    Google -Mediapipe
    https://ai.googleblog.com/2019/08/on-device-real-time-hand-tracking-with.html


    Nathan Whitehead
    https://github.com/nwhitehead/pyfluidsynth

    y otros

    Referencias:
    Python
    https://www.python.org/dev/peps/pep-0008/#package-and-module-names


# TODOES:
# TODO1: Crear una cola (queue) para estabilizar con un promedio la posición xy de los dedos
# TODO2: Calcular distancia angular para detectar cuando un dedo está bajo el umbral para tocar la tecla virtual
# TODO3: Incluir todos los dedos al mapa de XY + Depth
# TODO4: Mejorar performance, primera opcion GPU, y optimización

@author: mherrera
"""

import time
import traceback
import cv2

import video_thread as video_thread
#import calibration as calibration
import angles as angles

import handdetector
from toolbox import round_half_up
import virtual_keyboard as vkb
import keyboard_mapper as kbm
import numpy as np
import fluidsynth
import math

def frame_add_crosshairs(frame,
                         x,
                         y,
                         r=20,
                         lc=(0, 0, 255),
                         cc=(0, 0, 255),
                         lw=2,
                         cw=1):

    x = int(round(x, 0))
    y = int(round(y, 0))
    r = int(round(r, 0))

    cv2.line(frame, (x, y-r*2), (x, y+r*2), lc, lw)
    cv2.line(frame, (x-r*2, y), (x+r*2, y), lc, lw)

    cv2.circle(frame, (x, y), r, cc, cw)


def main():

    try:

        # ------------------------------
        # set up cameras
        # ------------------------------

        # cameras variables
        left_camera_source = 2   # Left Camera in Camrea Point of View (PoV)
        right_camera_source = 0  # Right Camera in Camrea Point of View (PoV)
        pixel_width = 640
        pixel_height = 480

        # Logi C920s HD Pro Webcam
        camera_hFoV = 70.42  # Horizontal Field of View
        camera_vFoV = 43.3   # Vertical Field of View
        hFoV_angle_rectification = 21.42 # Field of View (FoV) rectifcation
        vFoV_angle_rectification = \
            camera_vFoV * hFoV_angle_rectification/camera_hFoV

        angle_width = camera_hFoV - hFoV_angle_rectification
        angle_height = camera_vFoV - vFoV_angle_rectification

        # FPS
        frame_rate = 30
        camera_separation = 14.21 # cms

        camera_in_front_of_you = True

        # TODO: Better if is calculated in te setup with a image in the 
        # virtual center of the stereo image
        
        # Virtual Keyboard Center point distance (cms)
        vkb_center_point_camera_dist = 71 # 66.8

            # cam_resource = video_thread.VideoThread(
            #     video_source=c_id,
            #     video_width=pixel_width,
            #     video_height=pixel_height,
            #     video_frame_rate=frame_rate,
            #     buffer_all=False,
            #     try_to_reconnect=False
            # )
        # left camera 1
        cam_left = video_thread.VideoThread(
            video_source=left_camera_source,
            video_width=pixel_width,
            video_height=pixel_height,
            video_frame_rate=frame_rate,
            buffer_all=False,
            try_to_reconnect=False)

        # right camera 2
        cam_right = video_thread.VideoThread(
            video_source=right_camera_source,
            video_width=pixel_width,
            video_height=pixel_height,
            video_frame_rate=frame_rate,
            buffer_all=False,
            try_to_reconnect=False)

        # start cameras
        cam_left.start()
        cam_right.start()

        time.sleep(1)
        if camera_in_front_of_you:
            main_window_name = 'In fron of you: rigth+left cam'
        else:
            main_window_name = 'Same Point of View: left+rigth cam'

        cv2.namedWindow(main_window_name)
        cv2.moveWindow(main_window_name,
                       (pixel_width//2),
                       (pixel_height//2))        
        
        if cam_left.is_available():
            print('Name:{}'.format(main_window_name))
            print('cam_left.resource.get(cv2.CAP_PROP_AUTO_EXPOSURE:{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_AUTO_EXPOSURE)))
            print('cam_left.resource.get(cv2.CAP_PROP_EXPOSURE:{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_EXPOSURE)))
            print('cam_left.resource.get(cv2.CAP_PROP_AUTOFOCUS):{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_AUTOFOCUS)))
            print('cam_left.resource.get(cv2.CAP_PROP_BUFFERSIZE):{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_BUFFERSIZE)))
            print('cam_left.resource.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT):{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT)))

            print('cam_left.resource.get(cv2.CAP_PROP_HW_DEVICE):{}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_HW_DEVICE)))
            print('cam_left.resource.get(cv2.CAP_PROP_FRAME_COUNT):{:03f}'.
                  format(cam_left.resource.get(cv2.CAP_PROP_FRAME_COUNT)))
                

        if cam_right.is_available():
            print('Name:{}'.format(main_window_name))
            print('cam_right.resource.get(cv2.CAP_PROP_AUTO_EXPOSURE:{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_AUTO_EXPOSURE)))
            print('cam_right.resource.get(cv2.CAP_PROP_EXPOSURE:{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_EXPOSURE)))
            print('cam_right.resource.get(cv2.CAP_PROP_AUTOFOCUS):{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_AUTOFOCUS)))
            print('cam_right.resource.get(cv2.CAP_PROP_BUFFERSIZE):{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_BUFFERSIZE)))
            print('cam_right.resource.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT):{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_CODEC_PIXEL_FORMAT)))

            print('cam_right.resource.get(cv2.CAP_PROP_HW_DEVICE):{}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_HW_DEVICE)))
            print('cam_right.resource.get(cv2.CAP_PROP_FRAME_COUNT):{:03f}'.
                  format(cam_right.resource.get(cv2.CAP_PROP_FRAME_COUNT)))


        # left_window_name = 'frame left'
        # cv2.namedWindow(left_window_name)
        # cv2.moveWindow(left_window_name,
        #                (pixel_width//2),
        #                (pixel_height//2))

        # right_window_name = 'frame right'
        # cv2.namedWindow(right_window_name)
        # cv2.moveWindow(right_window_name,
        #                (pixel_width//2)+640,
        #                (pixel_height//2))



        # ------------------------------
        # set up virtual keyboards
        # ------------------------------

        N_BANK = 3
        N_MAYOR_NOTES_X_BANK = 7

        # KEYBOARD_WHIITE_N_KEYS + 1 agrega el ultimo DO
        KEYBOARD_WHIITE_N_KEYS = N_BANK*N_MAYOR_NOTES_X_BANK + 1

        KEYBOARD_TOT_KEYS = KEYBOARD_WHIITE_N_KEYS + N_BANK * 5
        print('KEYBOARD_TOT_KEYS:{}'.format(KEYBOARD_TOT_KEYS))
        octave_base = 0

        vk_left = vkb.VirtualKeyboard(pixel_width, pixel_height,
                                      KEYBOARD_WHIITE_N_KEYS)
        vk_right = vkb.VirtualKeyboard(pixel_width, pixel_height,
                                      KEYBOARD_WHIITE_N_KEYS)


        # ------------------------------
        # set up keyboards map
        # -----------------------------
        km = kbm.KeyboardMap()

        # ------------------------------
        # set up angles
        # ------------------------------
        # cameras are the same, so only 1 needed
        angler = angles.Frame_Angles(pixel_width, pixel_height, angle_width,
                                     angle_height)
        angler.build_frame()

        left_detector = handdetector.HandDetector(staticImageMode=False,
                                                  detectionCon=0.75,
                                                  trackCon=0.5)
        right_detector = handdetector.HandDetector(staticImageMode=False,
                                                   detectionCon=0.75,
                                                   trackCon=0.5)

        # ------------------------------
        # set up synth
        # ------------------------------

        fs = fluidsynth.Synth()
        fs.start(driver='alsa') # Linux
        # sfid = fs.sfload("/home/mherrera/Proyectos/Desa/\
        #                  00400-VirtualPianoKeyboard/0100-lab/example.sf2")
        sfid = fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")

        # 000-000 Yamaha Grand Piano
        fs.program_select(chan=0, sfid=sfid, bank=0, preset=0)

        # # 008-014 Church Bell
        # fs.program_select(chan=0, sfid=sfid, bank=8, preset=14)
        # # 008-026 Hawaiian Guitar
        # fs.program_select(chan=0, sfid=sfid, bank=8, preset=26)
        # # Standard
        # fs.program_select(chan=0, sfid=sfid, bank=128, preset=0)
        # # 000-103 Star Theme
        # fs.program_select(chan=0, sfid=sfid, bank=0, preset=103)

        # ------------------------------
        # stabilize
        # ------------------------------
        time.sleep(0.5)

        # variables
        # ------------------------------

        # length of target queues, positive target frames required
        # to reset set X,Y,Z,D
        queue_len = 3

        # target queues
        #fingers_left_queue, y1k = [], []
        #fingers_right_queue, y2k = [], []
        x_left_finger_screen_pos = 0
        y_left_finger_screen_pos = 0
        

        # mean values to stabilize the coordinates
        # x1m, y1m, x2m, y2m = 0, 0, 0, 0
        # X1_left_hand_ref, Y1_left_hand_ref = 0, 0
        
        # last positive target
        # from camera baseline midpoint
        X, Y, Z, D, = 0, 0, 0, 0
        delta_y = 0

        cycles = 0
        fps = 0
        start = time.time()
        display_dashboard = True
        while True:
            cycles += 1
            # get frames
            finished_left, frame_left = cam_left.next(black=True, wait=0.5)
            finished_right, frame_right = cam_right.next(black=True, wait=0.5)

            # if not finished_left:
            #     cv2.imshow('TEST-l', frame_left)
            # if not finished_right:
            #     cv2.imshow('TEST-r', frame_right)


            # #################################################################
            # # # ---- Cameras Calibration ----
            # frame_left, frame_right = calibration.undistortRectify(
            #       frame_left, frame_right)
            # #################################################################

            frame_left = cv2.flip(frame_left, -1)  # Selfie point of view
            frame_right = cv2.flip(frame_right, -1)  # Selfie point of view

            hands_left_image = fingers_left_image = []
            hands_right_image = fingers_right_image = []

            # Detect Hands
            if left_detector.findHands(frame_left):
                vk_left.draw_virtual_keyboard(frame_left)
                left_detector.drawHands(frame_left)
                left_detector.drawTips(frame_left)
                
                hands_left_image, fingers_left_image = \
                    left_detector.getFingerTipsPos()
            else:
                vk_left.draw_virtual_keyboard(frame_left)

            if right_detector.findHands(frame_right):
                #vk_right.draw_virtual_keyboard(frame_right)
                right_detector.drawHands(frame_right)
                right_detector.drawTips(frame_right)

                hands_right_image, fingers_right_image = \
                    right_detector.getFingerTipsPos()
            # else:
            #     vk_right.draw_virtual_keyboard(frame_right)

            # check 1: motion in both frames:
            if (len(fingers_left_image) > 0 and len(fingers_right_image) > 0):

                fingers_dist = []
                for finger_left, finger_right in \
                    zip(fingers_left_image, fingers_right_image):
                    # print('finger_left:{}'.format(finger_left))
                    # print('finger_right:{}'.format(finger_right))
                    # get angles from camera centers
                    xlangle, ylangle = angler.angles_from_center(
                        x = finger_left[2], y = finger_left[3],
                        top_left=True, degrees=True)
                    xrangle, yrangle = angler.angles_from_center(
                        x = finger_right[2], y = finger_right[3],
                        top_left=True, degrees=True)

                    # triangulate
                    X_local, Y_local, Z_local, D_local = angler.location(
                        camera_separation,
                        (xlangle, ylangle),
                        (xrangle, yrangle),
                        center=True,
                        degrees=True)
                    # angle normalization
                    delta_y = 0.006509695290859 * X_local * X_local + \
                        0.039473684210526 * -1 * X_local # + vkb_center_point_camera_dist
                    fingers_dist.append(D_local-delta_y)
                    # if finger_left[0] == 0 and 
                    if finger_left[0] == 0 and finger_left[1] == left_detector.mpHands.HandLandmark.INDEX_FINGER_TIP:
                        x_left_finger_screen_pos =  finger_left[2]
                        y_left_finger_screen_pos = finger_left[3]
                        X = X_local
                        Y = Y_local
                        Z = Z_local
                        D = D_local
                        

                on_map, off_map = km.get_kayboard_map(
                    virtual_keyboard=vk_left,
                    fingertips_pos=fingers_left_image,
                    fingers_height=fingers_dist,
                    center_point_distance=vkb_center_point_camera_dist-2.5,
                    keyboard_n_key=KEYBOARD_TOT_KEYS)

                if np.any((on_map == True)):
                    for k_pos, on_key in enumerate(on_map):
                        # print('k_pos:{}   on_key:{}'.format(k_pos, on_key))
                        if on_key:
                            # kb.press(keyboard_map[k_pos])
                            fs.noteon(
                                chan=0,
                                key=vk_left.note_from_key(k_pos)+octave_base,
                                vel=127*2//3)

                if np.any((off_map == True)):
                    for k_pos, off_key in enumerate(off_map):
                        # print('k_pos:{}   off_key:{}'.format(k_pos, off_key))
                        if off_key:
                            # kb.release(keyboard_map[k_pos])
                            fs.noteoff(
                                chan=0,
                                key=vk_left.note_from_key(k_pos)+octave_base
                                )

            # display camera centers
            angler.frame_add_crosshairs(frame_left)
            angler.frame_add_crosshairs(frame_right)

            if display_dashboard:
                # Display dashboard data
                fps1 = int(cam_left.current_frame_rate)
                fps2 = int(cam_right.current_frame_rate)
                cps_avg = int(round_half_up(fps))  # Average Cycles per second
                text = 'X: {:3.1f}\nY: {:3.1f}\nZ: {:3.1f}\nD: {:3.1f}\nDr: {:3.1f}\nFPS:{}/{}\nCPS:{}'.format(X, Y, Z, D, D-delta_y, fps1, fps2, cps_avg)
                lineloc = 0
                lineheight = 30
                for t in text.split('\n'):
                    lineloc += lineheight
                    cv2.putText(frame_left,
                                t,
                                (10, lineloc),              # location
                                cv2.FONT_HERSHEY_PLAIN,     # font
                                # cv2.FONT_HERSHEY_SIMPLEX, # font
                                1.5,                        # size
                                (0, 255, 0),                # color
                                2,                          # line width
                                cv2.LINE_AA,
                                False)

            # Display current target
            # if fingers_left_queue:
            #     frame_add_crosshairs(frame_left, x1m, y1m, 24)
            #     frame_add_crosshairs(frame_right, x2m, y2m, 24)

            # if fingers_left_queue:
            #     frame_add_crosshairs(frame_left, x1m, y1m, 24)
            #     frame_add_crosshairs(frame_right, x2m, y2m, 24)
            # if X > 0 and Y > 0:
            frame_add_crosshairs(frame_left, x_left_finger_screen_pos, y_left_finger_screen_pos, 24)
            # Pendiente : ...frame_add_crosshairs(frame_right, x_left_finger_screen_pos, y_left_finger_screen_pos, 24)



            # Display frames

            # cv2.imshow(left_window_name, frame_left)
            # cv2.imshow(right_window_name, frame_right)

            if camera_in_front_of_you:
                h_frames = np.concatenate((frame_right, frame_left), axis=1)
            else:
                h_frames = np.concatenate((frame_left, frame_right), axis=1)

            cv2.imshow(main_window_name, h_frames)



            if (cycles % 10 == 0):
                # End time
                end = time.time()
                # Time elapsed
                seconds = end - start
                # print ("Time taken : {0} seconds".format(seconds))
                # Calculate frames per second
                fps = 10 / seconds
                start = time.time()

            # Detect control keys
            key = cv2.waitKey(1) & 0xFF
            if cv2.getWindowProperty(
                    main_window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
            # elif cv2.getWindowProperty(
            #         right_window_name, cv2.WND_PROP_VISIBLE) < 1:
            #     break
            elif key == ord('q'):
                break
            elif key == ord('d'):
                if display_dashboard:
                    display_dashboard = False
                else:
                    display_dashboard = True
            elif key != 255:
                print('KEY PRESS:', [chr(key)])

    # ------------------------------
    # full error catch
    # ------------------------------
    except Exception:
        print(traceback.format_exc())

    # ------------------------------
    # close all
    # ------------------------------

    # Fluidsynth
    try:
        fs.delete()
    except Exception:
        pass
    # close camera1
    try:
        cam_left.stop()
    except Exception:
        pass

    # close camera2
    try:
        cam_right.stop()
    except Exception:
        pass

    # kill frames
    cv2.destroyAllWindows()

    # done
    print('DONE')


# ------------------------------
# Call to Main
# ------------------------------

if __name__ == '__main__':
    main()
