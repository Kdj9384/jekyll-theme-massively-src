#!/usr/bin/env python
#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#  lcd_i2c.py
#  LCD test script using I2C backpack.
#  Supports 16x2 and 20x4 screens.
#
# Author : Matt Hawkins
# Date   : 20/09/2015
#
# http://www.raspberrypi-spy.co.uk/
#
# Copyright 2015 Matt Hawkins
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#--------------------------------------
import smbus
import time
import vlc
import os
import RPi.GPIO as GPIO
import ftplib
import os

# Define some device parameters
I2C_ADDR  = 0x27 # I2C device address
LCD_WIDTH = 16   # Maximum characters per line

# Define some device constants
LCD_CHR = 1 # Mode - Sending data
LCD_CMD = 0 # Mode - Sending command

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

LCD_BACKLIGHT  = 0x08  # On
#LCD_BACKLIGHT = 0x00  # Off

ENABLE = 0b00000100 # Enable bit

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

#Open I2C interface
#bus = smbus.SMBus(0)  # Rev 1 Pi uses 0
bus = smbus.SMBus(1) # Rev 2 Pi uses 1

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off 
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = the data
  # mode = 1 for data
  #        0 for command

  bits_high = mode | (bits & 0xF0) | LCD_BACKLIGHT
  bits_low = mode | ((bits<<4) & 0xF0) | LCD_BACKLIGHT

  # High bits
  bus.write_byte(I2C_ADDR, bits_high)
  lcd_toggle_enable(bits_high)

  # Low bits
  bus.write_byte(I2C_ADDR, bits_low)
  lcd_toggle_enable(bits_low)

def lcd_toggle_enable(bits):
  # Toggle enable
  time.sleep(E_DELAY)
  bus.write_byte(I2C_ADDR, (bits | ENABLE))
  time.sleep(E_PULSE)
  bus.write_byte(I2C_ADDR,(bits & ~ENABLE))
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
    
def m_playing(player,a):
  while True:
    state = player.get_state()
    if state == 6:
      if a[i] == a[-1]:
        i = 0
        media = instance.media_new(path_m + a[i])
        player.set_media(media)
        player.play()
        time.sleep(1)
      
      i += 1
      media = instance.media_new(path_m + a[i])
      player.set_media(media)
      player.play()
      time.sleep(1)
    
    if GPIO.input(18) == 0:
      time.sleep(0.7)
      break
    if GPIO.input(23) == 0:
      time.sleep(0.7)
      player.pause()
    if GPIO.input(24) == 0:
      time.sleep(0.7)
      player.stop()
      break

def main():
  # Main program block
  stopcnt = 0
  # Initialise display
  lcd_init()
  lcd_string("    LOADING    ",LCD_LINE_1)
  lcd_string("....    ",LCD_LINE_2)
  
  templist = []
  dir_list = []
  dir_list1 = []
  music_list = []
  ftpn = ftplib.FTP('192.168.0.114','root','openmediavault')
  ftpn.cwd('/mediastorage')
  ftpn.retrlines("LIST", templist.append)
  i = 0;

  while i<len(templist):
    word = templist[i].split(None,8)
    filename = word[-1].lstrip()
    dir_list.append(filename)
    i+=1
    
  i = 0
  j = 0
  while i<len(dir_list):
    ch_name = dir_list[i]
    print(ch_name)
    ftpn.cwd("/mediastorage/"+ch_name)
    music_list = ftpn.nlst()
    print(music_list)
    path = "/home/pi/Downloads/"+ch_name
    if not os.path.isdir(path):
      os.mkdir(path)
    while j<len(music_list):
      if not os.path.isfile(path+"/"+music_list[j]):
        fd = open("/home/pi/Downloads/"+ch_name+"/"+music_list[j], 'wb')
        ftpn.retrbinary("RETR /mediastorage/"+ch_name+"/"+music_list[j], fd.write)
        fd.close()
      j+=1
    j=0 
    i+=1

  GPIO.setmode(GPIO.BCM)
  GPIO.setup(22, GPIO.IN)
  GPIO.setup(23, GPIO.IN)
  GPIO.setup(24, GPIO.IN)
  GPIO.setup(18, GPIO.IN)
  #GPIO.setup(21, GPIO.IN)

  instance = vlc.Instance()
  player = instance.media_player_new()

  if os.path.isfile("/home/pi/Downloads/load.txt"):
    f = open("/home/pi/Downloads/load.txt", 'r')
    line = f.readline()
    if line == None:
      index = 0
    else:
      loadindex = dir_list.index(line)
      index = loadindex
  else:
    index = 0
    
  while True:  
    path_m = "/home/pi/Downloads/"+dir_list[index]+"/"
    i = 0
    a = os.listdir(path_m)
    media = instance.media_new(path_m+ a[i])
    player.set_media(media)
    
    
    player.play()
    while True:
      lcd_string(a[i],LCD_LINE_1)
      lcd_string("Channel : "+dir_list[index],LCD_LINE_2)
      print(a[i])
      print(a)
      
      state = player.get_state()
      if state == 6:
        if a[i] == a[-1]:
          i = 0
          media = instance.media_new(path_m + a[i])
          lcd_string(a[i],LCD_LINE_1)
          player.set_media(media)
          player.play()
          time.sleep(1)
          continue
        
        i += 1
        media = instance.media_new(path_m + a[i])
        lcd_string(a[i],LCD_LINE_1)
        player.set_media(media)
        player.play()
        time.sleep(1)
      
      if GPIO.input(18) == 0: #next
        time.sleep(0.7)
        break
      if GPIO.input(23) == 0: #pause
        time.sleep(0.7)
        player.pause()
      if GPIO.input(24) == 0: #stop
        time.sleep(3)
        stopcnt += 1

        loadfile = open("/home/pi/Downloads/load.txt", 'w')
        loadfile.write(dir_list[index])
        loadfile.close()
        break
      
    if dir_list[-1] == dir_list[index]:
      index = 0
    else:
      index += 1
        
    if stopcnt == 1:
      break
    
  lcd_string("Good Bye",LCD_LINE_1)
  lcd_string("4",LCD_LINE_2)
  time.sleep(1)
  lcd_string("3",LCD_LINE_2)
  time.sleep(1)
  lcd_string("2",LCD_LINE_2)
  time.sleep(1)
  lcd_string("1",LCD_LINE_2)
  time.sleep(1)
  
if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(0x01, LCD_CMD)


