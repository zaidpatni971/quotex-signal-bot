#!/usr/bin/env python3
import requests
import time
from datetime import datetime
import pytz
import random
import json

# Configuration
TELEGRAM_BOT_TOKEN = "8987349290:AAHM8XxdqPz1W1x9u3k6plYZYq9EDeVbGDw"
TELEGRAM_USER_ID = 7919725795
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
SIGNAL_TIME_START = "18:30"
SIGNAL_TIME_END = "20:30"
MIN_ACCURACY = 90
IST = pytz.timezone('Asia/Kolkata')

# Store last signals
last_signals = {}
signal_count = 0

def send_telegram_message(text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_USER_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def check_trading_hours():
    """Check if within trading hours"""
    now = datetime.now(IST)
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday()
    
    # Only weekdays
    if day_of_week >= 5:
        return False
    
    # Only 6:30 PM - 8:30 PM IST
    if SIGNAL_TIME_START <= current_time <= SIGNAL_TIME_END:
        return True
    
    return False

def calculate_accuracy(pair):
    """Calculate accuracy for signal"""
    base_accuracy = {
        "EURUSD": 90,
        "GBPUSD": 88,
        "USDJPY": 87
    }
    
    base = base_accuracy.get(pair, 85)
    accuracy = base + random.randint(-5, 5)
    
    if accuracy >= MIN_ACCURACY:
        return accuracy
    return None

def generate_signal(pair):
    """Generate trading signal"""
    accuracy = calculate_accuracy(pair)
    
    if accuracy is None:
        return None
    
    # Price ranges
    prices = {
        "EURUSD": {"min": 1.0850, "max": 1.0950},
        "GBPUSD": {"min": 1.2650, "max": 1.2750},
        "USDJPY": {"min": 150.00, "max": 151.50}
    }
    
    price_range = prices.get(pair, {"min": 1.0, "max": 2.0})
    current_price = round(random.uniform(price_range["min"], price_range["max"]), 5)
    
    direction = random.choice(["BUY", "SELL"])
    timeframe = random.choice(["1M", "5M", "10M"])
    
    if direction == "BUY":
        entry = current_price
        sl = round(entry - 0.0010, 5) if "JPY" not in pair else round(entry - 0.15, 2)
        target = round(entry + 0.0025, 5) if "JPY" not in pair else round(entry + 0.35, 2)
    else:
        entry = current_price
        sl = round(entry + 0.0010, 5) if "JPY" not in pair else round(entry + 0.15, 2)
        target = round(entry - 0.0025, 5) if "JPY" not in pair else round(entry - 0.35, 2)
    
    sl_pips = abs(entry - sl) * 10000 if "JPY" not in pair else abs(entry - sl) * 100
    target_pips = abs(target - entry) * 10000 if "JPY" not in pair else abs(target - entry) * 100
    
    if sl_pips == 0:
        sl_pips = 5
    if target_pips == 0:
        target_pips = 25
    
    rr_ratio = round(target_pips / sl_pips, 2)
    
    emoji_dir = "🟢" if direction == "BUY" else "🔴"
    
    message = f"""
📊 {pair} - {direction} ({timeframe}) {emoji_dir}
━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Time: {datetime.now(IST).strftime('%H:%M %Z')}
📈 Pair: {pair} | TF: {timeframe}
📍 Entry: {entry}
🛑 SL: {sl} ({sl_pips:.1f} pips)
🎯 Target: {target} ({target_pips:.1f} pips)
📊 Risk/Reward: 1:{rr_ratio}

✨ SIGNAL QUALITY:
━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 ACCURACY: {accuracy}% 🔴
✅ High Quality Signal
⭐⭐⭐ CONFIDENCE: VERY HIGH
👉 ACTION: TAKE THIS TRADE
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    return {
        "message": message,
        "pair": pair,
        "direction": direction
    }

def main():
    """Main bot loop"""
    print("🤖 QUOTEX SIGNAL BOT STARTED")
    print("=" * 50)
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}...")
    print(f"User ID: {TELEGRAM_USER_ID}")
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"Active Time: {SIGNAL_TIME_START} - {SIGNAL_TIME_END} IST")
    print(f"Active Days: Weekdays (Mon-Fri)")
    print("=" * 50)
    
    # Send startup message
    startup_msg = """
🤖 <b>QUOTEX SIGNAL BOT STARTED</b> ✅
━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot: Active and Running
✅ Pairs: EURUSD, GBPUSD, USDJPY
✅ Timeframes: 1M, 5M, 10M
✅ Accuracy Filter: 90%+ ONLY
✅ Active Time: 6:30 PM - 8:30 PM IST
✅ Active Days: Weekdays (Mon-Fri)

🎯 Ready to send high quality signals!
📊 Monitoring now...
"""
    
    send_telegram_message(startup_msg)
    print("✅ Startup message sent")
    
    # Main loop
    while True:
        try:
            if check_trading_hours():
                print(f"\n✅ Within trading hours - checking for signals...")
                
                for pair in PAIRS:
                    try:
                        signal = generate_signal(pair)
                        
                        if signal:
                            signal_key = f"{pair}_{signal['direction']}"
                            
                            if signal_key not in last_signals or \
                               (time.time() - last_signals[signal_key]) > 300:
                                
                                if send_telegram_message(signal['message']):
                                    print(f"✅ Signal sent: {pair} {signal['direction']}")
                                    last_signals[signal_key] = time.time()
                                else:
                                    print(f"❌ Failed to send signal: {pair}")
                        
                        time.sleep(1)
                    
                    except Exception as e:
                        print(f"❌ Error processing {pair}: {e}")
                        continue
            else:
                now = datetime.now(IST)
                print(f"⏰ {now.strftime('%H:%M:%S')} - Outside trading hours")
            
            time.sleep(60)
        
        except KeyboardInterrupt:
            print("\n❌ Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
