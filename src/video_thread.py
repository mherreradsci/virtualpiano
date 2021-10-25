#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 20:00:06 2021
Idea y código original:
    https://www.youtube.com/watch?v=sW4CVI51jDY
    Clayton Darwin
    https://gitlab.com/duder1966/youtube-projects/-/tree/master/

@author: mherrera
"""
import time
import threading
import queue
import cv2
import numpy as np

# ------------------------------
# Camera Tread
# ------------------------------


class VideoThread:

    def __init__(self,
                 video_source=0,  # device, stream or file
                 video_width=640,
                 video_height=480,
                 video_frame_rate=10,
                 buffer_all=False,
                 video_fourcc=cv2.VideoWriter_fourcc(*"MJPG"),
                 try_to_reconnect=False):

        self.video_source = video_source
        self.video_width = video_width
        self.video_height = video_height
        self.video_frame_rate = video_frame_rate
        self.video_fourcc = video_fourcc

        self.buffer_all = buffer_all
        self.try_to_reconnect = try_to_reconnect



        # ------------------------------
        # System Variables
        # ------------------------------

        # buffer setup
        self.buffer_length = 5

        # control states
        self.frame_grab_run = False
        self.frame_grab_on = False

        # counts and amounts
        self.frame_count = 0
        self.frames_returned = 0
        self.current_frame_rate = 0.0
        self.loop_start_time = 0
        self.last_try_reconnection_time = 0

        # buffer
        if self.buffer_all:
            self.buffer = queue.Queue(self.buffer_length)
        else:
            # last frame only
            self.buffer = queue.Queue(1)
    
        self.finished = False

        # camera setup
        self.video_init_wait_time = 0.5

        self.resource = cv2.VideoCapture(self.video_source)
        self.resource.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_width)
        self.resource.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_height)
        self.resource.set(cv2.CAP_PROP_FPS, self.video_frame_rate)
        self.resource.set(cv2.CAP_PROP_FOURCC, self.video_fourcc)
        time.sleep(self.video_init_wait_time)
    
        if not self.resource.isOpened(): 
            self.resource_available = False
        else:
            self.resource_available = True
            # get the actual cam configuration 
            self.video_width = int(self.resource.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.resource.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.video_frame_rate = self.resource.get(cv2.CAP_PROP_FPS)
            self.video_fourcc = self.resource.get(cv2.CAP_PROP_FOURCC)

        # black frame (filler)
        self.black_frame = np.zeros((
            self.video_height, self.video_width, 3), np.uint8)

    def get_curr_config_fps(self):
        return self.video_frame_rate
    
    def get_curr_config_widht(self):
        return self.video_width
    
    def get_curr_config_height(self):
        return self.video_height
    
    def get_curr_frame_number(self):
        return self.frame_count

    def reconnect(self):
        self.stop()

        self.__init__(
            buffer_all=self.buffer_all,
            video_source=self.video_source,
            video_width=self.video_width,
            video_height=self.video_height,
            video_frame_rate=self.video_frame_rate,
            video_fourcc=self.video_fourcc,
            try_to_reconnect=self.try_to_reconnect
        )        
        
        self.start()
        print('reconnecting...')
        
    def is_available(self):
        return self.resource_available

    def start(self):

        # set run state
        self.frame_grab_run = True

        # start thread
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def stop(self):

        #print('########## stop')

        # set loop kill state
        self.frame_grab_run = False

        # let loop stop
        while self.frame_grab_on:
            time.sleep(0.1)

        # stop camera if not already stopped
        if self.resource:
            try:
                self.resource.release()
            except Exception:
                pass
        self.resource = None
        
        self.resource_available = False
        
        # drop buffer
        self.buffer = None
        # set recconection time
        self.last_try_reconnection_time = 0

    def loop(self):

        # load start frame
        frame = self.black_frame
        if not self.buffer.full():
            self.buffer.put(frame, False)

        # status
        self.frame_grab_on = True
        self.loop_start_time = time.time()

        # frame rate
        local_loop_frame_counter = 0
        local_loop_start_time = time.time()

        while self.resource.grab():
            # external shut down
            if not self.frame_grab_run:
                break

            # true buffered mode (for files, no loss)
            if self.buffer_all:

                # buffer is full, pause and loop
                if self.buffer.full():
                    time.sleep(1/self.video_frame_rate)

                # or load buffer with next frame
                else:
                    grabbed, frame = self.resource.retrieve()
                    # grabbed, frame = self.resource.read()
                    if not grabbed:
                        break

                    self.buffer.put(frame, False)
                    self.frame_count += 1
                    local_loop_frame_counter += 1
            # false buffered mode (for camera, loss allowed)
            else:
                grabbed, frame = self.resource.retrieve()
                # grabbed, frame = self.resource.read()
                if not grabbed:
                    break

                # open a spot in the buffer
                if self.buffer.full():
                    self.buffer.get()

                self.buffer.put(frame, False)
                self.frame_count += 1
                local_loop_frame_counter += 1

            # update frame read rate
            if local_loop_frame_counter >= 10:
                self.current_frame_rate = \
                    round(local_loop_frame_counter/
                          (time.time()-local_loop_start_time), 2)
                local_loop_frame_counter = 0
                local_loop_start_time = time.time()


        # shut down
        self.loop_start_time = 0
        self.frame_grab_on = False
        self.resource_available = False

        
        # self.stop()

    def next(self, black=True, wait=0):

        # black frame default
        if black:
            frame = self.black_frame.copy()
        # no frame default
        else:
            frame = None

        # # can't open camera by index or loss connection or EOF
        # if not self.is_available(): 
        #     print('not available:{}'.format(self.video_source))
        if not self.finished:
            # if self.is_available():
                # print('########## self.buffer.qsize():{}'.format(self.buffer.qsize()))
                # print('########## self.buffer.empty():{}'.format(self.buffer.empty()))
                    
            if self.is_available() or not self.buffer.empty(): 
                try:
                    #print('\t########## self.buffer.qsize():{}'.format(self.buffer.qsize()))
                    frame = self.buffer.get(timeout=wait)
                    self.frames_returned += 1
                except queue.Empty:
                    # print('Queue Empty!')
                    # print(traceback.format_exc())
                    pass
            # elif not self.buffer.empty(): 
            #     print('\t@@@@@@@@@@@@@@@@@ self.is_available() and self.buffer.empty()')
            elif self.try_to_reconnect:
                if self.last_try_reconnection_time == 0: 
                    self.last_try_reconnection_time = time.time()
                else:
                    if time.time() - self.last_try_reconnection_time >= 10.0:
                        self.reconnect()
                        if self.is_available(): 
                            self.last_try_reconnection_time = 0
                        else:
                            self.last_try_reconnection_time = time.time()
            else:
                #print('\t########## STOP: self.buffer.qsize():{}'.format(self.buffer.qsize()))
                self.finished = True
                #self.stop()
    
            #print('\n')

        return self.finished, frame
