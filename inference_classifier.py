import pickle

import cv2
import mediapipe as mp
import numpy as np

model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

cap = cv2.VideoCapture(0)
# Set lower resolution for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(static_image_mode=True, min_detection_confidence=0.3)

labels_dict = {0: 'Pain', 1: 'Sick', 2: 'Headache', 3: 'Dizzy', 4: 'Vomit', 5: 'Diarrhea', 6: 'Cough', 7: 'Allergy', 
               8: 'Strong', 9: 'Weak', 10: 'Stomachache', 11: 'Sore Throat', 12: 'Sore Throat', 13: 'Injury', 
               14: 'Breathing Difficulty', 15: 'Breathing Difficulty', 16: 'Food Poisoning', 17: 'Wound', 18: 'Stress',
               19: 'Conditions', 20: 'Fever', 21: 'Diabetes', 22: 'Back Pain', 23: 'Back Pain', 24: 'Colds', 25: 'Stroke',
               26: 'Blood Pressure', 27: 'A', 28: 'B', 29: 'C', 30: 'D', 31: 'E', 32: 'F', 33: 'G', 34: 'H', 35: 'I', 
               36: 'J', 37: 'K', 38: 'L', 39: 'M', 40: 'N', 41: 'O', 42: 'P', 43: 'Q', 44: 'R', 45: 'S', 46: 'T', 
               47: 'U', 48: 'V', 49: 'W', 50: 'X', 51: 'Y', 52: 'Z', 53: 'Hello', 54: 'Good Morning', 55: 'Good Afternooon',
               56: 'Good Evening', 57: 'Thank You'} 
