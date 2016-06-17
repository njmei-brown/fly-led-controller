# -*- coding: utf-8 -*-
"""
Created on Wed Jan 13 14:33:03 2016

@author: Nicholas Mei (Nicholas_Mei@brown.edu)

fly-led-controller

A simple LED controller user interface for doing fly optogenetic experiments
"""
import sys
import serial

import numpy as np

#If we are using python 2.7 or under
if sys.version_info[0] < 3:
    import Tkinter as tk
    import tkFileDialog as filedialog

#If we are using python 3.0 or above
elif sys.version_info[0] >= 3:
    import tkinter as tk
    import tkinter.filedialog as filedialog

#%%
def serial_port_scan():
   # scan for available ports. return a list of ports 'COM#'
   available = []
   for i in range(256):
       try:
           s = serial.Serial()
           s.port = 'COM'+str(i)
           s.setDTR(False)
           s.open()
           available.append(s.portstr)
           s.close()
       except serial.SerialException:
           pass
   return available

#%%

class LedControllerGui(tk.Frame):
    
   #============ Vars and intialization ===============
   def define_variables(self):
      self.led_freq = tk.StringVar()
      self.led_dur = tk.StringVar()
      
      self.led_freq.set("10")
      self.led_dur.set("5")
           
      self.coms = serial_port_scan()
      self.opmenu_var = tk.StringVar()
       
      if len(self.coms) >= 1:
          self.opmenu_var.set(self.coms[0])
      else:
          self.app_quit()
          raise AttributeError("Error! Could not find any open serial ports! Quitting program!")
          
   #============== Methods =======================
   def turn_on_leds(self):
       com_port = self.opmenu_var.get()
       self.opmenu_var.set(self.coms[self.coms.index(com_port)])
             
       try:
           if self.arduino_obj.arduino.isOpen():
               if self.arduino_obj.arduino.portstr != com_port:
                   self.arduino_obj.close()
                   del self.arduino_obj
                   self.arduino_obj = InitArduino(port=com_port)
               self.arduino_obj.turn_on_stim(float(self.led_freq.get()), float(self.led_dur.get()))
                               
       except AttributeError:
           self.arduino_obj = InitArduino(port=com_port)
           self.arduino_obj.turn_on_stim(float(self.led_freq.get()), float(self.led_dur.get()))
           
   def turn_off_leds(self):
       try:
           self.arduino_obj.turn_off_stim()
       except AttributeError:
           pass
       
   def app_quit(self):
       self.master.destroy()
       self.master.quit()

   def create_widgets(self):
       #------------------- Top Menu Bar ------------------------------
       menubar = tk.Menu(self.master)
       filemenu = tk.Menu(menubar, tearoff=0)
       filemenu.add_command(label="Exit", command=self.app_quit)
       menubar.add_cascade(label="File", menu=filemenu)
       self.master.config(menu=menubar)
       
       #---------------------- Top Frame -----------------------------
       top_frame = tk.Frame(self.master, padx=30, borderwidth=1, 
                            relief=tk.SUNKEN)
       top_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
       
       
       #+++++++++++++++ Arduino Serial Port Selector ++++++++++++++++++
       serial_port_frame = tk.Frame(top_frame)
       serial_port_frame.pack(side=tk.LEFT, fill=tk.X, pady=15)
             
       serial_port_label = tk.Label(serial_port_frame, text="Arduino Serial Port:")
       serial_port_opmenu = apply(tk.OptionMenu, (serial_port_frame, self.opmenu_var) + tuple(self.coms))
          
       serial_port_label .pack(side=tk.LEFT)
       serial_port_opmenu.pack(side=tk.LEFT)       

       
       #------------------------ Middle Frame ------------------------
       middle_frame = tk.Frame(self.master, padx=15)
       middle_frame.pack(side=tk.TOP, fill=tk.X, pady=5)      
       
       led_switch_on = tk.Button(middle_frame, text="ON", pady=35, command=self.turn_on_leds)
       led_switch_off = tk.Button(middle_frame, text="OFF", pady=35, command=self.turn_off_leds)
       
       led_switch_on.pack(side=tk.LEFT, fill=tk.X, expand=1)
       led_switch_on.config(font=('helvetica', 25, 'bold'))
       
       led_switch_off.pack(side=tk.LEFT, fill=tk.X, expand=1)
       led_switch_off.config(font=('helvetica', 25, 'bold'))
       
       #------------------------- Bottom Frame ----------------------
       bottom_frame = tk.Frame(self.master, padx=30, relief=tk.SUNKEN,
                               borderwidth=1)
       bottom_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=5)
       
       #++++++++++++++++++++++++ LED freq ++++++++++++++++++++++++++++
       led_freq_frame = tk.Frame(bottom_frame)
    
       led_freq_label = tk.Label(led_freq_frame, 
                                  text="Opto stim\nfrequency in Hz:")
       led_freq_entry = tk.Entry(led_freq_frame, textvariable=self.led_freq, 
                                  justify=tk.CENTER)    
                                  
       #++++++++++++++++++++++++ LED duration ++++++++++++++++++++++++++++
       led_dur_frame = tk.Frame(bottom_frame)
    
       led_dur_label = tk.Label(led_dur_frame, 
                                 text="Opto stim\npulse width in ms:")
       led_dur_entry = tk.Entry(led_dur_frame, textvariable=self.led_dur, 
                                 justify=tk.CENTER)       
       
       #++++++++++++++++++++ packing LED dur ++++++++++++++++++++++++   
       led_dur_frame.pack(side=tk.RIGHT,fill=tk.X, pady=15)                       
       led_dur_label.pack(side=tk.TOP)
       led_dur_entry.pack(side=tk.TOP)
        
       #++++++++++++++++++++ packing LED freq +++++++++++++++++++++++   
       led_freq_frame.pack(side=tk.LEFT,fill=tk.X, pady=15)     
       led_freq_label.pack(side=tk.TOP)
       led_freq_entry.pack(side=tk.TOP)

   def __init__(self, master=None):
       tk.Frame.__init__(self, master)
       self.master=master
       self.pack()
       self.define_variables()    
       self.create_widgets()


