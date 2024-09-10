import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageTk

# 数据库初始化
def init_db():
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (id INTEGER PRIMARY KEY, name TEXT, face_encoding BLOB)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clock_in
                      (id INTEGER PRIMARY KEY, user TEXT, time TEXT, location TEXT)''')
    conn.commit()
    conn.close()

# 保存用户面部信息
def save_face_encoding(name, encoding):
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, face_encoding) VALUES (?, ?)', (name, encoding))
    conn.commit()
    conn.close()

# 获取用户面部信息
def get_face_encoding(name):
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT face_encoding FROM users WHERE name = ?', (name,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return np.frombuffer(result[0], dtype=np.float64)
    else:
        return None

# 记录打卡信息
def record_clock_in(user, location):
    conn = sqlite3.connect('time_tracker.db')
    cursor = conn.cursor()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO clock_in (user, time, location) VALUES (?, ?, ?)', (user, current_time, location))
    conn.commit()
    conn.close()
    messagebox.showinfo("成功", f"打卡记录成功：{user} 在 {current_time}")

# 获取摄像头图像
def get_camera_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite('current_frame.jpg', frame)
        return 'current_frame.jpg'
    else:
        messagebox.showerror("错误", "无法捕获图像")
        return None

# 识别面部
def recognize_face(image_path, known_encoding=None):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    
    if len(face_encodings) > 0:
        if known_encoding is not None:
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces([known_encoding], face_encoding)
                if True in matches:
                    return True
        else:
            return face_encodings[0]  # 返回第一个识别到的面部编码
    return None

# 处理小键盘按钮事件
def handle_keypad_input(key):
    current_text = user_entry.get()
    if key == 'DEL':
        user_entry.delete(len(current_text)-1, tk.END)
    elif key == 'CLR':
        user_entry.delete(0, tk.END)
    else:
        user_entry.insert(tk.END, key)

# GUI设计
def main():
    init_db()
    
    def on_register():
        user = user_entry.get()
        if not user:
            messagebox.showwarning("输入错误", "请输入您的名字")
            return
        
        image_path = get_camera_image()
        if image_path:
            encoding = recognize_face(image_path)
            if encoding is not None:
                save_face_encoding(user, encoding.tobytes())
                messagebox.showinfo("成功", f"用户 {user} 注册成功")
            else:
                messagebox.showerror("面部识别错误", "无法识别面部，请重试。")

    def on_clock_in():
        user = user_entry.get()
        if not user:
            messagebox.showwarning("输入错误", "请输入您的名字")
            return
        
        known_encoding = get_face_encoding(user)
        if known_encoding is not None:
            image_path = get_camera_image()
            if image_path:
                face_encoding = recognize_face(image_path)
                if face_encoding is not None:
                    matches = face_recognition.compare_faces([known_encoding], face_encoding)
                    if True in matches:
                        record_clock_in(user, '办公室')  # 根据实际位置调整
                    else:
                        messagebox.showerror("面部识别错误", "面部未识别成功，请重试。")
                else:
                    messagebox.showerror("面部识别错误", "面部未识别成功，请重试。")
            else:
                messagebox.showerror("相机错误", "无法捕获图像")
        else:
            messagebox.showerror("用户错误", "用户未注册，请先注册。")

    root = tk.Tk()
    root.title("打卡系统")

    tk.Label(root, text="请输入您的名字：").pack(pady=10)
    global user_entry
    user_entry = tk.Entry(root, width=30)
    user_entry.pack(pady=5)

    register_button = tk.Button(root, text="注册", command=on_register)
    register_button.pack(pady=5)

    clock_in_button = tk.Button(root, text="打卡", command=on_clock_in)
    clock_in_button.pack(pady=20)

    # 小键盘布局
    keypad_frame = tk.Frame(root)
    keypad_frame.pack(pady=10)
    keys = [
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        'DEL', 'CLR'
    ]
    for key in keys:
        button = tk.Button(keypad_frame, text=key, width=5, height=2, command=lambda k=key: handle_keypad_input(k))
        button.grid(row=keys.index(key)//3, column=keys.index(key)%3, padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
