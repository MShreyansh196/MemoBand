import tkinter as tk
from tkinter import messagebox
import tkinterweb
from tkinterweb import HtmlFrame 
import webbrowser
from tkinter import *
import pygame
import tkinter as tk
##from tkhtmlview import HTMLLabel
import requests
import pyttsx3
import threading
import time
import calendar
import datetime
import json
import os
import random
import speech_recognition as sr
from tkinter import filedialog

pygame.mixer.init()
REMINDER_FILE = "reminders.json"
USER_FILE = "users.json"
CARD_SCORES_FILE = "card_matcher_scores.json"

class AIWatchAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Mate")
        self.root.geometry("480x320")
        self.root.configure(bg="aliceblue")
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('voice', 'mb-en1')
        rate = self.tts_engine.getProperty('rate')
        self.tts_engine.setProperty('rate', rate - 150) 
        self.running_game = False
        self.reminders = self.load_reminders()
        self.clock_label = None
        self.current_user = None
        self.update_clock()
        threading.Thread(target=self.reminder_checker, daemon=True).start()
        self.login_screen()

    # ---------- Login & Signup ----------
    def login_screen(self):
        self.clear_screen()
        LoginLabel = tk.Label(self.root, 
                              text="Login", 
                              font=("Arial", 22, "bold"), 
                              bg="aliceblue", 
                              fg="seagreen")
        LoginLabel.pack(pady=20)
        tk.Label(self.root, text="Username:", font=("Arial", 14), bg="aliceblue").pack(pady=2)
        username_entry = tk.Entry(self.root, font=("Arial", 14))
        username_entry.pack(pady=2)
        tk.Label(self.root, text="Password:", font=("Arial", 14), bg="aliceblue").pack(pady=2)
        password_entry = tk.Entry(self.root, font=("Arial", 14), show="*")
        password_entry.pack(pady=2)
        def try_login():
            users = self.load_users()
            username = username_entry.get()
            password = password_entry.get()
            if username in users and users[username] == password:
                self.current_user = username
                self.home_screen()
            else:
                messagebox.showerror("Login Failed", "Incorrect username or password.")
        LoginButton = tk.Button(self.root, 
                                text="Login", 
                                font=("Arial", 14), 
                                bg="limegreen", 
                                command=try_login)
        LoginButton.pack(pady=5)
        tk.Button(self.root, text="Sign Up", font=("Arial", 12), bg="skyblue", command=self.signup_screen).pack(pady=2)

    def signup_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Sign Up", font=("Arial", 22, "bold"), bg="aliceblue", fg="seagreen").pack(pady=20)
        tk.Label(self.root, text="Choose Username:", font=("Arial", 14), bg="aliceblue").pack(pady=2)
        username_entry = tk.Entry(self.root, font=("Arial", 14))
        username_entry.pack(pady=2)
        tk.Label(self.root, text="Choose Password:", font=("Arial", 14), bg="aliceblue").pack(pady=2)
        password_entry = tk.Entry(self.root, font=("Arial", 14), show="*")
        password_entry.pack(pady=2)
        def do_signup():
            users = self.load_users()
            username = username_entry.get()
            password = password_entry.get()
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
        tk.Button(self.root, text="Create Account", font=("Arial", 14), bg="limegreen", command=do_signup).pack(pady=5)
        tk.Button(self.root, text="Back to Login", font=("Arial", 12), bg="lightsalmon", command=self.login_screen).pack(pady=2)

    def load_users(self):
        if os.path.exists(USER_FILE):
            with open(USER_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_users(self, users):
        with open(USER_FILE, "w") as f:
            json.dump(users, f)

    # ---------- Utils ----------
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def speak(self, text):
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def exit_app(self):
        self.running_game = False
        self.save_reminders()
        self.root.quit()

    def update_clock(self):
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        if self.clock_label:
            self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def save_reminders(self):
        with open(REMINDER_FILE, "w") as f:
            json.dump(self.reminders, f)

    def load_reminders(self):
        if os.path.exists(REMINDER_FILE):
            try:
                with open(REMINDER_FILE, "r") as f:
                    data = f.read().strip()
                    if not data:
                        return {}
                    return json.loads(data)
            except Exception:
                return {}
        return {}

    # ---------- Reminder Notifications ----------
    def reminder_checker(self):
        while True:
            now = datetime.datetime.now()
            now_str = now.strftime("%Y-%m-%d|%I:%M %p")
            for key, task in list(self.reminders.items()):
                user, date_time = key.split(":", 1)
                if user == self.current_user and date_time == now_str:
                    self.root.after(0, self.show_reminder_popup, key, task)
            time.sleep(1)

    def show_reminder_popup(self, key, task):
        messagebox.showinfo("Reminder", f"{task}")
        self.speak(f"Reminder: {task}")
        if key in self.reminders:
            del self.reminders[key]
            self.save_reminders()

    def homescreen_keywords(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio).lower()
                # Check for keywords and open corresponding menu
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
    def reminder_keywords(self):
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio).lower()
                
                if "review" in text:
                    self.review_day()   # Implement this function to show today's reminders
                elif "upcoming" in text:
                    self.upcoming_reminders()  # Implement this function to list upcoming reminders
                elif "create" in text:
                    self.add_reminder()             # Opens add reminder form
                else:
                    print("No matching command found")
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError:
            print("API request failed")
        except sr.WaitTimeoutError:
            print("Listening timed out")

    # ---------- Home Screen ----------
    def home_screen(self):

        self.clear_screen()
        tk.Label(self.root, text=f"Welcome, {self.current_user}!", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=30)
        tk.Button(self.root, text="Reminders", font=("Arial", 18), width=20, command=self.reminders_menu).pack(pady=10)
        tk.Button(self.root, text="Games", font=("Arial", 18), width=20, command=self.games_menu).pack(pady=10)
        tk.Button(self.root, text="Location", font=("Arial", 18), width=20, command=self.location_menu).pack(pady=10)
        tk.Button(self.root, text="Stress Relief", font=("Arial", 18), width=20, command=self.stress_relief_menu).pack(pady=10)
        tk.Button(self.root, text="Logout", font=("Arial", 14), command=self.logout).pack(pady=30)
        tk.Button(self.root, text="😄 Speak It!", font=("Arial", 16), bg="limegreen", fg="white", command=lambda: threading.Thread(target=self.homescreen_keywords).start()).pack(pady=20)
    
    # ---------- Reminders Section ----------
    def reminders_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Reminders", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=30)
        tk.Button(self.root, text="Review My Day", font=("Arial", 16), width=20, command=self.review_day).pack(pady=10)
        tk.Button(self.root, text="Upcoming Reminders", font=("Arial", 16), width=20, command=self.upcoming_reminders).pack(pady=10)
        tk.Button(self.root, text="Create Reminder", font=("Arial", 16), width=20, command=self.add_reminder).pack(pady=10)
        tk.Button(self.root, 
        text="Back", font=("Arial", 14), command=self.home_screen).pack(pady=30)
        tk.Button(self.root,text="😄 Speak It!",font=("Arial", 16),bg="limegreen",fg="white",command=lambda: threading.Thread(target=self.reminder_keywords).start()).pack(pady=20)
    # ---------- Games Section ----------
    def games_menu(self):
        self.clear_screen()
        tk.Label(self.root, text="Games", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=30)
        tk.Button(self.root, text="Hangman", font=("Arial", 16), width=20, command=self.hangman_game).pack(pady=10)
        tk.Button(self.root, text="Card Matcher", font=("Arial", 16), width=20, command=self.card_matcher_game).pack(pady=10)
        tk.Button(self.root, text="Music Maker", font=("Arial", 16), width=20, command=self.music_maker_game).pack(pady=10)
        tk.Button(self.root, text="Object Finder", font=("Arial", 16), width=20, command=self.object_finder_game).pack(pady=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.home_screen).pack(pady=30)
    
   

    # ---------- Location Section ----------
    def location_menu(self):
        def callback(url):
                webbrowser.get("chromium-browser").open_new_tab(url)

        self.clear_screen()
        tk.Label(self.root, text="Location", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=30)
        tk.Label(self.root, text="Your current location is being opened in Chromium.", font=("Arial", 14), bg="aliceblue").pack(pady=10)
        Button(self.root, text="Back", font=("Arial", 14), command=self.home_screen).pack(pady=30)
        callback("file:///home/pi/Alzheimers_Project/map.html")

    # ---------- Stress Relief Section ----------
    def stress_relief_menu(self):
        # Directly open the breathing exercise when Stress Relief is selected
        self.breathing_exercise()

    def breathing_exercise(self):
        self.clear_screen()
        tk.Label(self.root, text="Breathing Exercise", font=("Arial", 24, "bold"), bg="aliceblue", fg="navy").pack(pady=30)
        instruction = tk.Label(self.root, text="Follow the breathing prompts below.", font=("Arial", 16), bg="aliceblue")
        instruction.pack(pady=10)
        breath_label = tk.Label(self.root, text="", font=("Arial", 32, "bold"), bg="aliceblue", fg="seagreen")
        breath_label.pack(pady=30)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.home_screen).pack(pady=30)

        def speak_with_pause(text):
            self.tts_engine.say("oh")  # Short, almost silent filler
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

        def breathing_cycle():  
            speak_with_pause("Oh")
            for _ in range(4):  # 4 cycles
                breath_label.config(text="Breathe In")
                speak_with_pause("Breathe in")
                self.root.update()
                time.sleep(3)
                breath_label.config(text="Breathe Out")
                speak_with_pause("Breathe out")
                self.root.update()
                time.sleep(3)
            breath_label.config(text="Done!")
            speak_with_pause("Great job! You finished the breathing exercise.")

        threading.Thread(target=breathing_cycle, daemon=True).start()

    # ---------- Game Placeholders ----------
    def hangman_game(self):
        messagebox.showinfo("Hangman", "Hangman game coming soon!")

    def card_matcher_game(self):
        self.clear_screen()
        tk.Label(self.root, text="Card Matcher", font=("Arial", 24, "bold"), bg="aliceblue", fg="navy").pack(pady=20)
        tk.Label(self.root, text="Choose number of cards:", font=("Arial", 16), bg="aliceblue").pack(pady=10)
        btn_frame = tk.Frame(self.root, bg="aliceblue")
        btn_frame.pack(pady=10)
        for num in [10, 16, 24]:
            tk.Button(btn_frame, text=f"{num} Cards", font=("Arial", 14), width=10,
                      command=lambda n=num: self.start_card_matcher(n)).pack(side=tk.LEFT, padx=10)
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.games_menu).pack(pady=30)

    def music_maker_game(self):
        messagebox.showinfo("Music Maker", "Music maker coming soon!")

    def object_finder_game(self):
        messagebox.showinfo("Object Finder", "Object finder (camera) coming soon!")

    # ---------- Reminders Functionality (existing code) ----------
    def add_reminder(self):
        self.clear_screen()
        self.clock_label = tk.Label(self.root, font=("Arial", 18, "bold"), bg="aliceblue", fg="navy")
        self.clock_label.pack(pady=10)
        tk.Label(self.root, text="Make Reminder", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=10)

        time_frame = tk.Frame(self.root, bg="aliceblue")
        time_frame.pack(pady=10)

        # --- Year selector ---
        tk.Label(time_frame, text="Year:", font=("Arial", 14), bg="aliceblue").grid(row=0, column=0, padx=5, pady=5)
        year_var = tk.StringVar(value=str(datetime.datetime.now().year))
        years = [str(y) for y in range(datetime.datetime.now().year, datetime.datetime.now().year + 11)]
        year_dropdown = tk.OptionMenu(time_frame, year_var, *years)
        year_dropdown.config(font=("Arial", 12))
        year_dropdown.grid(row=0, column=1, padx=5, pady=5)

        # --- Month selector ---
        tk.Label(time_frame, text="Month:", font=("Arial", 14), bg="aliceblue").grid(row=0, column=2, padx=5, pady=5)
        month_var = tk.StringVar(value=datetime.datetime.now().strftime("%B"))
        months = list(calendar.month_name)[1:]  # January–December
        month_dropdown = tk.OptionMenu(time_frame, month_var, *months)
        month_dropdown.config(font=("Arial", 12))
        month_dropdown.grid(row=0, column=3, padx=5, pady=5)

        # --- Day selector ---
        tk.Label(time_frame, text="Day:", font=("Arial", 14), bg="aliceblue").grid(row=0, column=4, padx=5, pady=5)
        day_var = tk.StringVar(value=str(datetime.datetime.now().day))
        day_dropdown = tk.OptionMenu(time_frame, day_var, *range(1, 32))
        day_dropdown.config(font=("Arial", 12))
        day_dropdown.grid(row=0, column=5, padx=5, pady=5)

        def update_days(*args):
            """Update day dropdown based on selected month and year."""
            month_num = list(calendar.month_name).index(month_var.get())
            year_num = int(year_var.get())
            last_day = calendar.monthrange(year_num, month_num)[1]  # number of days in month
            days = [str(d) for d in range(1, last_day + 1)]

            menu = day_dropdown["menu"]
            menu.delete(0, "end")
            for day in days:
                menu.add_command(label=day, command=lambda value=day: day_var.set(value))

            # Adjust current day if it's beyond last_day
            if int(day_var.get()) > last_day:
                day_var.set(str(last_day))

        # Trace changes to month and year
        month_var.trace_add("write", update_days)
        year_var.trace_add("write", update_days)
        update_days()  # initialize correctly

        # --- Hour / Minute / AM-PM ---
        tk.Label(time_frame, text="Hour (1-12):", font=("Arial", 14), bg="aliceblue").grid(row=1, column=0, padx=5, pady=5)
        hour_entry = tk.Entry(time_frame, font=("Arial", 14), width=5)
        hour_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(time_frame, text="Minute (00-59):", font=("Arial", 14), bg="aliceblue").grid(row=1, column=2, padx=5, pady=5)
        minute_entry = tk.Entry(time_frame, font=("Arial", 14), width=5)
        minute_entry.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(time_frame, text="AM/PM:", font=("Arial", 14), bg="aliceblue").grid(row=1, column=4, padx=5, pady=5)
        ampm_var = tk.StringVar(value="AM")
        ampm_dropdown = tk.OptionMenu(time_frame, ampm_var, "AM", "PM")
        ampm_dropdown.config(font=("Arial", 12))
        ampm_dropdown.grid(row=1, column=5, padx=5, pady=5)

        # --- Task entry ---
        tk.Label(self.root, text="Task:", font=("Arial", 14), bg="aliceblue").pack(pady=5)
        task_entry = tk.Entry(self.root, font=("Arial", 14))
        task_entry.pack(pady=5)

        # --- Save Reminder Function ---
        def save_reminder():
            year = year_var.get()
            month_name = month_var.get()
            month_num = list(calendar.month_name).index(month_name)
            day = day_var.get().zfill(2)
            hour = hour_entry.get()
            minute = minute_entry.get()
            ampm = ampm_var.get()
            task = task_entry.get()

            try:
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
            messagebox.showinfo("Success", f"Reminder set for {month_name} {day} {year} {time_str}: {task}")
            self.speak(f"Reminder added for {month_name} {day} {year} at {time_str}")
            self.reminders_menu()

        # --- Buttons ---
        btn_frame = tk.Frame(self.root, bg="aliceblue")
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Save Reminder", font=("Arial", 14), bg="limegreen", command=save_reminder).grid(row=0, column=0, padx=20)
        tk.Button(btn_frame, text="Back", font=("Arial", 14), bg="lightsalmon", command=self.reminders_menu).grid(row=0, column=1, padx=20)


    def review_day(self):
        self.clear_screen()
        self.clock_label = tk.Label(self.root, font=("Arial", 18, "bold"), bg="aliceblue", fg="navy")
        self.clock_label.pack(pady=10)
        tk.Label(self.root, text="Today's Review", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=20)
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
                tk.Label(self.root, text=f"{time_str} - {task}", font=("Arial", 16), bg="aliceblue").pack(pady=5)
            reminders_text = ", ".join([f"At {k.split('|')[1]}, {v}" for k, v in reminders_today])
            self.speak(f"Here are your reminders: {reminders_text}")
        else:
            tk.Label(self.root, text="No tasks for today!", font=("Arial", 16), bg="aliceblue").pack(pady=5)
            self.speak("You have no tasks for today.")
        tk.Button(self.root, text="Back", font=("Arial", 14), bg="plum",
                  command=self.reminders_menu).pack(pady=20)

    def upcoming_reminders(self):
        self.clear_screen()
        self.clock_label = tk.Label(self.root, font=("Arial", 18, "bold"), bg="aliceblue", fg="navy")
        self.clock_label.pack(pady=10)
        tk.Label(self.root, text="All Reminders", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=20)
        now = datetime.datetime.now()
        user_reminders = [(k, v) for k, v in self.reminders.items() if k.startswith(f"{self.current_user}:")]
        # Sort by date and time
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
                frame = tk.Frame(self.root, bg="aliceblue")
                frame.pack(pady=5)
                tk.Label(frame, text=f"{date} {time_str} - {task}", font=("Arial", 16), bg="aliceblue").pack(side=tk.LEFT)
                def make_delete_func(reminder_key=k):
                    return lambda: self.delete_reminder(reminder_key)
                tk.Button(frame, text="Delete", font=("Arial", 12), bg="tomato", command=make_delete_func()).pack(side=tk.LEFT, padx=10)
        else:
            tk.Label(self.root, text="No reminders!", font=("Arial", 16), bg="aliceblue").pack(pady=5)
        tk.Button(self.root, text="Back", font=("Arial", 14), bg="plum",
                  command=self.reminders_menu).pack(pady=20)

    def delete_reminder(self, key):
        if key in self.reminders:
            del self.reminders[key]
            self.save_reminders()
        self.upcoming_reminders()

    # ---------- Memory Game ----------
    def start_game(self):
        self.clear_screen()
        self.running_game = True
        self.clock_label = tk.Label(self.root, font=("Arial", 18, "bold"), bg="aliceblue", fg="navy")
        self.clock_label.pack(pady=10)
        tk.Label(self.root, text="Memory Game", font=("Arial", 24, "bold"), bg="aliceblue", fg="seagreen").pack(pady=10)
        self.game_status = tk.Label(self.root, text="Listen carefully!", font=("Arial", 16), bg="aliceblue")
        self.game_status.pack(pady=20)
        grid_frame = tk.Frame(self.root, bg="aliceblue")
        grid_frame.pack(pady=50)
        btn_correct = tk.Button(grid_frame, text="Correct (Y)", font=("Arial", 16), bg="limegreen", width=18, height=3,
                                command=lambda: self.answer(True))
        btn_wrong = tk.Button(grid_frame, text="Wrong (N)", font=("Arial", 16), bg="orangered", width=18, height=3,
                              command=lambda: self.answer(False))
        btn_skip = tk.Button(grid_frame, text="Skip Item", font=("Arial", 16), bg="orange", width=18, height=3,
                             command=lambda: self.answer(None))
        btn_back = tk.Button(grid_frame, text="Back", font=("Arial", 16), bg="lightsalmon", width=18, height=3,
                             command=self.games_menu)
        btn_correct.grid(row=0, column=0, padx=20, pady=20)
        btn_wrong.grid(row=0, column=1, padx=20, pady=20)
        btn_skip.grid(row=1, column=0, padx=20, pady=20)
        btn_back.grid(row=1, column=1, padx=20, pady=20)
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
            self.game_status.config(text=text)

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

    def load_card_scores(self):
        if os.path.exists(CARD_SCORES_FILE):
            with open(CARD_SCORES_FILE, "r") as f:
                return json.load(f)
        return {"10": [], "16": [], "24": []}

    def save_card_scores(self, scores):
        with open(CARD_SCORES_FILE, "w") as f:
            json.dump(scores, f)

    def start_card_matcher(self, num_cards):
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
        tk.Label(self.root, text=f"Card Matcher - {num_cards} Cards", font=("Arial", 20, "bold"), bg="aliceblue", fg="navy").grid(row=0, column=0, columnspan=10, pady=10)
        self.card_matcher_timer_label = tk.Label(self.root, text="Time: 0.0s", font=("Arial", 14), bg="aliceblue", fg="navy")
        self.card_matcher_timer_label.grid(row=1, column=0, columnspan=10)
        self.update_card_matcher_timer()
        # Scoreboard
        score_frame = tk.Frame(self.root, bg="aliceblue")
        score_frame.grid(row=2, column=10, rowspan=6, padx=20)
        tk.Label(score_frame, text="Top 3 Scores", font=("Arial", 14, "bold"), bg="aliceblue", fg="seagreen").pack(pady=5)
        top_scores = self.card_scores.get(str(num_cards), [])
        for i, score in enumerate(sorted(top_scores)[:3]):
            tk.Label(score_frame, text=f"{i+1}. {score:.2f} s", font=("Arial", 12), bg="aliceblue").pack()
        # Card grid layout
        if num_cards == 10:
            rows, cols = 2, 5
        elif num_cards == 16:
            rows, cols = 4, 4
        elif num_cards == 24:
            rows, cols = 4, 6
        else:
            rows, cols = 4, 4  # fallback
        idx = 0
        for r in range(rows):
            for c in range(cols):
                if idx >= num_cards:
                    continue
                btn = tk.Button(self.root, text="?", font=("Arial", 18, "bold"), width=6, height=3,
                                command=lambda i=idx: self.flip_card(i))
                btn.grid(row=r+2, column=c, padx=5, pady=5)
                self.card_matcher_buttons.append(btn)
                idx += 1
        tk.Button(self.root, text="Back", font=("Arial", 14), command=self.games_menu).grid(row=rows+3, column=0, columnspan=cols, pady=20)

    def update_card_matcher_timer(self):
        if hasattr(self, "card_matcher_start_time"):
            elapsed = time.time() - self.card_matcher_start_time
            self.card_matcher_timer_label.config(text=f"Time: {elapsed:.1f}s")
            if self.card_matcher_matches < self.card_matcher_total:
                self.root.after(100, self.update_card_matcher_timer)

    def flip_card(self, idx):
        if len(self.card_matcher_flipped) == 2 or self.card_matcher_buttons[idx]["text"] != "?":
            return
        btn = self.card_matcher_buttons[idx]
        btn.config(text=str(self.card_matcher_board[idx]))
        self.card_matcher_flipped.append(idx)
        if len(self.card_matcher_flipped) == 2:
            self.root.after(800, self.check_card_match)
   
    def check_card_match(self):
        def points_sound():
            pygame.mixer.music.load("point.mp3")
            pygame.mixer.music.play(loops=0)
        def winner_sound():
            pygame.mixer.music.load("winner.mp3")
            pygame.mixer.music.play(loops=0)
        i1, i2 = self.card_matcher_flipped
        if self.card_matcher_board[i1] == self.card_matcher_board[i2]:
            points_sound()
            self.card_matcher_buttons[i1].config(bg="lightgreen", state=tk.DISABLED)
            self.card_matcher_buttons[i2].config(bg="lightgreen", state=tk.DISABLED)
            self.card_matcher_matches += 1
            if self.card_matcher_matches == self.card_matcher_total:
                elapsed = time.time() - self.card_matcher_start_time
                self.save_card_matcher_score(elapsed)
                winner_sound()
                messagebox.showinfo("Congratulations!", f"You matched all cards in {elapsed:.2f} seconds!")
                self.games_menu()
        else:
            self.card_matcher_buttons[i1].config(text="?")
            self.card_matcher_buttons[i2].config(text="?")
        self.card_matcher_flipped = []

    def save_card_matcher_score(self, elapsed):
        scores = self.load_card_scores()
        key = str(self.card_matcher_num)
        if key not in scores:
            scores[key] = []
        scores[key].append(elapsed)
        scores[key] = sorted(scores[key])[:3]  # Keep only top 3
        self.save_card_scores(scores)

if __name__ == "__main__":
    root = tk.Tk()
    app = AIWatchAssistant(root)
    root.mainloop()
