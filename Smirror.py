"""
Inputs and outputs: 
DIGITAL----------
Ultrasonic Sensor - LED for Video Recording - LED for AC 
Switch for Recording Start - Switch for flask - Switch Capture
ANALOG-----------
Indoor Temp Sensor - Outdoor Temp Sensor (Potentiometer)
LED for Outdoor Light Intensity
Buzzer for PWM to indicate recording start and stop or for music
OTHER------------
Keypad and RFID for interrupt to start flask server
Flask server will let user look at pictures taken (Dynamic Route)
Flask server will also include static route to download video
Flask server will also include static route to check sensor readings
Temperature shown on LCD
"""
import RPi.GPIO as gpio
import time
import serial
from flask import Flask
from flask import send_file
import LCD1602 as lcd
import PCF8591 as adc
from picamera import PiCamera
# ----------------------------
# GPIO pin numbering
rfidpass = "5300C8121A"
trig = 18
echo = 27
buz = 10
ledvid = 6  # red
ledac = 12  # blue
recstart = 17  # Switch 1
flaskint = 16  # Switch 8
capt = 13  # Switch 4
# ----------------------------
# GPIO Setup
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(buz, gpio.OUT)
gpio.setup(trig, gpio.OUT)
gpio.setup(echo, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(ledvid, gpio.OUT)
gpio.setup(ledac, gpio.OUT)
gpio.setup(recstart, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(flaskint, gpio.IN, pull_up_down=gpio.PUD_DOWN)
gpio.setup(capt, gpio.IN, pull_up_down=gpio.PUD_DOWN)
# ----------------------------
# Songs for buzzer
CL = [0, 131, 147, 165, 175, 196, 211, 248]     # Frequency of Low C notes

CM = [0, 262, 294, 330, 350, 393, 441, 495]     # Frequency of Middle C notes

CH = [0, 525, 589, 661, 700, 786, 882, 990]     # Frequency of High C notes

song_1 = [CM[3], CM[5], CM[6], CM[3], CM[2], CM[3], CM[5], CM[6],  # Notes of song1
          CH[1], CM[6], CM[5], CM[1], CM[3], CM[2], CM[2], CM[3],
          CM[5], CM[2], CM[3], CM[3], CL[6], CL[6], CL[6], CM[1],
          CM[2], CM[3], CM[2], CL[7], CL[6], CM[1], CL[5]]

beat_1 = [1, 1, 3, 1, 1, 3, 1, 1,             # Beats of song 1, 1 means 1/8 beats
          1, 1, 1, 1, 1, 1, 3, 1,
          1, 3, 1, 1, 1, 1, 1, 1,
          1, 2, 1, 1, 1, 1, 1, 1,
          1, 1, 3]

song_2 = [CM[1], CM[1], CM[1], CL[5], CM[3], CM[3], CM[3], CM[1],  # Notes of song2
          CM[1], CM[3], CM[5], CM[5], CM[4], CM[3], CM[2], CM[2],
          CM[3], CM[4], CM[4], CM[3], CM[2], CM[3], CM[1], CM[1],
          CM[3], CM[2], CL[5], CL[7], CM[2], CM[1]]

beat_2 = [1, 1, 2, 2, 1, 1, 2, 2,             # Beats of song 2, 1 means 1/8 beats
          1, 1, 2, 2, 1, 1, 3, 1,
          1, 2, 2, 1, 1, 2, 2, 1,
          1, 2, 2, 1, 1, 3]


def song1():
    Buzz.stop()
    Buzz.start(50)
    for i in range(1, len(song_1)):     # Play song 1
        # Change the frequency along the song note
        Buzz.ChangeFrequency(song_1[i])
        time.sleep(beat_1[i] * 0.1)     # delay a note for beat * 0.5s
    Buzz.stop()


def song2():
    Buzz.stop()
    Buzz.start(50)
    print "\nGoodbye"
    for i in range(1, len(song_2)):     # Play song 2
        # Change the frequency along the song note
        Buzz.ChangeFrequency(song_2[i])
        time.sleep(beat_2[i] * 0.1)     # delay a note for beat * 0.5s
    Buzz.stop()


# ----------------------------
#Initializations and setup
adc.setup(0x48)
lcd.init(0x27, 1)
Buzz = gpio.PWM(buz, 100)
mycam = PiCamera()
mycam.resolution = (640, 480)
# ----------------------------
# RFID initialization
SERIAL_PORT = '/dev/ttyS0'
ser = serial.Serial(baudrate=2400,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    port=SERIAL_PORT,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=1)


def validate_rfid(code):
    s = code.decode("ascii")
    if (len(s) == 12) and (s[0] == "\n") and (s[11] == "\r"):
        return s[1:-1]
    else:
        return False


# ----------------------------
# Keypad initialization
gpio.setup(19, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(20, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(21, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(22, gpio.IN, pull_up_down=gpio.PUD_UP)
gpio.setup(23, gpio.OUT)
gpio.setup(24, gpio.OUT)
gpio.setup(25, gpio.OUT)
gpio.setup(26, gpio.OUT)


def keypad():
    while(True):

        gpio.output(26, gpio.LOW)
        gpio.output(25, gpio.HIGH)
        gpio.output(24, gpio.HIGH)
        gpio.output(23, gpio.HIGH)

        if (gpio.input(22) == 0):
            return(1)
            break

        if (gpio.input(21) == 0):
            return(4)
            break

        if (gpio.input(20) == 0):
            return(7)
            break

        if (gpio.input(19) == 0):
            return(0xE)
            break

        gpio.output(26, gpio.HIGH)
        gpio.output(25, gpio.LOW)
        gpio.output(24, gpio.HIGH)
        gpio.output(23, gpio.HIGH)

        if (gpio.input(22) == 0):
            return(2)
            break

        if (gpio.input(21) == 0):
            return(5)
            break

        if (gpio.input(20) == 0):
            return(8)
            break

        if (gpio.input(19) == 0):
            return(0)
            break

        gpio.output(26, gpio.HIGH)
        gpio.output(25, gpio.HIGH)
        gpio.output(24, gpio.LOW)
        gpio.output(23, gpio.HIGH)

        if (gpio.input(22) == 0):
            return(3)
            break

        if (gpio.input(21) == 0):
            return(6)
            break
        # Scan row 2
        if (gpio.input(20) == 0):
            return(0XA)
            break

        if (gpio.input(19) == 0):
            return(0XF)
            break

        gpio.output(26, gpio.HIGH)
        gpio.output(25, gpio.HIGH)
        gpio.output(24, gpio.HIGH)
        gpio.output(23, gpio.LOW)

        if (gpio.input(22) == 0):
            return(0XA)
            break

        if (gpio.input(21) == 0):
            return(0XB)
            break

        if (gpio.input(20) == 0):
            return(0XC)
            break

        if (gpio.input(19) == 0):
            return(0XD)
            break

# ----------------------------
# Ultrasonic Sensor Function


def distance():
    # Warming up the sensor
    gpio.output(trig, 0)
    time.sleep(0.000002)
    # Sending the trigger to send a signal
    gpio.output(trig, 1)
    time.sleep(0.00001)
    gpio.output(trig, 0)
    # Waiting for the return (echo) signal
    while gpio.input(echo) == 0:
        continue
    # Recording time at the beginning of the return signal
    t1 = time.time()
    while gpio.input(echo) == 1:
        continue
    # Recording time at the end of the return signal
    t2 = time.time()
    # Calculatin total time for signal and converting to cm
    duration = t2-t1
    dist = duration*1000000/58
    return dist
# ----------------------------
# Temperature Function


def temp(n):
    n = int(n)
    tempunit = adc.read(n)
    tempvolt = tempunit*3.3/256
    tempc = tempvolt/0.01
    return (tempc, tempunit)
# ----------------------------
# Light Intensity


def light(n):
    n = int(n)
    lightunit = adc.read(n)
    lightvolt = lightunit*3.3/256
    lightl = lightvolt * 394
    lightl = int(lightl)
    return (lightl, lightunit)


# ----------------------------
# Flask Server
app = Flask(__name__)
@app.route("/mirror")
def home():
    global tp, otp, lint  # Indoor Temp, Outdoor Temp, Outdoor Light intensity
    tp = float(tp)
    otp = float(otp)
    lint = int(lint)
    out = "Welcome to SMirror\nIndoor Temperature is: %2.2fC\nOutdoor Temperature is: %2.2fC\nOutdoor Light Intensity is %d Lumens" % (
        tp, otp, lint)
    return out


@app.route("/image/<n>")
def pics(n):
    n = str(n)
    photo = send_file("/home/pi/Desktop/smirror/image%s.jpg" %
                      n, mimetype='image/jpg')
    return photo


@app.route("/video")
def vid():
    video = send_file("/home/pi/Desktop/smirror/video.h264",
                      mimetype='video/h264')
    return video
# ----------------------------
# Interrupts


def action1(self):
    print "Taking Pictures!"
    for x in range(5):
        mycam.annotate_text = " "
        mycam.capture("/home/pi/Desktop/smirror/image%d.jpg" % x)


def action2(self):
    print "Recording a Video!"
    mycam.annotate_text = " "
    gpio.output(ledvid, 1)
    mycam.start_recording("/home/pi/Desktop/smirror/video.h264")
    time.sleep(5)
    gpio.output(ledvid, 0)
    mycam.stop_recording()
    print "Done Recording!"


def action3(self):
    print "Starting Flask Server"
    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=5040)


gpio.add_event_detect(capt, gpio.RISING, callback=action1, bouncetime=2000)
gpio.add_event_detect(recstart, gpio.RISING, callback=action2, bouncetime=2000)
gpio.add_event_detect(flaskint, gpio.RISING, callback=action3, bouncetime=2000)
# ----------------------------
# Main
kpass = "1"
apass = "Empty"
data = "Empty"
print"Where are you?"
while distance() > 100:
    continue
print "Oh, Hello! Welcome to SMirror"
y = raw_input("Choose 0 for Keypad or 1 for RFID\n")
y = int(y)
if y == 0:
    while apass != kpass:
        print "Please Enter Password\n"
        x1 = keypad()
        x1 = str(x1)
        apass = x1
        if apass != kpass:
            print "Invalid Password\n"
else:
    while validate_rfid(data) != rfidpass:
        data = ser.read(12)
        print "Invalid RFID Tag\n"


song1()
mycam.start_preview()
print "\nWelcome to SMirror\n Flip switch 1 to take a picture, 4 to take a video and 8 to start the server"
try:
    while True:
        (tp, tpunits) = temp(2)
        (otp, otpunits) = temp(1)
        (lint, lintunits) = light(3)
        adc.write(lintunits)
        tp = float(tp)
        otp = float(otp)
        otp = otp/5.00
        time.sleep(0.5)
        if tp >= 23:
            lcd.clear()
            gpio.output(ledac, 1)
            lcd.write(0, 0, "AC is ON")
            lcd.write(0, 1, "Room Temp: %2.2fC" % tp)
        else:
            lcd.clear()
            gpio.output(ledac, 0)
            lcd.write(0, 0, "AC is OFF")
            lcd.write(0, 1, "Room Temp: %2.2fC" % tp)

        if lint <= 650:
            if otp <= 20:
                mycam.annotate_text = "SMirror\nGood Evening. Grab a jacket, its %2.2fC outside!" % otp
            else:
                mycam.annotate_text = "SMirror\nGood Evening. Its %2.2fC outside!" % otp
        else:
            if otp <= 20:
                mycam.annotate_text = "SMirror\nGood Morning, grab some sunglasses, its bright outside. Grab a jacket, its %2.2fC   outside!" % otp
            else:
                mycam.annotate_text = "SMirror\nGood Morning, grab some sunglasses, its bright outside. Its %2.2fC outside!" % otp
        time.sleep(0.5)

# ctrl+c:
except KeyboardInterrupt:
    song2()
    mycam.stop_preview()
    gpio.cleanup()

