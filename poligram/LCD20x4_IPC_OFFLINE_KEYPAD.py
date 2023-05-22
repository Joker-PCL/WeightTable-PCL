##============================================================================##
##                              Dev.  Nattapon                                ##
##                       Program Author and Designer                          ##
##============================================================================##
# update 23/6/2022 ส่งเวลา และวันที่ อัตโนมัติ
# update 27/6/2022 แก้ระบบ Login ระบบตรวจสอบการส่งข้อมูล ส่งไลน์แจ้งเตือนเมื่อน้ำหนักไม่ได้อยู่ในช่วง
#                  หรือโปรแกรม Error
# update 08/1/2023  เพิ่มการบันทึกข้อมูลแบบ offline กรณีไม่สามารถเชื่อมต่อ internet ได้
#                   โดยไฟล์จะบันทึกไว้ใน json_dir = "/home/pi/Json_offline/data_offline.json"

import json
import random

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

from RPLCD import *
from RPLCD.i2c import CharLCD
from gpiozero import LED, Buzzer
import RPi.GPIO as GPIO

buzzer = Buzzer(21) # BUZZER
RFID = LED(23) # RFID SWITCH
 
lcd = CharLCD('PCF8574', 0x27)  # address lcd 20x4

# LED Dotmatrix
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, TINY_FONT

serialSCR = spi(port=0, device=0, gpio=noop())
led_scr = max7219(serialSCR, cascaded=4, block_orientation=90, blocks_arranged_in_reverse_order=True)
led_scr.contrast(20)

led_passed = [0xf8, 0x58, 0x40, 0xfb,
          0x00, 0x08, 0x08, 0xf8,
          0x00, 0x18, 0xf8, 0x40,
          0xf8, 0xc0, 0x00, 0x00
        ]

led_notpass = [0x02, 0x04, 0xfe,0xc0,
           0x00, 0xd8, 0xf8, 0x40,
           0xfb, 0x00, 0xf8, 0x58,
           0x40, 0xfb, 0x00, 0x08,
           0x08, 0xf8, 0x00, 0x18,
           0xf8, 0x40, 0xf8, 0xc0
        ]
    
led_online = [0x7c, 0x44, 0x7c, 0x00, 
          0x7c, 0x08, 0x04, 0x7c, 
          0x00, 0x7c, 0x40, 0x40, 
          0x00, 0x44, 0x7c, 0x44, 
          0x00, 0x7c, 0x08, 0x04, 
          0x7c, 0x00, 0x7c, 0x54, 
          0x54, 0x00, 0x00, 0x00
        ]

led_online_th = [0x74, 0x54, 0x44, 0x7c, 
          0x00, 0x74, 0x54, 0x44, 
          0x7c, 0x00, 0x04, 0x7c, 
          0x20, 0x7c, 0x61, 0x02, 
          0x7f, 0x40, 0x00, 0x74, 
          0x54, 0x14, 0x7c, 0x00, 
          0x04, 0x7c, 0x20, 0x7d, 
          0x61, 0x00, 0x00, 0x00
        ]

led_offline = [0x7c, 0x44, 0x7c, 0x00, 
          0x7c, 0x14, 0x14, 0x00, 
          0x7c, 0x14, 0x14, 0x00, 
          0x7c, 0x40, 0x40, 0x00, 
          0x44, 0x7c, 0x44, 0x00, 
          0x7c, 0x08, 0x04, 0x7c, 
          0x00, 0x7c, 0x54, 0x54
        ]

led_offline_th = [0x74, 0x54, 0x44, 0x7c, 
          0x00, 0x74, 0x54, 0x44, 
          0x7c, 0x00, 0x04, 0x7c, 
          0x20, 0x20, 0x7f, 0x00, 
          0x01, 0x02, 0x7f, 0x40, 
          0x00, 0x74, 0x54, 0x14, 
          0x7c, 0x00, 0x04, 0x7c, 
          0x20, 0x7d, 0x61, 0x00
        ]

