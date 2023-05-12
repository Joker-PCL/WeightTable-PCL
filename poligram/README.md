## ============================================================================##
##                              Dev.  Nattapon                                 ##
##                       Program Author and Designer                           ##
## ============================================================================##
## ต้องใช้คำสั่ง sudo su pip install google-api-python-client 

#รายการอัพเดท
update 16/7/2022  ส่งเวลา และวันที่ อัตโนมัติ
                  ส่งเวลา Range ที่จะลงข้อมูลครั้งถัดไป,ส่งไลน์แจ้งเตือนเมื่อน้ำหนักไม่ได้อยู่ในช่วง
update 08/1/2023  เพิ่มการบันทึกข้อมูลแบบ offline กรณีไม่สามารถเชื่อมต่อ internet ได้
                  โดยไฟล์จะบันทึกไว้ใน json_dir = "/home/pi/Json_offline/data_offline.json"
update 08/5/2023  ใช้การแสกนบัตร rfid 125khz ในการเข้าใช้งาน
                  ดึงข้อมูลการรายชื่อ การตั้งค่ามาเก็บไว้ที่ตัวเครื่อง


##### จำเป็นต้องติดตั้ง Libraries ที่จำเป็นถึงจะสามารถใช้งานได้ #####
sudo apt update
sudo su pip install --upgrade google-api-python-client
pip install requests
pip install keyboard
sudo apt install python3-gpiozero

##### install LEDDOTMATRIX  #####
sudo usermod -a -G spi,gpio pi
#sudo apt install build-essential python3-dev python3-pip libfreetype6-dev libjpeg-dev libopenjp2-7 libtiff5 -y
sudo pip3 install setuptools
sudo pip3 install --upgrade luma.led_matrix
https://youtu.be/BImKhs59hU0
https://github.com/freedomwebtech/max7219voicecontrol

#####   install LCD 20x4    #####
sudo pip3 install RPLCD
#sudo apt-get install python-smbus
sudo pip install smbus2
sudo apt-get install pigpio python-pigpio python3-pigpio
