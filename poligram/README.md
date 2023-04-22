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

#####   install LCD 20x4    #####
sudo pip3 install RPLCD
#sudo apt-get install python-smbus
sudo pip install smbus2
sudo apt-get install pigpio python-pigpio python3-pigpio