while True:

    data_aux = []
    x_ = []
    y_ = []
    z_ = []

    ret, frame = cap.read()

    H, W, _ = frame.shape

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = hands.process(frame_rgb)
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,  # image to draw
                hand_landmarks,  # model output
                mp_hands.HAND_CONNECTIONS,  # hand connections
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style())

        for hand_landmarks in results.multi_hand_landmarks:
            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                z = hand_landmarks.landmark[i].z

                x_.append(x)
                y_.append(y)
                z_.append(z)

            # Extract the basic normalized coordinates (42 features)
            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                z = hand_landmarks.landmark[i].z
                
                data_aux.append(x - min(x_))
                data_aux.append(y - min(y_))
            
            # Add z-coordinates (21 additional features)
            for i in range(len(hand_landmarks.landmark)):
                z = hand_landmarks.landmark[i].z
                data_aux.append(z - min(z_))
            
            # Add distance features between fingertips and wrist (5 additional features)
            wrist_idx = 0
            fingertips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
            
            for tip_idx in fingertips:
                # Calculate Euclidean distance between fingertip and wrist
                wrist_x = hand_landmarks.landmark[wrist_idx].x
                wrist_y = hand_landmarks.landmark[wrist_idx].y
                wrist_z = hand_landmarks.landmark[wrist_idx].z
                
                tip_x = hand_landmarks.landmark[tip_idx].x
                tip_y = hand_landmarks.landmark[tip_idx].y
                tip_z = hand_landmarks.landmark[tip_idx].z
                
                distance = np.sqrt((tip_x - wrist_x)**2 + (tip_y - wrist_y)**2 + (tip_z - wrist_z)**2)
                data_aux.append(distance)
            
            # Add angles between adjacent fingers (4 additional features)
            for i in range(4):
                current_tip = fingertips[i]
                next_tip = fingertips[i+1]
                
                vec1_x = hand_landmarks.landmark[current_tip].x - hand_landmarks.landmark[wrist_idx].x
                vec1_y = hand_landmarks.landmark[current_tip].y - hand_landmarks.landmark[wrist_idx].y
                
                vec2_x = hand_landmarks.landmark[next_tip].x - hand_landmarks.landmark[wrist_idx].x
                vec2_y = hand_landmarks.landmark[next_tip].y - hand_landmarks.landmark[wrist_idx].y
                
                # Calculate the angle between two vectors (in radians)
                dot_product = vec1_x * vec2_x + vec1_y * vec2_y
                mag1 = np.sqrt(vec1_x**2 + vec1_y**2)
                mag2 = np.sqrt(vec2_x**2 + vec2_y**2)
                
                # Avoid division by zero
                if mag1 * mag2 > 0:
                    angle = np.arccos(min(1, max(-1, dot_product / (mag1 * mag2))))
                else:
                    angle = 0
                    
                data_aux.append(angle)
            
            # Add distance between adjacent fingertips (4 additional features)
            for i in range(4):
                current_tip = fingertips[i]
                next_tip = fingertips[i+1]
                
                tip1_x = hand_landmarks.landmark[current_tip].x
                tip1_y = hand_landmarks.landmark[current_tip].y
                tip1_z = hand_landmarks.landmark[current_tip].z
                
                tip2_x = hand_landmarks.landmark[next_tip].x
                tip2_y = hand_landmarks.landmark[next_tip].y
                tip2_z = hand_landmarks.landmark[next_tip].z
                
                distance = np.sqrt((tip2_x - tip1_x)**2 + (tip2_y - tip1_y)**2 + (tip2_z - tip1_z)**2)
                data_aux.append(distance)
            
            # Add curvature features of each finger (5 additional features)
            finger_bases = [1, 5, 9, 13, 17]  # Base of thumb, index, middle, ring, pinky
            finger_mids = [2, 6, 10, 14, 18]  # Middle joints
            
            for i in range(5):
                base_idx = finger_bases[i]
                mid_idx = finger_mids[i]
                tip_idx = fingertips[i]
                
                # Create vectors from base to mid and mid to tip
                base_to_mid_x = hand_landmarks.landmark[mid_idx].x - hand_landmarks.landmark[base_idx].x
                base_to_mid_y = hand_landmarks.landmark[mid_idx].y - hand_landmarks.landmark[base_idx].y
                
                mid_to_tip_x = hand_landmarks.landmark[tip_idx].x - hand_landmarks.landmark[mid_idx].x
                mid_to_tip_y = hand_landmarks.landmark[tip_idx].y - hand_landmarks.landmark[mid_idx].y
                
                # Calculate the angle between the vectors
                dot_product = base_to_mid_x * mid_to_tip_x + base_to_mid_y * mid_to_tip_y
                mag1 = np.sqrt(base_to_mid_x**2 + base_to_mid_y**2)
                mag2 = np.sqrt(mid_to_tip_x**2 + mid_to_tip_y**2)
                
                if mag1 * mag2 > 0:
                    curvature = np.arccos(min(1, max(-1, dot_product / (mag1 * mag2))))
                else:
                    curvature = 0
                    
                data_aux.append(curvature)
            
            # Add 3 more features to get from 81 to 84
            # 1. Palm area approximation
            palm_points = [0, 1, 5, 9, 13, 17]  # Wrist and base of fingers
            palm_x = [hand_landmarks.landmark[i].x for i in palm_points]
            palm_y = [hand_landmarks.landmark[i].y for i in palm_points]
            palm_area = abs(np.sum([palm_x[i]*palm_y[i+1] - palm_x[i+1]*palm_y[i] for i in range(len(palm_points)-1)]) / 2)
            data_aux.append(palm_area)
            
            # 2. Hand aspect ratio (width / height)
            x_min, x_max = min(x_), max(x_)
            y_min, y_max = min(y_), max(y_)
            width = x_max - x_min
            height = y_max - y_min
            if height != 0:
                aspect_ratio = width / height
            else:
                aspect_ratio = 1.0
            data_aux.append(aspect_ratio)
            
            # 3. Average z-depth of fingertips relative to wrist
            wrist_z = hand_landmarks.landmark[wrist_idx].z
            avg_fingertip_z = sum([hand_landmarks.landmark[i].z for i in fingertips]) / len(fingertips)
            z_depth_diff = avg_fingertip_z - wrist_z
            data_aux.append(z_depth_diff)
            
            # If we need exactly 84 features, trim any extra
            if len(data_aux) > 84:
                data_aux = data_aux[:84]
            
            # Add padding if we have less than 84 features
            while len(data_aux) < 84:
                data_aux.append(0.0)
            
            # Ensure we have 84 features before prediction
            if len(data_aux) != 84:
                continue  # Skip prediction if we don't have the right number of features

            x1 = int(min(x_) * W) - 10
            y1 = int(min(y_) * H) - 10

            x2 = int(max(x_) * W) - 10
            y2 = int(max(y_) * H) - 10

            prediction = model.predict([np.asarray(data_aux)])

            predicted_character = labels_dict[int(prediction[0])]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            cv2.putText(frame, predicted_character, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                        cv2.LINE_AA)

    cv2.imshow('frame', frame)
    cv2.waitKey(1)


cap.release()
cv2.destroyAllWindows()
