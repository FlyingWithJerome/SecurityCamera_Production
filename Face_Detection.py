'''
face_detection.py
'''

try:
    import Queue as queue
except ImportError:
    import queue

from datetime import datetime

import numpy as np
import cv2
# import video_capture

# from frame_tag import Tag

class Detector(object):

    def __init__(self, camera_serial=0, frame_skip=7, method="Haar_upperbody", event_logic="threshold", video_format="MJPG", video_handler=None, on_pi=False):

        # print("detector initializing")

        if method == "Haar_upperbody":
            self.__cascade = cv2.CascadeClassifier('haarcascade_upperbody.xml')

        elif method == "Haar_frontalface":
            self.__cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')

        elif method == "HOG":
            self.__cascade = cv2.HOGDescriptor()
            self.__cascade.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

        else:
            raise ValueError("need a valid detector name")

        if video_handler is None:
            self.__camera = cv2.VideoCapture(camera_serial)
        else:
            self.__camera = video_handler

        if on_pi:
            self.__writer = cv2.VideoWriter("out.avi", cv2.cv.CV_FOURCC(*video_format), 12, (1280, 720))
        else:
            self.__writer = cv2.VideoWriter("out.avi", cv2.VideoWriter_fourcc(*video_format), 12, (1280, 720))
        self.__method = method
        self.__output_buffer  = None
        self.__size_buffer    = []
        
        if event_logic == "threshold":
            self.__check_event_logic = self.__check_event_logic_threshold
        else:
            self.__check_event_logic = self.__check_event_logic_increase

        self.__event_level    = 1


    def main_loop(self):
        order = 0
        while(True):
            if order % self.__frame_skip == 0:
                frame = self.get_frame_single(skip=False)
            else:
                frame = self.get_frame_single(skip=True)
            
            order += 1
            if not (frame is None):
                cv2.imshow("frame", frame)
                cv2.waitKey(1)

    def get_event_level(self):
        return self.__event_level

    def get_frame_single(self, skip=False):
        try:
            ret, frame = self.__camera.read()
            if not ret:
                return None
            
            if not skip:
                frame = self.__detect_face(frame)
                self.__check_event_logic()
            # print(self.__size_buffer)

            if self.__event_level == 2:
                self.__output_media(frame, "lo-res pic")

            elif self.__event_level == 3:
                self.__output_media(frame, "hi-res pic")

            elif self.__event_level == 4:
                self.__output_media(frame, "video")

            return frame

        except (EOFError, IOError, KeyboardInterrupt):
            return None

    def __append_to_size_buffer(self, size):
        '''
        append to the size buffer, remove the earliest
        one if it reaches the size limit
        '''
        if len(self.__size_buffer) == 10:
            del self.__size_buffer[0]

        self.__size_buffer.append(size)

    def __is_approaching_for_long(self, is_approaching=True):
        '''
        check if the suspicious is keep approaching for
        the whole size buffer

        is_approaching: check it is approaching if true
        check it is leaving if false
        '''
        if not is_approaching and\
            all(i == 0 for i in self.__size_buffer[:-5]):
            return True
            
        size_buffer_copy = list()
        size_buffer_copy[:] = self.__size_buffer[:]
        size_buffer_copy.sort(reverse=not is_approaching)

        return size_buffer_copy == self.__size_buffer

    def __detect_face(self, frame):
        '''
        detect human faces and changes the event level if the condition
        matches
        '''
        faces = self.__cascade.detectMultiScale(frame)
        (x, y, w, h) = (0, 0, 0, 0)

        if len(faces) > 0:
            if self.__method.startswith("Haar"):
                (x, y, w, h)  = faces[0]
                self.__append_to_size_buffer(w*2 + h*2)

            elif self.__method == "HOG":
                if len(faces[0]) > 0 and len(faces[0][0]) > 0: 
                    (x, y, w, h)  = faces[0][0]

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)        
        self.__append_to_size_buffer(w*2 + h*2)

        return frame

    
    def __output_media(self, frame, option="lo-res pic"):

        time_now = "_".join(str(datetime.now())[:-7].split())
        
        if option == "lo-res pic":
            filename = "low_resolution_pic_{}.jpg".format(time_now)
            cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

        elif option == "hi-res pic":
            filename = "hi_resolution_pic_{}.jpg".format(time_now)
            cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

        elif option == "video":
            self.__writer.write(frame)


    def __check_event_logic_threshold(self):
        print(self.__size_buffer)

        if self.__event_level > 1:
            if 500 > self.__size_buffer[-1] >= 300:
                self.__event_level = 3
                return

            elif self.__size_buffer[-1] >= 500:
                self.__event_level = 4
                return
        else:
            if self.__size_buffer[-1] > 0:
                self.__event_level = 2
                return

        if all(i==0 for i in self.__size_buffer[-5:]):
            self.__event_level = 1


    def __check_event_logic_increase(self):
        '''
        change the event level based on the
        logic designed
        '''
        print(self.__size_buffer)
        if 2 <= self.__event_level < 4:
            if len(self.__size_buffer) == 10:
                if self.__is_approaching_for_long(True):
                    self.__event_level += 1

                elif self.__is_approaching_for_long(False):
                    self.__event_level = 1

        elif self.__event_level == 1:
            if any(i > 0 for i in self.__size_buffer):
                self.__event_level += 1

    def __del__(self):
        self.__camera.release()
        self.__writer.release()


if __name__ == "__main__":
    f = Detector(method="Haar_frontalface")
    f.main_loop()


        
