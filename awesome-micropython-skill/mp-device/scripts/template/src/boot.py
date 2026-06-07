# boot.py — Runs on every boot (once, before main.py)
import machine
import gc

# ── Wi-Fi ──────────────────────────────────────────────────────────
# Uncomment and fill in to auto-connect:
#
# import network, time
# wlan = network.WLAN(network.STA_IF)
# wlan.active(True)
# wlan.connect('YOUR_SSID', 'YOUR_PASSWORD')
# for _ in range(30):
#     if wlan.isconnected():
#         break
#     time.sleep(0.5)
# if wlan.isconnected():
#     print(f'WiFi: {wlan.ifconfig()[0]}')
# else:
#     print('WiFi: FAILED')

# ── Memory ─────────────────────────────────────────────────────────
gc.collect()

# ── One-time setup ─────────────────────────────────────────────────
# Add imports or hardware init that should persist across soft resets:
#
# from machine import Pin
# led = Pin(2, Pin.OUT)
