#!/usr/bin/ python3
#! /usr/bin/env python
from subprocess import call
call(['espeak "Welcome to granDome" 2>/dev/null'], shell=True)
"""
User interface to control simultanous captures and leds
-- Using i2c from Raspberry and Arduino 
@ mercurio
"""
from tkinter import *
from tkinter.ttk import Progressbar, Combobox, Style
from tkinter.font import Font
from PIL import ImageTk, Image, ImageGrab
import os, shutil, subprocess, signal, sys
import smbus, time, datetime
import json
from sh import gphoto2 as gp
import shutil
from glob import glob
import settings
import webbrowser, threading
from i2c_devices import i2c_checker
import RPi.GPIO as GPIO
from zipfile import ZipFile

###***

use_button=6                     # lowest button on PiTFT+

from gpiozero import Button as __Button__
from signal import pause
from subprocess import check_call

held_for=0.0

def rls():
        global held_for
        if (held_for > 6.0):
                check_call(['/sbin/poweroff'])
                try:
                    bus = smbus.SMBus(1)
                    bus.write_byte(0x44, 1)
                except:
                    pass
        elif (held_for > 1.0):
                check_call(['/sbin/reboot'])
                try:
                    bus = smbus.SMBus(1)
                    bus.write_byte(0x44, 1)
                except:
                    pass
        else:
            held_for = 0.0

def hld():
        global held_for
        # need to use max() as held_time resets to zero on last callback
        held_for = max(held_for, button.held_time + button.hold_time)
####
###### metadata ---------------------------------
# focal = settings.focal_length()
today_time = datetime.datetime.now().strftime("%H:%M")
today_date = datetime.datetime.now().strftime("%d/%m/%Y")


with open("/home/pi/grandDome/actor_data.json", "r") as r_actor:
    actor_data = json.load(r_actor)
try:
    who = {"Actor":actor_data["NOM d'UTILISATEUR"], "Company":actor_data["SOCIETE"]}
except:
    who = {"Actor":actor_data["Actor"], "Company":actor_data["Company"]}
where = {"Place":""}
when = {"Date":today_date, "Time":today_time}
what = {"Appelation":"rti", "Description":""}
how = {"Modality":{"Technique":"RTI", "Protocol":{"Automation":"", "Detail":{"AcquisitionType":"", "LPFilename":"LP", "DomeDiameterinmm":750}}}}
which = {"Camera":{"Type":"DSRL", "Model":"", "Focal":"", "Iso":"", "Aperture":"", "Whitebalance":"", "Shutterspeed":""},
         "Light":{"SourceType":"LED", "Number":"", "Natural":"True"}}
why = {"Project":""}

def metadata(who=who, where=where, when=when, what=what, how=how, which=which, why=why):    
    inside_data = {'WHO':who, 'WHERE':where, 'WHEN':when, 'WHAT':what, 'HOW':how, 'WHICH':which, 'WHY':why}
    metadata = {'Activity':inside_data}
    return metadata

try:
    os.mkdir("/home/pi/grandDome/json")
except:
    pass


#### Json file
json_file_name = "/home/pi/grandDome/json/metadonnees.json"

def json_file(metadata, path=None): ##### Save data
    json_object = json.dumps(metadata, indent=4)
    with open(json_file_name, "w") as json_file:
        json_file.write(json_object)
        print(json_file)
    if path is None:
        pass
    else:
        shutil.move(json_file_name, path)
        
####### ------------- Clavier
cara = settings.clavier()

global time_cut ## delay between LED On and trigger
global sortir ## boolean
global intensity
time_cut = 0.6 ## Default
sortir = True
intensity = 36

class user_interface:
   
    def __init__(self): 
        self.interface = Tk()
        #self.interface.geometry("800x480")
        self.interface.attributes("-fullscreen", True)
        self.interface.configure(bg="#212121")
        self.interface.title("Dome")
        
        self.dome_type = "GRAND DOME"
        self.aq_type = "RAPIDE"
        
        self.frame = Frame(self.interface, bg="#212121")
        self.frame_exit = Frame(self.interface, bg="#212121")
        self.frame_menu_reglages = Frame(self.interface, bg="#212121")
        self.frame_shutdown = Frame(self.interface, bg="#212121")
        self.frame_version = Frame(self.interface, bg="#212121")
        self.frame_bienvenue = Frame(self.interface, bg="#212121")

        self.label_bienvenue = Label(self.frame_bienvenue, text="DÔME Mercurio V1", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 35, "bold"))
        
        self.icon_exit = ImageTk.PhotoImage(Image.open(icons_path_+"IconeAnnuler.png").resize((70, 70)), Image.BILINEAR)
        self.icon_reglages = ImageTk.PhotoImage(Image.open(icons_path_+"IconeSettings.png").resize((70, 70)), Image.BILINEAR)
        self.icon_menu_capture = ImageTk.PhotoImage(Image.open(icons_path_+"menu_capture.png").resize((165, 165)), Image.BILINEAR)
        self.icon_menu_projects = ImageTk.PhotoImage(Image.open(icons_path_+"menu_projets.png").resize((165, 165)), Image.BILINEAR)
        self.icon_shutdown = ImageTk.PhotoImage(Image.open(icons_path_+"IconeEteindre.png").resize((70, 70)), Image.BILINEAR)
        self.icon_mercurio = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
          
        self.label_mercurio_icon = Label(self.interface, image=self.icon_mercurio, bg="#212121")
        
        self.info_label = Label(self.frame, bitmap='info', bg="#212121", fg="#FFF3AE")
        self.memory_label = Label(self.frame, text="Free Memory : "+str(settings.check_memory()[2])+" Go", fg="#FFF3AE", bg="#212121")
        
        self.button_exit = Button(self.frame_exit, text="Sortir", bg="#212121", fg="#212121", relief="flat"
                                     ,cursor="tcross", command=self.close_window)
        
        self.button_exit.grid(row=0, column=0, sticky='news')
        
        
        self.button_reglages = Button(self.frame_menu_reglages, text="Reglages",relief=FLAT, bg="#212121", fg="#212121", activebackground = "#33B5E5", bd=0
                                    , cursor="tcross", command=self.menu_reglages)
        self.button_capture = Button(self.frame, text="Commencer",relief="flat", bg="#212121", fg="#FFF3AE"
                                    ,compound=TOP, cursor="tcross", font=("Roboto Mono", 18 * -1), command=self.start_captures)
        self.button_projects = Button(self.frame, text="Projets",relief="flat", bg="#212121", fg="#FFF3AE"
                                    ,compound=TOP, cursor="tcross", font=("Roboto Mono", 18 * -1), command=self.projects)
        self.button_shutdown = Button(self.frame_shutdown, text="Eteindre",relief="flat", bg="#212121", fg="#212121", activebackground = "#33B5E5", bd=0, width=50, height=60
                                    ,compound=TOP, cursor="tcross", command=self.shutdown)
        
        self.button_exit['image'] = self.icon_exit
        self.button_reglages['image'] = self.icon_reglages
        self.button_capture['image'] = self.icon_menu_capture
        self.button_projects['image'] = self.icon_menu_projects
        self.button_shutdown['image'] = self.icon_shutdown
        
        self.interface.rowconfigure(0, weight=1)
        self.interface.columnconfigure(0, weight=1)
        
        self.frame_exit.grid(row=0, column=0, stick='nw') 
        self.frame_menu_reglages.grid(row=0, column=0, stick='ne')
        self.frame_shutdown.grid(row=0, column=0, stick='se')
        self.frame_version.grid(row=0, column=0, stick='s')
        self.frame_bienvenue.grid(row=0, column=0, stick='n')
        
        self.label_bienvenue.grid(row=0, column=0, sticky='n')
        self.button_exit.grid(row=0, column=0, sticky='news')
        self.button_reglages.grid(row=0, column=0, sticky='news')
        self.button_capture.grid(row=4, column=2, padx=10, pady=30, sticky='news')
        self.button_projects.grid(row=4, column=3, padx=10, pady=30, sticky='news')
        self.info_label.grid(row=5, column=2, padx=10, pady=20, sticky='news')
        self.memory_label.grid(row=5, column=3, pady=20, sticky='news')
        self.button_shutdown.grid(row=0, column=0, sticky='news')
        
        self.label_mercurio_icon.place(x=-15, y=425)
        self.frame.grid(row=0, column=0, padx=10, pady=50, sticky='n')
        
        self.interface.update()
    
    
    def close_window(self):
        try:
            bus = smbus.SMBus(1)
            bus.write_byte(0x44, 1)
            bus.close()
        except:
            pass
        mario_sound(100)
        self.interface.destroy()
        sys.exit("close")
