# import sys
# import numpy as np
# import time
# import imutils
import cv2

# TODO: Definir como clase y cargar archivo solo una vez

# Camera parameters to undistort and rectify images
cv_file = cv2.FileStorage()
cv_file.open('stereoMap.xml', cv2.FileStorage_READ)

stereoMapL_x = cv_file.getNode('stereoMapL_x').mat()
stereoMapL_y = cv_file.getNode('stereoMapL_y').mat()
stereoMapR_x = cv_file.getNode('stereoMapR_x').mat()
stereoMapR_y = cv_file.getNode('stereoMapR_y').mat()

print('stereoMapL_x:{}\n'.format(stereoMapL_x))


def undistortRectify(frameL, frameR):

    # Undistort and rectify images
    undistortedL = cv2.remap(frameL, stereoMapL_x, stereoMapL_y,
                             cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)
    undistortedR = cv2.remap(frameR, stereoMapR_x, stereoMapR_y,
                             cv2.INTER_LANCZOS4, cv2.BORDER_CONSTANT, 0)

    return undistortedL, undistortedR