# ตั้งค่า
LINE_TOKEN = 'XGeivDcekfbgCYH9eNi2rCbDU9jSpktLm6FZsAcTLs0'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_DIR = '/home/pi/Desktop/poligram/database/credentials.json'
TOKEN_DIR = '/home/pi/Desktop/poligram/token.pickle'

DATABASE_SHEETID = "1MLEcT9m76IOQVHOmwQJCfAhPi6KbjiYI7d5SBp2nbWs"
DATABASE_USER_RANGE = "User_Password!A3:F"
DATABASE_JSON_DIR = '/home/pi/Desktop/poligram/database/username.json'
SETTING_JSON_DIR = '/home/pi/Desktop/poligram/database/setting_ipc.json'
OFFLINE_JSON_DIR = '/home/pi/Desktop/poligram/database/offline_ipc.json'

WEIGHTTABLE_SETTING_RANGE = "Setting!A3:A18"
WEIGHTTABLE_DATA_NAME = "Weight Variation!"
WEIGHTTABLE_REMARKS_RANGE = "Remark!A3:F"

# ข้อมูล SHEETID ของ google sheet
TABLET_LIST = [
    {
        "TABLET_ID": "T11" ,
        "SHEET_ID": "1xQ9fZtQycxQFzKZ0YPS6Jh8n0ma55JSw8cDj1Jhk8yE",
        "SCRIPT_ID": "1gXG8FA3xad1jy0Z8NB8980tFUxXP1_KY1FAU1eokKsgye26BOx-bc3bl"
    },
    {
        "TABLET_ID": "T15" ,
        "SHEET_ID": "1_plXAUFWopvnAbeIe7QKTgr8HwhKMQsyGHy0iwbuQIQ",
        "SCRIPT_ID": "12Ze7g9jIBSxdwH_6z17ehfDwPTCxKJgV436PlOd_6KqaKb_z_Gx2kmkC"
    }
]