### ----------------------------------------   Menu Reglages ---------------------------------------------------------------------

    def menu_reglages(self):
        self.reglage_interface = Toplevel()
        self.reglage_interface.attributes('-fullscreen', True)
        #self.reglage_interface.geometry("800x480")
        self.reglage_interface.configure(bg="#212121")
        
        self.reglage_frame = Frame(self.reglage_interface, bg="#212121", relief=FLAT)
        self.reglage_frame_retour = Frame(self.reglage_interface, bg="#212121", relief=FLAT)
        
        self.icon_apropos = ImageTk.PhotoImage(Image.open(icons_path_+"IconeFaq.png").resize((160, 160)), Image.BILINEAR)
        self.icon_metadata = ImageTk.PhotoImage(Image.open(icons_path_+"reglage_metadata.png").resize((160, 160)), Image.BILINEAR)
        self.icon_dometester = ImageTk.PhotoImage(Image.open(icons_path_+"reglage_dome_tester.png").resize((160, 160)), Image.BILINEAR)
        self.icon_cameratester = ImageTk.PhotoImage(Image.open(icons_path_+"reglage_camera_tester.png").resize((160, 160)), Image.BILINEAR)
        self.icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        self._icon_mercurio_ = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
        
        self.__label_mercurio_icon = Label(self.reglage_frame, image=self._icon_mercurio_, bg="#212121")
        
        self.button_retour = Button(self.reglage_frame_retour, text="Sortir", bg="#212121", fg="#212121", width=50, height=50,
                                  relief="flat", compound=TOP, cursor="tcross",
                                      command=self.reglage_interface.destroy)
        
        self.button_retour['image'] = self.icon_retour
                
        self.button_apropos = Button(self.reglage_frame, text="A Propos", bg="#212121", fg="#FFF3AE", cursor="tcross", relief="flat",
                                        font=("Roboto Mono", 13 * -1), compound=TOP, command=self.apropos)
        self.button_metadata = Button(self.reglage_frame, text='Meta Data', cursor="tcross", bg="#212121", fg="#FFF3AE", relief="flat",
                                        compound=TOP, font=("Roboto Mono", 13 * -1), command=self._reglage_metadata_)
        self.button_dometester = Button(self.reglage_frame, text='Tester le Dome', cursor="tcross", bg="#212121", fg="#FFF3AE", relief="flat",
                                        compound=TOP, font=("Roboto Mono", 13 * -1), command=self.reglage_dometester)
        self.button_cameratester = Button(self.reglage_frame, text='Réglages de la Camera', cursor="tcross", bg="#212121", fg="#FFF3AE", relief="flat",
                                        compound=TOP, font=("Roboto Mono", 13 * -1), command=self.reglage_cameratester)
        
        self.button_apropos['image'] = self.icon_apropos
        self.button_metadata['image'] = self.icon_metadata
        self.button_dometester['image'] = self.icon_dometester
        self.button_cameratester['image'] = self.icon_cameratester
    
        self.reglage_interface.rowconfigure(0, weight=1)
        self.reglage_interface.columnconfigure(0, weight=1)
        
        self.reglage_frame.grid(row=0, column=0, sticky='news')
        
        self.reglage_frame_retour.grid(row=0, column=0, stick='nw')
        
        self.button_retour.pack(anchor=NW)
        self.button_metadata.place(x=250, y=250)
        self.button_cameratester.place(x=250, y=50)
        self.button_dometester.place(x=450, y=50)
        self.button_apropos.place(x=450, y=250)
        self.__label_mercurio_icon.place(x=-15, y=425)
          
    ### ----------------------------------------   start Captures ---------------------------------------------------------------------
    
    def apropos(self):
        others()
        
    ##### ---- chantier ici !!     
    
    def start_captures(self): 
        self.capture_wind = Toplevel(self.interface)
        self.capture_wind.attributes('-fullscreen', True)
        #self.capture_wind.geometry("800x480")
        self.capture_wind.configure(bg="#212121")
        
        try:
            bus.write_block_data(0x44, 0, [2, intensity])
        except:
            pass
        
        self.capture_frame = Frame(self.capture_wind, bg="#212121")
        self.capture_frame_exit = Frame(self.capture_wind, bg="#212121")
        
        self.label_projectName = Label(self.capture_frame, text="Nom du Projet", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1), width=20)
        self.entry_projectName = Entry(self.capture_frame, width=50, bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 14 * -1, "bold"))
        self.entry_projectName.insert(END, what["Appelation"])  ###
        
        self.icon_mercurio_logo = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
        self.label_mercurio_icone_ = Label(self.capture_frame, image=self.icon_mercurio_logo, bg="#212121")
        
        self.__icon_retour__ = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        self.capture_button_exit = Button(self.capture_frame_exit, text="Sortir", bg="#212121", fg="#212121",
                                  relief="flat", cursor="tcross", command=self.close_window_capture)
        
        self.capture_button_exit['image'] = self.__icon_retour__
        
        
        self.button_start_acquistion = Button(self.capture_frame, width=18, height=2, text="Lancer une Acquisition", font=("Roboto Mono", 26 * -1, "bold"),
                                         bg="#212121", fg="#FFF3AE", command=self._lancer_acquisition_)
        
        self.button_changer_acquisition = Button(self.capture_frame, text="Changer", font=("Roboto Mono", 16 * -1, "bold"),
                                         bg="#212121", fg="#FFF3AE", command=self._changer_acquisition_)
        
        self.label_acquistion_info = Label(self.capture_frame, width=25, height=3, text="Type d'acquisition : "+self.aq_type, 
                                           bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 15 * -1))
    
        
        self.capture_wind.rowconfigure(0, weight=1)
        self.capture_wind.columnconfigure(0, weight=1)
        
        self.capture_frame_exit.grid(row=0, column=0, sticky='nw')
        self.capture_button_exit.grid(row=0, column=0, sticky='nw')
        
        
        ############### CLAVIER #########################################
        keypad_frame = Frame(self.capture_wind, bg='#212121', relief='groove')
            
        for car, grid_value in cara.items():
            
            if grid_value[0] == 5:
                self.button_kb = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', activebackground ='green', bd=0, font=("Roboto Mono", 15 * -1, "bold"), width=5, height=2,
                            borderwidth=0, state=NORMAL, relief='flat', command=lambda x=car: self.set_text_(x))
                self.button_kb.grid(row=grid_value[0]-1, column=grid_value[1], padx=1, pady=2, sticky='news')
            
            if grid_value[0] == 6:
                self.button_kb = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, state=NORMAL, command=lambda x=car: self.set_text_(x))
                self.button_kb.grid(row=grid_value[0]-1, column=grid_value[1], pady=2, sticky='news')
            
            if grid_value[0] == 7:
                self.button_kb = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE',bd=5,  font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, state=NORMAL, command=lambda x=car: self.set_text_(x))
                self.button_kb.grid(row=grid_value[0]-1, column=grid_value[1], pady=2, sticky='news')
            
            if grid_value[0] == 8:
                self.button_kb = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, state=NORMAL, command=lambda x=car: self.set_text_(x))
                self.button_kb.grid(row=grid_value[0]-1, column=grid_value[1], pady=2, sticky='news')
                
        self.button_del = Button(keypad_frame, text='<', bg='#424035', fg='#FFF3AE', activebackground ='gray', font=('helvetica', 14, 'bold'), height=2,
                            borderwidth=0, state=NORMAL, command=self.delete_text_)       
        self.button_del.grid(row=7, column=11, pady=2, sticky='news')
        keypad_frame.grid(row=0, column=0, sticky='s')
        
        #################################################################
        
        self.capture_frame.grid(row=0, column=0, sticky="news")
        self.label_acquistion_info.place(x=250, y=70)
        self.button_changer_acquisition.place(x=475, y=128)
        
        self.label_projectName.place(x=125, y=20)
        self.entry_projectName.place(x=160, y=40)
        self.button_start_acquistion.place(x=250, y=180)
        self.label_mercurio_icone_.place(x=-15, y=425)
    
    def _changer_acquisition_(self): 
        self.capture_editer = Toplevel()
        self.capture_editer.attributes('-fullscreen', True)
        #self.capture_editer.geometry("800x480")
        self.capture_editer.configure(bg="#212121")
        
        try:
            bus.write_block_data(0x44, 1)
        except:
            pass
        
        
        self._capture_frame_aq_ = Frame(self.capture_editer, bg="#212121")
        self._capture_frame_exit_ = Frame(self.capture_editer, bg="#212121")
        
        
        self._icon_mercurio_cap_ = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
        self.___label_mercurio_icn___ = Label(self.capture_editer, image=self._icon_mercurio_cap_, bg="#212121")
        
        self.icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        self.capture_button_exit_ = Button(self._capture_frame_exit_, text="Sortir", bg="#212121", fg="#212121",
                                  relief="flat", cursor="tcross", command=self.go_out)
        self.capture_button_exit_['image'] = self.icon_retour
      
        self.aq_type_items = ["RAPIDE", "DENSE"]
        
        
        self.label_aq_type = Label(self.capture_editer, width=18, height=2, text="Type d'Acquisiton : ", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 23 * -1))
        self.aq_type_list = Listbox(self.capture_editer,  height=2, width=16, exportselection=0, font=("Roboto Mono", 50 * -1, "bold"), bg="#212121", fg="#FFF3AE",
                                         selectmode=SINGLE)
        
        for type_ in self.aq_type_items:
            self.aq_type_list.insert(END, type_)

        
        self.aq_type_list.bind('<<ListboxSelect>>', self.CurSelet_aq)

        self._capture_frame_exit_.grid(row=0, column=0, sticky='nw')
        self.capture_button_exit_.grid(row=0, column=0, sticky='nw')
        
        self._capture_frame_aq_.grid(row=0, column=0, sticky="news")
        self.label_aq_type.place(x=100, y=130)
        self.aq_type_list.place(x=100, y=180)
        self.___label_mercurio_icn___.place(x=-15, y=425)
        
    def go_out(self):
       
        print("Dome = ", self.dome_type) 
        print("AQ Type = ", self.aq_type)
        
        if len(self.dome_type) != 0 or len(self.aq_type) != 0:
            self.label_acquistion_info_ = Label(self.capture_frame, width=25, height=3, text="Type de Dome : "+self.dome_type+" \nType d'acquisition : "+self.aq_type, 
                                           bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 15 * -1))
            
        elif len(self.dome_type) == 0 or len(self.aq_type) == 0:
            self.label_acquistion_info_ = Label(self.capture_frame, width=25, height=3, text="Type de Dome : "+self.dome_type+" \nType d'acquisition : "+self.aq_type, 
                                           bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 15 * -1))
        
        self.label_acquistion_info_.place(x=250, y=70)
        self.capture_wind.update()
        self.capture_editer.destroy()
        
        
    def _lancer_acquisition_(self): 
        self.capture_wind_aq = Toplevel()
        self.capture_wind_aq.attributes('-fullscreen', True)
        #self.capture_wind_aq.geometry("800x480")
        self.capture_wind_aq.configure(bg="#212121")
        
        try:
            bus.write_block_data(0x44, 1)
        except:
            pass
        
        
        self.capture_frame_aq = Frame(self.capture_wind_aq, bg="#212121")
        self.__capture_frame_exit__ = Frame(self.capture_wind_aq, bg="#212121")
    
        
        self.icon_mercurio_cap_ = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
        self.___label_mercurio_icone___ = Label(self.capture_wind_aq, image=self.icon_mercurio_cap_, bg="#212121")
        
        self.icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        self.__capture_button_exit__ = Button(self.__capture_frame_exit__, text="Sortir", bg="#212121", fg="#212121",
                                  relief="flat", cursor="tcross", command=self.__stop__)
        self.__capture_button_exit__['image'] = self.icon_retour
        
        self.label_aq = Label(self.capture_wind_aq, text="", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1))
        
        self.label_attention = Label(self.capture_wind_aq, text="Ne Pas toucher le DOME SVP!", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1))
        
        self.project_name = self.entry_projectName.get()
        self.project_name_label =  Label(self.capture_wind_aq, width=15, height=2, text="Nom du Projet : "+self.project_name,
                                         bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 14 * -1))
        
        self.label_acquistion_info = Label(self.capture_wind_aq, width=25, height=3, text="Type de Dome : "+self.dome_type+" \nType d'acquisition  :   "+self.aq_type, 
                                           bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 15 * -1))
        
        self.label_image_begin = Label(self.capture_wind_aq, width=400, height=300, bg="#212121")
     
        self._mode_acquisition_(self.dome_type, self.aq_type)
       
        self.capture_wind_aq.rowconfigure(0, weight=1)
        self.capture_wind_aq.columnconfigure(0, weight=1)
        
        self.__capture_frame_exit__.grid(row=0, column=0, sticky='nw')
        self.__capture_button_exit__.grid(row=0, column=0, sticky='nw')
        
        
        self.capture_frame_aq.grid(row=0, column=0, sticky="news")
        self.label_attention.place(x=275, y=2)
        self.project_name_label.place(x=275, y=33)
        self.label_image_begin.place(x=230, y=50)
        self.label_acquistion_info.place(x=275, y=60)
        self.label_aq.place(x=275, y=400)
        self.___label_mercurio_icone___.place(x=-15, y=425)
        
        
    def CurSelet_dome(self, event):
        self.__selection__ = event.widget.curselection()
        self._index_ = self.__selection__[0]
        self._value_ = event.widget.get(self._index_)
        self.dome_type = self._value_
        print(self.dome_type)
        
    def CurSelet_aq(self, event):
        self._selection_ = event.widget.curselection()
        self.__index__ = self._selection_[0]
        self.__value__ = event.widget.get(self.__index__)
        self.aq_type =self.__value__
        print(self.aq_type)
        
    def close_window_capture(self):
        try:
            bus = smbus.SMBus(1)
            bus.write_byte(0x44, 1)
        except:
            pass
        mario_sound(100)
        self.capture_wind.destroy()
      
    def _mode_acquisition_(self, dome_type, aq_type):
        """
        Parameters
        ----------
        dome_type : TYPE : STRING 
            'MICRO DOME' or 'GRAND DOME'.
        aq_type : TYPE : STRING
           'RAPIDE' or 'DENSE'.
        Returns
        -------
        None.
        """
        dome_options = {"MICRO DOME":{"RAPIDE":35, "DENSE":105}, "GRAND DOME":{"RAPIDE":85, "DENSE":155}}
        nb_of_aq = dome_options[dome_type][aq_type]
        self.project_data()
        print("Mode Rapide lancé!")
        t = threading.Thread(target=trois_colors_250)
        t.start()
        try:
            bus.write_block_data[0x44, 0, [2, intensity]]
        except:
            pass
        self._aquisition_(image_nb=nb_of_aq)  ############
        #t.do_run = False
        try:
            bus.write_byte(0x44, 0)
            bus.write_byte(0x44, 1)
        except:
            pass
                    
               
    def project_data(self):
        p_name = self.entry_projectName.get()  ### p_name == Project name 
        what['Appelation'] = p_name
        json_file(metadata(what=what))
        return p_name
    
    def set_text_(self, text):
        widget = self.capture_wind.focus_get()
        self.entry_projectName.insert("insert", text)
            
    def delete_text_(self):
        self.entry_projectName.delete(len(self.entry_projectName.get())-1, END)
        
    ### ----------------------------------------   See Projects ---------------------------------------------------------------------
    
    def projects(self):
        os.system("rm /home/pi/grandDome/images/rti/*.JPG")
        os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
        self.project_wind = Toplevel(self.interface)
        self.project_wind.attributes('-fullscreen', True)
        #self.project_wind.geometry("800x480")
        self.project_wind.configure(bg="#212121")
        
        self.framePro = Frame(self.project_wind, bg="#212121")
        
        self.icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        self.icon_download_disa = ImageTk.PhotoImage(Image.open(icons_path_+"download_off.png").resize((45, 45)), Image.BILINEAR)
        self.icon_download = ImageTk.PhotoImage(Image.open(icons_path_+"download.png").resize((40, 40)), Image.BILINEAR)
        self.icon_trash = ImageTk.PhotoImage(Image.open(icons_path_+"corbeille.png").resize((45, 45)), Image.BILINEAR)
        self.button_exit_ = Button(self.framePro, text="Sortir", bg="#212121", fg='#424035', command=self.project_wind.destroy)
        self.button_exit_['image'] = self.icon_retour
        
        self.icon_mercurio_pro = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)
        self.label_mercurio_icone = Label(self.framePro, image=self.icon_mercurio_pro, bg="#212121")
        
        self.button_delete_project = Button(self.framePro, text="Supprimer", bg="#212121", relief="flat",
                                            state=DISABLED, command=self.message_box)
        
        self.button_delete_project['image'] = self.icon_trash
        
        self.button_copy_project = Button(self.framePro, text="Copier USB", bg="#212121", fg="#FFF3AE",
                                            state=DISABLED, command=self.copy_to_usb_)
        self.button_copy_project['image'] = self.icon_download
        
        self.label_display = Label(self.framePro, height=333, width=475,  bg="#212121", fg="#424035", relief="flat", font=("Roboto Mono", 15 * -1, "bold"))
        self.label_imageName = Label(self.framePro, height=3, width=25, bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"))
        self.label_Nombre = Label(self.framePro, bg="#212121", fg="#FFF3AE",font=("Roboto Mono", 10 * -1, "bold"))
        
        self.scrollbar = Scrollbar(self.framePro, width=45, bg="#FFF3AE", troughcolor="#212121")
        
        self.list_project = os.listdir(rti_path)
        self.list_project.sort()
        
        self.listeProjet = Listbox(self.framePro, height=20, width=12, yscrollcommand=self.scrollbar.set, bg="#212121", fg='#FFF3AE', font=("Roboto Mono", 20 * -1, "bold"))
        
        self.scrollbar.config(command=self.listeProjet.yview)
    
        for projet in self.list_project:
            self.listeProjet.insert(END, projet)
        self.listeProjet.bind("<<ListboxSelect>>", self.selection)
        
        self.project_wind.rowconfigure(0, weight=1)
        self.project_wind.columnconfigure(0, weight=1)
        
        self.framePro.rowconfigure(0, weight=1)
        self.framePro.columnconfigure(0, weight=1)
        
        self.framePro.grid(row=0, column=0, sticky="news")
        
        self.button_exit_.place(x=0, y=0)
        self.button_delete_project.pack(anchor=SE)
        self.button_copy_project.place(x=255, y=415)
        self.label_imageName.place(x=250, y=5)
        self.label_display.place(x=255, y=65)
        self.listeProjet.place(x=75, y=2)
        self.scrollbar.place(x=25, y=200)
        self.label_mercurio_icone.place(x=-15, y=425)
        self.label_Nombre.place(x=350, y=430)
        
    
    def selection(self, event):
        os.system("rm /home/pi/grandDome/images/rti/*.JPG")
        os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
        self.project_wind.update()
        self.button_delete_project['state'] = NORMAL 
        self.button_copy_project['state'] = NORMAL
        self.projet_select = self.listeProjet.get(self.listeProjet.curselection())
        print("----", self.projet_select)
        self.list_project = os.listdir(rti_path+str(self.projet_select))
        
        [root, folder, file] = next(os.walk(rti_path+str(self.projet_select)))
        for i in file:
            if i.endswith("thumbnail.JPG"):
                thumb_file = i
        
        json_image_data = open(rti_path+str(self.projet_select)+"/metadonnees.json")
        self.image_data = json.load(json_image_data)
        self.image_date = self.image_data['Activity']['WHEN']['Date']
        self.image_name = self.image_data['Activity']['WHAT']['Appelation']
        self.image_nbr = self.image_data['Activity']['WHICH']['Light']["Number"]
        
        self.label_imageName.config(text="Nom : "+self.image_name+" "+str(self.image_nbr)+"\n Date : "+self.image_date, width=32)
        self.previewImg = Image.open(rti_path+str(self.projet_select)+"/"+thumb_file).resize((475, 333))
        self.image__ = ImageTk.PhotoImage(self.previewImg, Image.BILINEAR)
        self.label_display.configure(image=self.image__)
        self.project_wind.update()
    
    def copying_cmd(self, projet_select):
        media_path = "/media/pi/"
        folders_in_media = os.listdir(media_path)
        usb_path = media_path+folders_in_media[0]
        os.system("cp -r "+rti_path+projet_select+" "+usb_path)
        #shutil.copy(rti_path+projet_select, usb_path)
        
    def copy_to_usb_(self):
        self.project_wind.update()
        
        projet_select = self.listeProjet.get(self.listeProjet.curselection())
        print("----selected--2--USB", projet_select)
        media_path = "/media/pi/"
        folders_in_media = os.listdir(media_path)
        if len(folders_in_media) == 0:
            print("Inserérez une clé USB")
            self.label_Nombre.config(text="Insérez Une Clé USB SVP !")
            
        else:    
            usb_path = media_path+folders_in_media[0]
            total, used, free = shutil.disk_usage(usb_path)
            project_existance = os.path.exists(usb_path+"/"+projet_select)
            
            if round((free/2**30), 2) > 1.0 and project_existance == False :                
                t = threading.Thread(target=blinkingRGB, args=("task",))
                t.start()
                number_of_files = self.number_of_files(rti_path+projet_select)
                print(projet_select, number_of_files)
                
                t2 = threading.Thread(target=self.copying_cmd, args=(projet_select,))
                t2.start()
                
                number_of_files_usb = self.number_of_files(usb_path+"/"+projet_select)
                print("USB +++ ",  number_of_files_usb) 
                
                self.button_copy_project['state'] = DISABLED
                self.button_delete_project['state'] = DISABLED
                
                while(number_of_files_usb<number_of_files):
                    print("copying")
                    number_of_files_usb = self.number_of_files(usb_path+"/"+projet_select)
                    print(number_of_files_usb)
                    self.label_Nombre.config(text="Copie en Cours ... "+str(number_of_files_usb)+" / "+str(number_of_files))
                    self.project_wind.update()
                    
                #os.system("cd "+usb_path+" ; "+"sudo zip -r "+projet_select+".zip "+str(projet_select))
                
                flash_green()
                print("Projet copié avec succès !")
                self.button_copy_project['state'] = NORMAL
                self.button_delete_project['state'] = NORMAL
                self.label_Nombre.config(text="Le Projet "+projet_select+" est copié vers la clé USB")
                self.project_wind.update()
                t.do_run = False
                time.sleep(2)
                self.label_Nombre.config(text=" ")
                
            elif round((free/2**30), 2) < 1.0:
                self.label_Nombre.config(text="Votre espace est insuffisant")
                self.label_Nombre.config(text="Disponible : "+str(round((free/2**30), 2))+"/"+str(round((total/2**30), 2))+" GO")
            elif project_existance == True :
                self.label_Nombre.config(text="Projet portant le même nom existe déjà !")
        os.system("sudo chmod 777 "+usb_path)
        os.system("sudo chmod 775 "+usb_path)
        self.project_wind.update()
        
    def number_of_files(self, path):
        leng_files = len(glob(path+"/*"))
        leng_files_sub = len(glob(path+"/rti/*"))
        return leng_files+leng_files_sub
        
          
    def message_box(self):
        self.message_box_ = Toplevel()
        self.message_box_.attributes('-fullscreen', True)
        #self.message_box.geometry("800x480")
        self.message_box_.configure(bg="#212121")
        
        projet_select = self.listeProjet.get(self.listeProjet.curselection())
        self.label_deleting = Label(self.message_box_, text="Voulez-vous supprimer le Projet : "+str(projet_select), bg="#424035", fg='#FFF3AE',
                                    font=("Roboto Mono", 20 * -1, "bold"))
        self.button_yes = Button(self.message_box_, text="OUI", width=10, height=5, bg="#420035", fg='#FFF3AE',
                                    font=("Roboto Mono", 22 * -1, "bold"), command=self.remove_selected)
        self.button_No = Button(self.message_box_, text="NON", width=10, height=5, bg="#4240F0", fg='#FFF3AE',
                                    font=("Roboto Mono", 22 * -1, "bold"), command=self.message_box_.destroy)
        
        self.message_box_.rowconfigure(0, weight=1)
        self.message_box_.columnconfigure(0, weight=1)
        
        self.label_deleting.grid(row=0, column=0, pady=5, sticky='news')
        self.button_yes.grid(row=1, column=0, pady=5, sticky='news')
        self.button_No.grid(row=2, column=0, pady=5, sticky='news')
        self.project_wind.update_idletasks()
        
    def remove_selected(self):
        self.project_wind.update_idletasks()
        projet_select = self.listeProjet.get(self.listeProjet.curselection())
        directotory_to_remove = rti_path+str(projet_select)
        dir_exists = os.path.exists(directotory_to_remove)
        t = threading.Thread(target=trois_colors_250)
        t.start()
        print("-----****", directotory_to_remove)
        if dir_exists:
            subprocess.run(["sudo", "rm", "-rf", directotory_to_remove])
        self.message_box_.destroy()
        self.project_wind.destroy()
        

    ### ---------------------------------------- Eteindre ---------------------------------------------------------------------
    def shutdown(self):
        try:
            bus.write_byte(0x44, 0)
        except:
            pass
        os.system('sudo shutdown -h now')
    
     
    ###############################################################################################
    ########################### REGLAGES Nombre LEDs #####################################################
    ##############################################################################################   
    
    def thumbnail(self, projectName):
        bus = smbus.SMBus(1)
        settings.killprocess()
        gp(clearCMD)
        bus.write_block_data(0x44, 0, [2, intensity])
        thumb_name = "thumbnail.JPG"
        subprocess.run(["gphoto2", "--capture-image-and-download", "--filename", rti_path+str(projectName)+"/image.JPG"])
    
        settings.killprocess()
        
        led_1_ctrl(1)
        
        im = Image.open(rti_path+str(projectName)+"/image.JPG")
        im.thumbnail((580, 400), Image.ANTIALIAS)
        im.save(rti_path+str(projectName)+"/thumbnail.JPG")
        print("Thumb Created !")
        self.label_aq.config(text="Ne pas Toucher le DOME SVP")
         
    def __stop__(self):
        """
        Stop i2c transmission 
        """
        try:
            bus.write_byte(0x44, 1)
        except:
            pass
        self.capture_wind_aq.destroy()
        self.capture_wind.destroy()
        
    def _aquisition_(self, image_nb):
        global time_cut
        settings.killprocess()
        i2c_state = i2c_checker() ### Check i2c ? 
        leds_85 = [0, 1, 4, 6, 8, 11, 12, 13, 14, 17, 19, 21, 23, 24, 26, 27, 30] ## 85 LEDs Mode !
        
        list_led85 = []
        for k in range(5):
            list_85 = [x+32*k for x in leds_85]
            list_led85 = list_led85+list_85
        
        nbLED_microDome = 105
        nbTiles_microdome = 35 
       
        ### For 155 LEDs (Deleting small LEds !
        leds_a_allumer_155 = [s for s in range(160)]
        for k in range(5):
            leds_a_allumer_155.remove(31+(32*k))
    
        default_projectname = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
        camera_available = settings.camera_available()
    
        settings.killprocess()
        if camera_available == True and i2c_state != 0 :
            
            subprocess.run(["gphoto2", "--folder", camera_folder,
                                    "-R", "--delete-all-files"])
            os.system("rm /home/pi/grandDome/images/rti/*.JPG")
            os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
            
            settings.killprocess()
            
            ######### Camera Battery Level
            try:
                settings.killprocess()
                battery_level = int(settings.image_data("batterylevel")['Current'][-4:-1])
                print("---Batterie---", battery_level)
                settings.killprocess()
                if (battery_level > 5):
       
                    self.icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeAnnuler.png").resize((65, 65)), Image.BILINEAR)
                    self.capture_button_exit_ = Button(self.capture_wind_aq, text="Sortir", bg="#212121", fg="#212121",
                                          relief="flat", cursor="tcross", command=self.__stop__)
                    
                    self.capture_button_exit_['image'] = self.icon_retour
                    self.capture_button_exit_.place(x=725, y=0)
                    
                    s = Style()
                    s.theme_use('clam')
                    s.configure("green.Horizontal.TProgressbar", foreground='green', background='green')
                    
                    self.progress_bar = Progressbar(self.capture_wind_aq, style="green.Horizontal.TProgressbar", orient=HORIZONTAL, length=400)
                   
                    
                    self.label_image_begin = Label(self.capture_wind_aq, width=450, height=300, bg="#212121")
                    self.label_image_begin.place(x=175, y=50)
                    
                    self.begin_image_ = ImageTk.PhotoImage(Image.open(icons_path_+"connected.png").resize((150, 100)), Image.BILINEAR)
                    self.label_image_begin.config(image=self.begin_image_)
                    
                    self.label_aq = Label(self.capture_wind_aq, text="", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1))
                    self.label_aq.place(x=275, y=400)
                    
                    self.label_aq.config(text="Caméra et i2c détectées" +"\n Ne pas Toucher le DOME SVP")
                    #self.progress_bar.place(x=200, y=360)
                    
                    self.capture_wind_aq.update_idletasks()
                    self.capture_wind_aq.update()
                    
                    ##########
                    
                    which["Light"]["Number"]= image_nb
                    
                    if image_nb == 85 :
                        how['Modality']['Protocol']['Detail']['AcquisitionType']="RTI LEGERE"
                        led_list = list_led85
                        
                    elif image_nb == 155:
                        how['Modality']['Protocol']['Detail']['AcquisitionType']="RTI DENSE"
                        led_list = leds_a_allumer_155
                        
                    elif image_nb == 105:
                        how['Modality']['Protocol']['Detail']['AcquisitionType']="RTI MICRODOME"
                        how["Modality"]['Protocol']['Detail']['DomeDiameterinmm']=280
                        led_list = range(nbLED_microDome)
                    
                    elif image_nb == 35:
                        how['Modality']['Protocol']['Detail']['AcquisitionType']="RTI MICRODOME"
                        how["Modality"]['Protocol']['Detail']['DomeDiameterinmm']=280
                        led_list = range(nbTiles_microdome)
                        
                    json_file(metadata(which=which))
                    json_file(metadata(how=how))
                    subprocess.run(["gphoto2", "--folder", camera_folder, "-R", "--delete-all-files"])
                    ############### ------
                    projectname = self.project_data()
                    
                    self.label_aq['text'] = ""
                    while(os.path.exists(rti_path+projectname+"_"+str(image_nb))):
                        self.label_aq.config(text="Le nom de projet existe déjà")
                        self.capture_wind_aq.update()
                    
                    if len(projectname) == 0:
                        try:
                            os.mkdir(rti_path+default_projectname+"_"+str(image_nb))
                        except:
                            pass
                        if os.path.exists(rti_path+default_projectname+"_"+str(image_nb)):
                            print("ça existe!")
                            while(os.path.exists(rti_path+default_projectname+"_"+str(image_nb))):
                                self.label_aq.config(text="Le nom de projet existe déjà")
                                self.capture_wind_aq.update()
                        self.thumbnail(default_projectname+"_"+str(image_nb))
                        self.thumbnail_image = ImageTk.PhotoImage(Image.open(rti_path+default_projectname+"_"+str(image_nb)+"/image.JPG"
                                                                             ).resize((400, 300)), Image.BILINEAR)
                    else:
                        try:
                            os.mkdir(rti_path+projectname+"_"+str(image_nb))
                        except:
                            pass
                        self.thumbnail(projectname+"_"+str(image_nb))
                        self.thumbnail_image = ImageTk.PhotoImage(Image.open(rti_path+projectname+"_"+str(image_nb)+"/image.JPG"
                                                                             ).resize((400, 300)), Image.BILINEAR)
                        
                    #####################################
                    
                   
                    self.label_image_begin['image'] = self.thumbnail_image
                    
                    what["Appelation"]=projectname
                    json_file(metadata(what=what))
                    
                    file_name = rti_path+projectname+"rti%Y%m%d%H%M%S%f.%C"
                    
                    #### Save Json File
                    camera_data = save_camera_data()
                    which.update(camera_data)
                    
                    lp_filename = how['Modality']['Protocol']['Detail']['LPFilename']
                    
                    if len(projectname) == 0:
                        json_file(metadata(what=what, how=how, who=who, where=where, when=when, which=which, why=why),
                                  path=str(rti_path+default_projectname+"_"+str(image_nb)+"/"))
                        shutil.copy(lp_path+"LP_"+str(image_nb)+".lp", str(rti_path+default_projectname+"_"+str(image_nb)+"/"))
                        os.rename(rti_path+default_projectname+"_"+str(image_nb)+"/"+"LP_"+str(image_nb)+".lp",
                                      str(rti_path+default_projectname+"_"+str(image_nb)+"/"+lp_filename+".lp"))
                    else:
                        json_file(metadata(what=what, how=how, who=who, where=where, when=when, which=which,why=why),
                                  path=str(rti_path+projectname+"_"+str(image_nb)+"/"))
                        shutil.copy(lp_path+"LP_"+str(image_nb)+".lp", str(rti_path+projectname+"_"+str(image_nb)+"/"))
                        
                        os.rename(rti_path+projectname+"_"+str(image_nb)+"/"+"LP_"+str(image_nb)+".lp",
                                      rti_path+projectname+"_"+str(image_nb)+"/"+lp_filename+".lp")
                        
                    try:
                        bus = smbus.SMBus(1)
                        bus.write_byte(0x44, 1)
                    except:
                        pass
                    
                    self.progress_bar.place(x=200, y=375)
                    for s, i in enumerate(led_list):
                        settings.killprocess()
                        print(str(s), i)
                        self.label_aq.config(text="En Cours de PDV "+str(s)+"/"+str(image_nb)+" ... "+"\n Ne Pas toucher le DOME SVP")
                        self.label_attention.config(text="Ne Pas toucher le DOME SVP "+str(s)+"/"+str(image_nb)+" ... ")
                        self.progress_bar['value'] += 100/(len(led_list))
                        self.capture_wind_aq.update_idletasks()
                        if image_nb == 35:
                            bus.write_block_data(0x44, 0, [6, i])
                        else:
                            bus.write_block_data(0x44, 0, [3, i])
                        time.sleep(0.01)
                        subprocess.run(["gphoto2", "--trigger-capture", "--wait-event=10ms"])
                        time.sleep(time_cut)
                        self.capture_wind_aq.update()
                    bus.write_byte(0x44, 1)
                                   
                    self.label_aq['text'] = "Enregistrement des images..."
                    self.progress_bar['value'] = 0
                    self.capture_wind_aq.update()
                    
                    try:
                        if len(projectname) == 0:
                            os.mkdir(rti_path+default_projectname+"_"+str(image_nb)+"/rti")
                        else:
                            os.mkdir(rti_path+projectname+"_"+str(image_nb)+"/rti")
                    except:
                        pass       
        
                    print("filename===", file_name)
                    data_getter = threading.Thread(target=settings.get_data_from_camera, args=(file_name,))
                    
                    self.progress_bar['value'] = 0
                    nombre_img = len(glob(rti_path+"*.JPG"))
                    
                    data_getter.start()
                    
                    while(nombre_img<image_nb):
                        nombre_img = len(glob(rti_path+"*.JPG"))
                        self.progress_bar['value'] = ((nombre_img)/(image_nb))*100
                        self.label_aq.config(text=str(nombre_img)+"/"+str(image_nb))
                        self.capture_wind_aq.update_idletasks()
                        self.capture_wind_aq.update()
                                 
                    nombre_img = len(glob(rti_path+"*.JPG"))
                    print("init", nombre_img)
        
                    self.progress_bar['value'] = 0
                    self.capture_wind_aq.update()
                    
                    jpg_files = glob(rti_path+'*.JPG')
                    jpg_files.sort()
                    print("On a trouvé ---> ", len(jpg_files), "Images")
                    
                    for i, img in enumerate(jpg_files):
                        renamed_file = rti_path+"IMG_"+str(i+1).zfill(4)
                        os.rename(img, renamed_file+".JPG")
                        self.label_aq.config(text="Image  "+str(i)+"/"+str(image_nb)+ " renommée ! ")
                        if len(projectname) == 0:
                            dest = shutil.move(renamed_file+".JPG", rti_path+default_projectname+"_"+str(image_nb)+"/rti/")
                            dest = shutil.copy(rti_path+default_projectname+"_"+str(image_nb)+"/"+lp_filename+".lp", rti_path+default_projectname+"_"+str(image_nb)+"/rti/")
                            self.label_aq.config(text="Image  "+str(i)+"/"+str(image_nb)+ " déplacée ! ")
                            self.progress_bar['value'] += 100/image_nb
                            self.capture_wind_aq.update()
                            
                        else :
                            dest = shutil.move(renamed_file+".JPG", rti_path+projectname+"_"+str(image_nb)+"/rti/")
                            dest = shutil.copy(rti_path+projectname+"_"+str(image_nb)+"/"+lp_filename+".lp", rti_path+projectname+"_"+str(image_nb)+"/rti/")
                            self.label_aq.config(text="Image "+str(i)+"/"+str(image_nb)+" déplacée ! ")
                            self.progress_bar['value'] += 100/image_nb
                            self.capture_wind_aq.update()
                    
                    try:
                        bus.write_byte(0x44, 0)
                    except:
                        pass
                    
                    subprocess.run(["gphoto2", "--folder", camera_folder,
                                    "-R", "--delete-all-files"])
                    
                    os.system("rm /home/pi/grandDome/images/rti/*.JPG")
                    os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
                    
                    while (len(glob("/home/pi/grandDome/images/rti/*.JPG")) == 0):
                        self.capture_wind_aq.destroy()
                        self.capture_wind.update_idletasks()()
                        self.capture_wind.update()
                    
                        self.capture_wind.destroy()
                        
                    try:
                        bus.close()
                    except:
                        pass
                    
                elif (battery_level <= 5): 
                    self.project_name_label.config(text=" ") 
                    self.label_aq['text'] = " Le niveau de batterie de la caméra est < 25%"
                    self.camera_battery = ImageTk.PhotoImage(Image.open(icons_path_+"camera_battery.png").resize((300, 280)), Image.BILINEAR)
                    self.label_image_begin['image'] = self.camera_battery
                    self.label_image_begin.place(x=100, y=50)
            except:
                settings.killprocess()
                self.project_name_label.config(text=" ") 
                self.label_aq['text'] = " Caméra pas prête, redémarrez l'Application !"
                self.camera_disconnected = ImageTk.PhotoImage(Image.open(icons_path_+"camera_deconnectee.png").resize((260, 180)), Image.BILINEAR)
                self.label_image_begin['image'] = self.camera_disconnected
                camera_available = settings.camera_available()
                
                                        
        elif camera_available == False or i2c_state == 0 : 
            self.project_name_label.config(text=" ") 
            self.label_aq['text'] = " Caméra ou i2c non connectée !"
            self.camera_disconnected = ImageTk.PhotoImage(Image.open(icons_path_+"camera_deconnectee.png").resize((260, 180)), Image.BILINEAR)
            self.label_image_begin['image'] = self.camera_disconnected
            camera_available = settings.camera_available()
            
        self.capture_wind_aq.update()
    
    ##   -----
        
    def _reglage_metadata_(self):
        self.reglage_metadata = Toplevel()
        self.reglage_metadata.attributes('-fullscreen', True)
        #self.reglage_metadata.geometry("800x480")
        self.reglage_metadata.configure(bg="#212121")
        
        self.reglage_frame = Frame(self.reglage_metadata, bg="#212121")
        self.reglage_frame_exit = Frame(self.reglage_metadata)
        
        self.icon_user = ImageTk.PhotoImage(Image.open(icons_path_+"utilisateur.png").resize((160, 160)), Image.BILINEAR)
        self.icon_camera_info = ImageTk.PhotoImage(Image.open(icons_path_+"camera_info.png").resize((160, 160)), Image.BILINEAR)
        self.icon_environdata = ImageTk.PhotoImage(Image.open(icons_path_+"environement.png").resize((160, 160)), Image.BILINEAR)
        self.icon_other_data  = ImageTk.PhotoImage(Image.open(icons_path_+"autres.png").resize((160, 160)), Image.BILINEAR)
        self.icon_retour_ = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
        
        self.__label_mercurio_icon__ = Label(self.reglage_metadata, image=self.icon_mercurio, bg="#212121")
        
        self.button_exit = Button(self.reglage_frame_exit, relief="flat", compound=TOP, bg="#212121", 
                                  command=self.reglage_metadata.destroy)
        
        self.button_user = Button(self.reglage_frame, text="Utilisateur", relief="flat", compound=TOP, bg="#212121", font=("Roboto Mono", 13 * -1, "bold"),
                                  fg="#FFF3AE", command=self.user_data)
        
        self.button_camera_info = Button(self.reglage_frame, text="Caméra info", relief="flat", compound=TOP, bg="#212121", font=("Roboto Mono", 13 * -1, "bold"),
                                  fg="#FFF3AE", command=self.camera_info)
        
        self.button_environement_data = Button(self.reglage_frame, text="Environement", relief="flat", compound=TOP, bg="#212121", font=("Roboto Mono", 13 * -1, "bold"),
                                  fg="#FFF3AE", command=self.environement_data)
                                  
        
        self.button_other_data = Button(self.reglage_frame, text="Autres", relief="flat", compound=TOP, bg="#212121", font=("Roboto Mono", 13 * -1, "bold"),
                                  fg="#FFF3AE", command=self.other_data)
        
        self.button_exit['image'] = self.icon_retour_
        self.button_user['image'] = self.icon_user
        self.button_camera_info['image'] = self.icon_camera_info
        self.button_environement_data['image'] = self.icon_environdata
        self.button_other_data['image'] = self.icon_other_data
        
        self.reglage_metadata.rowconfigure(0, weight=1)
        self.reglage_metadata.columnconfigure(0, weight=1)
        
        self.reglage_frame.grid(row=0, column=0, sticky='n')
        self.reglage_frame_exit.grid(row=0, column=0, sticky='nw')
        
        self.button_exit.grid(row=0, column=0, sticky='news')
        self.button_user.grid(row=2, column=2, padx=5, pady=20, sticky='news')
        self.button_camera_info.grid(row=2, column=3, padx=5, pady=20, sticky='news')
        self.button_environement_data.grid(row=3, column=2, padx=5, pady=20, sticky='news')
        self.button_other_data.grid(row=3, column=3, padx=5, pady=20, sticky='news')
        self.__label_mercurio_icon__.place(x=-15, y=425)
        ### --  --
               
    def user_data(self):  
        photographer_data()
         
    def camera_info(self):
        camera_info()
    
    def environement_data(self):
        environement_data()
    
    def other_data(self):
        _camera_folder_()
    
    ##   -----
    
    def reglage_dometester(self):
        self.dome_wind = Toplevel()
        self.dome_wind.attributes('-fullscreen', True)
        #self.dome_wind.geometry("800x480")
        self.dome_wind.configure(bg="#212121")
        
        self.frame = Frame(self.dome_wind, bg="#212121")
        self.frame_scales = Frame(self.dome_wind, bg="#212121")
        
        global led_allumee_check
        led_allumee_check = False
        
        self.button_retour_icon = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((75, 75)), Image.BILINEAR)
        self.tout_allumer_icon = ImageTk.PhotoImage(Image.open(icons_path_+"toutAllumer.png").resize((120, 120)), Image.BILINEAR)
        self.tout_eteindre_icon = ImageTk.PhotoImage(Image.open(icons_path_+"toutEteindre.png").resize((120, 120)), Image.BILINEAR)
        self.allumer_ledX = ImageTk.PhotoImage(Image.open(icons_path_+"allumerledXon.png").resize((120, 120)), Image.BILINEAR)
        self.eteindre_ledX = ImageTk.PhotoImage(Image.open(icons_path_+"eteindreLed.png").resize((120, 120)), Image.BILINEAR)
        
        self._label_mercurio_icon_ = Label(self.dome_wind, image=self.icon_mercurio, bg="#212121")
        
        self.button_exit = Button(self.frame, image=self.button_retour_icon, bg="#212121",
                                  compound=TOP, command=self.destroy_)
        self.button_tout_allumer = Button(self.frame, text="Tout Allumer", bg="#212121", relief='flat',
                                  compound=TOP, fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"), command=self._allOn_)
        self.button_tout_eteindre = Button(self.frame, text="Tout Eteindre", bg="#212121", relief='flat',
                                  compound=TOP, fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"), command=self._AllOff_)
        self.button_allumer_led_x = Button(self.frame, text="Allumer LED X", bg="#212121", relief='flat',
                                  compound=TOP, fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"), command=self._allummer_led_x_)
        
        self.button_tout_allumer['image'] = self.tout_allumer_icon
        self.button_tout_eteindre['image'] = self.tout_eteindre_icon
        self.button_allumer_led_x['image'] = self.eteindre_ledX
        
        
        ## --------------------- Slides --------------------------------------------------------------------
        self.slider_allumer_LedNum = Scale(self.frame_scales, width=20, length=535, label="Allumer LED N° x/160",  activebackground='white', from_=0, to=160,
                                           orient="horizontal", state=DISABLED, bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"),
                                            troughcolor="#424035", highlightbackground="#FFF3AE", command=self._on_scale_LedN)
        
        self.slider_intensity = Scale(self.frame_scales, width=20, length=535, label="Intensité", from_=0, to=35, orient="horizontal", state=DISABLED, 
                                         troughcolor="#424035", fg="#FFF3AE", font=("Roboto Mono", 13 * -1, "bold"), bg="#212121",
                                              highlightbackground="#FFF3AE", command=self._on_scale_intensity)
        
        
        
        ## --------------------------- Set Positions -----------------------------------------------------
        self.dome_wind.rowconfigure(0, weight=1)
        self.dome_wind.columnconfigure(0, weight=1)
        
        self.frame_scales.grid(row=1, column=0, padx=100, sticky='s')
        
        self.button_exit.pack(anchor=NW)
        self.button_tout_allumer.place(x=150, y=100)
        self.button_tout_eteindre.place(x=350, y=100)
        self.button_allumer_led_x.place(x=550, y=100)
        
        
        self.slider_allumer_LedNum.grid(row=5, column=0, pady=5, padx=50, sticky='s')
        self.slider_intensity.grid(row=7, column=0, pady=5, padx=50, sticky='s')
        
        self.frame.grid(row=0, column=0, sticky='news')
        self._label_mercurio_icon_.place(x=-15, y=425)
               
        ####---------------------------------------------------------------------------------------------------------
    ### -------------------------------- FUNCTIONS ---------------------------------------------------------------
    def _on_scale_LedN(self, value):
        print(value)
        bus.write_byte(0x44, 1)
        time.sleep(0.1)
        bus.write_block_data(0x44, 0, [3, int(value)])
        value=0 
        
    def _on_scale_intensity(self, value):
        print(value)
        self.slider_allumer_LedNum['troughcolor'] = '#a0a0a0'
        self.slider_allumer_LedNum['state'] = 'disabled'
        
        self.slider_intensity['troughcolor'] = 'green'
        self.slider_intensity['state'] = 'active'
        
        bus.write_block_data(0x44, 0, [2, int(value)])
         
    def destroy_(self):
        try:
            bus.write_byte(0x44, 1)
        except:
            pass
        self.dome_wind.destroy()
        
        
    def _allOn_(self):
        time.sleep(0.1)
        self._AllOff_()
        bus.write_block_data(0x44, 0, [2, 15])
        
        self.button_allumer_led_x['image'] = self.eteindre_ledX
        self.slider_intensity['troughcolor'] = 'green'
        self.slider_intensity['state'] = 'active'
        
        self.slider_intensity.set(15)
        
        self.slider_allumer_LedNum['state'] = 'disabled'
        self.slider_allumer_LedNum['troughcolor'] = '#a0a0a0'

    def _AllOff_(self):
        bus.write_byte(0x44, 1)
        
        self.button_allumer_led_x['image'] = self.eteindre_ledX
        self.slider_allumer_LedNum['state'] = 'disabled'
        self.slider_intensity['state'] = 'disabled'

        self.slider_allumer_LedNum['troughcolor'] = '#a0a0a0'
        self.slider_intensity['troughcolor'] = '#a0a0a0'
    
    def _allummer_led_x_(self):
        global led_allumee_check
        
        if led_allumee_check:
            self._AllOff_()
            self.button_allumer_led_x['image'] = self.eteindre_ledX
            self.slider_allumer_LedNum['troughcolor'] = '#a0a0a0'
            self.slider_allumer_LedNum['state'] = 'disabled'
            led_allumee_check = False
            
        else:

            bus.write_block_data(0x44, 0, [3, 0])
            self.button_allumer_led_x['image'] = self.allumer_ledX
            self.slider_allumer_LedNum['troughcolor'] = 'green'
            self.slider_allumer_LedNum['state'] = 'active'
           
            self.slider_intensity['state'] = 'disabled'
            self.slider_intensity['troughcolor'] = '#a0a0a0'
            led_allumee_check = True
                    
    ##   -----
    
    def reglage_cameratester(self):
        global camera
        camera = {}
        
        self.cam_wind = Toplevel()
        self.cam_wind.attributes('-fullscreen', True)
        #self.cam_wind.geometry("800x480")
        self.cam_wind.configure(bg="#212121")
        
        self.frame_exit = Frame(self.cam_wind, bg="#212121")
        self.frame = Frame(self.cam_wind, bg="#212121")
        
        self.camera_deconnctee_icon = ImageTk.PhotoImage(Image.open(icons_path_+"camera_deconnectee.png").resize((200, 200)), Image.BILINEAR)
        self._button_retour_icon_ = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((75, 75)), Image.BILINEAR)
        self.label_mercurio_icon_ = Label(self.cam_wind, image=self.icon_mercurio, bg="#212121")
        
        self.button_exit = Button(self.cam_wind, bg="#212121", command=self.cam_wind.destroy)
        self.button_exit['image'] = self._button_retour_icon_
        
        settings.killprocess()
        if settings.camera_available() == True :
        
            camera_infos = []
            settings.killprocess()
            for line in settings.about_camera():
                line = str(line)[2:].split(':')
                camera_infos.append(line)
            
            try:
                aperture = float(settings.image_data("aperture")['Current'].split(':')[-1])
                iso = int(settings.image_data("iso")['Current'].split(':')[-1])
                whitebalance = settings.image_data("whitebalance")['Current'].split(':')[-1].strip()
                shutterspeed = settings.image_data("shutterspeed")['Current'].split(':')[-1].strip()
                
                _parameters_ = {'aperture':aperture, 'shutterspeed':shutterspeed,
                                         'iso':iso, 'whitebalance':whitebalance
                                         }

                display_list = list(_parameters_.keys())
                            
                self.entry_param = []
               
                for i, param in enumerate(display_list):
                    self.scrollbar = Scrollbar(self.frame, orient="vertical", width=35, bg="#FFF3AE", troughcolor="#212121")
                    self.list_para = Listbox(self.frame, height=2, width=25, exportselection=0, font=("Roboto Mono", 20 * -1, "bold"), bg="#212121", fg="#FFF3AE",
                                             selectmode=SINGLE, yscrollcommand=self.scrollbar.set)
                    para_list = settings.image_data(param)['Choices']
                    for j in para_list:
                        self.list_para.insert(END, param+" "+j.split(" ")[-1]+" "+j.split(" ")[1])    
                    self.scrollbar.grid(row=i+1, column=2, padx=5, pady=20, sticky='news')
                    self.list_para.grid(row=i+1, column=1, padx=15, pady=20, sticky='news')
                    self.scrollbar.config(command=self.list_para.yview)
                    self.list_para.bind('<<ListboxSelect>>', self.select_text)
      
                
                for i,d in enumerate(display_list):
                    self.label = Label(self.frame, text=" "+d+" ", height=2, bd=2, width=20, relief="flat", font=("Roboto Mono", 15 * -1, "bold"), fg="#FFF3AE",
                                          bg="#212121").grid(row=i+1, column=0, padx=50, pady=20, sticky='news')
                which["Camera"] = camera
                settings.killprocess()
                
            except:
                self.label = Label(self.frame, text="Camera Pas Prête, Veuillez redémarrer l'application !", bg="#212121", width=50, font=("Roboto Mono", 16 * -1, "bold"),
                               fg="#FFF3AE").place(x=150, y=100)
            
                self.label_camera_deconnectee = Label(self.cam_wind, bg="#212121", image=self.camera_deconnctee_icon)
                self.label_camera_deconnectee.place(x=325, y=235)
                self.button_exit = Button(self.frame, bg="#212121", command=self.cam_wind.destroy)
                self.button_exit['image'] = self._button_retour_icon_
        
        else :
            self.label = Label(self.frame, text=" Aucune caméra détectée, branchez la caméra SVP !", bg="#212121", width=50, font=("Roboto Mono", 16 * -1, "bold"),
                               fg="#FFF3AE").place(x=150, y=100)
            
            self.label_camera_deconnectee = Label(self.cam_wind, bg="#212121", image=self.camera_deconnctee_icon)
            self.label_camera_deconnectee.place(x=325, y=235)
            self.button_exit = Button(self.frame, bg="#212121", command=self.cam_wind.destroy)
            self.button_exit['image'] = self._button_retour_icon_
            
            
        self.cam_wind.rowconfigure(0, weight=1)
        self.cam_wind.columnconfigure(0, weight=1)
        
        self.frame_exit.grid(row=0, column=0, sticky='nw')
        self.frame.grid(row=0, column=0, sticky='news')
        self.button_exit.place(x=0, y=0)
        
        self.label_mercurio_icon_.place(x=-15, y=425)
        
        
    def select_text(self, text):
        self.selection = text.widget.curselection()
        self.index = self.selection[0]
        self.value = text.widget.get(self.index)
        settings.set_camera_data(self.value.split(" ")[0], self.value.split(" ")[1])
        print(self.value.split(" ")[0], self.value.split(" ")[-1])
        
    def mainloop(self):
        self.interface.mainloop()
        

class photographer_data(Tk):
    def __init__(self):
        Tk.__init__(self)
        #self.geometry("800x480")
        self.attributes("-fullscreen", True)
        self.configure(bg="#212121")
        self.title("Dome")
        
        self.data = ["NOM d'UTILISATEUR", "SOCIETE", "LIEU de PDV"]
        self.date = ["DATE", "TIME"]
        
        keypad_frame = Frame(self, bg="#212121")
        self.label_frame = Frame(self, bg="#212121")
        
        for i,d in enumerate(self.data+self.date):
            self.label = Label(self.label_frame, text=" "+d+" ", height=2, bd=2, width=18, bg="#212121", fg="#FFF3AE",
                                  font=("Roboto Mono", 12 * -1, "bold")).grid(row=i+1, column=0, padx=15, pady=5, sticky='news')
            
        self.label_y = Label(self.label_frame, text=datetime.datetime.now().strftime("%d/%m/%Y"), height=1, bd=1, width=15, relief="flat",
                             bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 12 * -1, "bold"))
        self.label_y.grid(row=4, column=1, padx=15, pady=5, sticky='news')
        self.label_d = Label(self.label_frame, text=datetime.datetime.now().strftime("%H:%M"), height=1, bd=1, width=15, relief="flat",
                             bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 12 * -1, "bold"))
        self.label_d.grid(row=5, column=1, padx=15, pady=5, sticky='news')
       
        self.entries = [Entry(self.label_frame, width=30, bd=3, bg="#424035", fg="#FFF3AE", font=("Roboto Mono", 15 * -1, "bold")) for i in range(len(self.data))]
        self.entry_list = []
        for i,e in enumerate(self.entries):
            #e.grid(row=i+1, column=1, padx=5, pady=5)
            self.entry_list.append(e)
        self.entry_list[0].insert(END, who["Actor"])
        self.entry_list[1].insert(END, who["Company"])
        
        who["Actor"] = str(self.entry_list[0].get())
        who["Company"] = str(self.entry_list[1].get())
        
        print("who ____ ", who)
        
        with open('/home/pi/grandDome/actor_data.json', 'w') as actor_data:
            json.dump(who, actor_data)
        
        print("who ____** ", actor_data)
        
        for i,e in enumerate(self.entry_list):
            e.grid(row=i+1, column=1, padx=20, pady=5)


        self.label_frame.place(x=100, y=25)
        
        self.image_de_retour = Image.open(icons_path_+"IconeRetour.png").resize((75, 75))
        self.icone_de_retour = ImageTk.PhotoImage(master=self, image=self.image_de_retour)
        self.btn_quit = Button(self, text='Sortir', bg="#212121", command=self.destroy)
        self.btn_quit['image'] = self.icone_de_retour
        self.btn_quit.place(x=0, y=0)
        
        self.btn_save = Button(self, text='Enregistrer', bd=2, fg='#FFF3AE', bg='#212121', font=("Roboto Mono", 15 * -1, "bold"),
                            borderwidth=0, state=DISABLED, command=self.save_data)
        self.btn_save.pack(anchor=NE)
        
        
        cara = settings.clavier()
            
        for car, grid_value in cara.items():
            if grid_value[0] == 5:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=2, sticky='news')
                
            if grid_value[0] == 6:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
            if grid_value[0] == 7:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
            if grid_value[0] == 8:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
        self.btn_delete = Button(keypad_frame, text='<', bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=self.delete_text).grid(row=8, column=11, pady=2, sticky='news')
                
        
        keypad_frame.place(x=90, y=265)
        
        self._logo_mercurio_ = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo_ = ImageTk.PhotoImage(master=self, image=self._logo_mercurio_)
        self.__label_logo_ = Label(self, image=self.__logo_, bg="#212121").place(x=-15, y=425)
        
         

    def set_text(self, text):
        self.btn_save['state'] = NORMAL
        self.btn_save['bg'] = "#424035"
        widget = self.focus_get()
        if widget in self.entries:
            widget.insert("insert", text)
            
    def delete_text(self):
        self.btn_save['state'] = NORMAL
        widget = self.focus_get()
        widget.delete(len(widget.get())-1, END)
    
    
    def save_data(self):
        data_dict = {}
        inside_data = {} 
        for s, i in enumerate(self.entry_list):
            widget = i
            data = widget.get()
            data_dict[s] = data
            data_dict[self.data[s]] = data_dict.pop(s)
        print(data_dict)
        
        with open('/home/pi/grandDome/actor_data.json', 'w') as actor_data:
            json.dump(data_dict, actor_data)
        
        
        who["Actor"] = data_dict["NOM d'UTILISATEUR"]
        who["Company"] = data_dict["SOCIETE"]
        where["Place"] = data_dict["LIEU de PDV"]
        when["Date"] = datetime.datetime.now().strftime("%d/%m/%Y")
        when["Time"] = datetime.datetime.now().strftime("%H:%M")
        json_file(metadata(who=who, where=where, when=when))
        try:
            bus.write_byte(0x44, 13)
            time.sleep(0.1)
            bus.write_byte(0x44, 0)
        except:
            pass
        new_wind = Toplevel(self)
        #new_wind.geometry("800x480")
        new_wind.attributes("-fullscreen", True)
        new_wind.configure(bg="#212121")
        new_wind.title("info")
        new_lab = Label(new_wind, text=" Données Enregistrées avec Succès !", bg="#212121", fg="#FFF3AE", font=("Roboto Mono", 18 * -1, "bold")).place(x=150, y=100)
        
        self.image_de_retour_ = Image.open(icons_path_+"IconeRetour.png").resize((75, 75))
        self.icone_de_retour_ = ImageTk.PhotoImage(master=new_wind, image=self.image_de_retour_)
        btn_quit_ = Button(new_wind, text="Sortir", bg="#212121", fg="#FFF3AE", image=self.icone_de_retour_, command=new_wind.destroy).pack(side=TOP, anchor=NW)
        
        self._logo_mercurio_s = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__ = ImageTk.PhotoImage(master=new_wind, image=self._logo_mercurio_s)
        self.__label_logo__ = Label(new_wind, image=self.__logo__, bg="#212121").place(x=-15, y=425)
        

