# SalinSign: A Filipino Sign Language Recognition System for Doctor-Deaf Interaction Using Long Short-Term Memory (LSTM) Architecture

## About the Project

SalinSign is a Filipino Sign Language recognition system specializing for doctor-patient interaction, centering on creating a real-time application optimized for clinical environments. During consultations, it enables deaf patients to communicate with a general practitioner using medical-related FSL gestures, which will be translated into text. The general practitioner will respond by typing messages, which will be displayed as text for the patient to read. This setup eliminates the need for an interpreter—which may be limited or not available at all clinics—ensuring confidentiality and facilitating direct communication between the patient and the general practitioner.

## Getting Started


<h3> salinsign_v1 </h3>

<br> 

**Windows**

1. Inside the `salinsign_v1` Folder, Create a Virtual Environment <br><br>
   ```
   python -m venv salinenv 
   ```
2. Activate the Virtual Environment (salinenv) <br><br>
   ```
   salinenv\Scripts\activate
   ```
   or
   ```
   salinenv\Scripts\activate.bat
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
-If the instructions are unclear, refer to this [tutorial](https://youtu.be/Y21OR1OPC9A?si=U4c5jl8k4528wqL5) <br><br>

**Linux**

1. Open `salinsign_v1` Directory 
   ```
   $ cd salinsign_v1
   ```

2. Create and Activate a Virtual Environment
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
    <br><br>

**Notes**<br><br>

-Make sure the virtual environment folder and the .py files are _inside_ the `salinsign_v1` folder
<br><br>
![image](https://github.com/user-attachments/assets/bfb83ae0-a793-4dc9-822c-d64b26f4c015)
<br><br>
-When Adding, Commiting, Pushing, **❗❗DO NOT❗❗** include the virtual environment folder `salinenv`
