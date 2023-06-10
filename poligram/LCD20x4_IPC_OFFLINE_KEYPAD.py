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

from RPLCD import *
from RPLCD.i2c import CharLCD
from gpiozero import LED, Buzzer
import RPi.GPIO as GPIO

RFID = LED(23) # RFID SWITCH
BUZZER = Buzzer(24) # BUZZER
BUZZER.beep(0.1, 0.1, 1)
 
LCD = CharLCD('PCF8574', 0x27)  # address LCD 20x4

# LED Dotmatrix
from luma.led_matrix.device import max7219
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, TINY_FONT

serialSCR = spi(port=0, device=0, gpio=noop())
LED_SCR = max7219(serialSCR, cascaded=4, block_orientation=90, blocks_arranged_in_reverse_order=True)
LED_SCR.contrast(20)

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
LINE_TOKEN = 'p9YWBiZrsUAk7Ef9d0hLTMMF2CxIaTnRopHaGcosM4q'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_DIR = '/home/pi/Desktop/poligram/database/credentials.json'
TOKEN_DIR = '/home/pi/Desktop/poligram/token.pickle'

DATABASE_SHEETID = "1rUBfrqt40NhJGKIg5TwIIjFZHvS8UZ2NRAjpKKqpk2M"
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
        "SHEET_ID": "1Jf4zcZoIafRXQpAdLOdnroN9JDfr-r5JMDnnR0duUpg",
        "SCRIPT_ID": "1ea3JIcR5ejz3eG4bkvYUnQKsUpgmhhXfnIERgqbJodJfanYfko_Aac2i"
    },
    {
        "TABLET_ID": "T17" ,
        "SHEET_ID": "1YidBH7JCtjswegCp8BnxblEpm0iDbyGJtQIrYIR2Swo",
        "SCRIPT_ID": "1yC8mB5VAr1S4jHDxazy8VW--kwkabzZkKogEYwnhBe9TP6uwfyg-vx5a"
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
    setTimer = 120  # settimeout sec.
    Timer = setTimer
    keypad_cache = ""
    text = f"{Message}:"
    LCD.cursor_pos = (3, 0)
    LCD.write_string(text.ljust(20))

    while Timer:
        for i in range(len(keypad_rows)):
            gpio_out = keypad_rows[i]
            GPIO.output(gpio_out, GPIO.HIGH)

            for x in range(len(keypad_cols)):
                gpio_in = keypad_cols[x]
                # on GPIO checkkey 
                if (GPIO.input(gpio_in) == 1):
                    BUZZER.beep(0.1, 0.1, 1)
                    key = keypad[i][x]
                    Timer = setTimer

                    if key == "*" or  key == "#":
                        quit()
                    elif key == "D" and keypad_cache:
                        keypad_cache = keypad_cache[0:-1] # ลบ
                    elif key != "A" and key != "B" and key != "C" and key != "D" and len(keypad_cache) < 2:
                        keypad_cache = keypad_cache+key
                    elif key == "C" and keypad_cache:
                        amount = int(keypad_cache)
                        if amount < 10 or amount > 50:
                            BUZZER.beep(0.1, 0.1, 5)
                        else:
                            return keypad_cache
                    else:
                        pass

                    text = f"{Message}: {keypad_cache}"
                    text = text.ljust(20)
                    LCD.cursor_pos = (3, 0)
                    LCD.write_string(text)
                    sleep(0.3)

            # off GPIO checkkey            
            GPIO.output(gpio_out, GPIO.LOW)

        # จับเวลา
        currentMillis = time()
        if currentMillis - previousMillis > 1:
            previousMillis = currentMillis

            Timer_text = f"Timeout {Timer}s."
            if Timer == 9 or Timer == 99:   
                clearScreen(2)
                
            LCD.cursor_pos = (2, int((20-len(Timer_text))/2))
            LCD.write_string(Timer_text)

            Timer -= 1
            # timeout
            if not Timer:
                textEnd(3, "Restart...")
                quit()
            elif Timer < 15:
                BUZZER.beep(0.5, 0.5, 1) 

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
            LCD.clear()
            LCD.cursor_pos = (1, 0)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+2:
            LCD.cursor_pos = (2, 0)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+3:
            LCD.cursor_pos = (3, 0)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+4:
            LCD.cursor_pos = (1, 12)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+5:
            LCD.cursor_pos = (2, 12)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        elif len(total_weight) == i+6:
            LCD.cursor_pos = (3, 12)
            LCD.write_string(str(len(total_weight))+")"+str(weight))
            break
        else:
            continue

# แสดงผลหน้าจอ
def printScreen(row, text):
    clearScreen(row)
    LCD.cursor_pos = (row, int((20-len(text))/2))
    LCD.write_string(text)

# แสดงผลแบบเรียงอักษร
def textEnd(row, text):
    clearScreen(row)
    for i in range(len(text)):
        LCD.cursor_pos = (row, int((20-len(text))/2)+i)
        LCD.write_string(text[i])
        sleep(0.15)

# ลบอักษรหน้าจอแบบกำหนด แถว ตำแหน่ง จำนวน
def clearScreen(row, col=0, numcol=20):
    text = ""
    LCD.cursor_pos = (row, col)
    LCD.write_string(text.rjust(numcol, " "))

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
                get_setting_data = read_json(SETTING_JSON_DIR) # อ่านข้อมูลการตั้งค่าน้ำหนัก
                setting_data = next((item for item in get_setting_data['SETTING'] if item['tabletID'] == str(_data["TABLET_ID"])), None)
                WEIGHTTABLE_SHEETID = checkSheetID(_data["TABLET_ID"])  # หาข้อมูลจากเลขเครื่องตอก
                SCRIPT_ID = WEIGHTTABLE_SHEETID["SCRIPT_ID"] # SCRIPT ID
                SHEET_ID = WEIGHTTABLE_SHEETID["SHEET_ID"] # SHEET ID
                GET_CURRENT_RANGE = getData_sheets(SHEET_ID, WEIGHTTABLE_SETTING_RANGE) # ตำแหน่งปัจจุบัน

                if GET_CURRENT_RANGE:
                    CURRENT_RANGE = GET_CURRENT_RANGE[0][0]
                    # ข้อมูล
                    _data["CURRENT_RANGE"] = CURRENT_RANGE

                    print(_data)
                    status = sendData_sheets(SCRIPT_ID, _data) # ส่งข้อมูล
                    if status and setting_data:
                        remarksRecord(setting_data, _data)

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
                    "min_avg": None,
                    "max_avg": None,
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

# แสดงเวลา
stop_print_time = False
def print_time():
    while not stop_print_time:
        current_time = datetime.now().strftime("%H:%M:%S")
        with canvas(LED_SCR) as draw:
            text(draw, (2, 0), f"{current_time}", fill="red", font=proportional(TINY_FONT))
        sleep(1)
    
    LED_SCR.clear()

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
            
            print_time_thread = threading.Thread(target=print_time)
            print_time_thread.start()
            id = input("RFID: ")
            printScreen(1,f"ID: {id}")

            result = list(filter(lambda item: (
                        item['rfid']) == id, jsonData["DATA"]))
            if result:
                BUZZER.beep(0.1, 0.1, 1)
                global stop_print_time
                stop_print_time = True
                print_time_thread.join()  # รอให้เทรด print_time สิ้นสุดการทำงาน
                
                for key in jsonData["LOGIN_IPC"]:
                    jsonData["LOGIN_IPC"][key] = result[0][key]

                write_json(DATABASE_JSON_DIR, jsonData)
                printScreen(3, result[0]["nameEN"])
                RFID.off() # ปิดการทำงาน RFID Reader
                sleep(1.5)
                return result[0]
            
            else:
                BUZZER.beep(0.1, 0.1, 5)
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
    if not service:
        firtconnect()

    laps = 0
    while laps < 3:
        laps += 1
        printScreen(3, f"Get current range {laps}")

        try:
            get_data = service.spreadsheets().values().get(
                spreadsheetId=SHEETID, range=RANGE).execute()
            data_list = get_data["values"]
            
            return data_list

        except Exception as e:
            print(f"<<get data sheet error>> \n {e} \n")
            pass
            
    return False

# function Send Data to googlesheets
def sendData_sheets(SCRIPT_ID, packetdata_obj):
    if not service_script:
        firtconnect()

    laps = 0
    while laps < 3:
        laps += 1
        printScreen(3, f"Sending data {laps}")
        
        try:
            request = {
                'function': "reciveData",
                'parameters': [packetdata_obj],
                'devMode': True
            }
            response = service_script.scripts().run(body=request, scriptId=SCRIPT_ID).execute()
            
            print(response)
            return response
        
        except errors.HttpError as error:
            print(f"<<send data sheet error>> \n {error.content} \n") 
            pass
        
    return False
       
# อ่านค่าน้ำหนักจากเครื่องชั่ง
def getWeight(USERNAME, TABLET_ID, Max_Tab, Min_Control=0, Max_Control=0, Min_Dvt=0, Max_Dvt=0):
    
    dataWeight = []  # เก็บค่าน้ำหนัก
    sr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)

    while len(dataWeight) < int(Max_Tab):
        printScreen(0, "<< Ready >>")
        
        print("READY:", TABLET_ID)
        sleep(0.2)

        # อ่านค่าจาก port rs232
        w = sr.readline()
        # currentWeight = str(random.uniform(0.650,0.685))
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
        print(f"\n{str(Timestamp)}")
        print(str(len(dataWeight))+")"+str(weight))
        screen(dataWeight, '%.3f' % weight)
        BUZZER.beep(0.1, 0.1, 1)

        with canvas(LED_SCR) as draw:
            text(draw, (7, 0), '%.3f' % weight, fill="red", font=proportional(TINY_FONT))
        
        sleep(0.5)

        # รีเซ็ตโปรแกรม
        if weight < 0.005:
            LCD.clear()
            printScreen(0, "WEIGHT VARIATION")
            textEnd(1, "Restart.....")
            print("Reset!")
            quit()

        if Min_Control and Max_Control and Min_Dvt and Max_Dvt:
            # ไฟแสดงค่า LED1_GREEN,LED2_ORANGE,LED3_RED
            if weight >= Min_Control and weight <= Max_Control:
                print("ผ่าน อยู่ในช่วงที่กำหนด")
            elif weight >= Min_Dvt and weight <= Max_Dvt:
                with canvas(LED_SCR) as draw:
                    dotmatrix(draw, (4, 0), led_notpass, fill="red")
                BUZZER.beep(0.1, 0.1, 5, background=False)
                print("ผ่าน อยู่ในช่วงที่กฏหมายกำหนด")
            else:
                with canvas(LED_SCR) as draw:
                    dotmatrix(draw, (4, 0), led_notpass, fill="red")
                BUZZER.beep(0.1, 0.1, 5, background=False)
                print("ไม่ผ่าน")

    TIMESTAMP = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")  # วันที่เวลา
    packetdata_obj = {
        "TABLET_ID": TABLET_ID,
        "TIMESTAMP": TIMESTAMP,
        "SIGNATURE": USERNAME,
        "TYPE": "ONLINE",
        "WEIGHT": dataWeight
    }

    sleep(2)
    LED_SCR.clear()
    return packetdata_obj

