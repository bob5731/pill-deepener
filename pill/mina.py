import tkinter as tk
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import time
import datetime

app_flask = Flask(__name__)
DATABASE = 'pill_dispenser.db'

# Initialize the database
def initialize_database():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, hour INTEGER, am_pm TEXT, bin_number INTEGER)''')
    conn.commit()
    conn.close()

# Add a new pill to the schedule
def add_pill_to_schedule(name, hour, am_pm, bin_number):
    if len(get_all_pills()) >= 30:
        raise ValueError("Maximum limit of 30 pills reached.")
    else:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("INSERT INTO pills (name, hour, am_pm, bin_number) VALUES (?, ?, ?, ?)", (name, hour, am_pm, bin_number))
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
    c.execute("SELECT * FROM pills WHERE hour=? AND am_pm=?", current_time)
    pills = c.fetchall()
    conn.close()
    return pills

# Delete a pill from the schedule
def delete_pill_from_schedule(pill_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM pills WHERE id=?", (pill_id,))
    conn.commit()
    conn.close()

# Initialize the database when the application starts
initialize_database()

# Flask routes
@app_flask.route('/')
def index():
    return render_template('index.html')

@app_flask.route('/dispense')
def dispense_pills():
    try:
        # Code to activate the pill dispensing mechanism
        return "Pills dispensed"
    except Exception as e:
        print("Error in dispense_pills route:", e)
        return "An error occurred while dispensing pills"

@app_flask.route('/schedule')
def view_schedule():
    try:
        pills = get_all_pills()
        return render_template('schedule.html', pills=pills)
    except Exception as e:
        print("Error in view_schedule route:", e)
        return "An error occurred while viewing schedule"

@app_flask.route('/add_pill', methods=['GET', 'POST'])
def add_pill():
    if request.method == 'POST':
        try:
            name = request.form['name']
            hour = int(request.form['hour'])
            am_pm = request.form['am_pm']
            bin_number = int(request.form['bin_number'])  # Assuming bin_number is an integer
            add_pill_to_schedule(name, hour, am_pm, bin_number)
            return redirect(url_for('view_schedule'))
        except ValueError as e:
            return render_template('error.html', error=str(e))
        except Exception as e:
            print("Error in add_pill route:", e)
            return "An error occurred while adding pill"
    else:
        return render_template('add_pill.html')

@app_flask.route('/delete_pill/<int:pill_id>')
def delete_pill_route(pill_id):
    try:
        delete_pill_from_schedule(pill_id)
        return redirect(url_for('view_schedule'))
    except Exception as e:
        print("Error in delete_pill_route:", e)
        return "An error occurred while deleting pill"

# Tkinter GUI
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
                # You need to define get_slot_number_for_pill method
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
                pill_label = tk.Label(schedule_window, text=f"Name: {pill[1]}, Time: {pill[2]}:{pill[3]} {pill[4]}, Bin: {pill[5]}")
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

if __name__ == '__main__':
    app_flask.run(host='0.0.0.0', port=5000)
