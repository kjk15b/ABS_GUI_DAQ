'''
Abilene Buoy Systems

Authors: Kelsey Shelton, Kolby Kiesling

Emails: kxs15c@acu.edu , kjk15b@acu.edu

This program serves as a simple GUI interface for handling data-acquisition on a Raspberry Pi
'''

# General imports
from tkinter import *
import tkinter
from tkinter import ttk
import numpy as np
from matplotlib import pyplot as plt
import datetime
#import time
from matplotlib import colors
#from matplotlib import image as mpimg
from bs4 import BeautifulSoup as bs
import webbrowser
import warnings

warnings.filterwarnings("ignore") # bad practice, but deprecated warnings always come up


# Imports for the RF module
import busio
from digitalio import DigitalInOut, Direction, Pull
import board
import adafruit_ssd1306
import adafruit_rfm69


btnA = DigitalInOut(board.D5)
btnA.direction = Direction.INPUT
btnA.pull = Pull.UP

btnB = DigitalInOut(board.D6)
btnB.direction = Direction.INPUT
btnB.pull = Pull.UP

btnC = DigitalInOut(board.D12)
btnC.direction = Direction.INPUT
btnC.pull = Pull.UP

i2c = busio.I2C(board.SCL, board.SDA)

reset_pin = DigitalInOut(board.D4)
display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c, reset=reset_pin)

display.fill(0)
display.show()
width = display.width
height = display.height

CS = DigitalInOut(board.CE1)
RESET = DigitalInOut(board.D25)
#spi = busio.SPI(board.SCK, MOSI=board.MOSI, MIS0=board.MISO)
spi = busio.SPI(board.SCK, MOSI=board.MOSI)

prev_packet = None

rfm69 = adafruit_rfm69.RFM69(spi, CS, RESET, 915.0)

rfm69.encryption_key = b'\x01\x02\x03\x04\x05\x06\x07\x08\x01\x02\x03\x04\x05\x06\x07\x08'



####################
#
# This function serves to open the buoy webpage
#
####################
def daq_home():
    webbrowser.open("http://localhost:80") # the Apache2 server
    return # placeholder



####################
#
# This function serves to establish connection to the RPi in the multi-sensor buoy
#
####################
def connect_rpi():
    rpi_status.set("Connected")
    global connection_status 
    connection_status = 1
    error.set("Error: Null")
    return # placeholder


####################
#
# This function serves to start data-acquisition
#
####################
def daq_start():
    daq_status.set("Starting")
    global daq_running
    daq_running = 1
    return # placeholder


####################
#
# This function serves to stop data-acquisition
#
####################
def daq_stop():
    daq_status.set("Stopping")
    global daq_running
    daq_running = -1
    return # placeholder



####################
#
# This function serves to reset all settings and connections
#
####################
def daq_reset():
    daq_status.set("Reset")
    rpi_status.set("Disconnected")
    daq_status.set("Stopped")
    global daq_running
    daq_running = -1
    return # placeholder




def alarm_finder():
    for i in range(len(data_array)):
        for j in range(len(data_array[0])):
            if data_array[i+1][j] >= critical_values[i]:
                return "alarm"
            else:
                return "normal"



####################
#
# This function serves to find the linear regression 
#
####################
def linear_regression_fit(i):
    '''
    x = np.arange(0, 10)
    y = 5 * x + 4
    
    # find the line of line of regression
    z = np.polyfit(x, y, 1)
    f = np.poly1d(z)
    '''
    # find the r**2 value
    if len(data_array[i+1]) <= 1:
        return "- Processing -"
    
    
    x = np.arange(0, len(data_array[i+1])) #list()
    #for j in range(len(data_array[i+1])):
        #x.append(j)
        
    z = np.polyfit(x, data_array[i+1], 1)
    f = np.poly1d(z)
    
    yhat = f(x)
    ybar = np.sum(data_array[i+1]) / len(data_array[i+1])
    ssreg = np.sum((yhat - ybar)**2)
    sstot = np.sum((data_array[i+1] - ybar)**2)
    
    r_squared = " R Squared: " + str(round(ssreg / sstot, 2))
    
    
    return str(round(f[1], 2)) + "x [" + units[i] + "] + (" + str(round(f[0], 2)) + ") [" + units[i] + "], " + r_squared



