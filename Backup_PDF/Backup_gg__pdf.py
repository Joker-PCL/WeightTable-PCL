import os
import os.path
import subprocess
import io

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

from time import sleep

# กำหนด path ของ credentials.json ที่คุณดาวน์โหลดมา
CREDENTIALS_DIR = 'D:\\Project VS Code\\Backup_GGSH_PDF\\credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_DIR = 'D:\\Project VS Code\\Backup_GGSH_PDF\\token.pickle'


# กำหนดค่าไฟล์ที่จะดาวน์โหลด
# ระบุ ID ของโฟล์เดอร์ที่ต้องการดาวน์โหลด
folder_id = '10JT2s9zd8pcmSj-kB2T5s-kFHlW58IE3'
# กำหนด path ของโฟล์เดอร์ที่ต้องการบันทึกไฟล์ PDF
output_folder = 'D:\\Project VS Code\\Backup_GGSH_PDF\\path\\ROOM'


def main():
    print("กำลังเชื่อมต่อ.....")
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

        # ดึงรายการไฟล์ในโฟล์เดอร์
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        results = service.files().list(
            q=query, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        # วนลูปเพื่อดาวน์โหลดไฟล์และบันทึกเป็นไฟล์ PDF
        for item in items:
            file_id = item['id']
            file_name = item['name']
            file_name = file_name.replace("/", "-")

            # สร้างไฟล์ PDF และกำหนดค่า MediaIoBaseDownload
            output_path = os.path.join(output_folder, f"{file_name}.pdf")
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, service.files().export_media(
                fileId=file_id, mimeType='application/pdf'))
            done = False

            # ตรวจสอบว่าตำแหน่งและชื่อไฟล์ปลายทางนั้นมีอยู่จริง
            if not os.path.exists(output_path):
                # ดาวน์โหลดไฟล์และบันทึกเป็นไฟล์ PDF
                while done is False:
                    status, done = downloader.next_chunk()
                    print(f"Download {file_name} {int(status.progress() * 100)}%")

                # เขียนข้อมูลในไฟล์ PDF
                file.seek(0)

                # สามารถใช้โค้ดต่อไปนี้เพื่อเปิดไฟล์ใหม่ในโหมด binary และทำการบันทึกไฟล์
                with open(output_path, 'wb') as f:
                    # ทำการบันทึกไฟล์ PDF ที่ต้องการดาวน์โหลด
                    f.write(file.read())
            else:
                print("ไฟล์ที่กำหนดมีอยู่แล้ว")

            print(f"File saved to {output_path} \n")
        
        print("\n <<<<<< การสำรองข้อมูลเสร็จเรียบร้อยแล้ว >>>>>>>")
        print("โปรแกรมจะปิดตัวลงใน...")
        for i in range(5, 0, -1):
            print(i, "วินาที")
            sleep(1)

        # เรียกใช้คำสั่งเปิดโฟลเดอร์ของ Windows
        subprocess.run('explorer "{}"'.format(output_folder), shell=True)
        quit()

    except Exception as e:
        print(e)
        print("เกิดข้อผิดพลาดระหว่างดาวน์โหลด กำลังเชื่อมต่อไหม่....")
        main()

if __name__ == '__main__':
    main()