#################################################################################################
###############################  Camera INFOs ##################################################
class camera_info(Tk):
    global camera_
    camera_ = {} 
    def __init__(self):
        Tk.__init__(self)
        #self.geometry("800x480")
        self.attributes("-fullscreen", True)
        self.configure(bg="#212121")
        self.title("Dome")
        
        keypad_frame = Frame(self, bg="#212121")
        self.exit_frame = Frame(self, bg="#212121")
        self.label_frame = Frame(self, bg="#212121")
        
        settings.killprocess()
        if settings.camera_available() == True :
    
            aperture = float(settings.image_data("aperture")['Current'].split(':')[-1])
            iso = int(settings.image_data("iso")['Current'].split(':')[-1])
            whitebalance = settings.image_data("whitebalance")['Current'].split(':')[-1].strip()
            shutterspeed = settings.image_data("shutterspeed")['Current'].split(':')[-1].strip()
            model = settings.image_data("cameramodel")['Current'].split(':')[-1].strip()
            
            which["Camera"]["Model"] = model
            try:
                which["Camera"]["Focal"] = focal
            except:
                pass
            which["Camera"]["Iso"] = iso
            which["Camera"]["Aperture"] = aperture
            which["Camera"]["Whitebalance"] = whitebalance
            which["Camera"]["Shutterspeed"] = shutterspeed
            json_file(metadata(which=which))
            
    
            try:
                focal = settings.focal_length()
            except:
                focal="nA"
                
            additional_parameters = {'Focal':focal, 'Aperture':aperture,
                                     'ISO':iso, 'Whitebalance':whitebalance,
                                     'Shutterspeed':shutterspeed, 'Model':model}
            
            display_list = list(additional_parameters.keys())
            
            for i,d in enumerate(display_list):
                self.label = Label(self.label_frame, text=" "+d+" ", height=2, bd=2, width=15, relief="flat", bg='#424035',  font=('helvetica', 12, 'bold'),
                                      fg="#FFF3AE").grid(row=i+1, column=0, padx=30, pady=15, sticky='news')
        
            
            camera_list = list(additional_parameters.values())
            for i,d in enumerate(camera_list):
                self.label = Label(self.label_frame, text=" "+str(d)+" ", height=2, bd=2, bg='#424035', fg="#FFF3AE", width=40, font=("Roboto Mono", 16 * -1, "bold")
                                      ).grid(row=i+1, column=1, padx=30, pady=15, sticky='news')
        
        else :
            
            self.label = Label(self, text=" Aucune caméra détectée, branchez la caméra SVP !", bg="#212121", width=50, font=("Roboto Mono", 16 * -1, "bold"),
                               fg="#FFF3AE").place(x=150, y=100)
            
        
        self.image_quitter_icon = Image.open(icons_path_+"IconeRetour.png").resize((75, 75))
        self._icon_quitter_ = ImageTk.PhotoImage(master=self.label_frame, image=self.image_quitter_icon)
        self.btn_quit = Button(self, text='Sortir', bg="#212121", command=self.destroy)
        self.btn_quit['image'] = self._icon_quitter_
        self.btn_quit.pack(side=TOP, anchor=NW)
        
        self._logo_mercurio_cam = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__cam = ImageTk.PhotoImage(master=self, image=self._logo_mercurio_cam)
        self.__label_logo__c = Label(self, image=self.__logo__cam, bg="#212121").place(x=-15, y=425)
                
        self.label_frame.place(x=100, y=100)
        

