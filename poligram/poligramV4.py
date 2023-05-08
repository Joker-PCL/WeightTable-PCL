## ============================================================================##
##                              Dev.  Nattapon                                 ##
##                       Program Author and Designer                           ##
## ============================================================================##
## ต้องใช้คำสั่ง sudo su pip install google-api-python-client 
# update 16/7/2022  ส่งเวลา และวันที่ อัตโนมัติ
#                   ส่งเวลา Range ที่จะลงข้อมูลครั้งถัดไป,ส่งไลน์แจ้งเตือนเมื่อน้ำหนักไม่ได้อยู่ในช่วง
# update 08/1/2023  เพิ่มการบันทึกข้อมูลแบบ offline กรณีไม่สามารถเชื่อมต่อ internet ได้
#                   โดยไฟล์จะบันทึกไว้ใน json_dir = "/home/pi/Json_offline/data_offline.json"


import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import random
import serial
from datetime import datetime
from time import sleep
import requests

import keyboard
import json

# Libary LCD20x4
from RPLCD import *
from RPLCD.i2c import CharLCD

# Libary LED
from gpiozero import LED

# ประกาศตัวแปล จอLCD
lcd = CharLCD('PCF8574', 0x27)  # address lcd 20x4

# ประกาศตัวแปล LED
led1 = LED(24)
led2 = LED(23)
led3 = LED(22)

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_DIR = '/home/pi/Desktop/WEIGHT4/New_Weight/database/credentials.json'
TOKEN_DIR = '/home/pi/Desktop/WEIGHT4/New_Weight/token.pickle'

DATABASE_SHEETID = "1MLEcT9m76IOQVHOmwQJCfAhPi6KbjiYI7d5SBp2nbWs"
DATABASE_USER_RANGE = "User_Password!A3:F"
DATABASE_JSON_DIR = '/home/pi/Desktop/WEIGHT4/New_Weight/database/username.json'
SETTING_JSON_DIR = '/home/pi/Desktop/WEIGHT4/New_Weight/database/setting.json'
OFFLINE_JSON_DIR = '/home/pi/Desktop/WEIGHT4/New_Weight/database/offline.json'

WEIGHTTABLE_SHEETID = "1Vfy1ovKCEVWl9X3cO-M4AV9IzOmuK467IeMWragfq-o"
WEIGHTTABLE_SETTING_RANGE = "Setting!A2:A14"
WEIGHTTABLE_DATA_RANGE = "WEIGHT!A5:S"

TABLET_ID = 'T15'

# แสดงผลแบบเรียงอักษร
def textEnd(text, rows, cols):
    for i in range(len(text)):
        lcd.cursor_pos = (rows, cols+i)
        lcd.write_string(text[i])
        sleep(0.15)

# ลบอักษรหน้าจอแบบกำหนด แถว ตำแหน่ง จำนวน
def clearScreen(row, col=0, numcol=20):
    text = ""
    lcd.cursor_pos = (row, col)
    lcd.write_string(text.rjust(numcol, " "))

# ส่งไลน์แจ้งเตือน
def lineNotify(msg):
    url = 'https://notify-api.line.me/api/notify'
    token = 'p9YWBiZrsUAk7Ef9d0hLTMMF2CxIaTnRopHaGcosM4q'
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer '+token}
    requests.post(url, headers=headers, data={'message': msg})

# อ่านข้อมูล json
def read_json(dir):
    with open(dir, 'r', encoding='utf-8') as f:
        jsonData = json.load(f)
    return jsonData

# เขียนข้อมูล json
def write_json(dir, jsonData):
    with open(dir, 'w', encoding='utf-8') as f:
        json.dump(jsonData, f, ensure_ascii=False, indent=4)

# อัพเดท JSON *offline
def update_json(dir, jsonData):
    with open(dir, 'r+', encoding='utf-8') as file:
        file_data = json.load(file)
        file_data["DATA"].append(jsonData)
        file.seek(0)
        json.dump(file_data, file, indent=4, ensure_ascii=False)

# ตรวจสอบการเชื่อมต่อกับเซิฟเวอร์ของ google
def firtconnect():
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
        return service

    except Exception as e:
        print(f"<<First connect error>> \n {e} \n")
        return False

