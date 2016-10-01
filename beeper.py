# -*- coding: utf8 -*-
import RPi.GPIO as gpio
from time import sleep

gpio.setmode(gpio.BOARD)
gpio.setup(8, gpio.OUT)
gpio.output(8, gpio.LOW)


def beep(beeps=1, length=0.25):
    for _ in range(beeps):
        gpio.output(8, gpio.HIGH)
        sleep(length)
        gpio.output(8, gpio.LOW)
        sleep(0.25)


