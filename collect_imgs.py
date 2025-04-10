import os
import cv2
import time

DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

number_of_classes = 56
dataset_size = 200

cap = cv2.VideoCapture(0)
# Set lower resolution for better performance
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

for j in range(number_of_classes):
    if not os.path.exists(os.path.join(DATA_DIR, str(j))):
        os.makedirs(os.path.join(DATA_DIR, str(j)))

    print('Collecting data for class {}'.format(j))

    done = False
    while True:
        ret, frame = cap.read()
        cv2.putText(frame, 'Ready? Press "Q" ! :)', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3,
                    cv2.LINE_AA)
        cv2.imshow('frame', frame)
        if cv2.waitKey(25) == ord('q'):
            break
    
    # Add countdown timer (5 seconds)
    for timer in range(5, 0, -1):
        ret, frame = cap.read()
        cv2.putText(frame, f'Starting in {timer} seconds...', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, 'Get ready!', (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        cv2.waitKey(25)
        time.sleep(1)  # Wait for 1 second
    
    # Indicate that collection is starting
    ret, frame = cap.read()
    cv2.putText(frame, 'Collecting data NOW!', (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (255, 0, 0), 3, cv2.LINE_AA)
    cv2.imshow('frame', frame)
    cv2.waitKey(500)  # Small pause so user sees the message

    counter = 0
    while counter < dataset_size:
        ret, frame = cap.read()
        # Display counter on frame
        cv2.putText(frame, f'Collecting: {counter+1}/{dataset_size}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        cv2.waitKey(15)
        cv2.imwrite(os.path.join(DATA_DIR, str(j), '{}.jpg'.format(counter)), frame)

        counter += 1

cap.release()
cv2.destroyAllWindows()
