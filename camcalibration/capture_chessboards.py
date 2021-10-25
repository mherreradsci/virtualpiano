#!/bin/python
# Copyright (C) 2014 Daniel Lee <lee.daniel.1986@gmail.com>
#
# This file is part of StereoVision.
#
# StereoVision is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# StereoVision is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with StereoVision.  If not, see <http://www.gnu.org/licenses/>.

"""
Take pictures of a chessboard visible to both cameras in a stereo pair.
"""

from argparse import ArgumentParser
import os

import cv2
#from progressbar import ProgressBar, Bar, Percentage

from tqdm import tqdm



#from stereovision.stereo_cameras import ChessboardFinder
#from stereovision.ui_utils import calibrate_folder, CHESSBOARD_ARGUMENTS
#from stereovision.ui_utils import find_files
import time

class StereoPair(object):

    """
    A stereo pair of cameras.

    This class allows both cameras in a stereo pair to be accessed
    simultaneously. It also allows the user to show single frames or videos
    captured online with the cameras. It should be instantiated with a context
    manager to ensure that the cameras are freed properly after use.
    """

    #: Window names for showing captured frame from each camera
    windows = ["{} camera".format(side) for side in ("Left", "Right")]

    def __init__(self, devices):
        """
        Initialize cameras.

        ``devices`` is an iterable containing the device numbers.
        """

        if devices[0] != devices[1]:
            #: Video captures associated with the ``StereoPair``
            self.captures = [cv2.VideoCapture(device) for device in devices]
        else:
            # Stereo images come from a single device, as single image
            self.captures = [cv2.VideoCapture(devices[0])]
            self.get_frames = self.get_frames_singleimage

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for capture in self.captures:
            capture.release()
        for window in self.windows:
            cv2.destroyWindow(window)

    def get_frames(self):
        """Get current frames from cameras."""
        return [capture.read()[1] for capture in self.captures]

    def get_frames_singleimage(self):
        """
        Get current left and right frames from a single image,
        by splitting the image in half.
        """
        frame = self.captures[0].read()[1]
        height, width, colors = frame.shape
        left_frame = frame[:, :int(width / 2), :]
        right_frame = frame[:, int(width / 2):, :]
        return [left_frame, right_frame]

    def show_frames(self, wait=0):
        """
        Show current frames from cameras.

        ``wait`` is the wait interval in milliseconds before the window closes.
        """
        for window, frame in zip(self.windows, self.get_frames()):
            cv2.imshow(window, frame)
        cv2.waitKey(wait)

    def show_videos(self):
        """Show video from cameras."""
        while True:
            self.show_frames(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
class ChessboardFinder(StereoPair):

    """A ``StereoPair`` that can find chessboards in its images."""

    def get_chessboard(self, columns, rows, show=False):
        """
        Take a picture with a chessboard visible in both captures.

        ``columns`` and ``rows`` should be the number of inside corners in the
        chessboard's columns and rows. ``show`` determines whether the frames
        are shown while the cameras search for a chessboard.
        """
        found_chessboard = [False, False]

        # Placeholder for corners
        found_corners = [None, None]

        while not all(found_chessboard):
            frames = self.get_frames()
            if show:
                self.show_frames(1)

            for i, frame in enumerate(frames):
                # Our operations on the frame come here
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                fm = cv2.Laplacian(gray, cv2.CV_64F).var()
                if fm <= 200:
                    print("Blurred image...")
                else:                
                    for i, frame in enumerate(frames):
                        (found_chessboard[i],
                         found_corners[i]) = cv2.findChessboardCorners(frame, (columns, rows),
                                                          flags=cv2.CALIB_CB_FAST_CHECK)
        return frames, found_corners

def find_files(folder):
    """Discover stereo photos and return them as a pairwise sorted list."""
    files = [i for i in os.listdir(folder) if i.startswith("left")]
    files.sort()
    for i in range(len(files)):
        insert_string = "right{}".format(files[i * 2][4:])
        files.insert(i * 2 + 1, insert_string)
    files = [os.path.join(folder, filename) for filename in files]
    return files


# def calibrate_folder(args):
#     """
#     Calibrate camera based on chessboard images, write results to output folder.

#     All images are read from disk. Chessboard points are found and used to
#     calibrate the stereo pair. Finally, the calibration is written to the folder
#     specified in ``args``.

#     ``args`` needs to contain the following fields:
#         input_files: List of paths to input files
#         rows: Number of rows in chessboard
#         columns: Number of columns in chessboard
#         square_size: Size of chessboard squares in cm
#         output_folder: Folder to write calibration to
#     """
#     height, width = cv2.imread(args.input_files[0]).shape[:2]
#     calibrator = StereoCalibrator(args.rows, args.columns, args.square_size,
#                                   (width, height))
#     progress = ProgressBar(maxval=len(args.input_files),
#                           widgets=[Bar("=", "[", "]"),
#                           " ", Percentage()])
#     print("Reading input files...")
#     progress.start()
#     while args.input_files:
#         left, right = args.input_files[:2]
#         img_left, im_right = cv2.imread(left), cv2.imread(right)
#         calibrator.add_corners((img_left, im_right),
#                                show_results=args.show_chessboards)
#         args.input_files = args.input_files[2:]
#         progress.update(progress.maxval - len(args.input_files))

#     progress.finish()
#     print("Calibrating cameras. This can take a while.")
#     calibration = calibrator.calibrate_cameras()
#     avg_error = calibrator.check_calibration(calibration)
#     print("The average error between chessboard points and their epipolar "
#           "lines is \n"
#           "{} pixels. This should be as small as possible.".format(avg_error))
#     calibration.export(args.output_folder)
    
PROGRAM_DESCRIPTION=(
"Take a number of pictures with a stereo camera in which a chessboard is "
"visible to both cameras. The program waits until a chessboard is detected in "
"both camera frames. The pictures are then saved to a file in the specified "
"output folder. After five seconds, the cameras are rescanned to find another "
"chessboard perspective. This continues until the specified number of pictures "
"has been taken."
)


def main():
    parser = ArgumentParser(description=PROGRAM_DESCRIPTION)
                           #parents=[CHESSBOARD_ARGUMENTS])

    parser.add_argument("--rows", type=int,
                                  help="Number of inside corners in the "
                                  "chessboard's rows.", default=9)
    parser.add_argument("--columns", type=int,
                                  help="Number of inside corners in the "
                                  "chessboard's columns.", default=6)
    parser.add_argument("--square-size", help="Size of chessboard "
                                  "squares in cm.", type=float, default=1.8)


    parser.add_argument("left", metavar="left", type=int,
                        help="Device numbers for the left camera.")
    parser.add_argument("right", metavar="right", type=int,
                        help="Device numbers for the right camera.")
    parser.add_argument("num_pictures", type=int, help="Number of valid "
                        "chessboard pictures that should be taken.")
    parser.add_argument("output_folder", help="Folder to save the images to.")
    parser.add_argument("--calibration-folder", help="Folder to save camera "
                        "calibration to.")
    args = parser.parse_args()
    if args.calibration_folder and not args.square_size:
        args.print_help()

    # progress = ProgressBar(maxval=args.num_pictures,
    #                       widgets=[Bar("=", "[", "]"),
    #                       " ", Percentage()])
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)
    #progress.start()
    with ChessboardFinder((args.left, args.right)) as pair:

        # Sets initial position of windows, based on image size
        set_window_position(pair)

        # for i in range(args.num_pictures):
        for i in tqdm(range(1, args.num_pictures+1)):

            # Introduces a 5 second delay before the camera pair is scanned for new images
            enforce_delay(pair, 5)

            frames, corners = pair.get_chessboard(args.columns, args.rows, True)
            for side, frame in zip(("stereoL", "stereoR"), frames):
                # number_string = ''.format(i)
                filename = 'img-{:04d}.png'.format(i)
                output_path = os.path.join(args.output_folder, side, filename)
                cv2.imwrite(output_path, frame)

            # progress.update(progress.maxval - (args.num_pictures - i))

            # Displays the recent accepted image pair. Helps in generating diverse calibration images.
            show_selected_frames(frames, corners, pair, args, True)

        # progress.finish()
        #cv2.destroyAllWindows()

    # if args.calibration_folder:
    #     args.input_files = find_files(args.output_folder)
    #     args.output_folder = args.calibration_folder
    #     args.show_chessboards = True
    #     calibrate_folder(args)


