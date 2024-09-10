import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import cv2
import face_recognition
import easyocr
import sqlite3
import os

# 初始化EasyOCR
reader = easyocr.Reader(['ch_sim'])  # 使用中文

# 手写画板类
class HandwritingPad(tk.Toplevel):
    def __init__(self, master=None, on_recognize=None):
        super().__init__(master)
        self.title("手写画板")
        self.geometry("400x400")
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.button_recognize = tk.Button(self, text="识别", command=self.recognize_handwriting)
        self.button_recognize.pack(pady=10)
        self.draw = None
        self.image = Image.new("RGB", (400, 400), "white")
        self.image_draw = ImageDraw.Draw(self.image)
        self.on_recognize = on_recognize

        self.canvas.bind("<B1-Motion>", self.paint)

    def paint(self, event):
        x, y = event.x, event.y
        if self.draw is None:
            self.draw = [(x, y)]
        else:
            self.draw.append((x, y))
            self.canvas.create_line(self.draw[-2], self.draw[-1], fill="black", width=2)
            self.image_draw.line(self.draw[-2:] , fill="black", width=2)
        self.draw = self.draw[-1:]

    def recognize_handwriting(self):
        self.image.save("handwriting.png")
        text = recognize_handwriting("handwriting.png")
        if self.on_recognize:
            self.on_recognize(text)
        self.destroy()

def recognize_handwriting(image_path):
    results = reader.readtext(image_path)
    text = ""
    for result in results:
        text += result[1] + "\n"
    return text.strip()

# 打卡系统类
class ClockInApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("打卡系统")
        self.geometry("400x250")
        
        self.label_number = tk.Label(self, text="输入数字:")
        self.label_number.pack(pady=5)
        self.entry_number = tk.Entry(self)
        self.entry_number.pack(pady=5)
        
        self.label_name = tk.Label(self, text="姓名:")
        self.label_name.pack(pady=5)
        self.entry_name = tk.Entry(self)
        self.entry_name.pack(pady=5)
        
        self.button_handwriting = tk.Button(self, text="手写", command=self.open_handwriting_pad)
        self.button_handwriting.pack(pady=10)
        
        self.button_register = tk.Button(self, text="注册", command=self.register_face)
        self.button_register.pack(pady=5)
        
        self.button_check_in = tk.Button(self, text="打卡", command=self.check_in)
        self.button_check_in.pack(pady=5)
        
        self.face_encodings = {}
        self.load_face_encodings()

    def open_handwriting_pad(self):
        def on_recognize(text):
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, text)

        HandwritingPad(self, on_recognize)

    def register_face(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showerror("错误", "请先输入姓名")
            return
        
        video_capture = cv2.VideoCapture(0)
        ret, frame = video_capture.read()
        video_capture.release()
        if not ret:
            messagebox.showerror("错误", "无法获取视频帧")
            return
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            messagebox.showerror("错误", "未检测到人脸")
            return
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            messagebox.showerror("错误", "无法编码人脸")
            return
        
        self.face_encodings[name] = face_encodings[0]
        self.save_face_encodings()
        messagebox.showinfo("成功", "人脸注册成功")

    def check_in(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showerror("错误", "请先输入姓名")
            return
        
        video_capture = cv2.VideoCapture(0)
        ret, frame = video_capture.read()
        video_capture.release()
        if not ret:
            messagebox.showerror("错误", "无法获取视频帧")
            return
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            messagebox.showerror("错误", "未检测到人脸")
            return
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        if not face_encodings:
            messagebox.showerror("错误", "无法编码人脸")
            return
        
        matched = False
        for known_face_encoding in self.face_encodings.values():
            matches = face_recognition.compare_faces([known_face_encoding], face_encodings[0])
            if True in matches:
                matched = True
                break
        
        if matched:
            self.record_check_in(name)
            messagebox.showinfo("成功", f"{name} 打卡成功")
        else:
            messagebox.showerror("错误", "人脸识别失败")

    def load_face_encodings(self):
        if os.path.exists("face_encodings.db"):
            with sqlite3.connect("face_encodings.db") as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS face_encodings (name TEXT PRIMARY KEY, encoding BLOB)")
                cursor.execute("SELECT name, encoding FROM face_encodings")
                rows = cursor.fetchall()
                for name, encoding in rows:
                    self.face_encodings[name] = face_recognition.face_encodings(face_recognition.load_image_file(encoding))[0]

    def save_face_encodings(self):
        with sqlite3.connect("face_encodings.db") as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS face_encodings (name TEXT PRIMARY KEY, encoding BLOB)")
            for name, encoding in self.face_encodings.items():
                cursor.execute("INSERT OR REPLACE INTO face_encodings (name, encoding) VALUES (?, ?)", (name, encoding.tobytes()))
            conn.commit()

    def record_check_in(self, name):
        with sqlite3.connect("check_in_records.db") as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS check_in_records (name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            cursor.execute("INSERT INTO check_in_records (name) VALUES (?)", (name,))
            conn.commit()

if __name__ == "__main__":
    app = ClockInApp()
    app.mainloop()
