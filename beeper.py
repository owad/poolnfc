import RPi.GPIO as GPIO
from time import sleep


def beep(beeps=1, length=0.25):
    for i in range(beeps):
        # set pin to HIGH
        print "BEEP!!1"
        sleep(length)
        # set ping to LOW