# สรุปผล
def weightSummary(Min_W=0, Max_W=0, AVG_W=0, status=None):
    if status == "OFFLINE":
        BUZZER.beep(0.5, 0.5, 5)
        with canvas(LED_SCR) as draw:
                dotmatrix(draw, (1, 0), led_offline_th, fill="red")
    elif status == "ONLINE":
        with canvas(LED_SCR) as draw:
                dotmatrix(draw, (1, 0), led_online_th, fill="red")

    LCD.clear()
    printScreen(0, "WEIGHT VARIATION")
    printScreen(1, f"<< {status} >>")
    textEnd(2, "MIN:"+ str('%.3f' % Min_W) + "  " + "MAX:" + str('%.3f' % Max_W))
    textEnd(3, "AVG:"+str('%.3f' % AVG_W))
    sleep(5)

# ลงบันทึก remarks
def remarksRecord(setting_data, packetdata_obj):
    # มีข้อมูลการตั้งค่าน้ำหนักยา
    productName = setting_data["productName"]
    lot = setting_data["Lot"]
    # ค่า min,max ที่กำหนด
    Min_Control = float(setting_data["min_control"])
    Max_Control = float(setting_data["max_control"])

    TABLET_ID = packetdata_obj["TABLET_ID"]
    timestamp_alert = packetdata_obj["TIMESTAMP"]
    total_weight = packetdata_obj["WEIGHT"]

    meseage_weight = "❎น้ำหนักไม่ได้อยู่ในช่วงที่กำหนด \n" +\
        "✅ช่วงที่กำหนด \n" +\
        f"({'%.3f' % Min_Control}g. - {'%.3f' % Max_Control}g.) \n" +\
        "🔰ข้อมูลน้ำหนัก \n"
    
    meseage_alert = f"\n {timestamp_alert} \n" +\
        "🔰ระบบเครื่องชั่ง IPC \n" +\
        f"🔰เครื่องตอก: {TABLET_ID} \n" +\
        f"🔰ชื่อยา: {productName} \n" +\
        "🔰Lot. " + str(lot) + "\n"

    # ตรวจหาน้ำหนักที่ไม่อยู่ในช่วง
    weight_cache = []
    weightOutOfRange = False
    for index, weight in enumerate(total_weight):
        weight_cache.append(weight[-1])
        if float(weight[-1]) < Min_Control or float(weight[-1]) > Max_Control:
            weightOutOfRange = True
            meseage_weight += f"❌{index+1}) {'%.3f' % weight[-1]}g. \n"
        else:
            meseage_weight +=  f"✅{index+1}) {'%.3f' % weight[-1]}g. \n"
    
    # ค่าเฉลี่ย
    average = sum(weight_cache) / len(weight_cache)
    meseage_weight += f"🔰ค่าเฉลี่ยที่ได้ {'%.3f' % average}g."

    # น้ำหนักไม่อยู่ในช่วง
    if weightOutOfRange:
        WEIGHTTABLE_SHEETID = checkSheetID(TABLET_ID) # หาข้อมูลจากเลขเครื่องตอก
        SHEET_ID = WEIGHTTABLE_SHEETID["SHEET_ID"] # SHEET ID

        # ส่งบันทึกค่าน้ำหนักที่ไม่ผ่านเกณฑ์
        response = service.spreadsheets().values().append(
            spreadsheetId=SHEET_ID,
            range=WEIGHTTABLE_REMARKS_RANGE,
            body={
                "majorDimension": "ROWS",
                "values": [[timestamp_alert, meseage_weight]]
            },
            valueInputOption="USER_ENTERED"
        ).execute()
    
        meseage_alert += meseage_weight

        # ส่งไลน์แจ้งเตือนค่าน้ำหนักที่ไม่ผ่านเกณฑ์
        lineNotify(meseage_alert)
              