# อัพเดทฐานข้อมูลผู้ใช้งาน
def update_user_data():
    try:
        # อัพเดทรายชื่อพนักงาน
        print("Update datalist...")
        get_data = service.spreadsheets().values().get(
            spreadsheetId=DATABASE_SHEETID, range=DATABASE_USER_RANGE).execute()
        data_list = get_data["values"]

        jsonData = read_json(DATABASE_JSON_DIR)

        data_dict = []
        for data in data_list:
            data_dict.append({
                'rfid': data[0],
                'employeeID': data[1],
                'nameTH': data[2],
                'nameEN': data[3],  
                'password': data[4],
                'root': data[5],
            })

        jsonData["DATA"] = data_dict
        write_json(DATABASE_JSON_DIR, jsonData)

        # อัพเดทการตั้งค่าน้ำหนัก
        print("Update Setting datalist...")
        get_setting_data = service.spreadsheets().values().get(
            spreadsheetId=WEIGHTTABLE_SHEETID, range=WEIGHTTABLE_SETTING_RANGE).execute()
        setting_data_list = get_setting_data["values"]

        setting_jsonData = read_json(SETTING_JSON_DIR)
        
        index = 0
        for data in setting_jsonData:
            setting_jsonData[data] = setting_data_list[index][0]
            index += 1

        write_json(SETTING_JSON_DIR, setting_jsonData)
        print("<<< update success >>>", end='\n\n')

    except Exception as e:
        print(f"<<update user data error>> \n {e} \n")

# ลงชื่อเข้าใช้งาน
def login():
    try:
        jsonData = read_json(DATABASE_JSON_DIR)
        id = ""
        result = None

        def on_key_press(event):
            nonlocal id, result
            if event.name == 'enter' and len(id) == 10:
                result = list(filter(lambda item: (
                    item['rfid']) == id, jsonData["DATA"]))
                if result:
                    for key in jsonData["LOGIN"]:
                        jsonData["LOGIN"][key] = result[0][key]

                    write_json(DATABASE_JSON_DIR, jsonData)

                    # keyboard.unhook_all()  # ยกเลิกการติดตามการกดคีย์
                    return result[0]
                else:  
                    print(f"ไม่พบข้อมูล id {id}")
                    id = ""
            elif len(event.name) == 1:
                id += event.name
            else:
                id = ""

        print("<< LOGIN >>")
        print("Please scan your RFID card...")
        keyboard.on_press(on_key_press)
        keyboard.wait("enter")

        return result[0]
        
    except Exception as e:
        print(f"<<login error>> \n {e} \n")

# ลงชื่อออก
def logout():
    jsonData = read_json(DATABASE_JSON_DIR)

    for key in jsonData["LOGIN"]:
        jsonData["LOGIN"][key] = None

    write_json(DATABASE_JSON_DIR, jsonData)

# อ่านค่าน้ำหนักจากเครื่องชั่ง
def getWeight(Min_AVG=0, Max_AVG=0, Min_Control=0, Max_Control=0):
    
    dataWeight = []  # เก็บค่าน้ำหนัก
    sr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)

    while len(dataWeight) < 2:
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")  # วันที่เวลา
        Today = now.strftime("%d/%m/%Y")  # วันที่
        Time = now.strftime("%H:%M:%S")  # เวลา

        lcd.cursor_pos = (1, 4)
        lcd.write_string("<< Ready >>")
        print(str(date_time))
        print("READY:", TABLET_ID)
        
        # อ่านค่าจาก port rs232
        w = sr.readline()
        currentWeight = w.decode('ascii', errors='ignore')
        currentWeight = currentWeight.replace("?", "").strip().upper()
        currentWeight = currentWeight.replace("G", "").strip()
        currentWeight = currentWeight.replace("N", "").strip()
        currentWeight = currentWeight.replace("S", "").strip()
        currentWeight = currentWeight.replace("T,", "").strip()  # AND FX
        currentWeight = currentWeight.replace("G", "").strip()  # AND FX
        currentWeight = currentWeight.replace("+", "").strip() 
        weight = round(float(currentWeight), 3)
        
        dataWeight.append(weight)
        print(len(dataWeight),".) ",weight)
        
        lcd.cursor_pos = (1, 4)
        lcd.write_string("  Wait.... ")
        
        for i in dataWeight:
            if len(dataWeight) == 1:
                clearScreen(3, 9, 10)
                lcd.cursor_pos = (3, 0)
            else: 
                lcd.cursor_pos = (3, 11)
            lcd.write_string((str(len(dataWeight)))+".) "+str('%.3f' % weight))
            
        led1.off()
        led2.off()
        led3.off()
        sleep(0.5)

        # รีเซ็ตโปรแกรม
        if weight < 0.005:
            lcd.clear()
            lcd.cursor_pos = (0, 3)
            lcd.write_string("WEIGHT VARIATION")
            textEnd("Restart.....", 1, 5)
            print("Reset!")
            quit()

        # ไฟแสดงค่า LED1_GREEN,LED2_ORANGE,LED3_RED
        elif weight >= Min_AVG and weight <= Max_AVG:
            led1.on()
            print("ผ่าน อยู่ในช่วงที่กำหนด")
        elif weight >= Min_Control and weight <= Max_Control:
            led2.on()
            print("ผ่าน อยู่ในช่วงที่กฏหมายกำหนด")
        else:
            led3.on()
            print("ไม่ผ่าน")

        if len(dataWeight) == 2:
            weight_obj = {
                "time": date_time,
                "weight1": str('%.3f' % dataWeight[0]),
                "weight2": str('%.3f' % dataWeight[1]),
                "quantity": str('%.3f' % round(sum(dataWeight)/len(dataWeight), 3))
            }

            # Timestamp dataWeight
            dataWeight.insert(0, Time)
            return weight_obj
        else:
            pass

