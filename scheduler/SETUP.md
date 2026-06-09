# Windows Task Scheduler Setup

## Prerequisites
- Python is installed and on your PATH
- You have created a `.env` file in the project root with all required credentials (see `.env.example`)
- You have run `pip install -r requirements.txt` at least once

## Steps

1. **Open Task Scheduler**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create a Basic Task**
   - In the right panel, click **Create Basic Task...**
   - Name: `Job Finder Daily Digest`
   - Description: `Fetches co-op/internship listings and emails a daily digest`
   - Click **Next**

3. **Set the Trigger**
   - Select **Daily**
   - Set your preferred start time (e.g., 8:00 AM)
   - Recur every **1** day
   - Click **Next**

4. **Set the Action**
   - Select **Start a program**
   - Program/script: Browse to `C:\Users\Jacob\Documents\Coding\personal\job_finder\scheduler\run_daily.bat`
   - Click **Next**

5. **Finish**
   - Check **Open the Properties dialog for this task when I click Finish**
   - Click **Finish**

6. **Configure Properties** (in the Properties dialog that opens)
   - On the **General** tab:
     - Check **Run whether user is logged on or not**
     - Check **Run with highest privileges**
     - Configure for: **Windows 10/11**
   - Click **OK** (you may be prompted for your Windows password)

## Verifying It Works

Run the task manually to confirm it works before relying on the schedule:
1. In Task Scheduler, right-click **Job Finder Daily Digest** → **Run**
2. Check `logs\scheduler.log` for output
3. Check `logs\run.log` for detailed pipeline output

## Troubleshooting

- **"python is not recognized"**: Use the full path to python.exe in `run_daily.bat`, e.g. `C:\Users\Jacob\AppData\Local\Programs\Python\Python312\python.exe`
- **No email received**: Check `logs\run.log` for errors; verify `.env` credentials; ensure Gmail 2FA + App Password are set up
- **Task shows "Last Run Result: 0x1"**: The pipeline errored — check `logs\run.log` for the traceback
