"""
launcher.py — Streamlit launcher with auto-shutdown when browser closes
"""

import sys
import os
import socket
import threading
import webbrowser
import time
import subprocess
import psutil


def find_free_port(start=8501, end=8600):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 8501


def open_browser(port, delay=1.0):
    time.sleep(delay)
    webbrowser.open(f"http://localhost:{port}")


def get_base_dir():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def browser_is_open(port):
    """Returns True if any browser has an active connection to our port."""
    browser_names = {"chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"}
    for proc in psutil.process_iter(["name", "connections"]):
        try:
            if proc.info["name"].lower() in browser_names:
                for conn in proc.connections():
                    if conn.raddr and conn.raddr.port == port:
                        return True
        except Exception:
            continue
    return False


def watch_browser(port, streamlit_proc, grace_seconds=10):
    """
    Waits for browser to open, then shuts down Streamlit when it closes.
    grace_seconds: how long to wait after browser closes before killing.
    """
    # Wait until browser actually connects
    time.sleep(10)

    print("Watching browser connection...")
    while True:
        time.sleep(5)
        if not browser_is_open(port):
            # Give a grace period in case of page refresh
            time.sleep(grace_seconds)
            if not browser_is_open(port):
                print("Browser closed. Shutting down Streamlit...")
                streamlit_proc.terminate()
                sys.exit(0)


def main():
    base_dir = get_base_dir()
    app_path = os.path.join(base_dir, "app.py")
    port     = find_free_port()

    # If frozen as EXE, use Streamlit's internal CLI
    if getattr(sys, "frozen", False):
        threading.Thread(target=open_browser, args=(port,), daemon=True).start()
        import streamlit.web.cli as stcli
        sys.argv = [
            "streamlit", "run", app_path,
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false",
            "--theme.primaryColor", "#00AEEF",
            "--theme.backgroundColor", "#F4F6F8",
            "--theme.secondaryBackgroundColor", "#FFFFFF",
            "--theme.textColor", "#1A2B3C",
        ]
        sys.exit(stcli.main())

    # Normal (non-frozen) path — used by VBS/BAT launcher
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_path,
        "--server.port", str(port),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--browser.gatherUsageStats", "false",
        "--browser.gatherUsageStats", "false",
        "--theme.primaryColor", "#00AEEF",
        "--theme.backgroundColor", "#F4F6F8",
        "--theme.secondaryBackgroundColor", "#FFFFFF",
        "--theme.textColor", "#1A2B3C",
        "--theme.font", "sans serif",
    ]

    streamlit_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Open browser
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()

    # Watch browser in background thread
    threading.Thread(
        target=watch_browser,
        args=(port, streamlit_proc),
        daemon=True
    ).start()

    # Keep main thread alive until Streamlit exits
    streamlit_proc.wait()


if __name__ == "__main__":
    main()