## ============================================================================##
##                              Dev.  Nattapon                                 ##
##                       Program Author and Designer                           ##
## ============================================================================##
## ต้องใช้คำสั่ง sudo su pip install google-api-python-client 
# update 16/7/2022  ส่งเวลา และวันที่ อัตโนมัติ
#                   ส่งเวลา Range ที่จะลงข้อมูลครั้งถัดไป,ส่งไลน์แจ้งเตือนเมื่อน้ำหนักไม่ได้อยู่ในช่วง
# update 08/1/2023  เพิ่มการบันทึกข้อมูลแบบ offline กรณีไม่สามารถเชื่อมต่อ internet ได้
#                   โดยไฟล์จะบันทึกไว้ใน json_dir = "/home/pi/Json_offline/data_offline.json"


import json
import random

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

buzzer = Buzzer(21)

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
SETTING_JSON_DIR = '/home/pi/Desktop/poligram/database/setting_room.json'
OFFLINE_JSON_DIR = '/home/pi/Desktop/poligram/database/offline_room.json'

WEIGHTTABLE_SHEETID = "1Vfy1ovKCEVWl9X3cO-M4AV9IzOmuK467IeMWragfq-o"
WEIGHTTABLE_SETTING_RANGE = "Setting!A2:A14"
WEIGHTTABLE_DATA_RANGE = "WEIGHT!A5:S"
WEIGHTTABLE_REMARKS_RANGE = "Remark!A3:F"

TABLET_ID = 'T15'

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
          ["*", "0", "#", "D"]]

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

# แสดงข้อความ dot matrix
def dotmatrix(draw, xy, txt, fill=None):
    x, y = xy
    for byte in txt:
        for j in range(8):
            if byte & 0x01 > 0:
                draw.point((x, y + j), fill=fill)

            byte >>= 1
        x += 1

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

# ตรวจสอบข้อมูล offline
def checkData_offline():
    offline_data = read_json(OFFLINE_JSON_DIR)
    if offline_data["DATA"]:
        dataArr = []
        for data in offline_data["DATA"]:
            data.extend(["-"] * 11) # เพิ่ม - ไปอีก 11 ตัว
            dataArr.append(data)
        try: 
            print("Sending data offline...")
            textEnd(3, "Sending data..")
            status = sendData_sheets(WEIGHTTABLE_DATA_RANGE, dataArr)

            Timestamp_offline = offline_data["DATA"][0][0]

            if status:      
                msg_Notify = '\n🔰 มีข้อมูล offline เพิ่มเข้ามาไหม่ \n' +\
                    '🔰 ระบบเครื่องชั่ง 10 เม็ด \n' +\
                    '🔰 เครื่องตอก: '+ TABLET_ID + '\n' +\
                    '❎ ขาดการเชื่อมต่อ \n  ' +\
                    Timestamp_offline + '\n' +\
                    '✅ เชื่อมต่ออีกครั้ง \n  ' +\
                    datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
                
                # ส่งไลน์แจ้งเตือน
                lineNotify(msg_Notify)

                # ล้างข้อมูล JSON
                write_json(OFFLINE_JSON_DIR, {"DATA": []})
                print("<<< send data success >>>", end='\n\n')

                textEnd(3, "<<Success>>")
            else:
                textEnd(3, "<<Failed!>>")

        except Exception as e:
            print(f"\n<< checkData offline >> \n {e} \n")
            
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
        
        while True:
            printScreen(1, "<< LOGIN >>")
            printScreen(3, "...RFID SCAN...")

            id = input("RFID: ")
            buzzer.beep(0.1, 0.1, 1)
            printScreen(1,f"ID: {id}")

            result = list(filter(lambda item: (
                        item['rfid']) == id, jsonData["DATA"]))
            if result:
                for key in jsonData["LOGIN_ROOM"]:
                    jsonData["LOGIN_ROOM"][key] = result[0][key]

                write_json(DATABASE_JSON_DIR, jsonData)
                printScreen(3, result[0]["nameEN"] + " " + TABLET_ID)
                sleep(1)
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

    for key in jsonData["LOGIN_ROOM"]:
        jsonData["LOGIN_ROOM"][key] = None

    write_json(DATABASE_JSON_DIR, jsonData)

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

# อ่านค่าน้ำหนักจากเครื่องชั่ง
def getWeight(Min_AVG=0, Max_AVG=0, Min_Control=0, Max_Control=0):
    
    dataWeight = []  # เก็บค่าน้ำหนัก
    clearScreen(3)
    sr = serial.Serial(port="/dev/ttyUSB0", baudrate=9600)
    
    while len(dataWeight) < 2:
        now = datetime.now()
        date_time = now.strftime("%d/%m/%Y, %H:%M:%S")  # วันที่เวลา
        Today = now.strftime("%d/%m/%Y")  # วันที่
        Time = now.strftime("%H:%M:%S")  # เวลา

        printScreen(1, "<< Ready >>")
        print(str(date_time))
        print("READY:", TABLET_ID)
        sleep(0.2)

        # อ่านค่าจาก port rs232
        w = sr.readline()
        # w = random(0.155, 0.165)
        # currentWeight = str(random.uniform(0.155,0.165))
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
        
        printScreen(1, "Wait....")
        
        for i in dataWeight:
            if len(dataWeight) == 1:
                clearScreen(3, 9, 10)
                lcd.cursor_pos = (3, 0)
            else: 
                lcd.cursor_pos = (3, 11)
            lcd.write_string(f"{len(dataWeight)}){str('%.3f' % weight)}")

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


        if len(dataWeight) == 2:
            weight_obj = {
                "time": date_time,
                "weight1": str('%.3f' % dataWeight[0]),
                "weight2": str('%.3f' % dataWeight[1]),
                "quantity": str('%.3f' % round(sum(dataWeight)/len(dataWeight), 3))
            }

            # Timestamp dataWeight
            dataWeight.insert(0, Time)
            sleep(2)
            led_scr.clear()
            return weight_obj
        else:
            sleep(1)

# สรุปผล
def weightSummary(Min_W, Max_W, AVG_W, status):
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
    textEnd(2, "MN:"+ str('%.3f' % Min_W) + "  " + "MX:" + str('%.3f' % Max_W))
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
    global service
    service = firtconnect()
    
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
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_passed, fill="red")
                    textEnd(1, "<<Very Good>>")

                elif AVG_W >= Min_DVT and AVG_W <= Max_DVT:
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_notpass, fill="red")

                    buzzer.beep(0.5, 0.5, 5)
                    textEnd(1, "<<Failed!>>")

                else:
                    with canvas(led_scr) as draw:
                        dotmatrix(draw, (4, 0), led_notpass, fill="red")

                    buzzer.beep(0.5, 0.5, 5)
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
                    lineNotify(meseage_alert)
                
    except Exception as e:
        print(f"<<main error>> \n {e} \n")

if __name__ == '__main__':
    main()
