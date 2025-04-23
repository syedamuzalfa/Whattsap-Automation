# 📲 WhatsApp Message Automation with Selenium

This project is a Python-based automation tool that uses **Selenium WebDriver** to send WhatsApp messages (including images) to saved or unsaved contacts through [web.whatsapp.com](https://web.whatsapp.com). It provides a graphical interface to load phone numbers, compose messages, and attach images. The app supports logging and automatic error handling.

---

## 🚀 Features

- 📇 Load phone numbers from CSV files
- 📨 Send custom text messages
- 🖼️ Attach and send images
- ⚡ Fallback to direct number messaging if contact not found
- ✅ Delivery status confirmation (based on double-check icons)
- 📸 Capture screenshots on failure
- 🔛 Log message status with timestamp to a local SQL Server database

---

## 📂 Project Structure

```bash
whatsapp-automation/
├── main.py                  # Full GUI and backend automation script
├── unfound_numbers.txt      # Tracks numbers not found in contact list
├── requirements.txt         # Required Python libraries
├── README.md                # Project documentation
```

---

## 🛠️ Installation

### 1. Clone this Repository
```bash
git clone https://github.com/your-username/whatsapp-automation.git
cd whatsapp-automation
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install ChromeDriver
- Download the matching version from: [https://chromedriver.chromium.org](https://chromedriver.chromium.org)
- Add it to your system PATH or update the path in `main.py`

---

## 👍 Usage

### Step 1: Prepare a CSV
Ensure your CSV has a `number` column:
```csv
number
+1234567890
+0987654321
```

### Step 2: Run the Application
```bash
python main.py
```

### Step 3: Interact with the GUI
- Load your CSV
- Write a message
- Optionally, attach an image
- Click "Send Messages"

### Step 4: For unfound numbers
Click on **"Send to Unfound Numbers"** to retry with direct messaging.

---

## 📅 Logging
- Sent messages are logged to a SQL Server database table `MessageLogs`
- Unfound numbers are saved in `unfound_numbers.txt`
- Screenshots of errors are saved with a timestamp

---

## ⚠️ Disclaimer
This tool is intended for personal and educational use. **Sending bulk automated messages may violate WhatsApp's Terms of Service.** Use at your own discretion.

---

## 👨‍💼 Author
- **Your Name**
- GitHub: [@yourgithub](https://github.com/yourgithub)
- Email: your.email@example.com

---

## ⭐ Show your support
If you like this project, star it on GitHub and share it with others!

