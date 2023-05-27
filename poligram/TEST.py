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

main()