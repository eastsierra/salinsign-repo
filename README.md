# SalinSign: A Filipino Sign Language Recognition System for Doctor-Deaf Interaction Using Long Short-Term Memory (LSTM) Architecture

## About the Project

SalinSign is a Filipino Sign Language recognition system specializing for doctor-patient interaction, centering on creating a real-time application optimized for clinical environments. During consultations, it enables deaf patients to communicate with a general practitioner using medical-related FSL gestures, which will be translated into text. The general practitioner will respond by typing messages, which will be displayed as text for the patient to read. This setup eliminates the need for an interpreter—which may be limited or not available at all clinics—ensuring confidentiality and facilitating direct communication between the patient and the general practitioner.

## Getting Started


<h3> salinsign_v1 </h3>



**Windows**

1. Create a virtual environment <br><br>
   ```
   python -m venv salinenv 
   ```
2. Activate the virtual environment (salinenv) <br><br>
   ```
   env\Scripts\activate
   ```
   or
   ```
   env\Scripts\activate.bat
   ```
3. Install Packages 
* Method 1 - Install Packages from `requirements.txt` <br> 
    ```
  pip install -r requirements.txt
    ```

* Method 2 - Manual Installation of Packages <br>
    ```
    pip install tensorflow==2.18.0 opencv-python mediapipe scikit-learn matplotlib
    ```
4. Check the installed Packages <br><br>
    ```
    pip list
    ```
   <br>
   
**Linux**

1. Create a Directory 
   ```
   $ mkdir salinenv
   ``` 
   ```
   $ cd salinenv
   ```

2. Create and Activate a virtual Environment
   ```
   $ python3 -m venv .salinenv
   ```
  
   ```
   $ source .salinenv/bin/activate
   ```
   
3. Install Packages
* Method 1 - Install Packages from `requirements.txt`
    ```
    pip install -r requirements.txt
    ```

* Method 2 - Manual Installation of Packages 
  ```
  pip install tensorflow==2.18.0 opencv-python mediapipe scikit-learn matplotlib
  ```

4. Check the installed packages <br><br>
    ```
    pip list
    ```
