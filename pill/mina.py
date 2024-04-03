import tkinter as tk
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import RPi.GPIO as GPIO
import time
import datetime

app_flask = Flask(__name__)
DATABASE = 'pill_dispenser.db'

# Initialize the database
def initialize_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, hour INTEGER, minute INTEGER, am_pm TEXT)''')
    conn.commit()
    conn.close()

# Add a new pill to the schedule
def add_pill(name, hour, minute, am_pm):
    if len(get_all_pills()) >= 30:
        raise ValueError("Maximum limit of 30 pills reached.")
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO pills (name, hour, minute, am_pm) VALUES (?, ?, ?, ?)", (name, hour, minute, am_pm))
        conn.commit()
        conn.close()

# Get all pills from the schedule
def get_all_pills():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM pills")
    pills = c.fetchall()
    conn.close()
    return pills

# Get pills scheduled at the current time
def get_pills_at_schedule(current_time):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM pills WHERE hour=? AND minute=? AND am_pm=?", current_time)
    pills = c.fetchall()
    conn.close()
    return pills

# Delete a pill from the schedule
def delete_pill(pill_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM pills WHERE id=?", (pill_id,))
    conn.commit()
    conn.close()

# Initialize GPIO pins for servo control
GPIO.setmode(GPIO.BCM)
#servo_pins = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]
servo_pins = [18]
GPIO.setup(servo_pins, GPIO.OUT)
servo_objects = [GPIO.PWM(pin, 50) for pin in servo_pins]
for servo in servo_objects:
    servo.start(0)

# Function to move servo to specified angle
def move_servo(servo, angle):
    duty = angle / 18 + 2
    servo.ChangeDutyCycle(duty)
    time.sleep(1)
    servo.ChangeDutyCycle(0)

# Function to dispense pills from a specific slot
def dispense_pills(slot_number):
    move_servo(servo_objects[slot_number], 90)  # Move servo to dispense pills
    time.sleep(1)  # Wait for pills to be dispensed
    move_servo(servo_objects[slot_number], 0)   # Reset servo position

# Initialize the database when the application starts
initialize_database()

class PillDispenserApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automatic Pill Dispenser")
        self.geometry("400x300")
        
        self.label = tk.Label(self, text="Press dispense to release pills")
        self.label.pack(pady=10)
        
        self.dispense_button = tk.Button(self, text="Dispense", command=self.dispense_pills_at_schedule)
        self.dispense_button.pack(pady=5)

        self.schedule_button = tk.Button(self, text="View Schedule", command=self.view_schedule)
        self.schedule_button.pack(pady=5)

    def dispense_pills_at_schedule(self):
        current_time = datetime.datetime.now().strftime('%I:%M %p')
        pills = get_pills_at_schedule(current_time)
        if pills:
            for pill in pills:
                slot_number = get_slot_number_for_pill(pill)
                self.dispense_pills(slot_number)
            self.label.config(text="Pills dispensed")
            self.after(2000, self.reset_label)
        else:
            self.label.config(text="No pills scheduled at the current time")

    def reset_label(self):
        self.label.config(text="Press dispense to release pills")

    def view_schedule(self):
        pills = get_all_pills()
        if pills:
            schedule_window = tk.Toplevel(self)
            schedule_window.title("Pill Schedule")
            for pill in pills:
                pill_label = tk.Label(schedule_window, text=f"Name: {pill[1]}, Time: {pill[2]}:{pill[3]} {pill[4]}")
                pill_label.pack(pady=5)
            edit_button = tk.Button(schedule_window, text="Edit Pill", command=self.edit_pill)
            edit_button.pack(pady=5)
            delete_button = tk.Button(schedule_window, text="Delete Pill", command=self.delete_pill)
            delete_button.pack(pady=5)
        else:
            tk.messagebox.showinfo("Info", "No pills scheduled.")

    def edit_pill(self):
        pass  # Implement edit functionality here

    def delete_pill(self):
        pass  # Implement delete functionality here

@app_flask.route('/')
def index():
    return render_template('index.html')

@app_flask.route('/dispense')
def dispense_pills():
    # Code to activate the pill dispensing mechanism
    return "Pills dispensed"

@app_flask.route('/schedule')
def view_schedule():
    pills = get_all_pills()
    return render_template('schedule.html', pills=pills)

@app_flask.route('/add_pill', methods=['GET', 'POST'])
def add_pill():
    if request.method == 'POST':
        name = request.form['name']
        hour = int(request.form['hour'])
        minute = int(request.form['minute'])
        am_pm = request.form['am_pm']
        try:
            add_pill(name, hour, minute, am_pm)
            return redirect(url_for('view_schedule'))
        except ValueError as e:
            return render_template('error.html', error=str(e))
    else:
        return render_template('add_pill.html')

@app_flask.route('/delete_pill/<int:pill_id>')
def delete_pill_route(pill_id):
    delete_pill(pill_id)
    return redirect(url_for('view_schedule'))

if __name__ == '__main__':
    app_flask.run(host='0.0.0.0', port=5000)
    app = PillDispenserApp()
    app.mainloop()