#%%
class InitArduino:
    """
    InitArduino class initializes an arduino serial port connection instance.
    The class is configured with methods to communicate with Arduinos
    loaded with the "opto-blink" or "opto-blink_and_solenoid" sketches
    """
    def __init__(self, port='COM3', baudrate=115200, timeout=0.05):
        #Initialize the arduino!
        #Doing it this way prevents the serial reset that occurs!
        self.arduino = serial.Serial()
        self.arduino.port = port
        self.arduino.baudrate = baudrate
        self.arduino.timeout = timeout
        self.arduino.setDTR(False)
        self.arduino.open()
        #When serial connection is made, arduino opto-blink script sends an initial
        #"OFF" signal. We'll just read the line and empty the serial buffer
        self.arduino.readline()
        self.is_on = False

        #Arduino state consists of 6 values (LED_freq,LED_PW,SOL1,SOL2,SOL3,SOL4)
        self.state = '0.00,0.00,0.00,0.00,0.00,0.00'

        #Loop optimizations
        self.arduino_readline = self.arduino.readline
        self.np_fromstring = np.fromstring

    def update_state(self, new_state, roi_id):
        #first convert state string of floats into numpy array
        prior_state = self.np_fromstring(self.state, dtype=float, sep=',')
        state_indx = roi_id + 1

        if int(prior_state[state_indx] - new_state) != 0:
            prior_state[state_indx] = new_state
            new_state = ",".join(map(str, prior_state))
            self.write(new_state)

    #Avoid using this method on its own, update_state() is far safer!!
    def write(self, values):
        self.arduino.write(values)
        self.state = self.arduino_readline()

    def turn_on_stim(self, led_freq, led_dur):
        self.arduino.write('{freq},{dur}'.format(freq=led_freq, dur=led_dur))
        self.state = self.arduino_readline()
        #if str(arduino_state) == 'ON':
            #self.is_on = True

    def turn_off_stim(self):
        self.arduino.write('0,0')
        self.state = self.arduino_readline()
        #if str(arduino_state) == 'OFF':
            #self.is_on = False

    def turn_off_solenoids(self):
        self.arduino.write('0,0,0,0,0,0')
        self.state = self.arduino_readline()

    def close(self):
        '''
        Closes the serial connection to the arduino.

        Note: Make sure to close serial connection when finished with arduino
        otherwise subsequent attempts to connect to the arduino will be blocked!!
        '''
        self.arduino.close()
        
#%%        

if __name__ == '__main__': 
    
    root = tk.Tk()
    root.title("Fly LED Controller - UI")
    app = LedControllerGui(master=root)
    
    def on_close():
        app.app_quit()
        try:
            app.arduino_obj.close()
        except:
            pass
    root.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()