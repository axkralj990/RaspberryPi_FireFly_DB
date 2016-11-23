import pygatt.backends
import paho.mqtt.client as mqtt
import time
import timeit
import threading
import sys
import json
from datetime import datetime

global client
global devices
global continuousRead
continuousRead = []

class BLEdevice:

    deviceCount = 0
    busy = False
    
    def __init__(self, name, mac, interval, command):
        self.name = name
        self.mac = mac
        self.interval = interval
        self.command = command
        self.newCommand = ""
        self.commandToSend = False
        self.end = False
        BLEdevice.deviceCount += 1

    def lowerCount(self):
        BLEdevice.deviceCount -= 1

    def makeBusy(self):
        BLEdevice.busy = True

    def free(self):
        BLEdevice.busy = False

    def endThread(self):
        self.end = True

    def changeCommand(self, newCommand, newInterval):
        self.command = newCommand
        self.interval = newInterval

def readChar(firefly,mac):
    received = firefly.char_read_hnd(24)
            
def tryConnect(adapter2, mac):

    error = 0
    
    while True:
        try:
            print("Trying to connect...")
            if(error > 3):
                return 'null'
            else:
                return(adapter2.connect(mac, 5, 'random'))
            break
        except pygatt.exceptions.NotConnectedError:
            error += 1
            print("Had an Error...")
            time.sleep(2)
            pass


def writeCommand(firefly, endNode, cmd):
    cmd = endNode + cmd
    firefly.char_write_handle(24, map(ord, cmd))

def scanForDevices():
    print("Scanning...")
    return(adapter.scan(3,True))

class myThread(threading.Thread):

    def __init__(self, threadID, device):
        print("Thread initialized!")
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.device = device

    def run(self):
        print("Thread started!")
        loopRead(self.threadID, self.device)
        print("Thread ended!")

def write2File(telemetryData):
    with open('telemetry.json','a') as outfile:
        json.dump(telemetryData, outfile)

