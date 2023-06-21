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

import requests
import os

url = "https://docs.google.com/spreadsheets/d/1I1ZdnnAeP8pMmAsSkGk1Nti0gTZMeMwRH1rPFLELn68/export?format=pdf"
output_path = "D:\Backup_GGSH_PDF\PDF\output.pdf"

# ดาวน์โหลดไฟล์ PDF
response = requests.get(url)
response.raise_for_status()

# บันทึกไฟล์
with open(output_path, "wb") as file:
    file.write(response.content)

print("ดาวน์โหลดและบันทึกไฟล์เสร็จสิ้น")
