#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time
import tables

SDI   = 17
RCLK  = 18
SRCLK = 27

per_line = [0xfe, 0xfd, 0xfb, 0xf7, 0xef, 0xdf, 0xbf, 0x7f]


class Keypad():

    def __init__(self, rowsPins, colsPins, keys):
        self.rowsPins = rowsPins
        self.colsPins = colsPins
        self.keys = keys
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.rowsPins, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.colsPins, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def read(self):
        pressed_keys = []
        for i, row in enumerate(self.rowsPins):
            GPIO.output(row, GPIO.HIGH)
            for j, col in enumerate(self.colsPins):
                index = i * len(self.colsPins) + j
                if (GPIO.input(col) == 1):
                    pressed_keys.append(self.keys[index])
            GPIO.output(row, GPIO.LOW)
        return pressed_keys

def setup():
    global keypad, last_key_pressed, first_num, second_num, operator
    rowsPins = [19,23,24,25]
    colsPins = [10,22,26,16]
    keys = ["1","2","3","A",
            "4","5","6","B",
            "7","8","9","C",
            "*","0","#","D"]
    keypad = Keypad(rowsPins, colsPins, keys)
    last_key_pressed = []
    first_num = None
    second_num = None
    operator = None
    GPIO.setup(SDI, GPIO.OUT)
    GPIO.setup(RCLK, GPIO.OUT)
    GPIO.setup(SRCLK, GPIO.OUT)
    GPIO.output(SDI, GPIO.LOW)
    GPIO.output(RCLK, GPIO.LOW)
    GPIO.output(SRCLK, GPIO.LOW)

def hc595_in(dat):
	for bit in range(0, 8):	
		GPIO.output(SDI, 1 & (dat >> bit))
		GPIO.output(SRCLK, GPIO.HIGH)
		time.sleep(0.000001)
		GPIO.output(SRCLK, GPIO.LOW)

def hc595_out():
	GPIO.output(RCLK, GPIO.HIGH)
	time.sleep(0.000001)
	GPIO.output(RCLK, GPIO.LOW)

def flash(table):
	for i in range(8):
		hc595_in(per_line[i])
		hc595_in(table[i])
		hc595_out()
	# Clean up last line
	hc595_in(per_line[7])
	hc595_in(0x00)
	hc595_out()

def show(table, second):
	start = time.time()
	while True:
		flash(table)
		finish = time.time()
		if finish - start > second:
			break

def rotate_90_left(data):

    rotated = []

    if not data:
        return rotated

    for col in range(8):
        new_row = 0
        for row in range(8):
            new_row |= ((data[row] >> col) & 0x01) << (7 -row)
        rotated.append(new_row)
    return rotated

def add(first_num: int, second_num: int):
    result = first_num + second_num
    print(f'{first_num} + {second_num} = {result}')
    show(rotate_90_left(tables.charactors.get(str(result))),3)  
    
def subtract(first_num: int, second_num: int):
    result = first_num - second_num
    print(f'{first_num} - {second_num} = {result}')
    show(rotate_90_left(tables.charactors.get(str(result))),3)  
    
def times(first_num: int, second_num: int):
    result = first_num * second_num
    print(f'{first_num} * {second_num} = {result}')
    show(rotate_90_left(tables.charactors.get(str(result))),3)  

def divide(first_num: int, second_num: int):
    if second_num == 0:
        print("Can't divide by zero")
        show(rotate_90_left(tables.charactors.get('E')),3)
    else:
        result = first_num // second_num
        print(f'{first_num} // {second_num} = {result}')
        show(rotate_90_left(tables.charactors.get(str(result))),3)  

def check_int(value: str):
    try:
        int(value)
        return True
    except Exception:
        return False


def loop():
    global keypad, last_key_pressed, first_num, second_num, operator
    
    pressed_keys = keypad.read()
   
    if len(pressed_keys) != 0:
        print(f'pressed_keys: {pressed_keys}')
        print(f'last_key_pressed: {last_key_pressed}')
        show(rotate_90_left(tables.charactors.get(pressed_keys[0])),1)

        now_key = pressed_keys[0] if pressed_keys else ''
        last_key = last_key_pressed[0] if last_key_pressed else ''

        if last_key in ['A','B','C','D','*'] and check_int(now_key):
            operator = last_key
            second_num = now_key    

        if check_int(now_key):
            if check_int(last_key):
                first_num = last_key + now_key
            elif not second_num:
                first_num = now_key
	    
        print(f'first_num: {first_num}')
        print(f'second_num: {second_num}')
        print(f'operator: {operator}')

        if now_key == '#':
            if operator == 'A':
                add(int(first_num), int(second_num))

            if operator == 'B':
                subtract(int(first_num), int(second_num))
            
            if operator in ['C', '*']:
                times(int(first_num), int(second_num))

            if operator == 'D':
                divide(int(first_num), int(second_num))

            first_num = None
            second_num = None
            operator = None
	    
        last_key_pressed = pressed_keys
	
    time.sleep(0.1)

# Define a destroy function for clean up everything after the script finished
def destroy():
    # Release resource
    GPIO.cleanup() 

if __name__ == '__main__':     # Program start from here
    try:
        setup()
        while True:
            loop()
    except KeyboardInterrupt:   # When 'Ctrl+C' is pressed, the program destroy() will be executed.
        destroy()