def save_camera_data():
    aperture = settings.image_data("aperture")
    aperture = aperture['Current'].split(':')[-1]
    iso = int(settings.image_data("iso")['Current'].split(':')[-1])
    whitebalance = settings.image_data("whitebalance")['Current'].split(':')[-1]
    shutterspeed = settings.image_data("shutterspeed")['Current'].split(':')[-1]
    model = settings.image_data("cameramodel")['Current'].split(':')[-1]
    
    try:
        which["Camera"]["Focal"] = focal
    except:
        pass
    
    which["Camera"]["Model"] = model
    which["Camera"]["Iso"] = iso
    which["Camera"]["Aperture"] = aperture
    which["Camera"]["Whitebalance"] = whitebalance
    which["Camera"]["Shutterspeed"] = shutterspeed
    
    return which
                      
class environement_data:
    def __init__(self):
        self.envi_wind = Tk()
        #self.envi_wind.geometry("800x480")
        self.envi_wind.attributes("-fullscreen", True)
        self.envi_wind.title('environment')
        self.envi_wind.configure(bg="#212121")
        
        self.frame_exit = Frame(self.envi_wind, bg="#212121")
        self.frame = Frame(self.envi_wind, bg="#212121")
        keypad_frame = Frame(self.envi_wind, bg="#212121")
        
        self.environment_list = ["Technique", "Diamètre du Dôme mm"]
        self.environment_to_edit = ["Prefix", "Description", "Projet", "LP Filename"]
        
        
        self.sortir_icone = Image.open(icons_path_+"IconeRetour.png").resize((65, 65))
        self.___sortir_icn__ = ImageTk.PhotoImage(master=self.envi_wind, image=self.sortir_icone)
        self.button_exit = Button(self.envi_wind, text="Sortir", bg="#212121", command=self.envi_wind.destroy)
        self.button_exit['image'] = self.___sortir_icn__
        
        
        for i, data in enumerate(self.environment_to_edit+self.environment_list):
            label = Label(self.frame, text=data, width=30, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"))
            label.grid(row=i, column=0, padx=10, pady=10, sticky='news')
            
            
        self.entries = [Entry(self.frame, width=30, bd=2, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold")) for i in range(len(self.environment_to_edit))]
        self.entry_list = []
        for i,e in enumerate(self.entries):
            ## e.grid(row=i, column=1, padx=5, pady=5)
            self.entry_list.append(e)
        self.entry_list[-4].insert(END, what["Appelation"])
        self.entry_list[-1].insert(END, how["Modality"]["Protocol"]["Detail"]["LPFilename"])
        
        for i,e in enumerate(self.entry_list):
            e.grid(row=i, column=1, padx=5, pady=5)
            
        self.label_technique = Label(self.frame, text="RTI", width=30, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold")
                                     ).grid(row=4, column=1, padx=5, pady=5, stick='news')
        self.label_diam = Label(self.frame, text="750", width=30, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold")
                                ).grid(row=5, column=1, padx=5, pady=5, stick='news')
        
            
        self.btn_save = Button(self.envi_wind, text='Enregistrer', bd=2, fg='#FFF3AE', bg='#212121', font=("Roboto Mono", 15 * -1, "bold"),
                            borderwidth=0, state=DISABLED, command=self.save_data)
        self.btn_save.pack(anchor=NE)
        
        cara = settings.clavier()
            
        for car, grid_value in cara.items():
            if grid_value[0] == 5:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), width=4, height=2, 
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=2, sticky='news')
                
            if grid_value[0] == 6:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
            if grid_value[0] == 7:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
            if grid_value[0] == 8:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], pady=2, sticky='news')
                
        self.btn_delete = Button(keypad_frame, text='<', bg='#424035', fg='#FFF3AE', bd=5, font=("Roboto Mono", 15 * -1, "bold"), height=2,
                            borderwidth=0, command=self.delete_text).grid(row=8, column=11, pady=2, sticky='news')
                
        
        self.envi_wind.rowconfigure(0, weight=1)
        self.envi_wind.columnconfigure(0, weight=1)
        
        self.frame.place(x=75, y=25)
        keypad_frame.place(x=90, y=265)
        self.button_exit.place(x=0, y=0)
        
        self._logo_mercurio_env = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__env = ImageTk.PhotoImage(master=self.envi_wind, image=self._logo_mercurio_env)
        self.__label_logo__e = Label(self.envi_wind, image=self.__logo__env, bg="#212121").place(x=-15, y=425)
    
        
    def set_text(self, text):
        self.btn_save['state'] = NORMAL
        self.btn_save['bg'] = "#424035"
        widget = self.envi_wind.focus_get()
        if widget in self.entries:
            widget.insert("insert", text)
            
    def delete_text(self):
        widget = self.envi_wind.focus_get()
        widget.delete(len(widget.get())-1, END)
    
    
    def save_data(self):
        global data
        data_dict = {}
        for s, i in enumerate(self.entry_list):
            widget = i
            data = widget.get()
            data_dict[s] = data
            data_dict[self.environment_to_edit[s]] = data_dict.pop(s)
            
        what["Description"]= data_dict["Description"]
        what["Appelation"]= data_dict["Prefix"]
        why["Project"] = data_dict["Projet"]
        how["Modality"]["Protocol"]["Detail"]["LPFilename"] = data_dict["LP Filename"]
        
        json_file(metadata(what=what, why=why, how=how))
        try:
            bus.write_byte(0x44, 13)
            time.sleep(0.1)
            bus.write_byte(0x44, 0)
        except:
            pass
        new_wind = Toplevel()
        new_wind.title("info")
        #new_wind.geometry("800x480")
        new_wind.attributes("-fullscreen", True)
        new_wind.configure(bg="#212121")
        new_lab = Label(new_wind, text="Donneés enregistrées avec Succès !", bg="#212121", fg="#FFF3AE",
                        font=("Roboto Mono", 16 * -1, "bold")).place(x=150, y=100)
        
        self.image_de_retour_ = Image.open(icons_path_+"IconeRetour.png").resize((75, 75))
        self.icone_de_retour_ = ImageTk.PhotoImage(master=new_wind, image=self.image_de_retour_)
        btn_quit_ = Button(new_wind, text="Sortir", bg="#212121", fg="#FFF3AE", image=self.icone_de_retour_, command=new_wind.destroy).pack(side=TOP, anchor=NW)
        
        self._logo_mercurio_s = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__ = ImageTk.PhotoImage(master=new_wind, image=self._logo_mercurio_s)
        self.__label_logo__ = Label(new_wind, image=self.__logo__, bg="#212121").place(x=-15, y=425)