# function Send Data to googlesheets
def sendData_sheets(sheetRange, dataArr):
    try:
        response = service.spreadsheets().values().append(
            spreadsheetId=WEIGHTTABLE_SHEETID,
            range=sheetRange,
            body={
                "majorDimension": "ROWS",
                "values": dataArr
            },
            valueInputOption="USER_ENTERED"
        ).execute()

        print(f"{response} \n")

        return True
    
    except Exception as e:
        print(f"\n<<Send data sheets error>> \n {e} \n")
        return False

# สรุปผล
def weightSummary(status):
    Min_W = min(dataWeight[1:])
    Max_W = max(dataWeight[1:])
    AVG_W = round(sum(dataWeight[1:])/len(dataWeight[1:]), 3)
    
    lcd.clear()
    lcd.cursor_pos = (0, int((20-len(status))/2))
    lcd.write_string(status)
    lcd.cursor_pos = (1, 2)
    lcd.write_string("WEIGHT VARIATION")
    textEnd("MIN:"+str('%.3f' % Min_W), 2, 0)
    textEnd("MAX:"+str('%.3f' % Max_W), 2, 11)
    textEnd("AVG:"+str('%.3f' % AVG_W), 3, 6)
    sleep(5)

def main():
    lcd.clear()
    led1.blink()
    sleep(0.5)
    led2.blink()
    sleep(0.5)
    led3.blink()
    print("WEIGHT VARIATION")
    print("Loading....")
    textEnd("WEIGHT VARIATION", 0, 2)
    textEnd("Loading....", 1, 5)

    # ตรวจสอบการเชื่อมต่อกับเซิฟเวอร์ของ google
    global service
    service = firtconnect()
    
    # ตรวจสอบข้อมูล OFFLINE
    if service:
        print("<<<< CHECK_OFFLINE_DATA >>>>")
        offline_data = read_json(OFFLINE_JSON_DIR)
        if offline_data["DATA"]:
            print("Sending data offline...")
            dataArr = []
            for data in offline_data["DATA"]:
                data.extend(["-"] * 11) # เพิ่ม - ไปอีก 11 ตัว
                dataArr.append(data)

            status = sendData_sheets(WEIGHTTABLE_DATA_RANGE, dataArr)
            if status:
                write_json(OFFLINE_JSON_DIR, {"DATA": []})

    # อัพเดพข้อมูลรายชื่อ
    clearScreen(1)
    lcd.cursor_pos = (1, 4)
    lcd.write_string("UPDATE DATA")
    print("<<<< UPDATE_DATA >>>>")
    update_user_data()

    lcd.cursor_pos = (3, 3)
    lcd.write_string("<< SUCCESS >>")

    # ตรวจสอบสถานะ login
    try:
        result = read_json(DATABASE_JSON_DIR)["LOGIN"]
        if not result["rfid"]:
            result = login() # เข้าหน้า login
        if result:
            print(result)
            rfid = result["rfid"]
            employeeID = result["employeeID"]
            nameEN = result["nameEN"]
            nameTH = result["nameTH"]
            password = result["password"]
            root = result["root"]

            setting_data = read_json(SETTING_JSON_DIR) # อ่านข้อมูลการตั้งค่าน้ำหนัก
            if setting_data["productName"]:
                weight = getWeight(
                    float(setting_data["min"]),
                    float(setting_data["max"]),
                    float(setting_data["min_control"]),
                    float(setting_data["max_control"])) # อ่านข้อมูลน้ำหนักจากเครื่องชั่ง
            else:
                weight = getWeight()

            packetdata_arr = [
                weight["time"],
                "ONLINE",
                weight["weight1"],
                weight["weight2"],
                None,
                None,
                None,
                nameTH,
            ]

            # เพิ่ม - ไปอีก 11 ตัว
            packetdata_arr.extend(["-"] * 11) 

            status = sendData_sheets(WEIGHTTABLE_DATA_RANGE, [packetdata_arr])
            if status:
                pass
            else:
                packetdata_arr[1] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                update_json(OFFLINE_JSON_DIR, packetdata_arr[0:8]) # บันทึกข้อมูล 1-7 ไปยัง offline.json 

            logout() # ออกจากระบบ

    except Exception as e:
        print(f"<<main error>> \n {e} \n")

if __name__ == '__main__':
    main()
