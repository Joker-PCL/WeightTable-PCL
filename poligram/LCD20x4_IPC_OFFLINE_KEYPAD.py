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

buzzer = Buzzer(12)

lcd = CharLCD('PCF8574', 0x27)  # address lcd 20x4
led1 = LED(27)  # red
led2 = LED(22)  # yellow
led3 = LED(23)  # green

# LED Dotmatrix
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, TINY_FONT

serialSCR = spi(port=0, device=0, gpio=noop())
led_scr = max7219(serialSCR, cascaded=4, block_orientation=90, blocks_arranged_in_reverse_order=True)
led_scr.contrast(10)

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
CURRENT_DATA_RANGE = "Setting!A3"

# ข้อมูล SHEETID ของ google sheet
TABLET_LIST = [
    {
        "TABLET_ID": "11" ,
        "SHEETID": "1xQ9fZtQycxQFzKZ0YPS6Jh8n0ma55JSw8cDj1Jhk8yE",
        "SCRIPT_ID": "AKfycbz3ewnHJMnv7NU_714IF5D_kFf-M0a6ZRKM3snDWDSTiNPor925JhtrQ3lYI-UZEmFi"
    },
    {
        "TABLET_ID": "15" ,
        "SHEETID": "1xQ9fZtQycxQFzKZ0YPS6Jh8n0ma55JSw8cDj1Jhk8yE",
        "SCRIPT_ID": "AKfycbz3ewnHJMnv7NU_714IF5D_kFf-M0a6ZRKM3snDWDSTiNPor925JhtrQ3lYI-UZEmFi"
    }
]

# ตำแหน่งการบันทึกข้อมูล
RANGE_LIST = [
    {
        "data_range": "A19:B68",
        "timestamp": "A17",
        "signature": "B76"
    },
    {
        "data_range": "D19:E68",
        "timestamp": "D17",
        "signature": "E76"
    },
    {
        "data_range": "G19:H68",
        "timestamp": "G17",
        "signature": "H76"
    },
    {
        "data_range": "J19:K68",
        "timestamp": "J17",
        "signature": "K76"
    }
]

keypad_rows = [26, 16, 20, 21]
keypad_cols = [5, 6, 13, 19]

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