class others:
    
    def __init__(self):
        self.envi_wind = Tk()
        self.envi_wind.attributes('-fullscreen', True)
        self.envi_wind.title('Autres')
        self.envi_wind.configure(bg="#212121")
        #self.envi_wind.geometry("800x480")
        
        
        self.frame_exit = Frame(self.envi_wind, bg="#212121")
        self.frame = Frame(self.envi_wind, bg="#212121")
        keypad_frame = Frame(self.envi_wind, bg="#212121")
        
        self.environment_list = ["Version", "Contact", "A Propos"]
        self.autres_data = ["1.0.0", "contact@mercurioimaging.com", "Imagerie d'expertise"]
        
        self.retour___icone = Image.open(icons_path_+"IconeRetour.png").resize((65, 65))
        self.retour____ = ImageTk.PhotoImage(master=self.envi_wind, image=self.retour___icone)
        self.button_exit = Button(self.frame_exit, text="Sortir", bg='#212121', command=self.envi_wind.destroy)
        self.button_exit['image'] = self.retour____
        
        
        for i, data in enumerate(self.environment_list):
            label = Label(self.frame, text=data, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
            label.grid(row=i, column=0, padx=25, pady=35, sticky='news')
            
            
        for i, e in enumerate(self.autres_data):
            label = Label(self.frame, text=e, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 15 * -1, "bold"),  width=30)
            label.grid(row=i, column=1, padx=5, pady=35, sticky='news')
            
        web_label = Label(self.frame, text="Notre Site Web", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        web_label.grid(row=len(self.environment_list), column=0, padx=10, pady=35, sticky='news')
        web_label_ = Label(self.frame, text="mercurioimaging.com", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 15 * -1, "bold"), cursor="hand2", width=30)
        web_label_.grid(row=len(self.environment_list), column=1, padx=5, pady=35, sticky='news')
        web_label_.bind("<Button-1>", lambda e: self.callback("https://mercurioimaging.com/"))
        
        self.envi_wind.rowconfigure(0, weight=1)
        self.envi_wind.columnconfigure(0, weight=1)
        
        self.frame_exit.grid(row=0, column=0, sticky='nw')
        self.frame.grid(row=0, column=0, sticky='n')
        self.button_exit.grid(row=0, column=0, sticky='news')
        
        self._logo_mercurio_au = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__au = ImageTk.PhotoImage(master=self.envi_wind, image=self._logo_mercurio_au)
        self.__label_logo__au = Label(self.envi_wind, image=self.__logo__au, bg="#212121").place(x=-15, y=425)
                
    def callback(self, url):
        webbrowser.open_new(url)
        

