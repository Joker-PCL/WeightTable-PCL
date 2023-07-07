## ============================================================================##
##                              Dev.  Nattapon                                 ##
##                       Program Author and Designer                           ##
## ============================================================================##

#รายการอัพเดท
update 16/07/2022  ส่งเวลา และวันที่ อัตโนมัติ
                  ส่งเวลา Range ที่จะลงข้อมูลครั้งถัดไป,ส่งไลน์แจ้งเตือนเมื่อน้ำหนักไม่ได้อยู่ในช่วง
update 08/01/2023  เพิ่มการบันทึกข้อมูลแบบ offline กรณีไม่สามารถเชื่อมต่อ internet ได้
                  โดยไฟล์จะบันทึกไว้ใน json_dir = "/home/pi/Json_offline/data_offline.json"
update 08/05/2023  ใช้การแสกนบัตร rfid 125khz ในการเข้าใช้งาน
                  ดึงข้อมูลการรายชื่อ การตั้งค่ามาเก็บไว้ที่ตัวเครื่อง
update 10/06/2023  เพิ่มโมดูล DS3231 (โมดูลนาฬิกา) ในการเก็บค่าเวลา

เพิ่มไวไฟ
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

##### จำเป็นต้องติดตั้ง Libraries ที่จำเป็นถึงจะสามารถใช้งานได้ #####
sudo apt update
sudo su pip install --upgrade google-api-python-client
pip install google-api-python-client
pip install requests
pip install keyboard
sudo apt install python3-gpiozero

##### install LEDDOTMATRIX #####
##### เปิดใช้งาน SPI #####
sudo usermod -a -G spi,gpio pi
#sudo apt install build-essential python3-dev python3-pip libfreetype6-dev libjpeg-dev libopenjp2-7 libtiff5 -y
sudo pip3 install setuptools
sudo pip3 install --upgrade luma.led_matrix
https://youtu.be/BImKhs59hU0
https://github.com/freedomwebtech/max7219voicecontrol

##### install LCD 20x4 #####
sudo pip3 install RPLCD
#sudo apt-get install python-smbus
sudo pip install smbus2
sudo apt-get install pigpio python-pigpio python3-pigpio

##### install DS3231 แบบที่1 #####
1.เปิดใช้งาน I2C:
เปิดไฟล์ /boot/config.txt ด้วยบรรทัดคำสั่งต่อไปนี้: 
    sudo nano /boot/config.txt
    *ตรวจสอบว่ามีบรรทัด dtparam=i2c_arm=on และ dtparam=i2c1=on         
    ถูกเพิ่มหรือไม่ ถ้าไม่มีให้เพิ่มแล้วบันทึกไฟล์

2.ติดตั้งและกำหนดค่าแพ็กเกจของ RTC ผ่านคำสั่งต่อไปนี้: 
    sudo apt-get update
    sudo apt-get install -y python-smbus i2c-tools

3.เปิดไฟล์ /etc/modules ด้วยคำสั่งต่อไปนี้: 
    sudo nano /etc/modules
    เพิ่มบรรทัด rtc-ds3231 และบันทึกไฟล์

4.เปิดไฟล์ /etc/rc.local โดยใช้คำสั่ง:
    sudo nano /etc/rc.local
    4.1 ก่อนบรรทัด exit 0 เพิ่มบรรทัดต่อไปนี้และบันทึกไฟล์:
        echo ds3231 0x68 | tee /sys/class/i2c-adapter/i2c-1/new_device
        รีสตาร์ท Raspberry Pi

5.หลังจากติดตั้งแพ็กเกจเสร็จสิ้น ให้ใช้คำสั่ง: 
    sudo i2cdetect -y 1 เพื่อตรวจสอบที่อยู่ของ RTC ในบรรทัดที่แสดงผล

6.ตั้งค่า Raspberry Pi เพื่อใช้เวลาจาก DS3231:
เปิดไฟล์ /lib/udev/hwclock-set ด้วยคำสั่งต่อไปนี้: 
    sudo nano /lib/udev/hwclock-set

    *ค้นหาบรรทัด if [ -e /run/systemd/system ] และทำการแก้ไขให้ดูเหมือนนี้:
        if [ -e /run/systemd/system ] ; then
            exit 0
        fi

7.เปิด Raspberry Pi Terminal ปิดการใช้งาน "fake-hwclock" โดยใช้คำสั่งต่อไปนี้:
    sudo systemctl stop fake-hwclock
    
    7.1 ตั้งค่าเวลาใน DS3231 RTC โดยใช้คำสั่งต่อไปนี้: 
        sudo hwclock -w
    7.2 เปิดใช้งาน DS3231 RTC เพื่อให้ Raspberry Pi อ้างอิงเวลาจากนั้น โดยใช้คำสั่งต่อไปนี้: 
        sudo hwclock -s
    7.3 เปิดการใช้งาน "fake-hwclock" อีกครั้งเพื่อรักษาการจดจำเวลาของ Raspberry Pi ในกรณีที่ DS3231 RTC ไม่สามารถอ่านได้ในอนาคต: 
        sudo systemctl start fake-hwclock
    7.4 รีสตาร์ท Raspberry Pi เพื่อให้การตั้งค่ามีผลสมบูรณ์: 
        sudo reboot
