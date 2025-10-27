import os
import json
import time
import random
import calendar
import datetime
import threading
import webbrowser
import cv2
from PIL import Image, ImageTk
import threading
import pygame
import pyttsx3
import speech_recognition as sr
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import customtkinter as ctk
import tkintermapview
import cv2
import numpy as np
import time
from tkinter import simpledialog, messagebox
import gps
import emoji
from tkcalendar import Calendar
import gpsd

pygame.mixer.init()
REMINDER_FILE = "reminders.json"
USER_FILE = "users.json"
CARD_SCORES_FILE = "card_matcher_scores.json"


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("dark-blue")  


class WatchAssistant:
    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("MemoBand")
        self.root.geometry("480x300")
        self.tts_engine = pyttsx3.init()
       
        try:
            rate = self.tts_engine.getProperty('rate')
            self.tts_engine.setProperty('rate', max(80, rate - 50))
        except Exception:
            pass

        self.running_game = False
        self.reminders = self.load_reminders()
        self.clock_label = None
        self.current_user = None
        self.game_status = None
        self.load_users()
        self.profile_pic_path = None
      
        threading.Thread(target=self.reminder_checker, daemon=True).start()

        self.login_screen()
        self.update_clock()

    # ---------- Login & Signup ----------
    def login_screen(self):
        self.clear_screen()
        header = ctk.CTkLabel(self.root, text="Login", font=ctk.CTkFont(size=26, weight="bold"))
        header.pack(pady=(10,10))

        frm = ctk.CTkFrame(self.root)
        frm.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frm, text="Username:", anchor="w").pack(pady=(8, 2), fill="x")
        username_entry = ctk.CTkEntry(frm, placeholder_text="Enter username")
        username_entry.pack(pady=2, fill="x")

        ctk.CTkLabel(frm, text="Password:", anchor="w").pack(pady=(8, 2), fill="x")
        password_entry = ctk.CTkEntry(frm, placeholder_text="Enter password", show="•")
        password_entry.pack(pady=2, fill="x")

        def try_login():
            users = self.load_users()
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if username in users and users[username] == password:
                self.current_user = username
                self.home_screen()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")

        ctk.CTkButton(self.root, text="Login", command=try_login, width=200).pack(pady=(12, 6))
        ctk.CTkButton(self.root, text="Sign Up",
                      command=self.signup_screen, width=200).pack()

    def signup_screen(self):
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Sign Up", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 10))

        frm = ctk.CTkFrame(self.root)
        frm.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(frm, text="Choose Username:", anchor="w").pack(pady=(8, 2), fill="x")
        username_entry = ctk.CTkEntry(frm)
        username_entry.pack(pady=2, fill="x")

        ctk.CTkLabel(frm, text="Choose Password:", anchor="w").pack(pady=(8, 2), fill="x")
        password_entry = ctk.CTkEntry(frm, show="•")
        password_entry.pack(pady=2, fill="x")

        def do_signup():
            users = self.load_users()
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                messagebox.showwarning("Error", "Username and password cannot be empty!")
                return
            if username in users:
                messagebox.showwarning("Error", "Username already exists!")
                return
            users[username] = password
            self.save_users(users)
            messagebox.showinfo("Success", "Account created! Please log in.")
            self.login_screen()

        ctk.CTkButton(self.root, text="Create Account", command=do_signup, width=200).pack(pady=(10, 6))
        ctk.CTkButton(self.root, text="Back to Login", command=self.login_screen).pack()

    def load_users(self):
        if os.path.exists(USER_FILE):
            try:
                with open(USER_FILE, "r") as f:
                    users_list = json.load(f)
                    return {u["Username"]: u["Password"] for u in users_list}
            except Exception:
                return {}
        return {}

    def save_users(self, users_dict):
        users_list = [{"Username": k, "Password": v} for k, v in users_dict.items()]
        try:
            with open(USER_FILE, "w") as f:
                json.dump(users_list, f, indent=4)
        except Exception:
            pass



    # ---------- Utils ----------
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def speak(self, text):
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception:
            pass

    def exit_app(self):
        self.running_game = False
        self.save_reminders()
        self.root.quit()

    def update_clock(self):
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        if self.clock_label:
            self.clock_label.configure(text=now)
        self.root.after(1000, self.update_clock)

    def load_reminders(self):
        if os.path.exists(REMINDER_FILE):
            try:
                with open(REMINDER_FILE, "r") as f:
                    reminders_list = json.load(f)
                    reminders_dict = {}
                    for r in reminders_list:
                        key = f"{r['Username']}:{r['Date']}|{r['Time']}"
                        reminders_dict[key] = r["Message"]
                    return reminders_dict
            except Exception:
                return {}
        return {}

    def save_reminders(self):
        try:
            reminders_list = []
            for key, msg in self.reminders.items():
                user, date_time = key.split(":", 1)
                date, time_str = date_time.split("|")
                reminders_list.append({
                    "Username": user,
                    "Date": date,
                    "Time": time_str,
                    "Message": msg
                })
            with open(REMINDER_FILE, "w") as f:
                json.dump(reminders_list, f, indent=4)
        except Exception:
            pass
    # ---------- Reminder Notifications (background) ----------
    def reminder_checker(self):
        while True:
            now = datetime.datetime.now()
            now_str = now.strftime("%Y-%m-%d|%I:%M %p")
            for key, task in list(self.reminders.items()):
                try:
                    user, date_time = key.split(":", 1)
                except ValueError:
                    continue
                if user == self.current_user and date_time == now_str:
                    self.root.after(0, self.show_reminder_popup, key, task)
            time.sleep(1)

    def show_reminder_popup(self, key, task):
        try:
            messagebox.showinfo("Reminder", f"{task}")
            self.speak(f"Reminder: {task}")
        except Exception:
            pass
        if key in self.reminders:
            del self.reminders[key]
            self.save_reminders()

    # ---------- Speech Keyword Helpers ----------
    def homescreen_keywords(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio).lower()
                if "reminder" in text:
                    self.reminders_menu()
                elif "games" in text:
                    self.games_menu()
                elif "location" in text:
                    self.location_menu()
                elif "stress" in text or "relief" in text:
                    self.stress_relief_menu()
                elif "logout" in text:
                    self.logout()
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("API request failed")
        except sr.WaitTimeoutError:
            print("Listening timed out")
        except Exception:
            pass

    def reminder_keywords(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio).lower()
                if "review" in text:
                    self.review_day()
                elif "upcoming" in text:
                    self.upcoming_reminders()
                elif "create" in text:
                    self.add_reminder()
                else:
                    print("No matching command found")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("API request failed")
        except sr.WaitTimeoutError:
            print("Listening timed out")
        except Exception:
            pass

    def games_keywords(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio).lower()
                if "card" in text:
                    self.card_matcher_game()
                elif "hang" in text:
                    self.hangman_game()
                elif "object" in text:
                    self.object_finder_game()
                else:
                    print("No matching command found")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("API request failed")
        except sr.WaitTimeoutError:
            print("Listening timed out")
        except Exception:
            pass
    # ---------- Home Screen ----------
    def home_screen(self):
        self.clear_screen()
        top_frame = ctk.CTkFrame(self.root)
        top_frame.pack(pady=10, padx=10, fill="x")
        ctk.CTkLabel(top_frame, text=f"Welcome, {self.current_user}!", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=5)

        btn_frame = ctk.CTkFrame(self.root)
        btn_frame.pack(pady=10, padx=10, fill="both", expand=False)

        ctk.CTkButton(btn_frame, text="Reminders", command=self.reminders_menu, width=240).pack(pady=8)
        ctk.CTkButton(btn_frame, text="Games", command=self.games_menu, width=240).pack(pady=8)
        ctk.CTkButton(btn_frame, text="Location", command=self.location_menu, width=240).pack(pady=8)
        ctk.CTkButton(btn_frame, text="Stress Relief", command=self.stress_relief_menu, width=240).pack(pady=8)

        footer = ctk.CTkFrame(self.root)
        footer.pack(side="bottom", pady=10, padx=10, fill="x")
        ctk.CTkButton(footer, text="Logout", command=self.logout, width=100).pack(side="left", padx=10)
        ctk.CTkButton(footer, text= "\U0001f442 Speak It!", command=lambda: threading.Thread(target=self.homescreen_keywords).start(), width=150).pack(side="right", padx=10)

    # ---------- Reminders Section ----------
    def reminders_menu(self):
        self.clear_screen()
        header = ctk.CTkLabel(self.root, text="Reminders", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=12)

        ctk.CTkButton(self.root, text="Review My Day", command=self.review_day, width=200).pack(pady=6)
        ctk.CTkButton(self.root, text="Upcoming Reminders", command=self.upcoming_reminders, width=200).pack(pady=6)
        ctk.CTkButton(self.root, text="Create Reminder", command=self.add_reminder, width=200).pack(pady=6)
        ctk.CTkButton(self.root, text="Back", command=self.home_screen, width=200, fg_color="gray").pack(pady=16)
        ctk.CTkButton(self.root, text="\U0001f442 Speak It!", command=lambda: threading.Thread(target=self.reminder_keywords).start(), width=200).pack(pady=6)

    # ---------- Games Section ----------
    def games_menu(self): 
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Games", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=12)
        ctk.CTkButton(self.root, text="Hangman", command=self.hangman_game, width=240).pack(pady=8)
        ctk.CTkButton(self.root, text="Card Matcher", command=self.card_matcher_game, width=240).pack(pady=8)
        ctk.CTkButton(self.root, text="Object Finder", command=self.object_finder_game, width=240).pack(pady=8)
        ctk.CTkButton(self.root, text="Back", command=self.home_screen, width=200, fg_color="gray").pack(pady=16)
        ctk.CTkButton(self.root, text="\U0001f442 Speak It!", command=lambda: threading.Thread(target=self.games_keywords).start(), width=200).pack(pady=6)

    # ---------- Location Section ----------
   



    def location_menu(self):
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Location", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=6)
        ctk.CTkButton(self.root, text="Back", command=self.home_screen, width=200).pack(pady=6)

        map_frame = ctk.CTkFrame(self.root)
        map_frame.pack(pady=12, padx=12, fill="both", expand=True)

        map_widget = tkintermapview.TkinterMapView(map_frame, corner_radius=10)
        map_widget.pack(fill="both", expand=True)

        map_widget.set_position(0, 0)
        map_widget.set_zoom(15)

        marker = map_widget.set_marker(0, 0, text="My Location")

        gpsd.connect()

        prev_lat = None
        prev_lon = None
        steps_per_second = 10
        sleep_time = 100 

        def update_gps():
            nonlocal prev_lat, prev_lon

            packet = gpsd.get_current()
            if packet.mode >= 2: 
                lat = packet.lat
                lon = packet.lon

                if prev_lat is None:
                    prev_lat = lat
                    prev_lon = lon
                    marker.set_position(lat, lon)
                    map_widget.set_position(lat, lon)
                else:
                    steps = steps_per_second
                    delta_lat = (lat - prev_lat) / steps
                    delta_lon = (lon - prev_lon) / steps

                    for i in range(1, steps + 1):
                        smooth_lat = prev_lat + delta_lat * i
                        smooth_lon = prev_lon + delta_lon * i
                        self.root.after(i * sleep_time, lambda sl=smooth_lat, slon=smooth_lon: update_marker(sl, slon))

                    prev_lat = lat
                    prev_lon = lon

            self.root.after(1000, update_gps)

        def update_marker(lat, lon):
            marker.set_position(lat, lon)
            map_widget.set_position(lat, lon)

        update_gps()


    # ---------- Stress Relief Section ----------
    def stress_relief_menu(self):
        self.breathing_exercise()

    def breathing_exercise(self):
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Breathing Exercise", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=12)
        ctk.CTkLabel(self.root, text="Follow the breathing prompts below.").pack(pady=6)
        breath_label = ctk.CTkLabel(self.root, text="", font=ctk.CTkFont(size=28, weight="bold"))
        breath_label.pack(pady=16)
        ctk.CTkButton(self.root, text="Back", command=self.home_screen, width=200).pack(side="bottom", pady=12)

        def speak_with_pause(text):
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception:
                pass

        def breathing_cycle():
            for _ in range(4):
                breath_label.configure(text="Breathe In")
                speak_with_pause("Breathe in")
                time.sleep(3)
                breath_label.configure(text="Breathe Out")
                speak_with_pause("Breathe out")
                time.sleep(3)
            breath_label.configure(text="Done!")
            speak_with_pause("Great job! You finished the breathing exercise.")

        threading.Thread(target=breathing_cycle, daemon=True).start()

    # ---------- Game placeholders ----------
    def hangman_game(self):
        messagebox.showinfo("Hangman", "Hangman game coming soon!")

    def card_matcher_game(self):
        self.clear_screen()
        ctk.CTkLabel(self.root, text="Card Matcher", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=8)
        ctk.CTkLabel(self.root, text="Choose number of cards:").pack(pady=6)
        btn_frame = ctk.CTkFrame(self.root)
        btn_frame.pack(pady=6)
        for num in [10, 16, 24]:
            ctk.CTkButton(btn_frame, text=f"{num} Cards", width=120,
                          command=lambda n=num: self.start_card_matcher(n)).pack(side="left", padx=6)
        ctk.CTkButton(self.root, text="Back", command=self.games_menu, width=200, fg_color="gray").pack(pady=12)

    def object_finder_game(self):
       messagebox.showinfo("Object Finder", "Object Finder coming soon!")

    # ---------- Reminders Functionality ----------
    def add_reminder(self):
        self.clear_screen()
        top = ctk.CTkFrame(self.root)
        top.pack(pady=4, padx=10, fill="x")

        self.clock_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.clock_label.pack(pady=3)

        ctk.CTkLabel(self.root, text="Make Reminder", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=2)

        time_frame = ctk.CTkFrame(self.root)
        time_frame.pack(pady=4, padx=10, fill="x")

        # Year selector
        ctk.CTkLabel(time_frame, text="Year:").grid(row=0, column=0, padx=5, pady=3, sticky="w")
        year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        years = [str(y) for y in range(datetime.datetime.now().year, datetime.datetime.now().year + 11)]
        year_menu = ctk.CTkOptionMenu(time_frame, values=years, variable=year_var)
        year_menu.grid(row=0, column=1, padx=5, pady=5)

        # Month selector
        ctk.CTkLabel(time_frame, text="Month:").grid(row=0, column=2, padx=5, pady=3, sticky="w")
        month_var = tk.StringVar(value=datetime.datetime.now().strftime("%B"))
        months = list(calendar.month_name)[1:]
        month_menu = ctk.CTkOptionMenu(time_frame, values=months, variable=month_var, width=110)
        month_menu.grid(row=0, column=3, padx=5, pady=5)

        # Day selector
        ctk.CTkLabel(time_frame, text="Day:").grid(row=1, column=0, padx=4, pady=3, sticky="w")
        day_var = tk.StringVar(value=str(datetime.datetime.now().day))
        days_menu = ctk.CTkOptionMenu(time_frame, values=[str(d) for d in range(1, 32)], variable=day_var)
        days_menu.grid(row=1, column=1, padx=5, pady=5)

        def update_days(*args):
            try:
                month_num = list(calendar.month_name).index(month_var.get())
                year_num = int(year_var.get())
                last_day = calendar.monthrange(year_num, month_num)[1]
                days = [str(d) for d in range(1, last_day + 1)]
                days_menu.configure(values=days)
                if int(day_var.get()) > last_day:
                    day_var.set(str(last_day))
            except Exception:
                pass

        month_var.trace_add("write", lambda *_: update_days())
        year_var.trace_add("write", lambda *_: update_days())
        update_days()

        # Hour / Minute / AM-PM
        ctk.CTkLabel(time_frame, text="Hour (1-12):").grid(row=1, column=2, padx=5, pady=3, sticky="w")
        hour_entry = ctk.CTkEntry(time_frame, width=60)
        hour_entry.grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkLabel(time_frame, text="Minute (00-59):").grid(row=2, column=0, padx=5, pady=3, sticky="w")
        minute_entry = ctk.CTkEntry(time_frame, width=60)
        minute_entry.grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(time_frame, text="AM/PM:").grid(row=2, column=2, padx=5, pady=3, sticky="w")
        ampm_var = tk.StringVar(value="AM")
        ampm_menu = ctk.CTkOptionMenu(time_frame, values=["AM", "PM"], variable=ampm_var, width=110)
        ampm_menu.grid(row=2, column=3, padx=5, pady=5)

        ctk.CTkLabel(self.root, text="Task:", anchor="w").pack(pady=(2, 2), padx=10, fill="x")
        task_entry = ctk.CTkEntry(self.root)
        task_entry.pack(padx=10, fill="x")

        # Save reminder function
        def save_reminders():
            try:
                year = year_var.get()
                month_name = month_var.get()
                month_num = list(calendar.month_name).index(month_name)
                day = str(int(day_var.get())).zfill(2)
                hour = hour_entry.get().strip()
                minute = minute_entry.get().strip()
                ampm = ampm_var.get()
                task = task_entry.get().strip()

                hour_int = int(hour)
                minute_int = int(minute)
                if not (1 <= hour_int <= 12):
                    raise ValueError("Hour must be 1-12")
                if not (0 <= minute_int <= 59):
                    raise ValueError("Minute must be 0-59")
                # Validate date
                datetime.datetime(int(year), month_num, int(day))
            except Exception as e:
                messagebox.showwarning("Error", f"Invalid date/time: {e}")
                return

            if not task:
                messagebox.showwarning("Error", "Task cannot be empty!")
                return

            time_str = f"{hour_int:02}:{minute_int:02} {ampm}"
            key = f"{self.current_user}:{year}-{month_num:02}-{day}|{time_str}"
            self.reminders[key] = task
            self.save_reminders()
            messagebox.showinfo("Success", f"Reminder set for {month_name} {int(day)} {year} {time_str}: {task}")
            self.speak(f"Reminder added for {month_name} {int(day)} {year} at {time_str}")
            self.reminders_menu()

        btn_frame = ctk.CTkFrame(self.root)
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text="Save Reminder", command=save_reminders, width=130).grid(row=0, column=0, padx=8)
        ctk.CTkButton(btn_frame, text="Back", command=self.reminders_menu, width=130).grid(row=0, column=1, padx=8)

    def review_day(self):
        self.clear_screen()
        top = ctk.CTkFrame(self.root)
        top.pack(pady=6, padx=10, fill="x")
        self.clock_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.clock_label.pack(pady=6)
        ctk.CTkLabel(self.root, text="Today's Review", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=8)

        today = datetime.datetime.now().strftime("%Y-%m-%d")
        reminders_today = [(k, v) for k, v in self.reminders.items() if k.startswith(f"{self.current_user}:{today}")]
        # Sort by time
        def keyfunc(item):
            _, date_time = item[0].split(":", 1)
            date, time_str = date_time.split("|")
            dt = datetime.datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %I:%M %p")
            return dt
        reminders_today.sort(key=keyfunc)

        if reminders_today:
            for k, task in reminders_today:
                _, date_time = k.split(":", 1)
                date, time_str = date_time.split("|")
                ctk.CTkLabel(self.root, text=f"{time_str} - {task}").pack(pady=4)
            reminders_text = ", ".join([f"At {k.split('|')[1]}, {v}" for k, v in reminders_today])
            self.speak(f"Here are your reminders: {reminders_text}")
        else:
            ctk.CTkLabel(self.root, text="No tasks for today!").pack(pady=6)
            self.speak("You have no tasks for today.")
        ctk.CTkButton(self.root, text="Back", command=self.reminders_menu, width=200).pack(pady=12)

    def upcoming_reminders(self):
        self.clear_screen()
        top = ctk.CTkFrame(self.root)
        top.pack(pady=6, padx=10, fill="x")
        self.clock_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.clock_label.pack(pady=6)
        ctk.CTkLabel(self.root, text="All Reminders", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=8)

        user_reminders = [(k, v) for k, v in self.reminders.items() if k.startswith(f"{self.current_user}:")]

        def keyfunc(item):
            _, date_time = item[0].split(":", 1)
            date, time_str = date_time.split("|")
            dt = datetime.datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %I:%M %p")
            return dt

        user_reminders.sort(key=keyfunc)

        if user_reminders:
            for k, task in user_reminders:
                _, date_time = k.split(":", 1)
                date, time_str = date_time.split("|")
                frame = ctk.CTkFrame(self.root)
                frame.pack(fill="x", padx=10, pady=4)
                ctk.CTkLabel(frame, text=f"{date} {time_str} - {task}").pack(side="left", padx=6)
                def make_delete_func(reminder_key=k):
                    return lambda: self.delete_reminder(reminder_key)
                ctk.CTkButton(frame, text="Delete", command=make_delete_func(), width=80).pack(side="right", padx=6)
        else:
            ctk.CTkLabel(self.root, text="No reminders!").pack(pady=6)
        ctk.CTkButton(self.root, text="Back", command=self.reminders_menu, width=200).pack(pady=12)

    def delete_reminder(self, key):
        if key in self.reminders:
            del self.reminders[key]
            self.save_reminders()
        self.upcoming_reminders()

    # ---------- Memory Game (simple placeholder) ----------
    def start_game(self):
        self.clear_screen()
        self.running_game = True
        top = ctk.CTkFrame(self.root)
        top.pack(pady=6, padx=6, fill="x")
        self.clock_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.clock_label.pack(pady=6)
        ctk.CTkLabel(self.root, text="Memory Game", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=8)
        self.game_status = ctk.CTkLabel(self.root, text="Listen carefully!")
        self.game_status.pack(pady=12)

        btn_frame = ctk.CTkFrame(self.root)
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text="Correct (Y)", width=150, command=lambda: self.answer(True)).pack(pady=6)
        ctk.CTkButton(btn_frame, text="Wrong (N)", width=150, command=lambda: self.answer(False)).pack(pady=6)
        ctk.CTkButton(btn_frame, text="Skip Item", width=150, command=lambda: self.answer(None)).pack(pady=6)
        ctk.CTkButton(self.root, text="Back", command=self.games_menu, width=200).pack(pady=12)

        threading.Thread(target=self.run_game, daemon=True).start()

    def run_game(self):
        items = ["apple", "banana", "grape"]
        for item in items:
            if not self.running_game:
                break
            self.speak(f"Please show me a {item}")
            self.update_status(f"Please show me a {item}")
            time.sleep(5)

    def update_status(self, text):
        if self.game_status:
            self.game_status.configure(text=text)

    def answer(self, correct):
        if correct is True:
            self.update_status("Correct!")
            self.speak("Correct!")
        elif correct is False:
            self.update_status("Wrong!")
            self.speak("Wrong!")
        else:
            self.update_status("Skipped!")
            self.speak("Skipped!")

    def logout(self):
        self.current_user = None
        self.login_screen()

    def delete_account(self):
        if messagebox.askyesno("Delete Account", "Are you sure you want to delete your account? This cannot be undone."):
            users = self.load_users()
            if self.current_user in users:
                del users[self.current_user]
                self.save_users(users)
            # Remove all reminders for this user
            keys_to_delete = [k for k in self.reminders if k.startswith(f"{self.current_user}:")]
            for k in keys_to_delete:
                del self.reminders[k]
            self.save_reminders()
            self.current_user = None
            self.login_screen()

    # ---------- Card Matcher helpers ----------
    def load_card_scores(self):
        if os.path.exists(CARD_SCORES_FILE):
            try:
                with open(CARD_SCORES_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {"10": [], "16": [], "24": []}
        return {"10": [], "16": [], "24": []}

    def save_card_scores(self, scores):
        try:
            with open(CARD_SCORES_FILE, "w") as f:
                json.dump(scores, f)
        except Exception:
            pass

    def start_card_matcher(self, num_cards):
        # Setup board & state
        self.clear_screen()
        self.card_scores = self.load_card_scores()
        self.card_matcher_start_time = time.time()
        self.card_matcher_flipped = []
        self.card_matcher_buttons = []
        self.card_matcher_matches = 0
        self.card_matcher_total = num_cards // 2
        self.card_matcher_num = num_cards
        self.card_matcher_board = list(range(1, num_cards // 2 + 1)) * 2
        random.shuffle(self.card_matcher_board)

        ctk.CTkLabel(self.root, text=f"Card Matcher - {num_cards} Cards", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=6, pady=8, padx=8)
        self.card_matcher_timer_label = ctk.CTkLabel(self.root, text="Time: 0.0s")
        self.card_matcher_timer_label.grid(row=1, column=0, columnspan=6, pady=4)

        # Scoreboard
        score_frame = ctk.CTkFrame(self.root)
        score_frame.grid(row=2, column=6, rowspan=6, padx=8, pady=8)
        ctk.CTkLabel(score_frame, text="Top 3 Scores", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=6)
        top_scores = self.card_scores.get(str(num_cards), [])
        if top_scores:
            for i, score in enumerate(sorted(top_scores)[:3]):
                ctk.CTkLabel(score_frame, text=f"{i+1}. {score:.2f} s").pack()
        else:
            ctk.CTkLabel(score_frame, text="No scores yet!").pack()

        if num_cards == 10:
            rows, cols = 2, 5
        elif num_cards == 16:
            rows, cols = 4, 4
        elif num_cards == 24:
            rows, cols = 4, 6
        else:
            rows, cols = int(num_cards ** 0.5), int(num_cards ** 0.5)

        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= num_cards:
                    continue
                btn = ctk.CTkButton(self.root, text="?", width=60, height=60,
                                    command=lambda i=idx: self.flip_card(i))
                btn.grid(row=r+2, column=c, padx=4, pady=4)
                self.card_matcher_buttons.append(btn)
                idx += 1

        ctk.CTkButton(self.root, text="Back", command=self.games_menu, width=200).grid(row=rows+3, column=0, columnspan=cols, pady=12)
        self.update_card_matcher_timer()

    def update_card_matcher_timer(self):
        if hasattr(self, "card_matcher_start_time"):
            elapsed = time.time() - self.card_matcher_start_time
            self.card_matcher_timer_label.configure(text=f"Time: {elapsed:.1f}s")
            if self.card_matcher_matches < self.card_matcher_total:
                self.root.after(100, self.update_card_matcher_timer)
            else:
                elapsed = time.time() - self.card_matcher_start_time
                self.finish_card_matcher(elapsed)

    def flip_card(self, idx):
        if len(self.card_matcher_flipped) >= 2:
            return
        if idx < 0 or idx >= len(self.card_matcher_buttons):
            return
        btn = self.card_matcher_buttons[idx]
        if btn.cget("text") != "?":
            return
        # show value
        btn.configure(text=str(self.card_matcher_board[idx]))
        self.card_matcher_flipped.append(idx)
        if len(self.card_matcher_flipped) == 2:
            self.root.after(700, self.check_card_match)

    def check_card_match(self):
        def points_sound():
            try:
                pygame.mixer.music.load("point.mp3")
                pygame.mixer.music.play(loops=0)
            except Exception:
                pass

        def winner_sound():
            try:
                pygame.mixer.music.load("winner.mp3")
                pygame.mixer.music.play(loops=0)
            except Exception:
                pass

        if len(self.card_matcher_flipped) != 2:
            self.card_matcher_flipped = []
            return
        i1, i2 = self.card_matcher_flipped
        if self.card_matcher_board[i1] == self.card_matcher_board[i2]:
            points_sound()
            self.card_matcher_buttons[i1].configure(state="disabled", fg_color="transparent", text=str(self.card_matcher_board[i1]))
            self.card_matcher_buttons[i2].configure(state="disabled", fg_color="transparent", text=str(self.card_matcher_board[i2]))
            self.card_matcher_matches += 1
            if self.card_matcher_matches == self.card_matcher_total:
                elapsed = time.time() - self.card_matcher_start_time
                self.save_card_matcher_score(elapsed)
                winner_sound()
                messagebox.showinfo("Congratulations!", f"You matched all cards in {elapsed:.2f} seconds!")
                self.games_menu()
        else:
            # flip back
            self.card_matcher_buttons[i1].configure(text="?")
            self.card_matcher_buttons[i2].configure(text="?")
        self.card_matcher_flipped = []

    def save_card_matcher_score(self, elapsed):
        scores = self.load_card_scores()
        key = str(self.card_matcher_num)
        if key not in scores:
            scores[key] = []
        scores[key].append(elapsed)
        scores[key] = sorted(scores[key])[:3]  # Keep only top 3
        self.save_card_scores(scores)

    def finish_card_matcher(self, elapsed_time):
        messagebox.showinfo("Game Over", f"Completed in {elapsed_time:.2f} seconds!")
        self.speak(f"Good job! You finished in {elapsed_time:.1f} seconds.")
        # save result
        num_cards = self.card_matcher_num
        scores = self.load_card_scores()
        if str(num_cards) not in scores:
            scores[str(num_cards)] = []
        scores[str(num_cards)].append(elapsed_time)
        scores[str(num_cards)] = sorted(scores[str(num_cards)])[:3]
        self.save_card_scores(scores)
        self.games_menu()


if __name__ == "__main__":
    app_root = ctk.CTk()
    WatchAssistant(app_root)
    app_root.mainloop()