class _camera_folder_:
    global camera_folder
    def __init__(self):
        self.envi_wind = Tk()
        self.envi_wind.attributes('-fullscreen', True)
        self.envi_wind.title('environment')
        #self.envi_wind.geometry('800x480')
        self.envi_wind.configure(bg="#212121")
        
        self.frame = Frame(self.envi_wind, bg="#212121")
        keypad_frame = Frame(self.envi_wind, bg="#212121")
        
        self.camera_folder_label = "Dossier des images"
        self.camera_folder = "/store_00020001/DCIM/100CANON"

        
        self.icone_deRetour = Image.open(icons_path_+"IconeRetour.png").resize((65, 65))
        self.icone_Ret = ImageTk.PhotoImage(master=self.envi_wind, image=self.icone_deRetour)
        self.button_exit = Button(self.envi_wind, text="Sortir", bg='#212121', command=self.envi_wind.destroy)
        self.button_exit['image'] = self.icone_Ret
        self.button_exit.pack(side=TOP, anchor=NW)
        
        self.button_modifier = Button(self.envi_wind, text="Modifier", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"),
                                   command=self.edit_camera_folder)
        self.button_modifier.pack(anchor=NE)
        
        self.label_camera_text = Label(self.frame, text=self.camera_folder_label, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        self.label_camera_text.grid(row=1, column=0, sticky='news')
        
        self.capture_delay_label = Label(self.frame, text="Délai allumage / capture ms", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        self.capture_delay_label.grid(row=2, column=0, pady=10, sticky='news')

        self.label_camera_folder = Label(self.frame, text=self.camera_folder, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        self.label_camera_folder.grid(row=1, column=1, sticky='news')

        self.capture_delay_value = Label(self.frame, text=str(time_cut*1000)+"ms", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=33)
        self.capture_delay_value.grid(row=2, column=1, pady=10, sticky='news')        
        
        self.intensit_text = Label(self.frame, text="Intensité des LEDs ", bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        self.intensit_text.grid(row=3, column=0, pady=10, sticky='news')
        
        self.intensit_set = Label(self.frame, text=str(intensity), bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=30)
        self.intensit_set.grid(row=3, column=1, pady=10, sticky='news')
        
        self.envi_wind.rowconfigure(0, weight=1)
        self.envi_wind.columnconfigure(0, weight=1)
        
        self.frame.place(x=100, y=75)
        
        self._logo_mercurio_a = Image.open(icons_path_+"logo_mercurio.png").resize((100, 60))
        self.__logo__a = ImageTk.PhotoImage(master=self.envi_wind, image=self._logo_mercurio_a)
        self.__label_logo__a = Label(self.envi_wind, image=self.__logo__a, bg="#212121").place(x=-15, y=425)
        
                
    def edit_camera_folder(self):
        self.camera_folder_editer = Entry(self.frame, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=4)
        self.camera_folder_editer.insert(END, 100)
        self.camera_folder_editer.grid(row=1, column=1, padx=10, pady=10, sticky='news')
        
        self.capture_delay_set = Entry(self.frame, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=4)
        self.capture_delay_set.insert(END, time_cut*1000)
        self.capture_delay_set.grid(row=2, column=1, padx=10, pady=10, sticky='news')
        
        self.intensit_set = Entry(self.frame, bg='#212121', fg='#FFF3AE', font=("Roboto Mono", 13 * -1, "bold"), width=4)
        self.intensit_set.insert(END, intensity)
        self.intensit_set.grid(row=3, column=1, padx=10, pady=10, sticky='news')
        
        self.button_modifier['text'] = "Enregistrer"
        self.button_modifier['command'] = self.save_data
        
        keypad_frame = Frame(self.envi_wind, bg="#212121")
        
        cara = settings.numerical_pad()
            
        for car, grid_value in cara.items():
            if grid_value[0] == 5:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', font=("Roboto Mono", 16 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=3, sticky='news')
                
            if grid_value[0] == 6:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', font=("Roboto Mono", 16 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=3, sticky='news')
                
            if grid_value[0] == 7:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', font=("Roboto Mono", 16 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=3, sticky='news')
                
            if grid_value[0] == 8:
                button = Button(keypad_frame, text=str(car), bg='#424035', fg='#FFF3AE', font=("Roboto Mono", 16 * -1, "bold"), width=4, height=2,
                            borderwidth=0, command=lambda x=car: self.set_text(x)).grid(row=grid_value[0], column=grid_value[1], padx=1, pady=3, sticky='news')
            
            delete_button = Button(keypad_frame, text="<", bg='#424035', fg='#FFF3AE', font=("Roboto Mono", 16 * -1, "bold"), padx=1, width=4, height=2,
                            borderwidth=0, command=self.delete_text).grid(row=8, column=4, pady=2, sticky='news')
        
        keypad_frame.place(x=300, y=250)
    
    def set_text(self, text):
        widget = self.envi_wind.focus_get()
        if widget in [self.camera_folder_editer, self.capture_delay_set, self.intensit_set]:
            widget.insert("insert", text)
             
    def delete_text(self):
        widget = self.envi_wind.focus_get()
        widget.delete(0, END)
    
    
    def save_data(self):
        camera_folder = "/store_00020001/DCIM/"+str(self.camera_folder_editer.get())+"CANON"
        print(camera_folder)
        self.label_camera_text.config(text="Dossier des images")
        self.label_camera_text.grid(row=1, column=0, pady=10, sticky='news')
        self.label_camera_folder.config(text=camera_folder)
        self.label_camera_folder.grid(row=1, column=1, pady=10, sticky='news')
        self.button_modifier['text'] = "Modifier"
        self.button_modifier['command'] = self.edit_camera_folder
        time_cut = float(self.capture_delay_set.get())/1000
        print("time cut", time_cut)
        intensity = int(self.intensit_set.get())
        print("Intensity", intensity)
        try:
            bus.write_byte(0x44, 13)
            time.sleep(0.1)
            bus.write_byte(0x44, 0)
        except:
            pass
                  
##### --  --  ---

def main():
    settings.killprocess()
    return user_interface()


def mario_sound(frq):
    try:
        bus.write_block_data(0x44, 0, [8, frq])
    except:
        pass

def trois_colors(frq):
    try:
        bus.write_byte(0x44, 11)
        time.sleep(frq/1000)
        bus.write_byte(0x44, 12)
        time.sleep(frq/1000)
        bus.write_byte(0x44, 13)
        time.sleep(frq/1000)
    except:
        pass

def blinkingRGB(arg):
    t = threading.currentThread()
    try:
        while getattr(t, "do_run", True):
            bus.write_byte(0x44, 11)
            time.sleep(0.15)
            bus.write_byte(0x44, 12)
            time.sleep(0.2)
            bus.write_byte(0x44, 13)
            time.sleep(0.25)
    except:
        pass
    

def trois_colors_250():
    try:
        for i in range(50):
            bus.write_byte(0x44, 11)
            time.sleep(0.25)
            bus.write_byte(0x44, 12)
            time.sleep(0.25)
            bus.write_byte(0x44, 13)
            time.sleep(0.25)
    except:
        pass

def flash_green():
    try:
        t = threading.Thread(target=mario_s)
        t.start()
        for i in range(20):
            bus.write_byte(0x44, 12)
            time.sleep(0.1)
    except:
        pass

def mario_s():
    mario_sound(2640)
    time.sleep(0.15)
    mario_sound(2640)
    time.sleep(0.3)
    mario_sound(2640)
    time.sleep(0.3)
    mario_sound(2040)
    time.sleep(0.1)
    mario_sound(2640)
    time.sleep(0.3)
    mario_sound(3080)
    time.sleep(0.55)
    mario_sound(1520)
    time.sleep(0.575)

def led_1_ctrl(state): ### state should be 0 or 1
    try:
        bus.write_block_data(0x44, 0, [10, state])
    except:
        pass

def led_2_ctrl(state):
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.OUT)
    if state == 1:
        GPIO.output(4, GPIO.HIGH)
    elif state == 0:
        GPIO.output(4, GPIO.LOW)


if __name__ == '__main__':
    settings.killprocess()
    
    try:
        os.system("gphoto2 --set-config whitebalance=6")
        os.system("gphoto2 --set-config iso=1")
        os.system("gphoto2 --set-config aperture=3")
        os.system("gphoto2 --set-config shutterspeed=23")
    
    except:
        pass
    
    try:
        os.system("rm /home/pi/grandDome/images/rti/*.JPG")
        os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
    except:
        pass
    bus = smbus.SMBus(1) #### Enable i2c
    try:
        os.system("gphoto2 --set-config capturetarget=1")
    except:
        pass
    led_1_ctrl(1)
    led_2_ctrl(1)
    icons_path_ = "/home/pi/grandDome/ICONES/"
    ### ---- Create Folders ---------------
    try:
        os.mkdir("/home/pi/grandDome/data")
        os.mkdir("/home/pi/grandDome/images/rti")
    except:
        pass

    data_path = "/home/pi/grandDome/data/"
    image_path = "/home/pi/grandDome/images/"
    rti_path = "/home/pi/grandDome/images/rti/"
    lp_path = "/home/pi/grandDome/LPFiles/"
    
    try:
        for i in range(10):
            gp(["--folder", "/store_00020001/DCIM/10"+str(i)+"CANON", "-R", "--delete-all-files"])
    except:
        pass

    ### Camera options
    camera_folder = "/store_00020001/DCIM/100CANON"
    print("---****-----")
    try:
        subprocess.run(["gphoto2", "--set-config", "eosremoterelease=4"]) #### Release = Immediate 5 --- Release Full 4 
    except:
        pass
    print("---****-----****----")
    trigCMD = ["--trigger-capture"]
    download_allCMD = ["--get-all-files"] ## download files
    clearCMD = ["--folder", camera_folder, "-R", "--delete-all-files"] ### To Change if the camera is not Canon !!
    
    shot_date = datetime.datetime.now().strftime("%Y%m%d")
    shot_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    picID = "RTI"

    rti_folder_name = picID + shot_time
    print("--*-*-*-*")
    save_location = "/home/pi/grandDome/images/"
    mario_sound(3000)
    led_1_ctrl(0)
    led_2_ctrl(0)
    print("--*-*-*-*--***")
    
    main = main()
    
    def pauser():
        time.sleep(0.05)
        pause()
        
    
    button=__Button__(use_button, hold_time=1.0, hold_repeat=True)
    button.when_held = hld
    button.when_released = rls
    
    pause_ = threading.Thread(target=pause)
    #main_loop_f = threading.Thread(target=main.mainloop)

    #pause() # wait forever
    #main.mainloop()
    
    #main_loop_f.start()
    pause_.start()
    main.mainloop()
    try:
        os.system("sudo rm /home/pi/grandDome/images/rti/*.JPG")
    except:
        pass
    settings.killprocess()
    
