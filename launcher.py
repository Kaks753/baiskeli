import subprocess
import webbrowser
import time
import sys
import os

def main():
    # Get the directory where the exe is running from
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    app_path = os.path.join(base_dir, "app.py")
    
    # Start Streamlit
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", app_path,
         "--server.headless=true",
         "--server.port=8501",
         "--browser.gatherUsageStats=false"],
        cwd=base_dir
    )
    
    # Wait for it to start then open browser
    time.sleep(3)
    webbrowser.open("http://localhost:8501")
    
    # Keep running until closed
    process.wait()

if __name__ == "__main__":
    main()