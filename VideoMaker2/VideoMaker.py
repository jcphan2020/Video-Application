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
from moviepy.editor import VideoFileClip

# Class Constructor to store all variables used in VideoMaker
class DataConstructor:
    x0 = 0
    x1 = 0
    y0 = 0
    y1 = 0
    sel = 0
    begin = 0
    threads = []
    tags = []
    timer = 0
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    format = pyaudio.paInt16
    channel = 2
    rate = 48000
    chunk = 2048

    def __init__(self):
        self.curpath = os.path.dirname(os.path.realpath(__file__))
        self.dirpath = os.path.join(self.curpath, "videos")
        self.filename = os.path.join(self.curpath, "output.mp4")
        self.filewave = os.path.join(self.curpath, "output.wav")
        self.root = tk.Tk()
        self.root.title("VideoMaker")
        self.fps = 30.0

    def clearall(self):
        self.threads = []
        self.tags = []
        self.begin = 0
        self.timer = 0

clip = DataConstructor()

#Screen Selector
#This function is set to the left click. 1st and 2nd click stage sets the rectangular screen and
#3rd click stage to finalize then exit canvas mode to main.
def leftSelector(event):
    #Refresh the screen for new images
    event.widget.delete("all")
    if clip.sel == 0:
        #1st stage to select the first position
        clip.x0 = event.x
        clip.y0 = event.y
        clip.sel = 1
        #Draw the image of a point to show where the player clicked
        event.widget.create_oval(clip.x0 - 2, clip.y0 - 2, clip.x0 + 2, clip.y0 + 2, fill="black")
    elif clip.sel == 1:
        #2nd stage to select the second position
        clip.x1 = event.x
        clip.y1 = event.y
        clip.sel = 2
        #Size check and draw the full size image where the player clicked
        if abs(clip.y1 - clip.y0) < 100 or abs(clip.x1 - clip.x0) < 100:
            clip.sel = 1
            event.widget.create_oval(clip.x0 - 2, clip.y0 - 2, clip.x0 + 2, clip.y0 + 2, fill="black")
        else:
            event.widget.create_rectangle(clip.x0, clip.y0, clip.x1, clip.y1, fill="black", width=5)
    else:
        #3rd stage converts the 1st point to the upper left and 2nd point to the lower right
        #Then it will destroy the canvas state to return to main state
        if clip.x1 < clip.x0:
            temp = clip.x1
            clip.x1 = clip.x0
            clip.x0 = temp
        if clip.y1 < clip.y0:
            temp = clip.y1
            clip.y1 = clip.y0
            clip.y0 = temp
        clip.sel = 0
        stateMain(event.widget)

#Remove Selector - Downgrade the click stages. Necessary to correct miscalculations and errors.
def rightSelector(event):
    #Refresh the screen for new images and downgrade stage
    event.widget.delete("all")
    if clip.sel > 0:
        clip.sel -= 1
    if clip.sel == 1:
        event.widget.create_oval(clip.x0 - 2, clip.y0 - 2, clip.x0 + 2, clip.y0 + 2, fill="black")

#Canvas State - Destroy current state to enter Canvas state
def stateCanvas(event, text):
    clip.dirpath = text.get()
    event.destroy()
    createCanvas()

#Canvas State - Destroy current state
def stateDestroy(event):
    event.destroy()

#Main State - Destroy current state to enter Main state
def stateMain(event):
    event.destroy()
    createMain()

#Create Audio - Primary function to record and create the audio.
def videoA():
    #Initialize and access audio functions
    audio = pyaudio.PyAudio()
    stream = audio.open(format=clip.format, channels=clip.channel, rate=clip.rate,
                        input=True, input_device_index=1, frames_per_buffer=clip.chunk)
    frames = []
    #Begin recording
    while clip.begin == 1:
        frames.append(stream.read(clip.chunk))

    #Stop recording and close related audio functions
    stream.stop_stream()
    stream.close()
    audio.terminate()

    #Convert and create audio file then close related file operations
    filewave = wave.open(clip.filewave, 'wb')
    filewave.setnchannels(clip.channel)
    filewave.setsampwidth(audio.get_sample_size(clip.format))
    filewave.setframerate(clip.rate)
    filewave.writeframes(b''.join(frames))
    filewave.close()

#Create Video - Primary function to record and create the video.
def videoV():
    #Initialize and access video functions
    out = cv2.VideoWriter(clip.filename, clip.fourcc, clip.fps, (1366, 768), True)
    #fps = 14.0 at 1920x1080
    #Begin recording
    while clip.begin == 1:
        img = ImageGrab.grab(bbox=(clip.x0, clip.y0, clip.x1, clip.y1))
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
        reducedframe = cv2.resize(frame, (1366, 768), fx=0, fy=0, interpolation=cv2.INTER_CUBIC)
        out.write(reducedframe)
    #Stop recording and close VideoWriter
    out.release()

    # Get duration of the clip and check difference between audio and clip duration
    check_clip = VideoFileClip(clip.filename)
    sync = clip.timer / check_clip.duration
    check_clip.close()

    # Re-size clip to match audio duration size
    path = os.path.join(clip.curpath, "ffmpeg", "bin", "ffmpeg.exe")
    proc = subprocess.Popen(path + ' -i output.mp4 -vf "setpts='+str(sync)
                            + '*PTS" output2.mp4', cwd=clip.curpath)

    # Wait until process is done and close all windows
    while proc.poll() is None:
        continue
    cv2.destroyAllWindows()

