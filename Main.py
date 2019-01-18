import cv2
from tkinter import *
import threading
from PIL import Image, ImageTk
import yaml
import os
import requests
import numpy as np


class GuiThread(Tk):

    def __init__(self):

        self.lightBlue2 = "#9DC3E6"
        self.white = "#FFFFFF"
        self.thingspeak_key = '5R4V5HGPR71C27CS'
        self.fn = r"D:\\github\\parking_lot\\abc.mp4"

        self.check_lap = True
        self.check_select = True
        self.check_lap = False
        self.check_cap = True
        self.check_lap = True
        self.check_select = True
        self.FlagThread = False
        self.check_thingspeak = True
        self.stop_thingspeak = False

        self.frame_l = 890
        self.frame_h = 500

        self.count_point = 0
        self.green = 0
        self.red = 0
        self.green_temp = 0
        self.red_temp = 0
        self.total = 0
        self.f = -1
        self.id = -1
        self.InsertorNew = None
        self.park_writedata = []
        self.rect_writedata = []

        self.root = Tk()
        self.root.resizable(0, 0)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.configure(bg=self.lightBlue2)
        self.root.title("PARKING LOT")
        self.root.geometry("%dx%d+0+0" % (905, 740))

        self.lmain = Label(self.root, width=self.frame_l, height=self.frame_h)
        self.lmain.place(x=5, y=5)

        self.backr = PhotoImage(file='D:\\github\\parking_lot\\blu_cap.PNG')
        self.check_F = PhotoImage(file='D:\\github\\parking_lot\\check_F.png')
        self.check_F = self.check_F.subsample(8)
        self.check_T = PhotoImage(file='D:\\github\\parking_lot\\check_T.png')
        self.check_T = self.check_T.subsample(8)

        self.cap = cv2.VideoCapture(self.fn)
        self.read_lap()
        self.cread_id()
        self.CreateAll()
        self.ShowVideo()
        # self.run1 = threading.Thread(target=self.ShowVideo)
        # self.run1.start()
        self.root.mainloop()

    def close(self):
        pass

    def WriteSelect(self):
        if (self.park_writedata != []):
            with open(r'select_str.yml', 'w') as stream:
                yaml.dump(self.park_writedata, stream, default_flow_style=False)
            if (self.InsertorNew == False):
                with open(r'select_str.yml', 'r') as infile, open('select.yml', 'w') as outfile:
                    for line in infile:
                        line = line.replace("'", "")
                        outfile.write(line)
            else:
                with open(r'select_str.yml', 'r') as infile, open('select.yml', 'a') as outfile:
                    for line in infile:
                        line = line.replace("'", "")
                        outfile.write(line)
            self.park_writedata = []
            self.cread_id()
        self.InsertorNew = None

    def SetLaplacian(self):
        self.textBox = Text(self.root, font='Courier 15 bold', width=10, height=1)
        self.textBox.place(x=175, y=608)
        self.Label_erro = Label(self.root, text="Error.Try again !", bg=self.lightBlue2, foreground="red", width=12,
                                height=1, font='Constantia 10 bold')

        def getdt():
            try:
                abc = float(self.textBox.get("1.0", "end-1c"))
                self.textBox.delete('1.0', END)
                self.laplacian_num = abc
                self.check_lap = True
                with open('laplacian_num.yml', 'w') as stream:
                    yaml.dump(abc, stream, default_flow_style=False)
                self.Label_erro.place_forget()
            except ValueError:
                self.textBox.delete('1.0', END)
                self.Label_erro.place(x=120, y=645)
            self.Lable_usenum.configure(text=self.laplacian_num)

        self.buttonCommit = Button(self.root, height=1, font='Courier 13 bold', width=6, text="SET",
                                   command=lambda: getdt())
        self.buttonCommit.place(x=130, y=680)

    def cread_id(self):
        self.parking_mask = []
        try:
            with open('select.yml', 'r') as stream:
                self.data = yaml.load(stream)
                self.check_select = True
        except:
            open('select.yml', 'w')
            self.check_select = False
        self.content = os.stat("select.yml").st_size
        if (self.content != 0):  # cờ check nội dung tồn tại trong file detect.
            for park in self.data:  # đọc từng dictionary trong self.data - từ hàm self.read_detect_data
                points = np.array(park['points'])  # mảng đa chiều, lấy tọa độ vị trí tương ứng với points. ma trận 4x2
                self.id = int(np.array(park['id']))
                x, y = [], []
                for i in range(4):
                    x.append(points[i][0])
                    y.append(points[i][1])
                x1, x2, y1, y2 = min(x), max(x), min(y), max(y)
                points[:, 0] = points[:, 0] - x1  # Dịch về gốc tọa độ
                points[:, 1] = points[:, 1] - y1
                self.zero = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)  # Tạo ma trận rect[3] x rect[2]
                mask = cv2.drawContours(self.zero, [points], contourIdx=0, color=1, thickness=-1)
                # thickness <0 : lấp đầy ô, ngược lại thì chỉ kẻ đường viền
                # color=(255,0,0) xanh nước biển
                # contourIdx=-1:vẽ các đường viền bên trong
                # contourIdx=0:vẽ 1 đường bao quanh bên ngoài
                mask = mask == 1
                self.parking_mask.append(mask)
            self.total = self.id + 1
        else:
            self.data = []
            self.total = 0

    def read_lap(self):
        try:
            with open("laplacian_num.yml", 'r') as stream:  # doc file
                try:
                    self.laplacian_num = yaml.load(stream)  # lay gia tri tu file
                    a = float(self.laplacian_num)  # doi sang float, check là number hay string
                    self.check_lap = True
                except:  # khong phai la number
                    self.laplacian_num = 0  # set gia tri 1.5
                    with open('laplacian_num.yml', 'w') as stream:  # ghi lại vao file
                        yaml.dump(self.laplacian_num, stream, default_flow_style=False)
                    self.check_lap = False
        except:  # Neu khong tim thay file
            with open('laplacian_num.yml', 'w') as stream:  # tao file laplacian_num.yml moi
                self.laplacian_num = 0  # set gia tri 1.5
                yaml.dump(self.laplacian_num, stream, default_flow_style=False)  # ghi gia tri vao file
            self.check_lap = False

    def load_frame(self):
        cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGBA)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        self.lmain.imgtk = imgtk
        self.lmain.configure(image=imgtk)

    def points(self, event):
        x = event.x
        y = event.y
        self.count_point = self.count_point + 1
        if (x > 889):
            x = 889
        elif (x < 1):
            x = 1
        if (y > 499):
            y = 499
        elif (y < 1):
            y = 1
        self.rect_writedata.append([x, y])
        cv2.circle(self.frame, (x, y), 4, (255, 0, 0), -1)
        if (self.count_point == 1):
            self.x_one = x
            self.y_one = y
            self.x_temp = x
            self.y_temp = y
        elif (self.count_point == 4):
            cv2.line(self.frame, (x, y), (self.x_temp, self.y_temp), (255, 0, 0), 1, cv2.LINE_AA)
            cv2.line(self.frame, (x, y), (self.x_one, self.y_one), (255, 0, 0), 1, cv2.LINE_AA)
            self.f = self.f + 1
            self.park_writedata.append({'id': self.f, 'points': str(self.rect_writedata)})
            self.rect_writedata = []
            self.count_point = 0
        else:
            cv2.line(self.frame, (x, y), (self.x_temp, self.y_temp), (255, 0, 0), 1, cv2.LINE_AA)
            self.x_temp = x
            self.y_temp = y
        self.load_frame()

    def DrawInsert(self):
        self.InsertorNew = True
        if (self.content == 0):
            self.f = -1
        else:
            self.f = self.id
        self.lmain.bind("<Button 1>", self.points)

    def DrawNew(self):
        self.InsertorNew = False
        self.f = -1
        self.lmain.bind("<Button 1>", self.points)

    def ShowParking(self):
        if (self.InsertorNew != None):
            self.f = -1
            self.WriteSelect()
            self.count_point = 0
            self.rect_writedata = []
            self.ShowVideo()

    def DrawDelete(self):
        open('select.yml', 'w')
        self.cread_id()

    def StopThread(self):
        self.FlagThread = True
        # self.run1.join()
        if (self.stop_thingspeak == False):
            self.run2.join()
        self.root.destroy()

    def ShowVideo(self):
        ret, self.frame = self.cap.read()
        if (self.cap.isOpened() == False or ret == False):
            self.check_cap = False
        else:
            self.check_cap = True
            if (self.FlagThread == False):
                self.frame = cv2.resize(self.frame, (self.frame_l, self.frame_h))  # Thay đổi kích thước khung
                if (self.InsertorNew == None):
                    self.green_temp = 0
                    self.red_temp = 0
                    if (self.content != 0):
                        frame_blur = cv2.GaussianBlur(self.frame, (5, 5), 3)
                        frame_gray = cv2.cvtColor(frame_blur, cv2.COLOR_BGR2GRAY)
                        for ind, park in enumerate(self.data):
                            points = np.array(park['points'])
                            x, y = [], []
                            for i in range(4):
                                x.append(points[i][0])
                                y.append(points[i][1])
                            x1, x2, y1, y2 = min(x), max(x), min(y), max(y)
                            roi_gray = frame_gray[y1:y2, x1:x2]  # (x1,y1), (x2,y2)
                            laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F, ksize=1)
                            delta = np.mean(np.abs(laplacian * self.parking_mask[ind]))
                            status = delta < self.laplacian_num
                            if status != False:
                                cv2.drawContours(self.frame, [points], contourIdx=0, color=(0, 255, 0), thickness=2,
                                                 lineType=cv2.LINE_AA)
                                self.green_temp = self.green_temp + 1
                            else:
                                cv2.drawContours(self.frame, [points], contourIdx=0, color=(0, 0, 255), thickness=2,
                                                 lineType=cv2.LINE_AA)
                                self.red_temp = self.red_temp + 1
                    if (self.green_temp + self.red_temp == self.total):
                        self.Lable_green.configure(text=self.green_temp)
                        self.Lable_red.configure(text=self.red_temp)
                        self.CheckShowStatus()
                    if (self.green_temp != self.green or self.red_temp != self.red):
                        self.green = self.green_temp
                        self.red = self.red_temp
                        self.stop_thingspeak = False
                        self.run2 = threading.Thread(target=self.SendThingspeak)
                        self.run2.start()
                    self.load_frame()
                    self.root.after(10, self.ShowVideo)

    def SendThingspeak(self):
        while (self.FlagThread == False and self.stop_thingspeak == False):
            if (self.green + self.red == self.total):
                try:
                    r = requests.post('https://api.thingspeak.com/update.json',
                                      data={'api_key': self.thingspeak_key, 'field1': self.green, 'field2': self.red})
                    self.check_thingspeak = r.ok
                    if (r.ok == True):
                        self.stop_thingspeak = True
                except:
                    self.check_thingspeak = False

    def CheckShowStatus(self):
        if (self.check_cap == False):
            self.Lable_1_T.place_forget()
            self.Lable_1_F.place(x=878, y=555)
        else:
            self.Lable_1_F.place_forget()
            self.Lable_1_T.place(x=878, y=557)
        if (self.check_select == False):
            self.Lable_2_T.place_forget()
            self.Lable_2_F.place(x=878, y=576)
        else:
            self.Lable_2_F.place_forget()
            self.Lable_2_T.place(x=878, y=578)
        if (self.check_lap == False):
            self.Lable_3_T.place_forget()
            self.Lable_3_F.place(x=878, y=596)
        else:
            self.Lable_3_F.place_forget()
            self.Lable_3_T.place(x=878, y=600)
        if (self.check_thingspeak == True):
            self.Lable_4_F.place_forget()
            self.Lable_4_T.place(x=878, y=620)
        else:
            self.Lable_4_T.place_forget()
            self.Lable_4_F.place(x=878, y=618)

    def CreateAll(self):
        menubar = Menu(self.root, activeborderwidth=3)
        filemenu = Menu(menubar, tearoff=0)
        submenu = Menu(filemenu)
        submenu.add_command(label="New all", command=self.DrawNew)
        submenu.add_command(label="Insert", command=self.DrawInsert)
        submenu.add_command(label="Delete", command=self.DrawDelete)
        filemenu.add_command(label="Show parking", command=self.ShowParking)
        filemenu.add_cascade(label="Draw location", menu=submenu)
        filemenu.add_separator()
        filemenu.add_command(label="Close", command=self.StopThread)
        menubar.add_cascade(label="FILE", menu=filemenu)
        self.root.config(menu=menubar)
        Lable_control = Label(self.root, image=self.backr, borderwidth=0)
        Lable_control.configure(highlightthickness=0)
        Lable_control.place(x=3, y=510)
        self.Lable_1_F = Label(self.root, image=self.check_F, borderwidth=0, highlightthickness=0)
        self.Lable_1_T = Label(self.root, image=self.check_T, borderwidth=0, highlightthickness=0)
        self.Lable_2_F = Label(self.root, image=self.check_F, borderwidth=0, highlightthickness=0)
        self.Lable_2_T = Label(self.root, image=self.check_T, borderwidth=0, highlightthickness=0)
        self.Lable_3_F = Label(self.root, image=self.check_F, borderwidth=0, highlightthickness=0)
        self.Lable_3_T = Label(self.root, image=self.check_T, borderwidth=0, highlightthickness=0)
        self.Lable_4_F = Label(self.root, image=self.check_F, borderwidth=0, highlightthickness=0)
        self.Lable_4_T = Label(self.root, image=self.check_T, borderwidth=0, highlightthickness=0)
        self.Lable_usenum = Label(self.root, bg=self.lightBlue2, width=4, height=1, justify=LEFT,
                                  font='Courier 25 bold')
        self.Lable_usenum.configure(text=self.laplacian_num)
        self.Lable_usenum.place(x=215, y=523)
        self.Lable_green = Label(self.root, bg=self.lightBlue2, width=2, height=1, justify=LEFT, font='Courier 50 bold')
        self.Lable_green.place(x=550, y=550)
        self.Lable_red = Label(self.root, bg=self.lightBlue2, width=2, height=1, justify=LEFT, font='Courier 50 bold')
        self.Lable_red.place(x=550, y=610)
        self.SetLaplacian()


if __name__ == '__main__':
    GuiThread()