####################
#
# This function serves to update the HTML webpage
#
####################
def update_html():
    
    with open(html_file) as html:
        soup = bs(html.read(), features="html.parser")
        replace_str = list()
        
        for i in range(len(ids)):
            replace_str.append(titles[i] + " Average: " + str(round(np.average(data_array[i+1]), 2)) + units[i] + ", Standard Deviation: " + str(round(np.std(data_array[i+1]), 2)) + units[i] + ", Linear Regression: " + linear_regression_fit(i))
            
            
            #replace_str.append(titles[i] + " Average: " + str(round(np.average(x), 2)) + units[i] + ", Standard Deviation: " + str(round(np.std(x), 2)) + units[i] + ", Linear Regression: " + linear_regression_fit(i))
            
            #if debug_mode.get() > 0:
                #print(replace_str[i])
                
        for i in range(len(ids)):
            for tag in soup.find_all(id=ids[i]):
                tag.string.replace_with(replace_str[i])
                #tag.replace_with(replace_str[i])
        
        #for i in range(len(std_ids)):
            #for tag in soup.find_all(id=std_ids[i]):
                #tag.string.replace_with(replace_str_std[i])
        
        new_text = soup.prettify()
        replace_str.clear()
    with open(html_file, "w") as new_html:
        new_html.write(new_text)
    return


####################
#
# This function serves to produce all the graphs
#
####################
def graph_maker(i):
    
    if len(data_array[0]) == 0:
        return
    
    update_html()
    
    plt.figure(i)
    plt.cla()
    plt.clf()
    plt.tight_layout() # so we can see the axis correctly
    plt.gcf().subplots_adjust(bottom=0.15)
    
    plt.title(titles[i-1])
    plt.xlabel(xlabels)
    plt.ylabel(titles[i-1] + "  [" + ylabels[i-1] + "]")
        
    pv = data_array[i][len(data_array[i-1]) - 1]

    txtstr = "Process value: " + str(round(pv, 2)) + " " + ylabels[i-1]
    #if debug_mode.get() > 0:
        #print(titles[i-1])
        #print("----------\n" + txtstr + "\n----------\n")

    if i <= 6:
        cvstr = "Critical Value: " + str(round(critical_values[i-1], 2)) + " " + ylabels[i-1]
        cv_array = list()
        for k in range(len(data_array[i])):
            cv_array.append(critical_values[i-1])
        #plt.scatter(test_stamp, cv_array, color="red", alpha=1, label=cvstr)
        plt.plot(data_array[0], cv_array, color="red", alpha=1, label=cvstr)

    plt.scatter(data_array[0], data_array[i], color="blue", alpha=1, label=txtstr)
    plt.plot(data_array[0], data_array[i], color="blue", linestyle="-.", alpha=0.5)
    plt.legend(loc="upper left")
    plt.xticks(rotation=45)
    plt.grid()
    file_name = titles[i-1] + ".png"
    plt.savefig(file_name)
    
    if i == 9:
        plt.figure(i)
        plt.cla()
        plt.clf()
        plt.tight_layout() # so we can see the axis correctly
        plt.gcf().subplots_adjust(bottom=0.15)
        
        plt.title("Buoy Position")
        plt.xlabel("Latitude [" + r'$^{\circ}$' + "]")
        plt.ylabel("Longitude [" + r'$^{\circ}$' + "]")

        pv_lat = data_array[i-1][len(data_array[i-1]) - 1]
        txtstr = "Process value: " + str(round(pv_lat, 2)) + ", " + str(round(pv, 2))
        #if debug_mode.get() > 0:
            #print("Buoy Position")
            #print("----------\n" + txtstr + "\n----------\n")

        #plt.scatter(data_array[i-1], data_array[i], color="red", alpha=1, label=txtstr)
        #plt.plot(data_array[i-1], data_array[i], color="red", linestyle="-.", alpha=0.5)
        plt.hist2d(data_array[i-1], data_array[i], bins=int(np.sqrt(len(data_array[i]))), norm=colors.LogNorm())
        #plt.legend(loc="upper left")
        plt.xticks(rotation=45)
        plt.grid()
        plt.colorbar()
        file_name = "Lat_Long.png"
        plt.savefig(file_name)
       
    
    if len(data_array[0]) == 20:
        record_data()
    
    return


