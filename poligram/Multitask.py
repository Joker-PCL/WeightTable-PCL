import json
import random
import re
import threading

# from __future__ import print_function
import pickle
import os.path
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors

import serial
from datetime import datetime
from time import time, sleep

# ตั้งค่า
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_DIR = 'D:\\Project_Verified\\Github\\WeightTable-PCL\\poligram\\database\\credentials.json'
TOKEN_DIR = 'D:\\Project_Verified\\Github\\WeightTable-PCL\\poligram\\token.pickle'
OFFLINE_JSON_DIR = 'D:\\Project_Verified\\Github\\WeightTable-PCL\\poligram\\database\\offline_room.json'

# ตรวจสอบการเชื่อมต่อกับเซิฟเวอร์ของ google
service = None
def firtconnect():
    global sever_conection_status
    global service
    while True:
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
            break

        except Exception as e:
            sleep(3)
            print(f"<<First connect error>> \n {e} \n")
     
# อ่านข้อมูล json
def read_json(dir):
    with open(dir, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    return jsonData

# ตรวจสอบข้อมูล offline
stop_flag = False
def checkData_offline():
    global stop_flag
    while not stop_flag:
        offline_data = read_json(OFFLINE_JSON_DIR)
        if offline_data["DATA"]:
            print(offline_data["DATA"])
        else:
            print("data is not null")
            stop_flag = True

        sleep(1)

def main():
    first_connect = threading.Thread(target=firtconnect)
    data_offline = threading.Thread(target=checkData_offline)
    first_connect.start()
    data_offline.start()

    while True:
        print(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        sleep(1)

        if stop_flag:
            data_offline.join()

import subprocess
import socket
def get_wifi_signal_windows():
    while True:
        # command = "iwconfig wlan0"
        command = "netsh wlan show interfaces"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()

        # หาบรรทัดที่มีข้อมูลเกี่ยวกับระดับสัญญานไวไฟ
        output_lines = output.decode().split("\n")
        ssid_line = next((line for line in output_lines if "SSID" in line), None)
        signal_line = next((line for line in output_lines if "Signal" in line), None)
        
        if signal_line:
            try:
                socket.create_connection(("www.google.com", 80), timeout=1)
                print("internet is connected")
            except OSError:
                print("internet in not connect")

            key, ssid_line = ssid_line.split(':')
            key, signal_line = signal_line.split(':')
            signal = signal_line.strip()
            ssid = ssid_line.strip()
            print(ssid, signal)
        
        sleep(1)

def get_wifi_signal_linux():
    while True:
        command = "iwconfig wlan0"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()

        # หาบรรทัดที่มีข้อมูลเกี่ยวกับระดับสัญญานไวไฟ
        output_lines = output.decode().split("\n")
        ssid_line = next((line for line in output_lines if "SSID" in line), None)
        signal_line = next((line for line in output_lines if "Signal level" in line), None)
        
        if signal_line:
            try:
                socket.create_connection(("www.google.com", 80), timeout=1)
                print("internet is connected")
            except OSError:
                print("internet in not connect")
                
            key, ssid_line = ssid_line.split('=')
            key, signal_line = signal_line.split('=')
            signal = signal_line.strip()
            ssid = ssid_line.strip()
            print(ssid, signal)
        
        sleep(1)

main()