***เมื่อ Raspberry Pi เริ่มต้นใหม่ จะใช้เวลาจาก DS3231 RTC เป็นเวลาหลักของระบบ และจะปรับเวลาเองโดยอัตโนมัติจาก RTC เมื่อ Raspberry Pi เชื่อมต่อกับอินเทอร์เน็ต หรือหากเกิดเหตุการณ์เปลี่ยนแปลงเวลา (เช่น เมื่อรีสตาร์ทหรือตั้งค่าเวลาใหม่ใน Raspberry Pi)

##### install DS3231 แบบที่2 #####
sudo apt-get update
sudo apt-get install -y python-smbus i2c-tools

1.เปิดไฟล์ /etc/modules โดยใช้คำสั่ง sudo nano /etc/modules
เพิ่มบรรทัดต่อไปนี้และบันทึกไฟล์:
    i2c-bcm2708
    i2c-dev

2.เปิดไฟล์ /etc/rc.local โดยใช้คำสั่ง sudo nano /etc/rc.local
ก่อนบรรทัด exit 0 เพิ่มบรรทัดต่อไปนี้และบันทึกไฟล์:
    sudo i2cdetect -y 1
    รีสตาร์ท Raspberry Pi

3.ทดสอบการทำงานของ RTC:
เปิด Terminal และใช้คำสั่งต่อไปนี้เพื่อตรวจสอบการติดต่อกับ RTC:
    sudo i2cdetect -y 1

4.อ่านค่าจาก DS3231:
    sudo hwclock -r

5.ให้โมดูล DS3231 RTC อัปเดตค่าเวลาของตัวเองจากอินเตอร์เน็ตผ่าน Raspberry Pi:
    sudo nano /etc/systemd/timesyncd.conf
    sudo systemctl restart systemd-timesyncd

6.เพื่อให้ Raspberry Pi อัปเดตเวลาจาก DS3231 RTC เมื่อไม่มีการเชื่อมต่ออินเตอร์เน็ต ใช้โค้ด Python เพื่อเรียกใช้งาน API ของ NTP เพื่ออัปเดตเวลาใน Raspberry Pi เมื่อมีการเชื่อมต่ออินเตอร์เน็ตอยู่ และให้ Raspberry Pi ใช้เวลาจาก DS3231 RTC เมื่อไม่มีการเชื่อมต่ออินเตอร์เน็ต ดังนี้:

**ติดตั้งไลบรารี Python ntplib โดยใช้คำสั่งต่อไปนี้ใน Terminal:
    pip install ntplib
    ตัวอย่างโค้ด DS3231.py


##### install Keypad 4x4 #####
keypad_rows = [22, 27, 18, 17]
keypad_cols = [20, 16, 26, 19]

##### PIN GPIO SETUP #####
DS3231:
    POWER = 5V
    POWER = GND
    SDA I2C = GPIO 02
    SCL I2C = GPIO 03
    
LCD:
    POWER = 5V
    POWER = GND
    SDA I2C = GPIO 02
    SCL I2C = GPIO 03

LED DOTMATRIX:
    POWER = 5V
    POWER = GND
    DIN = GPIO 10
    CS = GPIO 08
    CLK = GPIO 11 (SPI0)

KEYPAD 4x4 LEFT >> RIGHT
    GPIO 17
    GPIO 18
    GPIO 27
    GPIO 22
    GPIO 19
    GPIO 26
    GPIO 16
    GPIO 20

##### หมายเหตุ #####
โปรแกรมสำหรับใช้ในห้อง IPC ใช้ appscript ในการรับข้อมูล
    ดูรหัสโครงการ https://console.cloud.google.com/home/dashboard?project=weighttable
    Project name: WeightTable
    Project number: 86238157032
    Project ID: weighttable

    *** นำ Project number ไปใส่ในตั้งค่า***
    *โครงการ Google Cloud Platform (GCP)
    *โครงการ Apps Script ใช้ Google Cloud Platform เพื่อจัดการการให้สิทธิ์ บริการขั้นสูง และรายละเอียดอื่นๆ *หากต้องการดูข้อมูลเพิ่มเติม โปรดไปที่ Google Cloud Platform


โปรแกรมสำหรับใช้ในห้องตอก ใช้ API ในการส่งข้อมูล