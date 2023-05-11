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

# สรุปผล
def weightSummary(Min_W, Max_W, AVG_W, status):
    if status == "OFFLINE":
        led3.blink()

    lcd.clear()
    printScreen(0, "WEIGHT VARIATION")
    printScreen(1, f"<< {status} >>")
    textEnd(2, "MIN:"+ str('%.3f' % Min_W) + "  " + "MAX:" + str('%.3f' % Max_W))
    textEnd(3, "AVG:"+str('%.3f' % AVG_W))
    sleep(5)

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
    main()
