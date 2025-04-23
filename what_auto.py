import time
import os
import platform
import pandas as pd
import pyodbc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import threading
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
from datetime import datetime
from urllib.parse import quote
from tkinter import PhotoImage, messagebox, filedialog
# Determine OS-specific paths
def get_paths():
    system = platform.system()
    if system == "Windows":
        chrome_driver_path = "C:\\Windows\\chromedriver.exe"
        chrome_profile_path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
    elif system == "Linux":
        chrome_driver_path = "/usr/bin/chromedriver"
        chrome_profile_path = os.path.expanduser("~/.config/google-chrome")
    elif system == "Darwin":  # macOS
        chrome_driver_path = "/usr/local/bin/chromedriver"
        chrome_profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        raise Exception(f"Unsupported OS: {system}")
    return chrome_driver_path, chrome_profile_path

CHROME_DRIVER_PATH, CHROME_PROFILE_PATH = get_paths()

# Global variable for the image path
image_path = None

# Database connection setup
def connect_to_database():
    try:
        connection = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=Server_Name;"  # Update with your server name
            "DATABASE=log;"  # Update with your database name
            # "UID=your_username;"  # Update with your SQL Server username
            # "PWD=your_password;"  
        )
        return connection
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

# Function to log message status
def log_message_status(phone_number, message, status, delay):
    try:
        max_status_length = 255
        status = status[:max_status_length]  # Ensure the status text does not exceed DB field limits.

        # Connect to the database
        connection = connect_to_database()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO MessageLogs (phone_number, message, status, delay, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                phone_number, message, status, delay, datetime.now()
            )
            connection.commit()
            cursor.close()
            connection.close()
            print(f"Log entry created for {phone_number} with status '{status}'.")
    except Exception as e:
        print(f"Error while logging message status for {phone_number}: {e}")


# Function to capture screenshots on errors
def capture_screenshot(driver, phone_number, error_msg):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_{phone_number}_{timestamp}.png"
    driver.save_screenshot(filename)
    print(f"Screenshot saved as {filename} due to error: {error_msg}")

# Initialize WebDriver
def initialize_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless")  # Uncomment to run in headless mode
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get("https://web.whatsapp.com")

        # Wait until QR code is scanned
        print("Please scan the QR code to log in to WhatsApp Web.")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='3']"))
        )
        print("Logged in to WhatsApp Web successfully.")
        return driver
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        return None

# Function to save unfound phone numbers
def save_unfound_number(phone_number):
    try:
        with open("unfound_numbers.txt", "a") as file:
            file.write(f"{phone_number}\n")
        print(f"Unfound number {phone_number} saved to unfound_numbers.txt")
    except Exception as e:
        print(f"Error saving unfound number {phone_number}: {e}")

def send_message_via_search(driver, phone_number, message, image_path=None):
    try:
        wait = WebDriverWait(driver, 30)

        # Locate the search box
        search_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
        ))
        search_box.clear()
        search_box.send_keys(phone_number)
        time.sleep(2)  # Allow time for the search results to load

        # Check for contact existence
        try:
            first_contact = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[@role='gridcell']//span[@title]")
            ))
            first_contact.click()
        except Exception:
            print(f"No contact found for {phone_number}. Attempting to send message directly.")
            try:
                # Direct message URL (whatsapp://send?phone=<phone_number>)
                encoded_message = quote(message)  # Encode the message
                driver.get(f"https://web.whatsapp.com/send?phone={phone_number}")
                time.sleep(5)

                # Wait for the "message" button to appear
                message_button = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@contenteditable='true'][@data-tab='10']")
                ))

                message_button.click()
                for line in message.split("\n"):
                    message_button.send_keys(line)
                    message_button.send_keys(Keys.SHIFT, Keys.ENTER)  # Add line break
                message_button.send_keys(Keys.ENTER)  # Send the message
                time.sleep(2)
                print(f"Message sent to {phone_number}.")
                log_message_status(phone_number, message, "Sent", 0)
                return
            except Exception as e:
                print(f"Error sending direct message to {phone_number}: {e}")
                log_message_status(phone_number, message, f"Direct Message Failed: {e}", 0)
                return

        # Proceed with sending message if contact is found
        message_box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@contenteditable='true'][@data-tab='10']")
        ))

        message_box.click()
        for line in message.split("\n"):
            message_box.send_keys(line)
            message_box.send_keys(Keys.SHIFT, Keys.ENTER)  # Add line break
        message_box.send_keys(Keys.ENTER)  # Send message
        time.sleep(2)

        # Handle image attachment if provided
        if image_path and os.path.isfile(image_path):
            try:
                attachment_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[@data-icon='clip']")
                ))
                attachment_button.click()
                image_input = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']")
                ))
                image_input.send_keys(image_path)
                time.sleep(2)
                send_image_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//span[@data-icon='send']")
                ))
                send_image_button.click()
                time.sleep(3)
                print(f"Image sent to {phone_number}.")
            except Exception as e:
                capture_screenshot(driver, phone_number, f"Image attachment failed: {e}")
                log_message_status(phone_number, message, f"Sent - Image Failed: {e}", 0)
                return

        # Confirm message was sent by checking for checkmarks
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//span[@data-icon='msg-dblcheck']")
            ))
            log_message_status(phone_number, message, "Sent", 0)
            print(f"Message sent to {phone_number}.")
        except Exception:
            log_message_status(phone_number, message, "Not Sent - No Confirmation", 0)
            print(f"Message not confirmed as sent to {phone_number}.")

    except Exception as e:
        capture_screenshot(driver, phone_number, f"General error: {e}")
        print(f"Error sending message to {phone_number}: {e}")

