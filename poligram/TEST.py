import time
import threading

stop_print_time = False
def print_time():
    while not stop_print_time:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        print(current_time)
        time.sleep(1)

def readRFID():         
    global stop_print_time
    id = input("RFID: ")
    stop_print_time = True
    print_thread.join()  # รอให้เทรด print_time สิ้นสุดการทำงาน
    return id

def main():
    global print_thread
    print_thread = threading.Thread(target=print_time)
    print_thread.start()
    time.sleep(5)
    id = readRFID()
    print("RFID:", id)

# main()

def remarksRecord(packetdata_arr, min_Tickness, max_Tickness):
    # ตรวจหาค่าความหนาที่ไม่อยู่ในช่วง
    thickness = packetdata_arr[9:19]  # ข้อมูลความหนา
    thicknessOutOfRange = False

    for index, tn in enumerate(thickness):
        print(tn)

        if(tn == "-"):
            break
        elif float(tn) <  min_Tickness or float(tn) > max_Tickness:
            # meseage_thickness +=  f"❌{index+1}) {'%.2f' % float(tn)}mm. \n"
            thicknessOutOfRange = True
        # else:
            # meseage_thickness +=  f"✅{index+1}) {'%.2f' % float(tn)}mm. \n"
    
    # meseage_alert += meseage_thickness

    print(thicknessOutOfRange)

packetdata_arr = ['16/06/2023, 13:06:20', 'ONLINE', '1.805', '1.805', None, None, 'ไม่ระบุ', 'ชลิตา', '-', '2.60', '2.59', '2.65', '2.65', '3.01', '2.99', '2.61', '2.60', '2.63', '2.65']


# remarksRecord(packetdata_arr, 2.00, 2.80)

# from __future__ import print_function
import pickle
import os.path
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors

# ตรวจสอบการเชื่อมต่อกับเซิฟเวอร์ของ google
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_DIR = 'poligram\database\credentials.json'
TOKEN_DIR = 'D:\\Project_Verified\\Github\\WeightTable-PCL\\poligram\\token.pickle'

SCRIPT_ID = "1ea3JIcR5ejz3eG4bkvYUnQKsUpgmhhXfnIERgqbJodJfanYfko_Aac2i"

def firtconnect():
    global service
    global service_script
    service = None
    service_script = None
    try:
        creds = None
        if os.path.exists(TOKEN_DIR):
            with open(TOKEN_DIR, 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_DIR, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_DIR, 'wb') as token:
                pickle.dump(creds, token)

        service = build('sheets', 'v4', credentials=creds)
        service_script = build('script', 'v1', credentials=creds)
        
        request = {
                'function': "testResponse",
                'parameters': ["test"],
                'devMode': True
            }
        
        response = service_script.scripts().run(body=request, scriptId=SCRIPT_ID).execute()
        
        print(response)

    except errors.HttpError as error:
        print(f"<<send data sheet error>> \n {error.status_code} \n") 


firtconnect()