def show_selected_frames(frames, corners, pair, args, draw_corners=False):
    """
    Display the most recently captured (left as well as right) images.
    If draw_corners is set to true, the identified corners are marked on the images.
    """

    if draw_corners:
        for frame, corner in zip(frames, corners):
            cv2.drawChessboardCorners(frame, (args.columns, args.rows), corner, True)

    cv2.imshow("{} selected".format(pair.windows[0]), frames[0])
    cv2.imshow("{} selected".format(pair.windows[1]), frames[1])


def enforce_delay(pair, delay):
    """
    Enforces a delay of 5 seconds. This helps the user to change the chessboard perspective.
    A timer is displayed indicating the time remaining before the next sample is captured.
    """

    font = cv2.FONT_HERSHEY_SIMPLEX
    line_type = cv2.LINE_4
    line_thickness = 4

    start_time = time.time()
    now = start_time

    while now - start_time < delay:

        frames = pair.get_frames()

        # Calculates the time remaining before the next sample is captured
        time_remaining = "{:.2f}".format(delay - now + start_time)

        # Estimating the scale factor.
        font_scale = get_approx_font_scale(frames[0], time_remaining, font, line_thickness)

        text_size = cv2.getTextSize(time_remaining, font, font_scale, line_thickness)[0]

        # Calculates the position of the text
        text_x = (frames[0].shape[1] - text_size[0]) // 2
        text_y = (frames[0].shape[0] + text_size[1]) // 2

        for frame, window in zip(frames, pair.windows):
            cv2.putText(img=frame,  
                        text=time_remaining, 
                        org=(text_x, text_y), 
                        fontFace=font, 
                        fontScale=font_scale, 
                        color=(255, 50, 50),
                        thickness=line_thickness,
                        lineType=line_type)
            cv2.imshow(window, frame)

        cv2.waitKey(1)
        now = time.time()


def get_approx_font_scale(frame, text, font, line_thickness):
    """
    Approximate the font scale for the timer display.
    """

    _, width = frame.shape[:2]
    target_width = width / 2

    base_text_size = cv2.getTextSize(text, font, 1.0, line_thickness)[0]
    scale_factor = float(target_width) / base_text_size[0]

    return scale_factor


def set_window_position(pair):

    """
    Set initial the positions of windows.
    The top left and right windows display the live cam stream with timer overlay.
    The bottom left and right windows display recently selected frame.
    """

    frames = pair.get_frames()
    pair.show_frames(1)

    # Setting initial position of cameras
    cv2.moveWindow(pair.windows[0], 0, 0)
    cv2.moveWindow(pair.windows[1], frames[1].shape[1], 0)

    # Setting initial position of selected frames
    cv2.namedWindow("{} selected".format(pair.windows[0]), cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow("{} selected".format(pair.windows[0]), 0, frames[0].shape[0] + 30)

    cv2.namedWindow("{} selected".format(pair.windows[1]), cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow("{} selected".format(pair.windows[1]), frames[1].shape[1], frames[1].shape[0] + 30)


if __name__ == "__main__":
    main()