keypad_rows = [22, 27, 18, 17]
keypad_cols = [20, 16, 26, 19]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for i in range(len(keypad_rows)):
    GPIO.setup(keypad_rows[i], GPIO.OUT)
    GPIO.setup(keypad_cols[i], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

keypad = [["1", "2", "3", "A"],
          ["4", "5", "6", "B"],
          ["7", "8", "9", "C"],
          [".", "0", ".", "D"]]

# แสดงข้อความ dot matrix
def dotmatrix(draw, xy, txt, fill=None):
    x, y = xy
    for byte in txt:
        for j in range(8):
            if byte & 0x01 > 0:
                draw.point((x, y + j), fill=fill)

            byte >>= 1
        x += 1

# อ่านค่า KEYPAD 4x4
def readKeypad(Message):
    currentMillis = 0
    previousMillis = 0
    Timer = 60  # settimeout sec.
    keypad_cache = ""
    text = f"{Message}:"
    lcd.cursor_pos = (3, 0)
    lcd.write_string(text.ljust(20))

    while Timer:
        for i in range(len(keypad_rows)):
            gpio_out = keypad_rows[i]
            GPIO.output(gpio_out, GPIO.HIGH)

            for x in range(len(keypad_cols)):
                gpio_in = keypad_cols[x]
                # on GPIO checkkey 
                if (GPIO.input(gpio_in) == 1):
                    buzzer.beep(0.1, 0.1, 1)
                    key = keypad[i][x]
                    Timer = 60

                    if key == "*" or  key == "#":
                        quit()
                    elif key == "D" and keypad_cache:
                        keypad_cache = keypad_cache[0:-1] # ลบ
                    elif key != "A" and key != "B" and key != "C" and key != "D" and len(keypad_cache) < 2:
                        keypad_cache = keypad_cache+key
                    elif key == "C" and keypad_cache:
                        return keypad_cache
                    else:
                        pass

                    text = f"{Message}: {keypad_cache}"
                    text = text.ljust(20)
                    lcd.cursor_pos = (3, 0)
                    lcd.write_string(text)
                    sleep(0.3)

            # off GPIO checkkey            
            GPIO.output(gpio_out, GPIO.LOW)

        # จับเวลา
        currentMillis = time()
        if currentMillis - previousMillis > 1:
            previousMillis = currentMillis
            printScreen(2, f"{Timer}s.")
            Timer -= 1
            # timeout
            if not Timer:
                quit()

# ตรวจสอบ ID Sheets
def checkSheetID(TABLET_ID):
    result = list(filter(lambda item: (item['TABLET_ID']) == TABLET_ID, TABLET_LIST))
    if(result):
        return result[0]
    else:
        return False

# แสดงผลค่าน้ำหนัก
def screen(total_weight, weight):
    for i in range(0, 50, 6):
        if len(total_weight) == i+1:
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+2:
            lcd.cursor_pos = (2, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+3:
            lcd.cursor_pos = (3, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+4:
            lcd.cursor_pos = (1, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+5:
            lcd.cursor_pos = (2, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+6:
            lcd.cursor_pos = (3, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            break
        else:
            continue

# แสดงผลหน้าจอ
def printScreen(row, text):
    clearScreen(row)
    lcd.cursor_pos = (row, int((20-len(text))/2))
    lcd.write_string(text)

# แสดงผลแบบเรียงอักษร
def textEnd(row, text):
    clearScreen(row)
    for i in range(len(text)):
        lcd.cursor_pos = (row, int((20-len(text))/2)+i)
        lcd.write_string(text[i])
        sleep(0.15)

# ลบอักษรหน้าจอแบบกำหนด แถว ตำแหน่ง จำนวน
def clearScreen(row, col=0, numcol=20):
    text = ""
    lcd.cursor_pos = (row, col)
    lcd.write_string(text.rjust(numcol, " "))

# ส่งไลน์แจ้งเตือน
def lineNotify(Message):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer '+LINE_TOKEN}
    requests.post(url, headers=headers, data={'message': Message})

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
    global service
    global service_script

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
        return True

    except Exception as e:
        print(f"<<First connect error>> \n {e} \n")
        return False

# ตรวจสอบข้อมูล offline
def checkData_offline():
    offline_data = read_json(OFFLINE_JSON_DIR)
    offline_data = offline_data["DATA"]

    if offline_data:
        deleted_cache = []  # สร้างลิสต์ที่จะเก็บ _data ที่จะลบออก
        tabletName_cache = [] # สร้างรายชื่อเครื่องตอกที่ถูกส่งข้อมูล offline
        Timestamp_offline = offline_data[0]["TIMESTAMP"]

        try: 
            for _data in offline_data:
                print("Sending data offline...")
                textEnd(3, "Sending data...")
                WEIGHTTABLE_SHEETID = checkSheetID(_data["TABLET_ID"])  # หาข้อมูลจากเลขเครื่องตอก
                SCRIPT_ID = WEIGHTTABLE_SHEETID["SCRIPT_ID"] # SCRIPT ID
                SHEET_ID = WEIGHTTABLE_SHEETID["SHEET_ID"] # SHEET ID
                GET_CURRENT_RANGE = getData_sheets(SHEET_ID, WEIGHTTABLE_SETTING_RANGE) # ตำแหน่งปัจจุบัน

                if GET_CURRENT_RANGE:
                    CURRENT_RANGE = GET_CURRENT_RANGE[0][0]
                    # ข้อมูล
                    DATA_LIST = {
                        "CURRENT_RANGE": CURRENT_RANGE,
                        "TIMESTAMP": _data["TIMESTAMP"],
                        "SIGNATURE": _data["SIGNATURE"],
                        "WEIGHT":  _data["WEIGHT"],
                        "TYPE": _data["TYPE"]
                    }

                    sendData_sheets(SCRIPT_ID, DATA_LIST) # ส่งข้อมูล

                    tabletName_cache.append(_data["TABLET_ID"]) # เก็บหมายเลขเครื่องตอกที่ถูกส่งข้อมูล offline
                    deleted_cache.append(_data) # เก็บ _data ไว้ในลิสต์ที่จะลบ

                else:
                    return "failed"
        
            if deleted_cache:
                # ลบ _data ที่ถูกเก็บไว้ในลิสต์ to_be_deleted ออกจาก offline_data
                for _data in deleted_cache:
                    offline_data.remove(_data)
                write_json(OFFLINE_JSON_DIR, {"DATA": offline_data})   

                tabletName_cache = list(set(tabletName_cache)) # ลบรายการเครื่องตอกที่ซ้ำออก
                tablet_msg = ', '.join([str(num) for num in tabletName_cache]) # รายชื่อเครื่องตอกที่ถูกส่งข้อมูล offline     
                msg_Notify = '\n🔰 มีข้อมูล offline เพิ่มเข้ามาไหม่ \n' +\
                    '🔰 ระบบเครื่องชั่ง IPC \n' +\
                    '🔰 เครื่องตอก: '+ tablet_msg + '\n' +\
                    '❎ ขาดการเชื่อมต่อ \n  ' +\
                    Timestamp_offline + '\n' +\
                    '✅ เชื่อมต่ออีกครั้ง \n  ' +\
                    datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                    
                # ส่งไลน์แจ้งเตือน
                lineNotify(msg_Notify)

                print("<<< send data success >>>", end='\n\n')
                textEnd(3, "<<Success>>")

        except Exception as e:
                print(f"\n<< checkData offline >> \n {e} \n")    
                textEnd(3, "<<Failed!>>")

# อัพเดทฐานข้อมูลผู้ใช้งาน
def update_user_data():
    try:
        # อัพเดทรายชื่อพนักงาน
        print("Update datalist...")
        textEnd(3, "Update datalist...")
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

        print("<<< update success >>>", end='\n\n')
        textEnd(3, "Success")

    except Exception as e:
        print(f"<<update user data error>> \n {e} \n")
        textEnd(3, "<<Failed!>>")

# อัพเดทฐานข้อมูลการตั้งค่า
def update_setting_data(WEIGHTTABLE_LIST):
        try:
            SHEETID = WEIGHTTABLE_LIST["SHEET_ID"]
            TABLET_ID = WEIGHTTABLE_LIST["TABLET_ID"]
        
            # อัพเดทการตั้งค่าน้ำหนัก
            print("Update Setting datalist...")
            textEnd(3, "Update Setting...")
            get_setting_data = service.spreadsheets().values().get(
                spreadsheetId=SHEETID, range=WEIGHTTABLE_SETTING_RANGE).execute()
            setting_data_list = get_setting_data["values"]

            setting_jsonData = read_json(SETTING_JSON_DIR)
            
            # ตรวจหาข้อมูล
            matching_tablet = next((item for item in setting_jsonData['SETTING'] if item['tabletID'] == str(TABLET_ID)), None)

            # ตรวจสอบผลลัพธ์setting_temp
            if matching_tablet is not None:
                for index, data in enumerate(matching_tablet):
                    matching_tablet[data] = setting_data_list[index][0]
            else:
                setting_temp = { 
                    "current_range": None,
                    "tabletID": None,
                    "scaleID": None,
                    "productName": None,
                    "pastle": None,
                    "Lot": None,
                    "number_tablets": None,
                    "weight_control,": None,
                    "percent": None,
                    "min": None,
                    "max": None,
                    "min_control": None,
                    "max_control": None,
                    "min_dvt": None,
                    "max_dvt": None,
                    "admin_set": None
                }
                
                for index, key in enumerate(setting_temp):
                    setting_temp[key] = setting_data_list[index][0]

                setting_jsonData["SETTING"].append(setting_temp)

            print(setting_jsonData)
            write_json(SETTING_JSON_DIR, setting_jsonData)
            print("<<< update success >>>", end='\n\n')
            textEnd(3, "Success")

        except Exception as e:
            print(f"<<update user data error>> \n {e} \n")
            textEnd(3, "<<Failed!>>")

# ลงชื่อเข้าใช้งาน
def login():
    try:
        jsonData = read_json(DATABASE_JSON_DIR)
        print("<< LOGIN >>")
        print("Please scan your RFID card...")
        
        RFID.on() # เปิดการทำงาน RFID Reader

        while True:
            printScreen(1, "<< LOGIN >>")
            printScreen(3, "...RFID SCAN...")

            id = input("RFID: ")
            buzzer.beep(0.1, 0.1, 1)
            printScreen(1,f"ID: {id}")

            result = list(filter(lambda item: (
                        item['rfid']) == id, jsonData["DATA"]))
            if result:
                for key in jsonData["LOGIN_IPC"]:
                    jsonData["LOGIN_IPC"][key] = result[0][key]

                write_json(DATABASE_JSON_DIR, jsonData)
                printScreen(3, result[0]["nameEN"])
                sleep(1)
                RFID.off() # ปิดการทำงาน RFID Reader
                return result[0]
            
            else:
                buzzer.beep(0.1, 0.1, 5)
                print(f"ไม่พบข้อมูล id {id}")
                printScreen(3, "id not found")
                sleep(1)

    except Exception as e:
        print(f"<<login error>> \n {e} \n")

# ลงชื่อออก
def logout():
    jsonData = read_json(DATABASE_JSON_DIR)

    for key in jsonData["LOGIN_IPC"]:
        jsonData["LOGIN_IPC"][key] = None

    write_json(DATABASE_JSON_DIR, jsonData)

# function Get Data from googlesheets
def getData_sheets(SHEETID, RANGE):
    try:
        get_data = service.spreadsheets().values().get(
            spreadsheetId=SHEETID, range=RANGE).execute()
        data_list = get_data["values"]
        
        return data_list

    except Exception as e:
        print(f"<<get data sheet error>> \n {e} \n")
        return False

# function Send Data to googlesheets
def sendData_sheets(SCRIPT_ID, DATA_LIST):
    try:
        request = {
            'function': "reciveData",
            'parameters': [DATA_LIST],
            'devMode': True
        }
        response = service_script.scripts().run(body=request, scriptId=SCRIPT_ID).execute()
        
        print(response)
        return response
    
    except errors.HttpError as error:
        print(f"<<send data sheet error>> \n {error.content} \n") 
        return False
    
# อ่านค่าน้ำหนักจากเครื่องชั่ง
def getWeight(USERNAME, TABLET_ID, Max_Tab, Min_AVG=0, Max_AVG=0, Min_Control=0, Max_Control=0):
    
    dataWeight = []  # เก็บค่าน้ำหนัก
    sr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)

    while len(dataWeight) < int(Max_Tab):
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")  # วันที่เวลา
        Today = now.strftime("%d/%m/%Y")  # วันที่
        Time = now.strftime("%H:%M:%S")  # เวลา

        printScreen(0, "<< Ready >>")
        print(f"\n{str(date_time)}")
        print("READY:", TABLET_ID)
        sleep(0.2)

        # อ่านค่าจาก port rs232
        w = sr.readline()
        # currentWeight = str(random.uniform(0.170,0.210))
        currentWeight = w.decode('ascii', errors='ignore')
        currentWeight = currentWeight.replace("?", "").strip().upper()
        currentWeight = currentWeight.replace("G", "").strip()
        currentWeight = currentWeight.replace("N", "").strip()
        currentWeight = currentWeight.replace("S", "").strip()
        currentWeight = currentWeight.replace("T,", "").strip()  # AND FX
        currentWeight = currentWeight.replace("G", "").strip()  # AND FX
        currentWeight = currentWeight.replace("+", "").strip() 
        weight = round(float(currentWeight), 3)
        
        printScreen(0, "Wait.... ")

        Timestamp = datetime.now().strftime("%H:%M:%S")
        dataWeight.append([Timestamp, weight])
        print(str(len(dataWeight))+")"+str(weight))
        screen(dataWeight, '%.3f' % weight)
        buzzer.beep(0.1, 0.1, 1)

        with canvas(led_scr) as draw:
            text(draw, (7, 0), '%.3f' % weight, fill="red", font=proportional(TINY_FONT))
        
        sleep(0.5)

        # รีเซ็ตโปรแกรม
        if weight < 0.005:
            lcd.clear()
            printScreen(0, "WEIGHT VARIATION")
            textEnd(1, "Restart.....")
            print("Reset!")
            quit()

        if Min_AVG and Max_AVG and Min_Control and Max_Control:
            # ไฟแสดงค่า LED1_GREEN,LED2_ORANGE,LED3_RED
            if weight >= Min_AVG and weight <= Max_AVG:
                print("ผ่าน อยู่ในช่วงที่กำหนด")
            elif weight >= Min_Control and weight <= Max_Control:
                with canvas(led_scr) as draw:
                    dotmatrix(draw, (4, 0), led_notpass, fill="red")
                buzzer.beep(0.1, 0.1, 5, background=False)
                print("ผ่าน อยู่ในช่วงที่กฏหมายกำหนด")
            else:
                with canvas(led_scr) as draw:
                    dotmatrix(draw, (4, 0), led_notpass, fill="red")
                buzzer.beep(0.1, 0.1, 5, background=False)
                print("ไม่ผ่าน")

    weight_obj = {
        "TABLET_ID": TABLET_ID,
        "TIMESTAMP": date_time,
        "SIGNATURE": USERNAME,
        "TYPE": "ONLINE",
        "WEIGHT": dataWeight
    }

    sleep(2)
    led_scr.clear()
    return weight_obj

# สรุปผล
def weightSummary(Min_W=0, Max_W=0, AVG_W=0, status=None):
    if status == "OFFLINE":
        buzzer.beep(0.5, 0.5, 5)
        with canvas(led_scr) as draw:
                dotmatrix(draw, (1, 0), led_offline_th, fill="red")
    elif status == "ONLINE":
        with canvas(led_scr) as draw:
                dotmatrix(draw, (2, 0), led_online_th, fill="red")

    lcd.clear()
    printScreen(0, "WEIGHT VARIATION")
    printScreen(1, f"<< {status} >>")
    textEnd(2, "MIN:"+ str('%.3f' % Min_W) + "  " + "MAX:" + str('%.3f' % Max_W))
    textEnd(3, "AVG:"+str('%.3f' % AVG_W))
    sleep(5)

# โปรแกรมหลัก
def main():
    with canvas(led_scr) as draw:
        text(draw, (4, 0), "PCL V.4", fill="red", font=proportional(TINY_FONT))

    logout() # ล้างข้อมูลผู้ใช้งาน
    lcd.clear()
    print("WEIGHT VARIATION")
    print("Loading....")
    textEnd(0, "WEIGHT VARIATION")
    textEnd(1, "Loading....")

    # ตรวจสอบการเชื่อมต่อกับเซิฟเวอร์ของ google
    firtconnect()
    
    # ตรวจสอบข้อมูล OFFLINE
    printScreen(1, "CHECK DATA OFFLINE")
    print("<<<< CHECK DATA OFFLINE >>>>")
    checkData_offline()

    # อัพเดพข้อมูลรายชื่อ
    printScreen(0, "WEIGHT VARIATION")
    printScreen(1, "UPDATE DATA LIST")
    print("<<<< UPDATE DATA >>>>")
    update_user_data()

    printScreen(3, "<< SUCCESS >>")

    try:
        result = read_json(DATABASE_JSON_DIR)["LOGIN_IPC"]
        # ตรวจสอบสถานะ login
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

            WEIGHTTABLE_LIST = False # ตรวจสอบความถูกต้องของหมายเลขเครื่องตอก
            while not WEIGHTTABLE_LIST:
                # อัพเดพข้อมูลรายชื่อ
                printScreen(1, "SELECT TABLET ID")
                # ป้อนหมายเลขเครื่องตอก
                TABLET_ID = readKeypad("TabletID")
                TABLET_ID = f"T{TABLET_ID}"
                # TABLET_ID = input("TabletID: ")
                WEIGHTTABLE_LIST = checkSheetID(TABLET_ID)
                if not WEIGHTTABLE_LIST:
                    printScreen(3, "Tablet not found")
                    buzzer.beep(0.1, 0.1, 5)
                    sleep(1)

            printScreen(2, TABLET_ID)
            update_setting_data(WEIGHTTABLE_LIST) # อัพเดทฐานข้อมูลการตั้งค่า

            # ตรวจหาข้อมูล
            get_setting_data = read_json(SETTING_JSON_DIR) # อ่านข้อมูลการตั้งค่าน้ำหนัก
            setting_data = next((item for item in get_setting_data['SETTING'] if item['tabletID'] == str(TABLET_ID)), None)
            print("Setting_DATA:", setting_data)

            # มีข้อมูลการตั้งค่าน้ำหนักยา
            if setting_data:
                # ค่า min,max ที่กำหนด
                Max_Tab = setting_data["number_tablets"]
                Min = float(setting_data["min"])
                Max = float(setting_data["max"])
                Min_CONTROL = float(setting_data["min_control"])
                Max_CONTROL = float(setting_data["max_control"])
                Min_DVT = float(setting_data["min_dvt"])
                Max_DVT = float(setting_data["max_dvt"])

                lcd.clear() # เคลียร์หน้าจอ
                weight = getWeight(nameTH, TABLET_ID, Max_Tab, Min, Max, Min_DVT, Max_DVT) # อ่านข้อมูลน้ำหนักจากเครื่องชั่ง
            else:
                # ป้อนจำนวนเม็ดที่ต้องชั่ง
                printScreen(1, "SELECT TABLET ID")
                Max_Tab = readKeypad("AMOUNT")
                sleep(1)
                # Max_Tab = input("AMOUNT: ")
                lcd.clear() # เคลียร์หน้าจอ
                weight = getWeight(nameTH, TABLET_ID, Max_Tab)        

            # ค่า min,max,avg ของน้ำหนักที่ชั่ง
            weight_cache = []
            for weight_record in weight["WEIGHT"]:
                weight_cache.append(float(weight_record[1]))

            Min_W = min(weight_cache)
            Max_W = max(weight_cache)
            AVG_W = round(sum(weight_cache)/len(weight_cache), 3)
            
            WEIGHTTABLE_SHEETID = checkSheetID(TABLET_ID) # หาข้อมูลจากเลขเครื่องตอก
            SCRIPT_ID = WEIGHTTABLE_SHEETID["SCRIPT_ID"] # SCRIPT ID
            SHEET_ID = WEIGHTTABLE_SHEETID["SHEET_ID"] # SHEET ID
            GET_CURRENT_RANGE = getData_sheets(SHEET_ID, WEIGHTTABLE_SETTING_RANGE) # ตำแหน่งปัจจุบัน
            print(GET_CURRENT_RANGE)
            
            lineAlert = False # สถานะการส่งไลน์

            if GET_CURRENT_RANGE:
                CURRENT_RANGE = GET_CURRENT_RANGE[0][0]
                # ข้อมูล
                DATA_LIST = {
                    "TYPE": weight["TYPE"],
                    "CURRENT_RANGE": CURRENT_RANGE,
                    "TIMESTAMP": weight["TIMESTAMP"],
                    "SIGNATURE": weight["SIGNATURE"],
                    "WEIGHT":  weight["WEIGHT"]
                }

                lcd.clear() # ล้างหน้าจอ
                checkData_offline() # ตรวจสอบและส่งข้อมูล offline
                textEnd(3, "Sending data....")
                status = sendData_sheets(SCRIPT_ID, DATA_LIST) # ส่งข้อมูลไปยัง google sheet
                if status:
                    lineAlert = True # สถานะการส่งไลน์
                else:
                    weight["TYPE"] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                    update_json(OFFLINE_JSON_DIR, weight) # offline.json 
            else:
                weight["TYPE"] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                update_json(OFFLINE_JSON_DIR, weight) # offline.json 
            
            # สรุปผล
            weightSummary(Min_W, Max_W, AVG_W, weight["TYPE"])
            
            # แจ้งเตือนไลน์
            if lineAlert:
                if AVG_W >= Min and AVG_W <= Max:
                    averageOutOfRange = False
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_passed, fill="red")
                    textEnd(1, "<<Very Good>>")
                elif AVG_W >= Min_DVT and AVG_W <= Max_DVT:
                    averageOutOfRange = True
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_notpass, fill="red")
                    
                    buzzer.beep(0.5, 0.5, 5)
                    textEnd(1, "<<Failed!>>")
                else:
                    averageOutOfRange = True
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_notpass, fill="red")

                    buzzer.beep(0.5, 0.5, 5)
                    textEnd(1, "<<Failed!>>")

                timestamp_alert = str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
                weightOutOfRange = [] # เก็บรายการเม็ดที่ไม่อยู่ในช่วง
                for w in weight["WEIGHT"]:
                    if w[-1] < Min or w[-1] > Max:
                        w[-1] = str('%.3f' % w[-1])
                        weightOutOfRange.append(w)

                # รายการเม็ดที่ไม่ได้อยู่ในช่วงที่กำหนด
                if weightOutOfRange:
                    weightOutOfRange = '\n'.join([str(item) for item in weightOutOfRange])  
                    weightOutOfRange = f"❎เม็ดที่ไม่ได้อยู่ในช่วงที่กำหนด\n{weightOutOfRange}"

                # ค่าเฉลี่ยไม่ได้อยู่ในช่วงที่กำหนด
                if averageOutOfRange:
                    averageOutOfRange = f"🔰ค่าเฉลี่ย {'%.3f' % AVG_W}g."
                   
                productName = setting_data["productName"]
                lot = setting_data["Lot"]
                if weightOutOfRange or averageOutOfRange:
                    if not weightOutOfRange:
                        weightOutOfRange = ""
                    if not averageOutOfRange:
                        averageOutOfRange = ""

                    meseage_alert = f"\n {timestamp_alert} \n" +\
                        "🔰ระบบเครื่องชั่ง IPC \n" +\
                        f"🔰เครื่องตอก: {TABLET_ID} \n" +\
                        f"🔰ชื่อยา: {productName} \n" +\
                        "🔰Lot. " + str(lot) + "\n" +\
                        "✅ช่วงที่กำหนด \n" +\
                        f"({'%.3f' % Min_DVT}g. - {'%.3f' % Max_DVT}g.) \n" +\
                        f"{weightOutOfRange} \n" +\
                        f"{averageOutOfRange}"
                    
                    # ส่งไลน์แจ้งเตือนค่าน้ำหนักที่ไม่ผ่านเกณฑ์
                    lineNotify(meseage_alert)

                    # ส่งบันทึกค่าน้ำหนักที่ไม่ผ่านเกณฑ์
                    response = service.spreadsheets().values().append(
                        spreadsheetId=SHEET_ID,
                        range=WEIGHTTABLE_REMARKS_RANGE,
                        body={
                            "majorDimension": "ROWS",
                            "values": [[
                                timestamp_alert, 
                                "✅ช่วงที่กำหนด \n" +\
                                f"({'%.3f' % Min_DVT}g. - {'%.3f' % Max_DVT}g.) \n" +\
                                f"{weightOutOfRange} \n {averageOutOfRange}"
                            ]]
                        },
                        valueInputOption="USER_ENTERED"
                    ).execute()
                
    except Exception as e:
        print(f"<<main error>> \n {e} \n")

if __name__ == '__main__':
    main()