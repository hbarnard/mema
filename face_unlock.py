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
import json

import cv2 as cv
import paho.mqtt.client as mqtt

# mema oriented libraries
import memalib.mema_utility as mu
import logging
from configobj import ConfigObj


# FIXME: program should really be 'control by face', does sign out as well
def on_connect(client, userdata, flags, rc):
    #print("Connected with result code "+str(rc))
    client.subscribe("hermes/intent/Unlock")
    client.subscribe("hermes/intent/Lock")

def on_message(client, userdata, msg):
    #logging.debug(userdata)
    decoded_message=str(msg.payload.decode("utf-8"))
    intent_data =json.loads(decoded_message)
    #logging.debug('intent name is ' + intent_data['intent']['intentName']) 
    if intent_data['intent']['intentName'] == 'Unlock':
        face_unlock(userdata)
    elif intent_data['intent']['intentName'] == 'Lock':
        logging.debug('intent name is ' + intent_data['intent']['intentName']) 
        mu.run_sign_out(None,None) #FIXME: need to fix some of these function signatues
        mu.open_url('static/offline.html')
    #client.disconnect()


def face_unlock(config):

    mu.curl_speak('please_look_directly_at_the_camera')
    # mema integration

    #FIXME: known_face_count face must be recognised 10 times, simplistic hack to deal with photos and relaxed recognition
    #FIXME: if 10 unknowns, display privacy page and sign in as guest account
    known_face_count = 0
    unknown_face_count = 0

    with open("face_data/trained_knn_model.clf", 'rb') as f:
        knn_clf = pickle.load(f)
        
    cap = cv.VideoCapture(0)
    #cv2.setWindowProperty(WindowName,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    if not cap.isOpened():
        exit()
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        X_face_locations = face_recognition.face_locations(frame,1,model="hog")
        #logging.debug(X_face_locations)
        title = 'Mema3 Unlock'
        
        if len(X_face_locations) != 0:        
                # Find encodings for faces in the test iamge
                faces_encodings = face_recognition.face_encodings(frame, known_face_locations=X_face_locations)

                # Use the KNN model to find the best matches for the test face
                closest_distances = knn_clf.kneighbors(faces_encodings, n_neighbors=1)
                are_matches = [closest_distances[0][i][0] <= 0.4 for i in range(len(X_face_locations))]
                # Predict classes and remove classifications that aren't within the threshold
                predictions = [(pred, loc) if rec else ("unknown", loc) for pred, loc, rec in zip(knn_clf.predict(faces_encodings), X_face_locations, are_matches)]

                for name, (top, right, bottom, left) in predictions:
                    
                    # let's be polite shall we!
                    head_title = ''
                    if name not in "unknown":
                        head_title = name
                    else:
                        head_title = 'Honoured Guest'

                    cv.rectangle(frame, (left,bottom),(right,top), (0, 255, 0), 2)
                    # show the face number
                    cv.putText(frame, "{}".format(head_title), (left-10, top-10),cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                        
                    if name not in "unknown":
                        known_face_count += 1
                        
                        cv.imshow(title,frame) 
                        cv.setWindowProperty(title, cv.WND_PROP_TOPMOST, 1)
                        if cv.waitKey(20) == 'ESC':
                            break   
                        if known_face_count == 10:
                            (first_name, last_name) = name.split()
                            mu.curl_speak('Hello_' + first_name)
                            mu.database_sign_in(first_name, last_name)
                            mu.declare_mema_health()
                            mu.curl_speak(config['en_prompts']['ok_going'])
                            cap.release()
                            cv.destroyAllWindows()
                            # Doesn't pass through privacy because, in principle onboarded
                            mu.open_url('memories.html')
                    else:
                        unknown_face_count += 1
    
                        cv.imshow(title,frame)
                        cv.setWindowProperty(title, cv.WND_PROP_TOPMOST, 1)                                           
                        cv.waitKey(20)
                        if unknown_face_count == 10:
                            mu.curl_speak('Hello_honored_guest')
                            mu.database_sign_in('Guest', 'Account')
                            mu.declare_mema_health()
                            mu.curl_speak(config['en_prompts']['ok_going'])
                            cap.release()
                            cv.destroyAllWindows()
                            # Passes through privacy, since guest
                            mu.open_url('static/privacy.html')
                        continue

                else:
                    continue
                    
        logging.debug('reach here?')
        mu.curl_speak('Sorry_no_human_faces_found')
        # When everything done, release the capture
        cap.release()
        cv.destroyAllWindows()
        return


def main():
    
    config = ConfigObj('etc/mema.ini')
    logging.basicConfig(filename=config['main']['logfile_name'], format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
    
    client = mqtt.Client(userdata=config)
    client.connect('localhost',1883,60)
    client.on_connect = on_connect
    client.on_message = on_message
    #FIXME: yes this is a small low load server, listening for log ins
    client.loop_forever()

if __name__ == '__main__':
    main()
    
