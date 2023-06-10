import ntplib
import time
from datetime import datetime
import os

from RPLCD import *
from RPLCD.i2c import CharLCD
LCD = CharLCD('PCF8574', 0x27)  # address LCD 20x4

# ฟังก์ชันสำหรับอัปเดตเวลาใน Raspberry Pi จากเซิร์ฟเวอร์ NTP
def update_time_from_ntp():
    c = ntplib.NTPClient()
    response = c.request('pool.ntp.org')
    current_time = response.tx_time
    os.system('sudo date -s @{}'.format(current_time))

# ฟังก์ชันสำหรับอัปเดตเวลาใน DS3231 RTC จาก Raspberry Pi
def update_time_to_rtc():
    rtc_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.system('sudo hwclock -w --date="{}"'.format(rtc_time))

# ฟังก์ชันสำหรับอ่านเวลาจาก DS3231 RTC
def read_rtc_time():
    rtc_time_str = os.popen('sudo hwclock -r').read().strip()
    rtc_time_str = rtc_time_str.split('.')[0]  # เอาเฉพาะส่วนที่ไม่เกี่ยวข้องกับช่วงทศนิยม
    rtc_time = datetime.strptime(rtc_time_str, '%Y-%m-%d %H:%M:%S')
    return rtc_time

# เรียกใช้งานฟังก์ชันเพื่ออัปเดตเวลา
try:
    update_time_from_ntp()
except Exception as e:
    print('เกิดข้อผิดพลาดในการอัปเดตเวลาจาก NTP: {}'.format(e))
    pass

# อัปเดตเวลาใน DS3231 RTC
try:
    update_time_to_rtc()
except Exception as e:
    print('เกิดข้อผิดพลาดในการอัปเดตเวลาใน DS3231 RTC: {}'.format(e))
    pass

# อ่านเวลาจาก DS3231 RTC
while True:
    rtc_time = read_rtc_time().strftime('%d/%m/%Y, %H:%M:%S')
    print('เวลาใน DS3231 RTC: {}'.format(rtc_time))
    LCD.cursor_pos = (3, 0)
    LCD.write_string(rtc_time)

