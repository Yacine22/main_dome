#!/usr/bin/ python3
import subprocess, re
import shutil
import os, signal
import pyexiv2
import unicodedata
from sh import gphoto2 as gp



def focal_length():
    killprocess()
    subprocess.run(["rm", "test.JPG"])
    subprocess.run(["gphoto2", "--capture-image-and-download", "--filename=test.JPG", "--force-overwrite"])
    metadata = pyexiv2.ImageMetadata('test.JPG')
    metadata.read()
    focal = metadata['Exif.Photo.FocalLength'].raw_value
    return focal

def configInCam():
    """ Check if config in camera settings"""
    settings_list = []
    p = subprocess.run(['gphoto2', '--list-config'], stdout=subprocess.PIPE, universal_newlines=True)
    #print(p.stdout)
    s = p.stdout
    s = unicodedata.normalize("NFKD", s)
    s = s.splitlines(0)
    for i in s:
        qs = i.split("/")[-1].strip()
        settings_list.append(qs)
        
    return settings_list
    

def queryCameras():
    """ return str -> camera folder """
    p = subprocess.run(['gphoto2', '--list-files'], stdout=subprocess.PIPE, universal_newlines=True)
    print(p.stdout)
    s = p.stdout
    s = unicodedata.normalize("NFKD", s)
    s = s.splitlines(0)
    print(s)
    for i in s:
        qs = i.split("/")
      
        if 'DCIM' in qs:
            print(len(qs))
            camera_path = qs
            break
  
    print(camera_path)
    folder = camera_path[-1].split("»")[0].strip()
    print(folder)
    camera_path = "/"+str(camera_path[1])+"/"+str(camera_path[2])+"/"+folder
      
      
    return camera_path


def image_data(parameter):
    
    if parameter == "iso" and "iso" in configInCam() :
        p = subprocess.Popen(["gphoto2", "--get-config", "iso"], stdout=subprocess.PIPE)
    elif parameter == "shutterspeed" and "shutterspeed" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "shutterspeed"], stdout=subprocess.PIPE)
    elif parameter == "whitebalance" and "whitebalance" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "whitebalance"], stdout=subprocess.PIPE)
    elif parameter == "aperture" and "aperture" in configInCam():
        try:
            p = subprocess.Popen(["gphoto2", "--get-config", "aperture"], stdout=subprocess.PIPE)
        except:
            p = subprocess.Popen(["gphoto2", "--get-config", "apertureatmaxfocallength"], stdout=subprocess.PIPE)
    
    elif parameter == "apertureatmaxfocallength" and "apertureatmaxfocallength" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "apertureatmaxfocallength"], stdout=subprocess.PIPE)
        
    elif parameter == "cameramodel" and "cameramodel" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "cameramodel"], stdout=subprocess.PIPE)
    
    elif parameter == "capturetarget" and "capturetarget" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "capturetarget"], stdout=subprocess.PIPE)
    
    elif parameter == "batterylevel" and "batterylevel" in configInCam():
        p = subprocess.Popen(["gphoto2", "--get-config", "batterylevel"], stdout=subprocess.PIPE)

    
    out, err = p.communicate()
    choices = []
    for line in out.splitlines():
        if line.startswith(b'Current'):
            current_ = line
        elif line.startswith(b'Choice'):
            choices.append(line.decode("utf-8"))
    
    return {"Current":current_.decode("utf-8"), "Choices":choices}

def set_camera_data(parameter, value):
    killprocess()
    subprocess.run(["gphoto2", "--set-config", str(parameter)+"="+value])



def clavier():
    return {1: (5, 2), 2: (5, 3), 3: (5, 4),
                4: (5, 5), 5: (5, 6), 6: (5, 7),
                7: (5, 8), 8: (5, 9), 9: (5, 10),
                0: (5, 11), 'A':(6, 2), 'Z':(6, 3), 'E':(6, 4), 'R':(6, 5), 'T': (6, 6), 'Y':(6, 7), 'U':(6, 8), 'I':(6, 9),
                'O':(6, 10), 'P':(6, 11), 'Q':(7, 2), 'S':(7, 3), 'D':(7, 4), 'F':(7, 5), 'G':(7, 6), 'H':(7, 7),
                'J':(7, 8), 'K':(7, 9), 'L':(7, 10), 'M':(7, 11), 'W':(8, 2), 'X':(8, 3), 'C':(8, 4), 'V':(8, 5),
                'B':(8, 6), 'N':(8, 7), ' ':(8, 8), '_':(8, 9), '-':(8, 10)}

def numerical_pad():
    
    return {1: (5, 2), 2: (5, 3), 3: (5, 4),
                4: (6, 2), 5: (6, 3), 6: (6, 4),
                7: (7, 2), 8: (7, 3), 9: (7, 4),
                0: (8, 2)}

#### ----- Checking memory
def check_memory():
    total, used, free = shutil.disk_usage("/")
    print("MEMOIRE TOTAL -> {:.2f} ".format(total/2**30), " Go " )
    print("MEMOIRE UTILISEE -> {:.2f} ".format(used/2**30), " Go " )
    print("MEMOIRE LIBRE -> {:.2f} ".format(free/2**30), " Go " )
    return round(total/2**30, 2), round(used/2**30, 2), round(free/2**30, 2)


def killprocess():
    p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    ## Search the process
    for line in out.splitlines():
        if b'gvfsd-gphoto2' in line:
            ## Kill the process
            pid = int(line.split(None, 1)[0])
            os.kill(pid, signal.SIGKILL)
            
            
def prepare_camera():
    subprocess.run(["gphoto2", "--set-config", "eosremoterelease=4"]) #### Release = Immediate 5 --- Release Full 4
    

def camera_available():
    p = subprocess.Popen(['gphoto2', '--auto-detect'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if len(out.splitlines()) == 3 :
        camera_is_available = True
    else:
        camera_is_available = False
    return camera_is_available
    
    
def about_camera():
    p = subprocess.Popen(['gphoto2', '--summary'], stdout=subprocess.PIPE)
    out, err = p.communicate()
    return out.splitlines()

def get_data_from_camera(file_name):
    killprocess()
    print("---**---")
    os.system("sudo gphoto2 --get-all-files --filename "+file_name)
    #gp(["--get-all-files", "--filename", file_name])
    print("--- IMAGES ARE READY ---")
    

import pigpio


def i2c_checker():
    pi = pigpio.pi() # connect to local Pi

    for device in range(128):

          h = pi.i2c_open(1, device)
          try:
             pi.i2c_read_byte(h)
             print(hex(device))
          except: # exception if i2c_read_byte fails
             print("No Device")
          pi.i2c_close(h)

    pi.stop # disconnect from Pi