def loopRead(thread, device):
    print("loopRead function")
    error = 0
    connection = None
    adapterTmp = pygatt.backends.GATTToolBackend()
    #adapterTmp.reset()
    adapterTmp.start()
    passed = False
    
    while True:
        if(passed == False):
            time1 = time.clock()

        #   ending thread if we got "kill continuous response" command
        if(device.end == True):
            device.makeBusy()
            try:
                writeCommand(connection, device.name, device.command)
            except:
                connection = tryConnect(adapterTmp, device.mac)
                try:
                    writeCommand(connection, device.name, device.command)
                except:
                    pass
            device.free()
            if(connection != None):
                connection.disconnect()
            break
        
        try:
            if(error > 2):
                error = 0
                connection = None

            if(connection is None and device.busy == False):
                device.makeBusy()
                connection = tryConnect(adapterTmp, device.mac)
                try:
                    writeCommand(connection, device.name, device.command)
                except:
                    pass
                device.free()
                time.sleep(0.1)
            if(connection != None):
                passed = False
                received = connection.char_read_hnd(24)
                #print(received)
                if(len(received) > 30):
                    publishData(received,client)
                error = 0
                if(device.commandToSend == True):
                    try:
                        writeCommand(connection, device.name, device.newCommand)
                    except:
                        pass
                    device.commandToSend = False
        except pygatt.exceptions.NotificationTimeout:
            error += 1
            passed = True
            print("passed ")
            #print(thread)
        
        if(passed == False):
            time2 = time.clock()
            delay1 = device.interval - (time2 - time1)

            if(delay1 < 0):
                delay1 = 0

            #   this part of the code disconnects from FlyTag module so it's visible by other devices,
            #   in this case if interval is longer than 10seconds
            if(device.interval >= 10 and connection != None):
                connection.disconnect()
                connection = None
            time.sleep(delay1)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("FFcmd/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def publishData(data,clientMQTT):

    g2x = (data[4] << 8) | (data[5])
    g2y = (data[6] << 8) | (data[7])
    g2z = (data[8] << 8) | (data[9])

    gx = g2x * 0.003125
    gy = g2y * 0.003125
    gz = g2z * 0.003125

    ax = (data[10] << 8) | data[11]
    ay = (data[12] << 8) | data[13] 
    az = (data[14] << 8) | data[15] 

    a1x = ax / 16384.0
    a1y = ay / 16384.0
    a1z = az / 16384.0

    if (data[10] > 127):
        a1x = a1x - 4.0
    if (data[12]> 127):
        a1y = a1y - 4.0
    if (data[14]> 127):
        a1z = a1z - 4.0

    mx = (data[16] << 8) | data[17]
    my = (data[18] << 8) | data[19] 
    mz = (data[20] << 8) | data[21]

    if (data[16] > 127):
        mx = mx - 65536
    if (data[18]> 127):
        my = my - 65536
    if (data[20]> 127):
        mz = mz - 65536

    lux = (data[26] << 8) | data[27]

    t = (data[22] << 8) | data[23]
    temp = ((175.72 * t) / 65536) - 46.85
    
    rh = (data[24] << 8) | data[25]
    humid = ((125.0 * rh) / 65536) - 6

    analog = data[30]
    
    #sendData = ("{\"d\": {\"ID\":\"FF-%c%c%c\",\"gX\":%.2f,\"gY\":%.2f,\"gZ\":%.2f,\"aX\":%.2f,\"aY\":%.2f,\"aZ\":%.2f,\"mX\":%d,\"mY\":%d,\"mZ\":%d,\"Lux\": %d, \"Temp\": %.1f,\"RelHum\" :%.1f, \"Analog\":%d}}" % (data[0],data[1], data[2], gx, gy, gz, a1x, a1y, a1z, mx, my, mz, lux, temp, humid, analog))
    device_name = ("FF-%c%c%c" %(data[0],data[1], data[2]))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    telemetryData = {"timestamp": timestamp, "ID": device_name,"gyro_X": gx, "gyro_Y": gy, "gyro_Z": gz, "accel_X": a1x, "accel_Y": a1y, "accel_Z": a1z, "mag_X": mx, "mag_Y": my, "mag_Z": mz, "lux": lux, "temp": temp, "humid": humid, "analog": analog}
    #testTelemetry = {"timestamp": timestamp, "ID": device_name}
    telemetryData = str(telemetryData)
    topicStr = "FFS/"+device_name
    clientMQTT.publish(topicStr,str(telemetryData))

try:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.64.104",1883,60)

    adapter = pygatt.backends.GATTToolBackend()
    adapter.reset()
    adapter.start()
    devices = scanForDevices()

    print("Devices found:")
    print(devices)
    
    connect = 0;
    for i in range(len(devices)):
        if(connect<3):
            if(devices[i]['name'].startswith('FF-')):
                print("FireFly address:")
                print(devices[i]['address'])
                print("FireFly name:")
                print(devices[i]['name'][3:6])
                device = BLEdevice(devices[i]['name'][3:6], devices[i]['address'], 5, '0001305')
                t = myThread(device.deviceCount, device)
                t.start()
                continuousRead.append(t)
                #print("reading")
                print("Device count:")
                print(t.device.deviceCount)
                connect+=1
    
    while(True):
        print("main")
        client.loop_forever()

#SHOULD BE A MULTILINE COMMENT
#print("DEVICE 0 ADDRESS:")
#print(devices[0]['address'])
#print("DEVICE 0 NAME:")
#print(devices[0]['name'])

#device = tryConnect(adapter,'D8:FB:3E:14:97:61')
#writeCommand(device,'FF-275','0001305')

#while True:
#    writeCommand(device,'FF-275','0001305')
#    time.sleep(1)
#    try:
#        received = device.char_read_hnd(24)
#        if(len(received)>30):
#            publishData(received)
#        pass_ctn = 0
#    except pygatt.exceptions.NotificationTimeout:
#        print("PASSED")
#        pass_ctn += 1
#    if (pass_ctn >= 10):
#        break


except KeyboardInterrupt:
    print("Exiting program!")
    for item in continuousRead:
        item.device.lowerCount()
        item.device.changeCommand("0002", 10)
        item.device.endThread()
        continuousRead.remove(item)
        print(continuousRead)
        
    sys.exit(1)