for i in range(len(keypad_rows)):
    GPIO.setup(keypad_rows[i], GPIO.OUT)
    GPIO.setup(keypad_cols[i], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

keypad = [["1", "2", "3", "A"],
          ["4", "5", "6", "B"],
          ["7", "8", "9", "C"],
          ["", "0", "", "D"]]

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
def readKeypad():
    currentMillis = 0
    previousMillis = 0
    Timer = 60  # settimeout sec.
    keypad_cache = ""

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

                    if key == "D" and keypad_cache:
                        keypad_cache = keypad_cache[0:-1] # ลบ
                    elif key != "A" and key != "B" and key != "C" and key != "D":
                        keypad_cache = keypad_cache+key
                    elif key == "C" and keypad_cache:
                        return keypad_cache
                    else:
                        pass

                    text = keypad_cache
                    text.ljust(10-len(text))
                    lcd.cursor_pos = (2, 10)
                    lcd.write_string(text)
                    sleep(0.3)

            # off GPIO checkkey            
            GPIO.output(gpio_out, GPIO.LOW)

        # จับเวลา
        currentMillis = time()
        if currentMillis - previousMillis > 1:
            previousMillis = currentMillis
            Timeout = str(Timer)+"s"
            if Timer < 10:
                Timeout  = " "+str(Timer)+"s"
            lcd.cursor_pos = (2, int((20-len(Timeout))/2))
            lcd.write_string(Timeout)
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

# ส่งตำแหน่งที่จะพิมพ์ในครั้งถัดไป
def nextRange(RangeName):
    current_range = next((i for i, item in enumerate(RANGE_LIST) if item['data_range'] == RangeName), None)
    next_range = RANGE_LIST[(current_range + 1) % len(RANGE_LIST)] if current_range is not None else None
    return next_range

# แสดงผลค่าน้ำหนัก
def screen(total_weight, weight):
    for i in range(0, 50, 6):
        if len(total_weight) == i+1:
            lcd.clear()
            lcd.cursor_pos = (1, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
            break
        if len(total_weight) == i+2:
            lcd.cursor_pos = (2, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
            break
        if len(total_weight) == i+3:
            lcd.cursor_pos = (3, 0)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
            break
        if len(total_weight) == i+4:
            lcd.cursor_pos = (1, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
            break
        if len(total_weight) == i+5:
            lcd.cursor_pos = (2, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
            break
        if len(total_weight) == i+6:
            lcd.cursor_pos = (3, 12)
            lcd.write_string(str(len(total_weight))+")"+str(weight))
            print(str(len(total_weight))+")"+str(weight))
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
                textEnd(3, "Sending data..")
                WEIGHTTABLE_SHEETID = checkSheetID(_data["TABLET_ID"]) # หาข้อมูลจากเลขเครื่องตอก
                SHEETID = WEIGHTTABLE_SHEETID["SHEETID"]
                CURRENT_RANGE = getData_sheets(SHEETID, WEIGHTTABLE_SETTING_RANGE)
                NEXT_RANGE = nextRange(CURRENT_RANGE[0][0])

                updateDATA_sheets(SHEETID, CURRENT_DATA_RANGE, NEXT_RANGE["data_range"])
                updateDATA_sheets(SHEETID, WEIGHTTABLE_DATA_NAME+NEXT_RANGE["timestamp"],  _data["TIMESTAMP"])
                updateDATA_sheets(SHEETID, WEIGHTTABLE_DATA_NAME+NEXT_RANGE["signature"], _data["SIGNATURE"])
                sendData_sheets(SHEETID, WEIGHTTABLE_DATA_NAME+NEXT_RANGE["data_range"], _data["WEIGHT"])

                tabletName_cache.append(_data["TABLET_ID"])
                deleted_cache.append(_data) # เก็บ _data ไว้ในลิสต์ที่จะลบ

                # เช็คข้อมูลว่าเต็มแผ่นงานหรือไม่
                if RANGE_LIST[-1]["data_range"] == NEXT_RANGE["data_range"]:
                    newSheet(WEIGHTTABLE_SHEETID["SCRIPT_ID"]) # สร้าง sheet ไหม่,เคลียร์ sheet

        
            if deleted_cache:
                # ลบ _data ที่ถูกเก็บไว้ในลิสต์ to_be_deleted ออกจาก offline_data
                for _data in deleted_cache:
                    offline_data.remove(_data)
                write_json(OFFLINE_JSON_DIR, {"DATA": offline_data})   

                tablet_msg = ', '.join(['T' + str(num) for num in tabletName_cache]) # รายชื่อเครื่องตอกที่ถูกส่งข้อมูล offline     
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

# สร้าง sheet ไหม่,เคลียร์ sheet โดยการรัน script ของ google appscript
def newSheet(script_id):
    try:
        request = {
            'function': "duplicate",
            'parameters': [],
            'devMode': True
        }
        response = service_script.scripts().run(body=request, scriptId=script_id).execute()
        print(response)
    except errors.HttpError as error:
        print(error.content)

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
def update_setting_data():
    WEIGHTTABLE_SHEETID = checkSheetID(tabletID) # หาข้อมูลจากเลขเครื่องตอก
    SHEETID = WEIGHTTABLE_SHEETID["SHEETID"]
    try:
        # อัพเดทการตั้งค่าน้ำหนัก
        print("Update Setting datalist...")
        get_setting_data = service.spreadsheets().values().get(
            spreadsheetId=SHEETID, range=WEIGHTTABLE_SETTING_RANGE).execute()
        setting_data_list = get_setting_data["values"]

        setting_jsonData = read_json(SETTING_JSON_DIR)
        
        # ตรวจหาข้อมูล
        matching_tablet = next((item for item in setting_jsonData['SETTING'] if item['tabletID'] == str(tabletID)), None)

        # ตรวจสอบผลลัพธ์
        if matching_tablet is not None:
            for index, data in enumerate(matching_tablet):
                matching_tablet[data] = setting_data_list[index][0]
        else:
            setting_key = { 
                "current_range": None,
                "tabletID": None,
                "scaleID": None,
                "productName": None,
                "pastle": None,
                "Lot": None,
                "number_tablets,": None,
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
            
            for index, key in enumerate(setting_key):
                setting_key[key] = setting_data_list[index][0]

            setting_jsonData["SETTING"].append(setting_key)

        print(setting_jsonData)
        write_json(SETTING_JSON_DIR, setting_jsonData)
        print("<<< update success >>>", end='\n\n')
        # textEnd(3, "Success")

    except Exception as e:
        print(f"<<update user data error>> \n {e} \n")
        # textEnd(3, "<<Failed!>>")

# ลงชื่อเข้าใช้งาน
def login():
    try:
        jsonData = read_json(DATABASE_JSON_DIR)
        print("<< LOGIN >>")
        print("Please scan your RFID card...")
        
        while True:
            printScreen(1, "<< LOGIN >>")
            printScreen(3, "...RFID SCAN...")

            id = input("RFID: ")
            printScreen(1,f"ID: {id}")

            result = list(filter(lambda item: (
                        item['rfid']) == id, jsonData["DATA"]))
            if result:
                for key in jsonData["LOGIN_IPC"]:
                    jsonData["LOGIN_IPC"][key] = result[0][key]

                write_json(DATABASE_JSON_DIR, jsonData)
                printScreen(3, result[0]["nameEN"] + " " + TABLET_ID)
                sleep(1)
                return result[0]
            
            else:
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

# function update Data from googlesheets
def updateDATA_sheets(SHEETID, RANGE, DATA):
    try:
        request = service.spreadsheets().values().update(
                spreadsheetId = SHEETID,
                range = RANGE, 
                valueInputOption = "RAW",  
                body = {"values": [[DATA]]}
            ).execute()
        
        return request
    except Exception as e:
            print(f"\n<<update data sheets error>> \n {e} \n")
            return False
    
# function Get Data from googlesheets
def getData_sheets(SHEETID, RANGE):
    get_data = service.spreadsheets().values().get(
        spreadsheetId=SHEETID, range=RANGE).execute()
    data_list = get_data["values"]
    
    return data_list

# function Send Data to googlesheets
def sendData_sheets(WEIGHTTABLE_SHEETID, sheetRange, dataArr):
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

# อ่านค่าน้ำหนักจากเครื่องชั่ง
def getWeight(Min_AVG=0, Max_AVG=0, Min_Control=0, Max_Control=0):
    
    dataWeight = []  # เก็บค่าน้ำหนัก
    # sr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)

    while len(dataWeight) < 2:
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")  # วันที่เวลา
        Today = now.strftime("%d/%m/%Y")  # วันที่
        Time = now.strftime("%H:%M:%S")  # เวลา

        printScreen(1, "<< Ready >>")
        print(str(date_time))
        print("READY:", TABLET_ID)
        sleep(5)
        
        led1.off()
        led2.off()
        led3.off()

        # อ่านค่าจาก port rs232
        # w = sr.readline()
        # w = random(0.155, 0.165)
        currentWeight = str(random.uniform(0.155,0.165))
        # currentWeight = w.decode('ascii', errors='ignore')
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
        
        printScreen(1, "Wait.... ")
        
        for i in dataWeight:
            if len(dataWeight) == 1:
                clearScreen(3, 9, 10)
                lcd.cursor_pos = (3, 0)
            else: 
                lcd.cursor_pos = (3, 11)
            lcd.write_string((str(len(dataWeight)))+".) "+str('%.3f' % weight))

        # รีเซ็ตโปรแกรม
        if weight < 0.005:
            lcd.clear()
            printScreen(0, "WEIGHT VARIATION")
            textEnd(1, "Restart.....")
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
            sleep(1)
            return weight_obj
        else:
            sleep(1)

# โปรแกรมหลัก
def main():
    lcd.clear()
    led1.blink()
    sleep(0.5)
    led2.blink()
    sleep(0.5)
    led3.blink()
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
    printScreen(1, "UPDATE DATA LIST")
    print("<<<< UPDATE DATA >>>>")
    update_user_data()

    printScreen(3, "<< SUCCESS >>")

    try:
        result = read_json(DATABASE_JSON_DIR)["LOGIN_ROOM"]
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
            
            # ป้อนหมายเลขเครื่องตอก

            setting_data = read_json(SETTING_JSON_DIR) # อ่านข้อมูลการตั้งค่าน้ำหนัก
            
            # มีข้อมูลการตั้งค่าน้ำหนักยา
            if setting_data["productName"]:
                # ค่า min,max ที่กำหนด
                Min = float(setting_data["min"])
                Max = float(setting_data["max"])
                Min_DVT = float(setting_data["min_control"])
                Max_DVT = float(setting_data["max_control"])
            
                weight = getWeight(Min, Max, Min_DVT, Max_DVT) # อ่านข้อมูลน้ำหนักจากเครื่องชั่ง
            else:
                weight = getWeight()              

            # สร้างข้อมูลเตรียมส่งบันทึก
            packetdata_arr = [
                weight["time"],
                "ONLINE",
                weight["weight1"],
                weight["weight2"],
                None,
                None,
                "ไม่ระบุ",
                nameTH,
            ]

            packetdata_arr.extend(["-"] * 11) # เพิ่ม - เข้า packetdata_arr 11 ตัว
            checkData_offline() # ตรวจสอบและส่งข้อมูล offline
            status = sendData_sheets(WEIGHTTABLE_DATA_RANGE, [packetdata_arr]) # ส่งข้อมูลไปยัง google sheet

            if not status:
                packetdata_arr[1] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                update_json(OFFLINE_JSON_DIR, packetdata_arr[0:8]) # บันทึกข้อมูล 1-7 ไปยัง offline.json 

            # ค่า min,max,avg ของน้ำหนักที่ชั่ง
            weight_cache = [float(weight["weight1"]), float(weight["weight2"])]
            Min_W = min(weight_cache)
            Max_W = max(weight_cache)
            AVG_W = round(sum(weight_cache)/len(weight_cache), 3)

            weightSummary(Min_W, Max_W, AVG_W, packetdata_arr[1])
            logout() # ออกจากระบบ

            # มีข้อมูลการตั้งค่าน้ำหนักยา
            if setting_data["productName"]:
                if AVG_W >= Min and AVG_W <= Max:
                    led1.blink()
                    led2.off()
                    led3.off()
                    textEnd(1, "<<Very Good>>")

                elif AVG_W >= Min_DVT and AVG_W <= Max_DVT:
                    led1.off()
                    led2.blink()
                    led3.off()
                    textEnd(1, "<<Failed!>>")

                else:
                    led1.off()
                    led2.off()
                    led3.blink()
                    textEnd(1, "<<Failed!>>")

                    meseage = 'ค่าเฉลี่ย '+str('%.3f' % AVG_W)+' g.'+\
                        '\n'+'ไม่ได้อยู่ในช่วงที่กฎหมายกำหนด('+str('%.3f' % Min_DVT)+\
                        'g. - '+str('%.3f' % Max_DVT)+'g.)'
                    
                    # ส่งบันทึกค่าน้ำหนักที่ไม่ผ่านเกณฑ์
                    sendData_sheets(WEIGHTTABLE_REMARKS_RANGE, [[weight["time"], meseage]])
    
                    
                    meseage_alert = '\n'+str(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))+'\n'+\
                        'ระบบเครื่องชั่ง 10 เม็ด'+'\n'+\
                        'เครื่องตอก: '+TABLET_ID+'\n'+\
                        'ชื่อยา: '+setting_data["productName"]+'\n'+\
                        'Lot.'+setting_data["Lot"]+'\n'+\
                        'ค่าเฉลี่ย '+str('%.3f' % AVG_W)+' g.'+'\n'+'ไม่ได้อยู่ในช่วงที่กฎหมายกำหนด'+'\n'+\
                        '('+str('%.3f' % Min_DVT)+'g. - '+str('%.3f' % Max_DVT) + 'g.)'
                    
                    # ส่งไลน์แจ้งเตือนค่าน้ำหนักที่ไม่ผ่านเกณฑ์
                    # lineNotify(meseage_alert)
                
    except Exception as e:
        print(f"<<main error>> \n {e} \n")

if __name__ == '__main__':
    # main()
    update_setting_data()