#!/usr/bin/env python3

# import the necessary packages
from imutils import face_utils
import numpy as np
import argparse
import imutils
import dlib

#import h5py

import pickle
import face_recognition
import os
import sys
import time

import cv2 as cv

# mema oriented libraries
import memalib.mema_utility as mu
import logging
from configobj import ConfigObj


with open("face_data/trained_knn_model.clf", 'rb') as f:
    knn_clf = pickle.load(f)

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    count = 0
    count += 1
    
    X_face_locations = face_recognition.face_locations(frame,1,model="hog")
    #print(X_face_locations)
    title = 'Mema Unlock'
    if len(X_face_locations) != 0:        
            # Find encodings for faces in the test iamge
            faces_encodings = face_recognition.face_encodings(frame, known_face_locations=X_face_locations)

            # Use the KNN model to find the best matches for the test face
            #print(np.array(faces_encodings).shape)
            closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
            are_matches = [closest_distances[0][i][0] <= 0.4 for i in range(len(X_face_locations))]
            # Predict classes and remove classifications that aren't within the threshold
            predictions = [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings), X_face_locations, are_matches)]
            #print(predictions)

            for name, (top, right, bottom, left) in predictions:
                
                if name not in "unknown":
 
                    cv.rectangle(frame, (left,bottom),(right,top), (0, 255, 0), 2)
                    # show the face number
                    cv.putText(frame, "{}".format(name), (left-10, top-10),cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    if count == 10:
                        print('count is ' + str(count))
                        mu.curl_speak('hello_' + '_'.join(name))
                        print(name.replace(' ','|'))
                        time.sleep(2)
                        sys.exit()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # Our operations on the frame come here
    cv.imshow(title,frame)
    if cv.waitKey(1) == 'ESC':
        break
# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
