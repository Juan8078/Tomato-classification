# dec,9 2023 6:55PM

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import json
import cv2
import os
import time
import shutil
import numpy as np
import serial #pyserial


# Authenticate and create a GoogleDrive instance
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # This will open a web page for authentication
drive = GoogleDrive(gauth)

# ser = serial.Serial('/dev/ttyUSB0', 115200)
# ser = serial.Serial('/dev/ttyACM0', 115200)
ser = serial.Serial('COM4', 115200)

cameraMode = 1 # RPI 0 (Next UP_LAN Port), Webcam windows 1/2
rpiMode = 0

if rpiMode:
    import RPi.GPIO as GPIO
    # Set up GPIO pin and configure mode
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(26, GPIO.OUT)

def beep(beep_count, short_duration, long_duration):
    if rpiMode:
        try:
            for _ in range(beep_count):
                GPIO.output(26, GPIO.HIGH)
                time.sleep(short_duration)
                GPIO.output(26, GPIO.LOW)
                time.sleep(long_duration)
        except KeyboardInterrupt:
            pass


def detect_tomatoes(frame):
    # Convert the frame from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the lower and upper bounds for the red color (tomatoes)
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])

    # Create a mask using the inRange function to filter out red pixels
    mask = cv2.inRange(hsv, lower_red, upper_red)

    # Use the mask to extract the red regions from the original frame
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Convert the result to grayscale for contour detection
    gray_result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

    # Find contours in the grayscale image
    contours, _ = cv2.findContours(gray_result, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours based on area (adjust the threshold based on your needs)
    min_contour_area = 500
    detected_tomatoes = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

    return detected_tomatoes


def image_classification():
    print(f"\nWelcome to Image Classification\n")
    input_folder = "1xpFjm0EGy4KZYcHdDWt87sjU7YQTcqG9"
    cap = cv2.VideoCapture(cameraMode)
    while True:
        ret, frame = cap.read()

        tomatoes = detect_tomatoes(frame)
        for cnt in tomatoes:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Image Classification", frame)
        if tomatoes:
            tomatoes_times = time.time()
            while time.time() - tomatoes_times < 3:
                ret, frame = cap.read()

                tomatoes = detect_tomatoes(frame)
                for cnt in tomatoes:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                cv2.imshow("Image Classification", frame)
                time.sleep(0.05)
            if tomatoes :
                print("Tomato Detected")

        if ser.in_waiting > 0:
            # Read data from the serial port
            serial_data = ser.readline().decode('utf-8').strip()
            if serial_data == "detected#":
                tomatoes = True

        if cv2.waitKey(1) == ord(' ') or tomatoes:
            beep(1, 0.1, 0.1)
            # Get the current timestamp
            timestamp = time.time()
            gmt_offset = 7 * 60 * 60
            time_struct_utc = time.gmtime(timestamp)
            time_struct_gmt7 = time.struct_time(
            time_struct_utc[:8] + (time_struct_utc.tm_yday,))  # Keep tm_yday unchanged
            timestamp_gmt7 = time.mktime(time_struct_gmt7) + gmt_offset
            time_struct = time.localtime(timestamp_gmt7)
            formatted_date = time.strftime("%b_%d_%Y_%H_%M_%S", time_struct)

            file_name = f"{formatted_date}.jpg"
            print(file_name)
            input_name = f"classification/input/{file_name}"
            cv2.imwrite(input_name, frame)
            item_path = os.path.join('classification/input', file_name)
            try:
                # Create a GoogleDriveFile instance and upload the photo with the unique
                file = drive.CreateFile({
                    'title': file_name,
                    'parents': [{'kind': 'drive#fileLink', 'id': input_folder}]  # Specify the parent folder ID
                })
                file.SetContentFile(item_path)
                file.Upload()

                if file.uploaded:
                    print(f'Uploaded: {file["title"]}, File ID: {file["id"]}\n')
                    get_json(formatted_date)
                else:
                    print(f'Upload failed: {file["title"]}\n')
            except Exception as e:
                print(f'Error uploading file: {str(e)}\n')

        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            break
    print("Image Calssification Prossess Done")


def get_json(input_name):
    print("Get JSON Response")
    # Specify the title of the JSON file you want to retrieve
    # file_title = 'test.json'
    file_title = f'{input_name}.json'

    # Search for the folder with the specified path
    folder_query = f"title = 'Colab Notebooks' and mimeType = 'application/vnd.google-apps.folder'"
    folder_list = drive.ListFile({'q': folder_query}).GetList()
    folder_query = f"title = 'projects' and mimeType = 'application/vnd.google-apps.folder'"
    folder_list = drive.ListFile({'q': folder_query}).GetList()
    folder_query = f"title = 'tomato_project' and mimeType = 'application/vnd.google-apps.folder'"
    folder_list = drive.ListFile({'q': folder_query}).GetList()
    folder_query = f"title = 'output' and mimeType = 'application/vnd.google-apps.folder'"
    folder_list = drive.ListFile({'q': folder_query}).GetList()

    # print(f"Folder query \n : {folder_query}")
    # print(f"Folder list \n : {folder_list}")

    if len(folder_list) > 0:
        # Assuming there's only one folder with the specified path, get its ID
        folder_id = folder_list[0]['id']

        file_list = []  # Initialize file_list as an empty list
        query_times = time.time()
        print("Waiting for JSON response")
        while len(file_list) == 0 and time.time() - query_times < 30:
            # Search for the JSON file within the specified folder
            file_query = f"title = '{file_title}' and '{folder_id}' in parents"
            file_list = drive.ListFile({'q': file_query}).GetList()
        # print(f"File query \n {file_query}")
        # print(f"File list \n {file_list}")

        if len(file_list) > 0:
            # Get the first matching file (assuming there's only one)
            json_file = file_list[0]
            # print(f"JSON File \n {json_file}")

            # Download the file content
            json_file.GetContentFile(file_title)
            output_folder = 'classification/output'
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            new_file_path = os.path.join(output_folder, os.path.basename(file_title))
            shutil.move(file_title, new_file_path)
            file_title = new_file_path

            # Read the JSON data from the file
            with open(file_title, 'r') as json_file:
                json_data = json.load(json_file)
            # Now you can work with the JSON data
            print(f"JSON Data \n {json_data}\n")
            # Extract condition (class_label) and accuracy from JSON data
            condition = json_data.get('class_label', 'unknown')
            accuracy_str = json_data.get('accuracy', '0.00%')
            accuracy = float(accuracy_str.rstrip('%'))

            # Print the extracted values for testing
            print(f"Condition: {condition}")
            print(f"Accuracy: {accuracy}%")
            
            # Format the data and send it over serial
            data = f"{condition}#{accuracy}#"
            ser.write(data.encode())
            print(f"Sent: {data}")
            time.sleep(1)
            # Close the serial port
            # ser.close()
            beep(3, 0.1, 0.1)

        else:
            beep(1, 1, 1)
            print(f'TIMEOUT or JSON file with title "{file_title}" NOT FOUND in the folder "{folder_query}".\n')
    else:
        beep(1, 1, 1)
        print(f'Folder with title "{folder_query}" not found in Google Drive.\n')


def image_register(take_count_train, take_count_val):
    print(f"\nWelcome to Image Register Training And Validation\n")
    # Version_1
    training_folder = [
        "damagedTrain",
        "oldTrain",
        "ripeTrain",
        "unripeTrain"
    ]
    validation_folder = [
        "damagedVal",
        "oldVal",
        "ripeVal",
        "unripeVal"
    ]

    counter = 0
    take_count_train = int(take_count_train)
    take_count_val = int(take_count_val)

    for key in training_folder:
        print(f"Caputre image with named : {key}1-{take_count_train}.jpg")
        cap = cv2.VideoCapture(cameraMode)
        while counter < take_count_train:
            ret, frame = cap.read()
            cv2.imshow(key, frame)
            # Check for a condition that triggers image capture (Press SPACE)
            if cv2.waitKey(1) == ord(' '):
                # Save the image to a file
                beep(1, 0.1, 0.1)
                counter += 1
                uploaded_name = f"register/trainings/{key}/{key}{counter}.jpg"
                print(f"{key}{counter}.jpg")
                cv2.imwrite(uploaded_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        counter = 0
        cap.release()
        cv2.destroyAllWindows()
        print(f"Finish capture for {key} category\n")

    for key in validation_folder:
        print(f"Caputre image with named : {key}1-{take_count_val}.jpg")
        cap = cv2.VideoCapture(cameraMode)
        while counter < take_count_val:
            ret, frame = cap.read()
            cv2.imshow(key, frame)
            # Check for a condition that triggers image capture (Press SPACE)
            if cv2.waitKey(1) == ord(' '):
                # Save the image to a file
                beep(1, 0.1, 0.1)
                counter += 1
                uploaded_name = f"register/validations/{key}/{key}{counter}.jpg"
                print(f"{key}{counter}.jpg")
                cv2.imwrite(uploaded_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        counter = 0
        cap.release()
        cv2.destroyAllWindows()
        print(f"Finish capture for {key} category\n")

    print("Image Register Done !")


def drive_upload():
    print("Welcome to Image Upload for Train And Val Google Drive")
    training_folder = {
        "damagedTrain": "1TOfHsuUDpVQ7God5tnHjdGDb1Iauyj3W",
        "oldTrain": "1IeRPIMd_55RaCv87zFYc2GV7reBpttmx",
        "ripeTrain": "1GIQ0lievvRSDJyKUtuvosBy7H2k4dTOp",
        "unripeTrain": "1BSdUsa3aH2hzUqRbwlVdY45sKQhu3JF2"
    }

    validation_folder = {
        "damagedVal": "1VbCrgiwZytYxq9y435v_icokQ9fhp5Aa",
        "oldVal": "1tNxts6DfXJegHsgvlwMuS8KM_b4OSovl",
        "ripeVal": "1aeQRqeugnugkjUKB0t7FJ8WVJPSzmSAQ",
        "unripeVal": "1KP4kwD2p-lrkdfTeNjm1ZLfxjOLDSRS6"
    }

    for key, value in training_folder.items():
        print(f'\nChecking local : "{key}" folder and upload to Google Drive id : "{value}"')
        folder_path = os.path.join('register', 'trainings', key)
        items = os.listdir(folder_path)
        for item in items:
            print(item)
            item_path = os.path.join(folder_path, item)
            # Upload the captured image to Google Drive
            if item != '.gitignore':
                try:
                    # Create a GoogleDriveFile instance and upload the photo with the unique
                    file = drive.CreateFile({
                        'title': item,
                        'parents': [{'kind': 'drive#fileLink', 'id': value}]  # Specify the parent folder ID
                    })
                    file.SetContentFile(item_path)
                    file.Upload()

                    if file.uploaded:
                        print(f'Uploaded success : {file["title"]}, File ID: {file["id"]}')
                        try:
                            os.remove(item_path)
                            print(f'Deleted locally: {file["title"]}')
                            beep(1, 0.1, 0.1)
                        except PermissionError:
                            print(f'File is still in use')
                            time.sleep(1)  # Add a short delay before trying again
                    else:
                        print(f'Upload failed : {file["title"]}')
                except Exception as e:
                    print(f'Error uploading file : {str(e)}')

    for key, value in validation_folder.items():
        print(f'\nChecking local : "{key}" folder and upload to Google Drive id : "{value}"')
        folder_path = os.path.join('register', 'validations', key)
        items = os.listdir(folder_path)
        for item in items:
            print(item)
            item_path = os.path.join(folder_path, item)
            # Upload the captured image to Google Drive
            if item != '.gitignore':
                try:
                    # Create a GoogleDriveFile instance and upload the photo with the unique
                    file = drive.CreateFile({
                        'title': item,
                        'parents': [{'kind': 'drive#fileLink', 'id': value}]  # Specify the parent folder ID
                    })
                    file.SetContentFile(item_path)
                    file.Upload()

                    if file.uploaded:
                        print(f'Uploaded success : {file["title"]}, File ID: {file["id"]}')

                        try:
                            os.remove(item_path)
                            print(f'Deleted locally: {file["title"]}')
                            beep(1, 0.1, 0.1)
                        except PermissionError:
                            print(f'File is still in use')
                    else:
                        print(f'Upload failed : {file["title"]}')
                except Exception as e:
                    print(f'Error uploading file : {str(e)}')
    print("FINISH UPLOAD IMAGE To GOOGLE DRIVE")


# Function to process user input
def process_input(user_input):
    if user_input.lower() == "1":
        beep(2, 0.1, 0.1)
        image_classification()
        # Call another function or perform some action here
    elif user_input.lower() == "2":
        beep(2, 0.1, 0.1)
        train = input("Berapa banyak gambar TRAINING yang ingin anda ambil per kategori  ? ")
        beep(2, 0.1, 0.1)
        val = input("Berapa banyak gambar VALIDATION yang ingin anda ambil per kategori  ? ")
        beep(2, 0.1, 0.1)
        image_register(train, val)
        # Call another function or perform some action here
    elif user_input.lower() == "3":
        beep(2, 0.1, 0.1)
        drive_upload()
    else:
        beep(1, 1, 1)
        print("Invalid input. Please enter 'classification' or 'register'.")


print("\nSistem Siap Digunakan ! ")
while True:
    beep(2, 0.1, 0.1)
    print(f"\n1 : classification \n2 : take \n3 : upload")
    user_choice = input("Apa yang ingin anda lakukan ? ")
    process_input(user_choice)
