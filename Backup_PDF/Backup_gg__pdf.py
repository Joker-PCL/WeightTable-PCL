import os
import os.path
import subprocess
import io
import json

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

from time import sleep
import ctypes

# กำหนด path ของ credentials.json ที่คุณดาวน์โหลดมา
SCOPES = ['https://www.googleapis.com/auth/drive']
CREDENTIALS_DIR = 'credentials.json'
TOKEN_DIR = 'token.pickle'

# กำหนด path ของโฟล์เดอร์ที่ต้องการบันทึกไฟล์ PDF
setting_json = "setting.json"
pdf_folder = 'PDF'

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()
user32.SetWindowPos(user32.GetForegroundWindow(), None, 0, 0, 800, 200, 0x0002)

def main():
    while True:
        print("Connecting...")
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

            # สร้าง Google Drive API service
            service = build('drive', 'v3', credentials=creds)

            with open(setting_json) as json_file:
                # แปลง JSON ไฟล์ เป็น Python Dict
                prog_dict = json.load(json_file)

            for data in prog_dict:
                folder_name = os.path.join(pdf_folder, data["folderName"])
                folder_id = data["folder_id"]

                downloadFile(service, folder_id, folder_name)

            # print("<<<<<< การสำรองข้อมูลเสร็จเรียบร้อยแล้ว >>>>>>>")
            # print("โปรแกรมจะตรวจสอบและสำรองข้อมูลในอีก")
            print("<<<<<< Data backup completed successfully >>>>>>>")
            print("The program will check and backup the data again in")    
            # print(f"You can view the files {pdf_folder}")
            subprocess.run('explorer "{}"'.format(pdf_folder), shell=True)
            
            # ตั้งเวลาในการรันรอบโปรแกรม
            breaktime(5, 30, 0)

        except Exception as e:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("<<ERROR>>",e)
            # print("เกิดข้อผิดพลาดระหว่างดาวน์โหลด กำลังเชื่อมต่อไหม่....")
            print("An error occurred during the download. Reconnecting...")
            breaktime(0, 0, 30) 

def breaktime(Hours=5, Min=0, Sec=0):
    for i in range((Hours*3600)+(Min*60)+Sec, 0, -1):
        hours = i // 3600  # หารเพื่อหาจำนวนชั่วโมง
        minutes = (i % 3600) // 60  # หารเพื่อหาจำนวนนาที
        seconds = i % 60  # หารเพื่อหาจำนวนวินาที

        # print(f"{hours} ชั่วโมง {minutes} นาที {seconds} วินาที", end='\r')
        time_str = f"Timer: {str(hours).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"  # แปลงเป็น string และใช้ zfill() เพื่อเติมศูนย์ด้านหน้าตัวเลข
        print(time_str, end='\r')
        sleep(1)

def downloadFile(service, folder_id, folder_name):
    # ดึงรายการไฟล์ในโฟล์เดอร์
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
    results = service.files().list(
        q=query,
        fields="nextPageToken, files(id, name)"
    ).execute()

    items = results.get('files', [])

    # วนลูปเพื่อดาวน์โหลดไฟล์และบันทึกเป็นไฟล์ PDF
    for item in items:
        file_id = item['id']
        file_name = item['name']
        file_name = file_name.replace("/", "-")

        output_path = os.path.join(folder_name, f"{file_name}.pdf")
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(
            file,
            service.files()
            .export_media(
                fileId=file_id,
                mimeType='application/pdf'
            )
        )

        done = False

        # ตรวจสอบว่าตำแหน่งและชื่อไฟล์ปลายทางนั้นมีอยู่จริง
        if not os.path.exists(output_path):
            # ดาวน์โหลดไฟล์และบันทึกเป็นไฟล์ PDF
            while done is False:
                status, done = downloader.next_chunk()
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"Download {file_name} {int(status.progress() * 100)}%")
                print(f"File saved to {output_path}", end='\n')
            # เขียนข้อมูลในไฟล์ PDF
            file.seek(0)

            # สามารถใช้โค้ดต่อไปนี้เพื่อเปิดไฟล์ใหม่ในโหมด binary และทำการบันทึกไฟล์
            with open(output_path, 'wb') as f:
                # ทำการบันทึกไฟล์ PDF ที่ต้องการดาวน์โหลด
                f.write(file.read())
        else:
            pass

if __name__ == '__main__':
    main()
