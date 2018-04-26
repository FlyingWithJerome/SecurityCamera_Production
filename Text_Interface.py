'''
Text Interface.py

This module represents the text interface for the camera system
'''

import cProfile
import gc
import sys
import threading
import time
from datetime import datetime

import cv2

import alarm
from Face_Detection import Detector

class TextInterface(object):

    def __init__(self, camera_num=0, detect_method="Haar_frontalface", event_logic="threshold", on_pi=False):

        print("Initializing Camera {}...".format(camera_num))
        self.__camera_num = camera_num
        self.__test_video = cv2.VideoCapture(camera_num)

        if not self.__test_video.isOpened():
            print("Camera", camera_num, "quits")
            exit(-1)

        self.__event_str = None
        self.__event_changed = False
        self.__isrunning = True
        self.__event_level = 1
        self.__image = None

        self.__detector = Detector(method=detect_method, video_handler=self.__test_video, event_logic=event_logic, on_pi=on_pi)
        self.__email_send_time = None
        print("Initialization Finished")


    def __get_event_level(self):
        try:
            event_lvl = self.__detector.get_event_level()
        except AttributeError:
            return None

        if event_lvl != self.__event_level:
            time_now = str(datetime.now())[:-7]
            verb = "raised to" if event_lvl > self.__event_level else "lowered to"

            fmt = "[Camera {}] <{}> Event {} {} {}".format(\
            self.__camera_num, time_now, self.__event_level, verb, event_lvl
            )
            self.__event_level = event_lvl
            print(fmt)

    
    def run(self):
        order = 0
        try:
            while(self.__isrunning):
                if self.__test_video.isOpened():
                    if order % 2 == 0:
                        self.__image = self.__detector.get_frame_single(skip=False)
                    else:
                        self.__image = self.__detector.get_frame_single(skip=True)
                    order += 1

                self.__get_event_level()
                if self.__event_level == 3:
                    send_time = time.time()
                    if (self.__email_send_time is None) or (send_time - self.__email_send_time > 100):
                        alarm_executor = threading.Thread(target=alarm.send_alarm)
                        alarm_executor.start()
                        time_now = str(datetime.now())[:-7]
                        print("[Camera {}] <{}> Send alarms to the receipents...".format(
                            self.__camera_num, time_now
                        ))
                        self.__email_send_time = time.time()

                gc.collect()

        except KeyboardInterrupt:
            return


    def __del__(self):
        time_now = str(datetime.now())[:-7]
        print("[Camera {}] <{}> Properly released".format(
            self.__camera_num, time_now
        ))
        self.__isrunning = False
        del self.__detector
        self.__test_video.release()

if __name__ == "__main__":
    on_pi = True if sys.argv[1] == "pi" else False
    t = TextInterface(on_pi=on_pi)
    t.run()