# โปรแกรมหลัก
def main():
    with canvas(LED_SCR) as draw:
        text(draw, (4, 0), "PCL V.4", fill="red", font=proportional(TINY_FONT))

    logout() # ล้างข้อมูลผู้ใช้งาน
    LCD.clear()
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
                    BUZZER.beep(0.1, 0.1, 5)
                    sleep(1)

            printScreen(2, TABLET_ID)
            update_setting_data(WEIGHTTABLE_LIST) # อัพเดทฐานข้อมูลการตั้งค่า

            # ตรวจหาข้อมูล
            get_setting_data = read_json(SETTING_JSON_DIR) # อ่านข้อมูลการตั้งค่าน้ำหนัก
            setting_data = next((item for item in get_setting_data['SETTING'] if item['tabletID'] == str(TABLET_ID)), None)

            # มีข้อมูลการตั้งค่าน้ำหนักยา
            if setting_data["productName"] and setting_data["productName"] != "xxxxx":
                # ค่า min,max ที่กำหนด
                Max_Tab = setting_data["number_tablets"]
                Min_AVG = float(setting_data["min_avg"])
                Max_AVG = float(setting_data["max_avg"])
                Min_CONTROL = float(setting_data["min_control"])
                Max_CONTROL = float(setting_data["max_control"])
                Min_DVT = float(setting_data["min_dvt"])
                Max_DVT = float(setting_data["max_dvt"])

                LCD.clear() # เคลียร์หน้าจอ
                packetdata_obj = getWeight(nameTH, TABLET_ID, Max_Tab, Min_CONTROL, Max_CONTROL, Min_DVT, Max_DVT) # อ่านข้อมูลน้ำหนักจากเครื่องชั่ง
            else:
                # ป้อนจำนวนเม็ดที่ต้องชั่ง
                printScreen(1, "SELECT TABLET ID")
                Max_Tab = readKeypad("AMOUNT")
                sleep(1)
                # Max_Tab = input("AMOUNT: ")
                LCD.clear() # เคลียร์หน้าจอ
                packetdata_obj = getWeight(nameTH, TABLET_ID, Max_Tab)        

            # ค่า min,max,avg ของน้ำหนักที่ชั่ง
            weight_cache = []
            for weight_record in packetdata_obj["WEIGHT"]:
                weight_cache.append(float(weight_record[1]))

            Min_W = min(weight_cache)
            Max_W = max(weight_cache)
            AVG_W = round(sum(weight_cache)/len(weight_cache), 3)
            
            WEIGHTTABLE_SHEETID = checkSheetID(TABLET_ID) # หาข้อมูลจากเลขเครื่องตอก
            SCRIPT_ID = WEIGHTTABLE_SHEETID["SCRIPT_ID"] # SCRIPT ID
            SHEET_ID = WEIGHTTABLE_SHEETID["SHEET_ID"] # SHEET ID

            LCD.clear() # ล้างหน้าจอ
            checkData_offline() # ตรวจสอบและส่งข้อมูล offline

            GET_CURRENT_RANGE = getData_sheets(SHEET_ID, WEIGHTTABLE_SETTING_RANGE) # ตำแหน่งปัจจุบัน
            if GET_CURRENT_RANGE:
                CURRENT_RANGE = GET_CURRENT_RANGE[0][0]
                # ข้อมูล
                packetdata_obj["CURRENT_RANGE"] = CURRENT_RANGE
                textEnd(3, "Sending data....")
                status = sendData_sheets(SCRIPT_ID, packetdata_obj) # ส่งข้อมูลไปยัง google sheet

                if not status:
                    packetdata_obj["TYPE"] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                    update_json(OFFLINE_JSON_DIR, packetdata_obj) # offline.json 
            else:
                packetdata_obj["TYPE"] = "OFFLINE" # เปลี่ยนสถานะเป็น OFFLINE
                update_json(OFFLINE_JSON_DIR, packetdata_obj) # offline.json 
            
            # สรุปผล
            weightSummary(Min_W, Max_W, AVG_W, packetdata_obj["TYPE"])
            
            # มีข้อมูลการตั้งค่าน้ำหนักยา
            if setting_data:
                if setting_data["productName"] != "xxxxx":
                    # ตรวจหาน้ำหนักที่ไม่อยู่ในช่วง
                    weightOutOfRange = False
                    for weight in packetdata_obj["WEIGHT"]:
                        if float(weight[-1]) < Min_CONTROL or float(weight[-1]) > Max_CONTROL:
                            weightOutOfRange = True
                            with canvas(LED_SCR) as draw:
                                dotmatrix(draw, (4, 0), led_notpass, fill="red")

                            BUZZER.beep(0.5, 0.5, 5)
                            textEnd(1, "<<Failed!>>")
                            break

                    # น้ำหนักที่อยู่ในช่วง
                    if not weightOutOfRange:
                        with canvas(LED_SCR) as draw:
                            dotmatrix(draw, (9, 0), led_passed, fill="red")
                        textEnd(1, "<<Very Good>>")
                    else:
                        remarksRecord(setting_data, packetdata_obj)

    except Exception as e:
        print(f"<<main error>> \n {e} \n")

if __name__ == '__main__':
    main()