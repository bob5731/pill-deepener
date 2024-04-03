from flask import Flask, render_template, request, redirect, url_for
import RPi.GPIO as GPIO
import time
import threading
import sqlite3
from datetime import datetime

app = Flask(__name__)

# GPIO pin numbers connected to servo motors
servo_pins = [17, 18, 27, 22]  # Adjust pin numbers according to your setup

# Initialize GPIO
def setup():
    GPIO.setmode(GPIO.BCM)
    for pin in servo_pins:
        GPIO.setup(pin, GPIO.OUT)

# Function to set servo angle
def set_angle(pin, angle):
    pwm = GPIO.PWM(pin, 50)
    pwm.start(0)
    duty = angle / 18 + 2
    GPIO.output(pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(1)
    GPIO.output(pin, False)
    pwm.ChangeDutyCycle(0)
    pwm.stop()

# Function to dispense pill from a specific bin
def dispense_pill(bin_number):
    # Calculate servo angle based on bin_number
    angle = bin_number * 10
    set_angle(servo_pins[bin_number], angle)

# Function to initialize SQLite database
def initialize_database():
    conn = sqlite3.connect('pill_dispenser.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pills
                 (id INTEGER PRIMARY KEY, name TEXT, schedule TEXT, bin_number INTEGER)''')
    conn.commit()
    conn.close()

# Function to add a new pill to the database
def add_pill_to_db(name, schedule, bin_number):
    conn = sqlite3.connect('pill_dispenser.db')
    c = conn.cursor()
    c.execute("INSERT INTO pills (name, schedule, bin_number) VALUES (?, ?, ?)", (name, schedule, bin_number))
    conn.commit()
    conn.close()

# Function to retrieve all pills from the database
def get_all_pills():
    conn = sqlite3.connect('pill_dispenser.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pills")
    pills = c.fetchall()
    conn.close()
    return pills

# Function to delete a pill from the database
def delete_pill_from_db(pill_id):
    conn = sqlite3.connect('pill_dispenser.db')
    c = conn.cursor()
    c.execute("DELETE FROM pills WHERE id=?", (pill_id,))
    conn.commit()
    conn.close()

# Function to get pill info by ID from the database
def get_pill_by_id(pill_id):
    conn = sqlite3.connect('pill_dispenser.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pills WHERE id=?", (pill_id,))
    pill = c.fetchone()
    conn.close()
    return pill

# Function to dispense pills based on schedule
def automatic_dispense():
    while True:
        current_time = datetime.now().strftime("%H:%M")
        pills = get_all_pills()
        for pill in pills:
            pill_id, _, schedule, bin_number = pill
            if current_time == schedule:
                dispense_pill(bin_number)  # Dispense pill from corresponding bin
                time.sleep(60)  # Avoid dispensing multiple pills at the same time
        time.sleep(10)  # Check every 10 seconds

# Home page
@app.route('/')
def index():
    pills = get_all_pills()
    return render_template('index.html', pills=pills)

# Route for adding a new pill
@app.route('/add_pill', methods=['GET', 'POST'])
def add_pill():
    if request.method == 'POST':
        name = request.form['name']
        schedule = request.form['schedule']
        bin_number = int(request.form['bin_number'])
        add_pill_to_db(name, schedule, bin_number)
        return redirect(url_for('index'))
    else:
        return render_template('add_pill.html')

# Route for deleting a pill
@app.route('/delete_pill/<int:pill_id>', methods=['POST'])
def delete_pill(pill_id):
    delete_pill_from_db(pill_id)
    return redirect(url_for('index'))

# Route for viewing the schedule of a pill
@app.route('/view_schedule/<int:pill_id>')
def view_schedule(pill_id):
    pill = get_pill_by_id(pill_id)  # Retrieve pill information by ID
    if pill:
        name = pill[1]  # Get the name of the pill
        schedule = pill[2]  # Assuming pill[2] contains the schedule in your database
        return render_template('view_schedule.html', name=name, schedule=schedule)
    else:
        return 'Schedule not found'  # Handle case where pill is not found

# Route to render add_pill.html
@app.route('/add_pill.html')
def add_pill_page():
    return render_template('add_pill.html')

if __name__ == '__main__':
    initialize_database()
    setup()
    
    # Start automatic scheduling thread
    auto_thread = threading.Thread(target=automatic_dispense)
    auto_thread.daemon = True
    auto_thread.start()
    
    try:
        app.run(debug=True, host='192.168.12.120')  # Run Flask app
    except KeyboardInterrupt:
        GPIO.cleanup()

