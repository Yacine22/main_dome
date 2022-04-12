#!/usr/bin/ python3
#! /usr/bin/env python
import git
from tkinter import *
from PIL import ImageTk, Image, ImageGrab
import os, shutil, subprocess

icons_path_ = "/home/pi/grandDome/ICONES/"

class Progress(git.remote.RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        return op_code, cur_count, max_count, message
    
repo = git.Repo.clone_from(
    'https://github.com/Yacine22/grandDome.git',
    '/home/pi/new_dome',
    progress=Progress())

dst = '/home/pi/grandDome/'

shutil.copy2('/home/pi/new_dome/main.py', dst)
shutil.copy2('/home/pi/new_dome/settings.py', dst)
shutil.copy2('/home/pi/new_dome/ext.py', dst)

src_dir = '/home/pi/new_dome/maj/'
dome_dir = '/home/pi/new_dome/dome_tester/'
try:
    os.system("cp -R "+src_dir+" "+dst)
    os.system("cp -R "+dome_dir+" "+dst)
except:
    pass

print("Data copied")

interface = Tk()
#self.interface.geometry("800x480")
interface.attributes("-fullscreen", True)
interface.configure(bg="#212121")
interface.title("Dome")


label = Label(interface, text="Mise à jour réussie", bg="#212121", fg='#FFF3AE', font=("Roboto Mono", 22 * -1))
label.grid(row=2, column=0, padx=100, pady=10, sticky="news")

label_maj = Label(interface, text="Veuillez Relancer l'application", bg="#212121", fg='#FFF3AE', font=("Roboto Mono", 22 * -1))
label_maj.grid(row=3, column=0, padx=100, pady=10, sticky="news")


icon_retour = ImageTk.PhotoImage(Image.open(icons_path_+"IconeRetour.png").resize((65, 65)), Image.BILINEAR)
icon_mercurio = ImageTk.PhotoImage(Image.open(icons_path_+"logo_mercurio.png").resize((100, 60)), Image.BILINEAR)

label_mercurio_icon = Label(interface, image=icon_mercurio, bg="#212121")

button_exit = Button(interface, text="Sortir", bg="#212121", fg="#FFF3AE", relief="flat"
                             ,cursor="tcross", font=("Roboto Mono", 15 * -1), command=interface.destroy)


button_exit['image'] = icon_retour
button_exit.place(x=0, y=0) 

label_mercurio_icon.place(x=-15, y=425)
interface.mainloop()