# Timer for how long the recording is running
def timeCounter():
    old_timer = time.time()
    while clip.begin == 1:
        clip.timer = time.time() - old_timer
        hour = str(int(clip.timer / 3600))
        minute = str(int((clip.timer % 3600) / 60))
        second = str(int((clip.timer % 3600) % 60))
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
        if clip.tags:
            clip.tags[0].config(text=display)

#Initialize and Start Recorder - Initialize and start both video and audio simultaneously
def startRecorder(frame, event):
    clip.dirpath = event.get()
    if clip.x0 != clip.x1 and clip.y0 != clip.y1 and clip.begin == 0 and os.path.isdir(event.get()):
        clip.begin = 1
        stateMain(frame)
        first = threading.Thread(target=videoV, name="Thread1")
        clip.threads.append(first)
        first.start()
        second = threading.Thread(target=videoA, name="Thread2")
        clip.threads.append(second)
        second.start()
        third = threading.Thread(target=timeCounter, name="Thread3")
        third.start()

#Stop Recorder
#Close off both video and audio simultaneously and wait for it to process.
#Combine and create the MP4 file with both video and audio files.
def stopRecorder(frame):
    if clip.begin == 1:
        #End video and audio functions and wait for processing
        clip.begin = 0
        cv2.waitKey(50)
        stateMain(frame)
        #Check for existing MP4 files and uses the latest name that does not exist
        i = 1
        while os.path.exists(os.path.join(clip.dirpath, "video_%d.mp4" % (i))):
            i = i + 1

        while clip.threads[0].is_alive() or clip.threads[1].is_alive():
            continue

        clip.clearall()
        if os.path.isdir(clip.dirpath):
            proc = subprocess.Popen(clip.curpath + "\\ffmpeg\\bin\\ffmpeg.exe" +
                                    " -i output.wav -i output2.mp4 -vcodec copy -acodec aac" +
                                    " -strict -2 -b:a 384k video_%d.mp4" % (i), cwd=clip.curpath)
            #Wait for processing
            while proc.poll() is None:
                continue

            cv2.waitKey(50)
            if os.path.exists(os.path.join(clip.curpath, "output.mp4")):
                os.remove(os.path.join(clip.curpath, "output.mp4"))
            if os.path.exists(os.path.join(clip.curpath, "output.wav")):
                os.remove(os.path.join(clip.curpath, "output.wav"))
            if os.path.exists(os.path.join(clip.curpath, "output2.mp4")):
                os.remove(os.path.join(clip.curpath, "output2.mp4"))

            os.replace(os.path.join(clip.curpath, "video_%d.mp4" % (i)),
                       os.path.join(clip.dirpath, "video_%d.mp4" % (i)))

#Main function - Creates the buttons for Record, Select, and Stop.
def createMain():
    #State to be non-transparent and small screen
    clip.root.attributes('-alpha', 1.0)
    clip.root.attributes('-fullscreen', False)
    #Create frame and store 3 buttons with separate functions for each
    topframe = tk.Frame(clip.root)
    topframe.pack()

    if clip.begin == 0:
        tk.Label(topframe, text="Directory", width=20).grid(row=1, column=0)
        text1 = tk.Entry(topframe, width=50)
        text1.insert(0, clip.dirpath)
        text1.grid(row=1, column=1, columnspan=2)
        button1 = tk.Button(topframe, text="Start", fg="white", bg="grey", height=2, width=20,
                         command=lambda: startRecorder(topframe, text1))
        button1.grid(row=0, column=0)
        button2 = tk.Button(topframe, text="Select", fg="white", bg="grey", height=2, width=20,
                     command=lambda: stateCanvas(topframe, text1))
        button2.grid(row=0, column=1)
    else:
        tk.Label(topframe, text="Time", width=20).grid(row=1, column=0)
        tag1 = tk.Label(topframe, text="00:00:00", width=40)
        tag1.grid(row=1, column=1, columnspan=2)
        clip.tags.append(tag1)
        button2 = tk.Button(topframe, text="Select", fg="white", bg="grey", height=2, width=20)
        button2.grid(row=0, column=1)
        button3 = tk.Button(topframe, text="Stop", fg="white", bg="grey", height=2, width=20,
                         command=lambda: stopRecorder(topframe))
        button3.grid(row=0, column=0)
        
    button4 = tk.Button(topframe, text="Exit", fg="white", bg="grey", height=2, width=20,
                     command=lambda: stateDestroy(clip.root))
    button4.grid(row=0, column=2)

#Canvas Function - Creates a transparent white screen for selecting recording screen size
def createCanvas():
    #State to be transparent and fullscreen
    clip.root.attributes('-alpha', 0.3)
    clip.root.attributes('-fullscreen', True)
    #Set left and right functions
    canvas = tk.Canvas(clip.root, width=clip.root.winfo_screenwidth(), height=clip.root.winfo_screenheight())
    canvas.bind("<Button-1>", leftSelector)
    canvas.bind("<Button-3>", rightSelector)
    canvas.pack()

if __name__ == "__main__":
    #Begin Application
    createMain()
    clip.root.resizable(width=False, height=False)
    #Loop to keep application going until exit
    clip.root.mainloop()