####################
#
# This function serves to collect data from the buoy
#
####################
def get_data():
    
    global reset_flag
    
    packet = None
    packet_text = ""
    for i in range(25):
        packet = rfm69.receive()
        if packet is None:
            display.show()
            now = datetime.datetime.now()
            display.text(now.strftime("%H:%M"), 0, 25, 1)
            if debug_mode.get() > 0:
                print("Packet:\t", packet)
        else:
            packet_text = str(packet, "utf-8")
            
            print("Received:\n", packet_text, "\n\n")
            break
            
            
    if len(packet_text) > 0:
        global tmp_data
        global data_array
        tmp_pkt = packet_text.split() # split the data
        print("Items received:\t", len(tmp_pkt))
        flag = False
        
        for i in range(len(tmp_pkt)):
            if i == 0:
                if len(data_array[0]) != 0:
                    print("Data 1:\t", data_array[0][i], " Packet:\t", tmp_pkt[i])
                    if str(tmp_pkt[i]) == str(data_array[0][len(data_array[0])-1]):
                        return # skip over data we already have
                data_array[i].append(tmp_pkt[i])
            else:
                try:
                    data_array[i].append(float(tmp_pkt[i]))
                except valueError:
                    data_array[i].append(-999) # rude error handling
        
        reset_flag = True # clear the reset flag, we got data
        
        #if data_array[0][len(data_array[0])-1] < data_array[0][len(data_array[0])-2]:
        
    return


####################
#
# This function serves to send updates to the buoy
#
####################
def send_data():
    send_str = bytes(str(op_mode.get()) + "\r\n", "utf-8")
    
    for i in range(10):
        rfm69.send(send_str)
    return


####################
#
# This function serves to save all data collected
#
####################
def record_data():
    global data_array
    global reset_flag
    global set_length
    
    
    fname = open("/home/pi/Desktop/Data/" + f'{datetime.datetime.now():%Y-%m-%d}' +  "_" + alarm_finder() +".csv", 'w') # works fine, doesn't handle well when excel opens it, but no worries
    header = "Time,Temperature,Conductivity,Ammonium,Nitrate,Oxygen,Turbidity,pH,Latitude,Longitude\n"
    fname.write(header) 
    for i in range(len(data_array[0])):
            line = str(data_array[0][i]) + "," + str(data_array[1][i]) + "," + str(data_array[2][i]) + "," + str(data_array[3][i]) + "," + str(data_array[4][i]) + "," + str(data_array[5][i]) + "," + str(data_array[6][i]) + "," + str(data_array[7][i]) + "," + str(data_array[8][i]) + "," + str(data_array[9][i]) + "\n"
            #if debug_mode.get() > 0:
                #print(line)
            fname.write(line)
    
    data_array = [[], [], [], [], [], [], [], [], [], []]
    set_length = 0
    reset_flag = False
    
    return
    


####################
#
# This function serves to perform continual readout and updates
#
####################
def auto_update():
    # In here we will make some fake data, write it to a file and make some figures too
    # for now, write the timestamp to the top of the file and move on
    display.text("Abilene Buoy Systems", 0, 0, 1)
    global set_length
    global data_array
    global connection_status
    global place
    global reset_flag
    
    
    if daq_running > 0:
        if connection_status < 0:
            daq_reset()
            error.set("ERROR: Buoy not connected")
            root.after(10000, auto_update)
        else:
            daq_status.set("Running") # indicate we are taking data
            get_data() # collect some new data
            if len(data_array[0]) > set_length:
                set_length = len(data_array[0]) # update the new length
                
                print("Data length:\t", len(data_array[0]))
                
                if op_mode.get() == "m":
                    for i in range(len(data_array) - 1): # timestamps are at zero, so we need to offset by one to get the data we want
                        graph_maker(i + 1) # generate some graphs
                
                elif op_mode.get() == "a":
                    update_html()
            
            elif len(data_array[0]) == set_length and reset_flag == False:
                update_html() # when we get through a new dataset
            
            place = (place + 1) % 8
            prog.set("Status: " + "*" * place)


    #send_data()
    display.show()
    display.fill(0)
    
    root.after(10000, auto_update)
    return # placeholder