# Function to send messages to unfound numbers
def send_messages_to_unfound_numbers(message, image_path=None):
    try:
        with open("unfound_numbers.txt", "r") as file:
            phone_numbers = file.readlines()

        # Clean up phone numbers
        phone_numbers = [number.strip() for number in phone_numbers]

        driver = initialize_driver()
        if not driver:
            print("WebDriver initialization failed. Exiting.")
            return

        for phone_number in phone_numbers:
            send_message_via_search(driver, phone_number, message, image_path)

        driver.quit()
        print("Messages sent to all unfound numbers.")

    except Exception as e:
        print(f"Error sending messages to unfound numbers: {e}")

# Load phone numbers from CSV
def load_csv():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df = pd.read_csv(file_path)
            if 'number' not in df.columns:
                raise ValueError("CSV must contain a 'number' column.")
            phone_numbers = df['number'].astype(str).tolist()
            phone_number_entry.delete(0, tk.END)
            phone_number_entry.insert(tk.END, ", ".join(phone_numbers))
            command_prompt_output.insert(tk.END, f"Loaded {len(phone_numbers)} phone numbers from CSV.\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
            print(f"Failed to load CSV: {e}")

# Select an image file
def select_image():
    global image_path
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
    if image_path:
        image_label.config(text=f"Image selected: {os.path.basename(image_path)}")
        command_prompt_output.insert(tk.END, f"Selected image: {os.path.basename(image_path)}\n")

# Schedule messages
def schedule_messages():
    try:
        phone_numbers = phone_number_entry.get().split(",")
        message = message_entry.get("1.0", tk.END).strip()
        if not phone_numbers or not message:
            raise ValueError("Phone numbers and message cannot be empty.")
        threading.Thread(target=send_messages_in_background, args=(phone_numbers, message, image_path), daemon=True).start()
        command_prompt_output.insert(tk.END, "Message scheduling started...\n")
    except ValueError as ve:
        messagebox.showerror("Error", str(ve))
        print(str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        print(f"An unexpected error occurred: {e}")

# Background function to send messages with random delay
def send_messages_in_background(phone_numbers, message, image_path):
    driver = initialize_driver()
    if not driver:
        command_prompt_output.insert(tk.END, "WebDriver initialization failed. Exiting.\n")
        return

    for phone_number in phone_numbers:
        phone_number = phone_number.strip()
        if not phone_number:
            continue

        delay_in_seconds = random.randint(25, 35)
        command_prompt_output.insert(tk.END, f"Waiting for {delay_in_seconds} seconds before sending to {phone_number}...\n")
        command_prompt_output.yview(tk.END)
        time.sleep(delay_in_seconds)

        command_prompt_output.insert(tk.END, f"Sending message to {phone_number}...\n")
        command_prompt_output.yview(tk.END)

        send_message_via_search(driver, phone_number, message, image_path=image_path)

    driver.quit()
    messagebox.showinfo("Done", "All messages have been sent.")
    command_prompt_output.insert(tk.END, "All messages sent.\n")
    command_prompt_output.yview(tk.END)

# GUI Setup
app = tk.Tk()
img = PhotoImage(file='al.png')
app.iconphoto(True, img)
app.title("Whatsapp Automation")

app.geometry("600x900")
app.configure(bg="#29b1e3")

# Import additional modules for image processing
# Add logo at the top
logo_path = "al.png"  # Replace with the path to your logo file
try:
    logo_image = Image.open(logo_path)
    logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)  # Corrected resampling method
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(app, image=logo_photo, bg="#29b1e3")
    logo_label.pack(pady=10)
except Exception as e:
    print(f"Failed to load logo: {e}")


# Footer Section
footer_frame = tk.Frame(app, bg="#29b1e3")
footer_frame.pack(side="bottom", fill="x")

footer_frame = tk.Frame(app, bg="#29b1e3", height=30)  # Set a fixed height
footer_frame.pack(side="bottom", fill="x")

footer_label = tk.Label(
    footer_frame,
    text="© 2025 Al Intisar Solutions (Private) Limited",
    bg="#29b1e3",
    fg="white",
    font=("Arial", 10),
    anchor="center"
)
footer_label.pack(fill="both", pady=5)
# Phone Numbers Section
phone_frame = tk.LabelFrame(app, text="Phone Numbers", bg="#29b1e3", padx=10, pady=10)
phone_frame.pack(fill="both", padx=15, pady=10)

phone_number_entry = tk.Entry(phone_frame, width=50)
phone_number_entry.pack(pady=5)
tk.Button(phone_frame, text="Load from CSV", command=load_csv).pack(pady=5)

# Message Section
message_frame = tk.LabelFrame(app, text="Message", bg="#29b1e3", padx=10, pady=10)
message_frame.pack(fill="both", padx=15, pady=10)

message_entry = tk.Text(message_frame, height=6, width=50)
message_entry.pack(pady=5)
command_prompt_output = tk.Text(app, height=10, width=70, state='normal')
command_prompt_output.pack(pady=10)

# Icon buttons for attachments
icon_frame = tk.Frame(message_frame, bg="#29b1e3")
icon_frame.pack(pady=5)

# Attach image button
image_label = tk.Label(message_frame, text="No image selected", bg="#29b1e3")
image_label.pack()
image_button = tk.Button(icon_frame, text="Attach Image", command=select_image)
image_button.pack(side="left", padx=10)

# Send message button
send_button = tk.Button(app, text="Send Messages", command=schedule_messages)
send_button.pack(pady=10)

# Send unfound messages button
# unfound_button = tk.Button(app, text="Send to Unfound Numbers", command=lambda: send_messages_to_unfound_numbers(message_entry.get("1.0", tk.END).strip(), image_path))
# unfound_button.pack(pady=10)

app.mainloop()