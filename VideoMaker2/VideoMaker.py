""" Python Code created by Johnson Phan
    The code creates an application that can:
        @Select recording screen size
        @Record in background
"""

import tkinter as tk       #Library that creates and operates windows, buttons, frames, and canvas
import wave                 #Library that Converts to a wave recording
import threading            #Library that creates and operate multiple functions separately
import subprocess           #Library that can manually trigger FFMPEG that merges an video and audio
import os                   #Library that is used to clean out the used files after creating a MP4
import time
import numpy as np          #Library that creates the grid or rectangle screen for video recording
import cv2                  #Library that converts images to video
from PIL import ImageGrab   #Library that contains codes to grab images from the screen
import pyaudio              #Library that contains the code to access the audio of the device
import math
import re
import moviepy.editor as mpe
import moviepy as mpy
from pydub import AudioSegment
from pydub.playback import play

class App():
    def __init__(self):
        self.coord = [-1, -1, -1, -1]
        self.text = ["Start", "Select", "Options"]
        self.state = 0
        self.startrecorder = False
        self.recorderthreads = []
        self.processthreads = []
        self.timer = 0
        self.duration = 0
        self.option_state = -1
        self.timer_state = 0
        self.default_page = 0
        self.all_page = 0

        self.fourcc = cv2.VideoWriter_fourcc(*'H264')
        self.format = pyaudio.paInt16
        self.channel = 2
        self.rate = 48000
        self.chunk = 2048
        self.default_audio = 1
        self.all_audio = []

        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        for i in range (0, numdevices):
            if p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                self.all_audio.append(p.get_device_info_by_host_api_device_index(0, i).get('name'))
        if len(self.all_audio) < 2:
            self.default_audio = 0
        self.curpath = os.path.dirname(os.path.realpath(__file__))
        self.dirpath = os.path.join(self.curpath, "videos")
        i = 0
        while os.path.exists(os.path.join(self.dirpath, 'output_%d.mp4' % i)):
            i = i + 1
        self.cur_inter = i
        self.filename = 'output_%d.mp4' % i
        self.filewave = 'output_%d.wav' % i
        self.root = tk.Tk()
        self.root.title("VideoMaker")
        self.upperframe = tk.Canvas(self.root, bg='grey', width=870, height=60)
        self.lowerframe = tk.Canvas(self.root, bg='grey', width=870, height=60)
        self.timerframe = tk.Canvas(self.root, bg='grey', width=870, height=60)
        self.timer_label = tk.Label(self.timerframe, text='00:00:00', font=('Times Bold', 25))
        self.timer_label.pack(side='right')
        self.selector = tk.Canvas(self.root, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
        self.fps = 30.0

    def reset(self):
        self.recorderthreads = []
        self.startrecorder = False
        self.timer = 0
        self.duration = 0

app = App()

def audio_process():
    #Initialize and access audio functions
    audio = pyaudio.PyAudio()
    stream = audio.open(format=app.format, channels=app.channel, rate=app.rate, input=True,
                        input_device_index=app.default_audio, frames_per_buffer=app.chunk)
    frames = []
    #Begin recording
    while app.startrecorder == 1:
        frames.append(stream.read(app.chunk))

    #Stop recording and close related audio functions
    stream.stop_stream()
    stream.close()
    audio.terminate()

    #Convert and create audio file then close related file operations
    filewave = wave.open(os.path.join(app.curpath, app.filewave), 'wb')
    filewave.setnchannels(app.channel)
    filewave.setsampwidth(audio.get_sample_size(app.format))
    filewave.setframerate(app.rate)
    filewave.writeframes(b''.join(frames))
    filewave.close()

def video_process():
    #Initialize and access video functions
    out = cv2.VideoWriter(os.path.join(app.curpath, app.filename),
                            app.fourcc, app.fps, (1366, 768), True)
    #Begin recording
    while app.startrecorder == 1:
        img = ImageGrab.grab(bbox=app.coord)
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        reducedframe = cv2.resize(frame, (1366, 768), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        out.write(reducedframe)
    #Stop recording and close VideoWriter
    out.release()

    cv2.destroyAllWindows()

def timer_process():
    while app.startrecorder:
        app.duration = time.time() - app.timer
        draw_timer()

def start_process():
    i = 0
    while os.path.exists(os.path.join(app.curpath, 'output_%d.mp4' % i)) or os.path.exists(os.path.join(app.dirpath, 'result_%d.mp4' % i)):
        i = i + 1
    app.cur_inter = i
    app.filename = 'output_%d.mp4' % i
    app.filewave = 'output_%d.wav' % i
    app.startrecorder = True
    app.timer = time.time()
    first = threading.Thread(target=video_process)
    app.recorderthreads.append(first)
    secon = threading.Thread(target=audio_process)
    app.recorderthreads.append(secon)
    third = threading.Thread(target=timer_process)
    app.recorderthreads.append(third)
    first.start()
    secon.start()
    third.start()

def stop_process():
    first = threading.Thread(target=merge_video)
    app.processthreads.append(first)
    first.start()
    app.reset()

def merge_video():
    video_name = app.filename
    audio_name = app.filewave
    current_iter = app.cur_inter
    duration = app.duration
    time.sleep(2)
    new_audio = "loader_%d.wav" %(current_iter)
    song = AudioSegment.from_mp3(os.path.join(app.curpath, audio_name))
    louder_song = song + 12
    louder_song.export(new_audio, "wav")
    time.sleep(2)
    video_clip = mpe.VideoFileClip(os.path.join(app.curpath, video_name))
    audio_clip = mpe.AudioFileClip(os.path.join(app.curpath, new_audio))
    trimmed_video_clip = mpy.video.fx.all.speedx(video_clip, final_duration=duration)
    result_video_clip = trimmed_video_clip.set_audio(audio_clip)
    result_video_clip.write_videofile("result_%d.mp4" % current_iter)
    if os.path.exists(os.path.join(app.curpath, video_name)):
        os.remove(os.path.join(app.curpath, video_name))
    if os.path.exists(os.path.join(app.curpath, audio_name)):
        os.remove(os.path.join(app.curpath, audio_name))
    if os.path.exists(os.path.join(app.curpath, new_audio)):
        os.remove(os.path.join(app.curpath, new_audio))
    os.replace(os.path.join(app.curpath, ("result_%d.mp4" % current_iter)), os.path.join(app.dirpath, ("result_%d.mp4" % current_iter)))

def create_main_gui():
    if app.selector.winfo_ismapped():
        app.selector.pack_forget()
    app.root.attributes('-alpha', 1.0)
    app.root.attributes('-fullscreen', False)
    app.root.resizable(width=False, height=False)
    app.upperframe.bind('<Motion>', main_event)
    app.upperframe.bind('<Button-1>', main_event_click)
    if not app.upperframe.winfo_ismapped():
        app.upperframe.pack()
    if not app.lowerframe.winfo_ismapped() and app.option_state >= 0:
        create_option_gui()
    elif app.timer_state == 0:
        create_timer_gui()
    draw_upper(0, 0)

def create_selector_gui():
    if app.upperframe.winfo_ismapped():
        app.upperframe.pack_forget()
    if app.lowerframe.winfo_ismapped():
        app.lowerframe.pack_forget()
    if app.timerframe.winfo_ismapped():
        app.timerframe.pack_forget()
    app.coord = [-1, -1, -1, -1]
    app.root.attributes('-alpha', 0.2)
    app.root.attributes('-fullscreen', True)
    app.selector.bind('<Button-1>', selector_left_click)
    app.selector.bind('<Button-2>', selector_right_click)
    if not app.selector.winfo_ismapped():
        app.selector.pack()

def create_option_gui():
    if app.selector.winfo_ismapped():
        app.selector.pack_forget()
        app.root.attributes('-alpha', 1.0)
        app.root.attributes('-fullscreen', False)
    if app.timerframe.winfo_ismapped():
        app.timerframe.pack_forget()
    app.lowerframe.config(height=180)
    app.lowerframe.bind('<Motion>', option_event)
    app.lowerframe.bind('<Button-1>', option_event_click)
    if not app.upperframe.winfo_ismapped():
        app.upperframe.pack()
    if not app.lowerframe.winfo_ismapped():
        app.option_state = 0
        app.timer_state = -1
        app.lowerframe.pack()
    draw_lower_option(0, 0)

def create_timer_gui():
    if app.selector.winfo_ismapped():
        app.selector.pack_forget()
        app.root.attributes('-alpha', 1.0)
        app.root.attributes('-fullscreen', False)
    if app.lowerframe.winfo_ismapped():
        app.lowerframe.pack_forget()
    app.lowerframe.config(height=180)
    app.lowerframe.bind('<Motion>', option_event)
    app.lowerframe.bind('<Button-1>', option_event_click)
    if not app.upperframe.winfo_ismapped():
        app.upperframe.pack()
    if not app.timerframe.winfo_ismapped():
        app.option_state = -1
        app.timer_state = 0
        app.timerframe.pack()
    draw_timer()

def main_event(event):
    draw_upper(event.x, event.y)

def main_event_click(event):
    click_upper(event.x, event.y)

def option_event(event):
    draw_upper(0, 0)
    draw_lower_option(event.x, event.y)

def option_event_click(event):
    if app.option_state == 1:
        click_lower_option(event.x, event.y)
    elif app.option_state != 1:
        if 340 < event.x and event.x < 630 and 50 < event.y and event.y < 90:
            app.option_state = 1
    if 660 < event.x and event.x < 700 and 100 < event.y and event.y < 140:
        app.default_page = 0
        if app.lowerframe.winfo_height() > 500:
            app.lowerframe.config(height=180)
        else:
            app.lowerframe.config(height=550)
    click_file_selector(event.x, event.y)
    draw_lower_option(event.x, event.y)

def selector_left_click(event):
    event.widget.delete('all')
    if app.coord[0] < 0:
        app.coord[0] = event.x
        app.coord[1] = event.y
        event.widget.create_oval(event.x - 2, event.y - 2, event.x + 2, event.y + 2, fill="black")
    elif app.coord[2] < 0:
        if 100 < (event.x - app.coord[0]) and 100 < (event.y - app.coord[1]):
            app.coord[2] = event.x
            app.coord[3] = event.y
            event.widget.create_rectangle(app.coord[0], app.coord[1], event.x, event.y, fill="black")
        else:
            event.widget.create_oval(app.coord[0] - 2, app.coord[1] - 2, app.coord[0] + 2, app.coord[1] + 2, fill="black")
    else:
        if app.coord[2] < app.coord[0]:
            tmp = app.coord[2]
            app.coord[2] = app.coord[0]
            app.coord[0] = tmp
        if app.coord[3] < app.coord[1]:
            tmp = app.coord[3]
            app.coord[3] = app.coord[1]
            app.coord[1] = tmp
        create_main_gui()

def selector_right_click(event):
    event.widget.delete('all')
    if 0 <= app.coord[2]:
        app.coord[2] = -1
        app.coord[3] = -1
        event.widget.create_oval(app.coord[0] - 2, app.coord[1] - 2, app.coord[0] + 2, app.coord[1] + 2, fill="black")
    elif 0 <= app.coord[0]:
        app.coord[0] = -1
        app.coord[1] = -1

def click_upper(x, y):
    width = 290
    heigh = 60
    if 0 < y and y < heigh:
        if 0 < x and x < width:
            if 0 < app.coord[0]:
                create_timer_gui()
                if app.startrecorder is False:
                    app.text[0] = "Stop"
                    start_process()
                else:
                    stop_process()
                    app.text[0] = "Start"
    if 0 < y and y < heigh and app.startrecorder is False:
        if width < x and x < 2*width:
            create_selector_gui()
    if 0 < y and y < heigh and app.startrecorder is False:
        if 2*width < x and x < 3*width:
            if app.option_state < 0:
                create_option_gui()
            else:
                create_timer_gui()
    draw_upper(x, y, True)

def draw_upper(x, y, state=False):
    width = 290
    heigh = 60
    app.upperframe.delete('all')
    i = 0
    for name in app.text:
        set_state = 0
        if 0 < y and y < heigh:
            if i*width < x and x < (width + i*width):
                set_state = 1
                if state:
                    set_state = 2
        draw_button_upper(i*width, 0, width, heigh, name, set_state)
        i = i + 1

def draw_button_upper(x, y, w, h, txt, state):
    l = 10
    text_color = 'black'
    lower_block_color = 'grey40'
    upper_block_color = 'grey60'
    if state == 1:
        lower_block_color = 'grey10'
        upper_block_color = 'grey30'
    elif state == 2:
        lower_block_color = 'grey10'
        upper_block_color = 'black'
        text_color = 'white'
    app.upperframe.create_rectangle(x, y, x + w, y + h, fill=lower_block_color)
    app.upperframe.create_line(x, y, x + l, y + l)
    app.upperframe.create_line(x, y + h, x + l, y + h - l)
    app.upperframe.create_line(x + w - l, y + l, x + w, y)
    app.upperframe.create_line(x + w - l, y + h - l, x + w, y + h)
    app.upperframe.create_rectangle(x + l, y + l, x + w - l, y + h - l, fill=upper_block_color)
    app.upperframe.create_text(int(w/2) + x, int(h/2) + y, fill=text_color, font="Times 20 bold", text=txt)

def click_lower_option(x, y):
    width = 290
    heigh = 40
    i = app.default_audio
    j = 0
    for _ in app.all_audio:
        if i == app.default_audio or app.option_state == 1:
            if (50 + width) < x and x < (50 + 2*width) and (50 + j*heigh) < y and y < (50 + (j + 1)*heigh) and i != app.default_audio:
                app.default_audio = i
            j = j + 1
        i = i + 1
        if len(app.all_audio) == i:
            i = 0
    app.option_state = 0

def click_file_selector(x, y):
    if app.lowerframe.winfo_height() > 500:
        if 800 < x and x < 840 and 280 < y and y < 310 and 0 < app.default_page:
            app.default_page = app.default_page - 1
        elif 800 < x and x < 840 and 330 < y and y < 360 and app.default_page < app.all_page:
            app.default_page = app.default_page + 1
        elif 800 < x and x < 840 and 450 < y and y < 490:
            tmp = app.dirpath.split('\\')
            app.dirpath = tmp[0] + '\\'
            if len(tmp) > 1:
                for i in range(1, len(tmp) - 1):
                    app.dirpath = os.path.join(app.dirpath, tmp[i])
        elif 800 < x and x < 840 and 390 < y and y < 430:
            app.lowerframe.config(height=180)
        output = os.scandir(app.dirpath)
        i, j = 0, 0
        for entry in output:
            if entry.is_dir():
                if 15*app.default_page <= i and i < 15*(app.default_page + 1):
                    if 60 < x and x < 770 and (240 + j*20) < y and y < (260 + j*20):
                        app.dirpath = os.path.join(app.dirpath, entry.name)
                    j = j + 1
                i = i + 1

def draw_lower_option(x, y):
    width = 290
    heigh = 40
    app.lowerframe.delete('all')
    app.lowerframe.create_rectangle(50, 50, 50 + width, 50 + heigh, fill='grey25')
    app.lowerframe.create_text(50 + int(width/2), 50 + int(heigh/2),  fill='black', font="Times 20 bold", text='Selected Audio')
    app.lowerframe.create_rectangle(50, 100, 50 + width, 100 + heigh, fill='grey25')
    app.lowerframe.create_text(50 + int(width/2), 100 + int(heigh/2), fill='black', font="Times 20 bold", text='Selected File')
    i = app.default_audio
    j = 0
    ln = len(app.all_audio[i])
    trim = (app.all_audio[i][:18] + '...') if ln > 18 else app.all_audio[i]
    if (50 + width) < x and x < (50 + 2*width) and (50 + j*heigh) < y and y < (50 + (j + 1)*heigh) and i != app.default_audio:
        app.lowerframe.create_rectangle(50 + width, 50 + j*heigh, 50 + 2*width, 50 + (j + 1)*heigh, fill='grey40')
    else:
        app.lowerframe.create_rectangle(50 + width, 50 + j*heigh, 50 + 2*width, 50 + (j + 1)*heigh, fill='grey80')
    app.lowerframe.create_text(50 + width + int(width/2), 50 + j*heigh + int(heigh/2), fill='black', font="Times 20 bold", text=trim)
    i = i + 1
    j = j + 1
    if len(app.all_audio) == i:
        i = 0
    path_list = app.dirpath.split('\\')
    last = len(path_list) - 1
    trim = ('...' + path_list[last][(len(path_list[last]) - 10):]) if len(path_list[last]) > 10 else path_list[last]
    app.lowerframe.create_rectangle(50 + width, 100, 50 + 2*width, 100 + heigh, fill='grey80')
    app.lowerframe.create_text(50 + width + int(width/2), 100 + int(heigh/2), fill='black', font="Times 20 bold", text=trim)
    if (80 + 2*width) < x and x < (120 + 2*width) and 100 < y and y < (100 + heigh):
        app.lowerframe.create_oval(80 + 2*width, 100, 120 + 2*width, 100 + heigh, fill='red')
    else:
        app.lowerframe.create_oval(80 + 2*width, 100, 120 + 2*width, 100 + heigh, fill='green')
    for _ in range(len(app.all_audio) - 1):
        if app.option_state == 1:
            ln = len(app.all_audio[i])
            trim = (app.all_audio[i][:18] + '...') if ln > 18 else app.all_audio[i]
            if (50 + width) < x and x < (50 + 2*width) and (50 + j*heigh) < y and y < (50 + (j + 1)*heigh) and i != app.default_audio:
                app.lowerframe.create_rectangle(50 + width, 50 + j*heigh, 50 + 2*width, 50 + (j + 1)*heigh, fill='grey40')
            else:
                app.lowerframe.create_rectangle(50 + width, 50 + j*heigh, 50 + 2*width, 50 + (j + 1)*heigh, fill='grey80')
            app.lowerframe.create_text(50 + width + int(width/2), 50 + j*heigh + int(heigh/2), fill='black', font="Times 20 bold", text=trim)
            j = j + 1
        i = i + 1
        if len(app.all_audio) == i:
            i = 0

    app.lowerframe.create_rectangle(50, 200, 780, 240, fill='grey80')
    trim = ('...' + app.dirpath[(len(app.dirpath) - 52):]) if len(app.dirpath) > 52 else app.dirpath
    app.lowerframe.create_text(60, 205, anchor='nw', fill='black', font="Times 20 bold", text=trim)
    app.lowerframe.create_rectangle(50, 240, 780, 540, fill='grey60')
    app.all_page = math.floor(len([name for name in os.scandir(app.dirpath) if name.is_dir()])/15)
    if app.default_page == 0:
        app.lowerframe.create_polygon([800, 310, 840, 310, 820, 280], fill='dim gray')
    else:
        app.lowerframe.create_polygon([800, 310, 840, 310, 820, 280], fill='red')
    if app.default_page == app.all_page:
        app.lowerframe.create_polygon([800, 330, 840, 330, 820, 360], fill='dim gray')
    else:
        app.lowerframe.create_polygon([800, 330, 840, 330, 820, 360], fill='red')
    app.lowerframe.create_rectangle(800, 450, 840, 490, fill='red')
    app.lowerframe.create_rectangle(800, 390, 840, 430, fill='sky blue')
    output = os.scandir(app.dirpath)
    i, j = 0, 0
    for entry in output:
        if entry.is_dir():
            if 15*app.default_page <= i and i < 15*(app.default_page + 1):
                if 60 < x and x < 770 and (240 + j*20) < y and y < (260 + j*20):
                    app.lowerframe.create_rectangle(60, 240 + j*20, 770, 260 + j*20, fill='grey50')
                else:
                    app.lowerframe.create_rectangle(60, 240 + j*20, 770, 260 + j*20, fill='grey90')
                app.lowerframe.create_text(80, 242 + j*20, anchor='nw', fill='black', font="Times 10 bold", text=entry.name)
                j = j + 1
            i = i + 1

def draw_timer():
    hour = str(int(app.duration / 3600))
    minute = str(int((app.duration % 3600) / 60))
    second = str(int((app.duration % 3600) % 60))
    display = ""
    for _ in range(2 - len(hour)):
        display += "0"
    display += hour + ":"
    for _ in range(2 - len(minute)):
        display += "0"
    display += minute + ":"
    for _ in range(2 - len(second)):
        display += "0"
    display += second
    app.timer_label.config(text=display)

if __name__ == "__main__":
    create_main_gui()
    app.root.mainloop()