root = tkinter.Tk() # declaration of GUI
mainframe = ttk.Frame(root, padding="3 6 12 12") # setup of the GUI
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
# Code to add widgets will go here...

root.title("Abilene Buoy Systems")
root.iconbitmap("@ABS-short.xbm") # linux does not like *.ico wants *.xbm

####################
#
# Declaration of variables
#
####################

rpi_status = StringVar()
daq_status = StringVar()
time_stamp = StringVar()
prog = StringVar()
error = StringVar()
debug_mode = IntVar()

MODES = [["Manual", "Auto"], ["m", "a"]]
op_mode = StringVar()
op_mode.set(MODES[0][0])

titles = ['Water Temperature', 'Conductivity', 'Ammonium Content', 'Nitrate Content', 'Oxygen Content', 'Turbidity', 'pH Level', 'Latitude', 'Longitude']
xlabels = "Time"

ids = ["water_temp", "conductivity", "ammonium", "nitrate", "oxygen", "turbidity","ph","latitude","longitude"]

units = [' C', ' mS/cm', ' mg/L',' mg/L', ' mg/L', ' NTU', ' pH' , " Degrees;", " Degrees;"]
ylabels = [r'$^{\circ}C$', r'$\frac{mS}{cm}$', r'$\frac{mg}{L}$', r'$\frac{mg}{L}$', r'$\frac{mg}{L}$', r'$NTU$', r'$pH$', r'$^{\circ}$', r'$^{\circ}$']

set_length = 0
reset_flag = False


data_array = [[], [], [], [], [], [], [], [], [], []]
tmp_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#data_array = list()
time_stamps = list()
daq_running = -1
place = 0
connection_status = -1
critical_values = [45, 32, 35, 16, 40, 5, 10, 25, 25]

html_file = "index.html"

img = PhotoImage(file="web_icon_2.png")

####################
#
# Declaration of buttons and boxes for GUI
#
####################

# Raspberry Pi Buoy
ttk.Button(mainframe, text="Connect to Buoy", command=connect_rpi).grid(column=0, row=0, sticky=W)
# DAQ Start
ttk.Button(mainframe, text="Start", command=daq_start).grid(column=0, row=5, sticky=W)
# DAQ Stop
ttk.Button(mainframe, text="Stop", command=daq_stop).grid(column=1, row=5, sticky=W)
# DAQ Reset
ttk.Button(mainframe, text="Reset", command=daq_reset).grid(column=0, row=6, sticky=W)

# Labels
# RPi Status
ttk.Label(mainframe, textvariable=rpi_status).grid(column=1, row=0, sticky=W)
# DAQ Status
ttk.Label(mainframe, textvariable=daq_status).grid(column=2, row=5, sticky=W)
# Time
ttk.Label(mainframe, textvariable=time_stamp).grid(column=0, row=7, sticky=W)
# Progress bar
ttk.Label(mainframe, textvariable=prog).grid(column=1, row=8, sticky=W)
# Error
ttk.Label(mainframe, textvariable=error).grid(column=1, row=6, sticky=W)

# Check boxes
# Debug mode
Checkbutton(mainframe, text="Debug", variable=debug_mode, onvalue=1, offvalue=-1).grid(column=0, row=8, sticky=W)

# Webpage link
daq_server = Button(mainframe, image=img, command=daq_home)
daq_server.grid(column=3, row=9)


# Setting initial status
rpi_status.set("Disconnected")
daq_status.set("Stopped")
error.set("Error: Null")
debug_mode.set(-1)

for i in range(len(MODES[0])):
    b = Radiobutton(mainframe, text=MODES[0][i], variable=op_mode, value=MODES[1][i])
    b.grid(column=i, row=4, sticky=W)


auto_update()

root.mainloop()
