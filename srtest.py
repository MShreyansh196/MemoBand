import tkinter as tk
import speech_recognition as sr

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            result_label.config(text=text)
        except sr.UnknownValueError:
            result_label.config(text="Could not understand audio")
        except sr.RequestError:
            result_label.config(text="Could not request results")

root = tk.Tk()
root.title("Speech Recognition App")
root.geometry("400x200")

recognize_button = tk.Button(root, text="Start Recognition", command=recognize_speech)
recognize_button.pack(pady=20)

result_label = tk.Label(root, text="")
result_label.pack(pady=20)

root.mainloop()

