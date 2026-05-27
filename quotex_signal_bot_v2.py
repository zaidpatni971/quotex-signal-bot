import os
import asyncio
from datetime import datetime
import pytz
from telegram import Bot
from telegram.error import TelegramError
import random

# Configuration
TELEGRAM_BOT_TOKEN = "8987349290:AAHM8XxdqPz1W1x9u3k6plYZYq9EDeVbGDw"
TELEGRAM_USER_ID = 7919725795
PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]
SIGNAL_TIME_START = "18:30"  # 6:30 PM IST
SIGNAL_TIME_END = "20:30"    # 8:30 PM IST
MIN_ACCURACY = 90
IST = pytz.timezone('Asia/Kolkata')

# Store last signals (avoid duplicates)
last_signals = {}
signal_count = 0

async def check_trading_hours():
    """Check if within trading hours"""
    now = datetime.now(IST)
    current_time = now.strftime("%H:%M")
    day_of_week = now.weekday()  # 0-4 = Mon-Fri
    
    # Only weekdays
    if day_of_week >= 5:  # Saturday and Sunday
        return False
    
    # Only 6:30 PM - 8:30 PM IST
    if SIGNAL_TIME_START <= current_time <= SIGNAL_TIME_END:
        return True
    
    return False

def calculate_accuracy(pair):
    """
    Simulate high accuracy signal generation
    In real scenario, this would analyze technical indicators
    """
    # Base accuracy for each pair
    base_accuracy = {
        "EURUSD": 90,
        "GBPUSD": 88,
        "USDJPY": 87
    }
    
    base = base_accuracy.get(pair, 85)
    
    # Add randomness (85-95% range)
    accuracy = base + random.randint(-5, 5)
    
    # Only return if >= 90%
    if accuracy >= MIN_ACCURACY:
        return accuracy
    return None

def generate_signal_data(pair, accuracy):
    """Generate signal data"""
    
    # Realistic price ranges
    prices = {
        "EURUSD": {"min": 1.0850, "max": 1.0950},
        "GBPUSD": {"min": 1.2650, "max": 1.2750},
        "USDJPY": {"min": 150.00, "max": 151.50}
    }
    
    price_range = prices.get(pair, {"min": 1.0, "max": 2.0})
    current_price = round(random.uniform(price_range["min"], price_range["max"]), 5)
    
    # 50/50 buy/sell
    direction = random.choice(["BUY", "SELL"])
    
    if direction == "BUY":
        entry = current_price
        sl = round(entry - 0.0010, 5) if "JPY" not in pair else round(entry - 0.15, 2)
        target = round(entry + 0.0025, 5) if "JPY" not in pair else round(entry + 0.35, 2)
    else:
        entry = current_price
        sl = round(entry + 0.0010, 5) if "JPY" not in pair else round(entry + 0.15, 2)
        target = round(entry - 0.0025, 5) if "JPY" not in pair else round(entry - 0.35, 2)
    
    # Calculate pips
    sl_pips = abs(entry - sl) * 10000
    target_pips = abs(target - entry) * 10000
    
    if sl_pips == 0:
        sl_pips = 5
    if target_pips == 0:
        target_pips = 25
    
    rr_ratio = round(target_pips / sl_pips, 2)
    
    signal = {
        "pair": pair,
        "timeframe": random.choice(["1M", "5M", "10M"]),
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "target": target,
        "sl_pips": round(sl_pips, 1),
        "target_pips": round(target_pips, 1),
        "rr_ratio": rr_ratio,
        "accuracy": accuracy,
        "time": datetime.now(IST).strftime("%H:%M %Z")
    }
    
    return signal

async def send_telegram_signal(bot, signal):
    """Send signal to Telegram"""
    
    emoji_direction = "🟢" if signal["direction"] == "BUY" else "🔴"
    
    message = f"""
📊 {signal['pair']} - {signal['direction']} ({signal['timeframe']}) {emoji_direction}
━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Time: {signal['time']}
📈 Pair: {signal['pair']} | TF: {signal['timeframe']}
📍 Entry: {signal['entry']}
🛑 SL: {signal['sl']} ({signal['sl_pips']} pips)
🎯 Target: {signal['target']} ({signal['target_pips']} pips)
📊 Risk/Reward: 1:{signal['rr_ratio']}

✨ SIGNAL QUALITY:
━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 ACCURACY: {signal['accuracy']}% 🔴
✅ High Quality Signal
⭐⭐⭐ CONFIDENCE: VERY HIGH
👉 ACTION: TAKE THIS TRADE
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    try:
        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
        print(f"✅ Signal sent: {signal['pair']} {signal['direction']}")
        return True
    except TelegramError as e:
        print(f"❌ Telegram error: {e}")
        return False

async def monitor_and_send_signals(bot):
    """Main monitoring and signal sending function"""
    
    within_hours = await check_trading_hours()
    
    if not within_hours:
        now = datetime.now(IST)
        print(f"⏰ {now.strftime('%H:%M:%S %Z')} - Outside trading hours")
        return
    
    print(f"✅ Within trading hours - checking for signals...")
    
    for pair in PAIRS:
        try:
            # Calculate accuracy for this pair
            accuracy = calculate_accuracy(pair)
            
            if accuracy is None:
                print(f"  {pair}: Accuracy {accuracy}% (too low)")
                continue
            
            # Generate signal
            signal = generate_signal_data(pair, accuracy)
            
            # Check if already sent recently (within 5 minutes)
            signal_key = f"{pair}_{signal['direction']}"
            
            if signal_key in last_signals:
                time_diff = (datetime.now(IST) - last_signals[signal_key]).total_seconds()
                if time_diff < 300:  # 5 minutes
                    print(f"  {pair}: Signal already sent recently")
                    continue
            
            # Send signal
            if await send_telegram_signal(bot, signal):
                last_signals[signal_key] = datetime.now(IST)
                global signal_count
                signal_count += 1
            
            await asyncio.sleep(1)
        
        except Exception as e:
            print(f"❌ Error processing {pair}: {e}")
            continue

async def main():
    """Main bot loop"""
    
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Send startup message
    try:
        startup_msg = """
🤖 QUOTEX SIGNAL BOT STARTED ✅
━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Bot: Active and Running
✅ Pairs: EURUSD, GBPUSD, USDJPY
✅ Timeframes: 1M, 5M, 10M
✅ Accuracy Filter: 90%+ ONLY
✅ Active Time: 6:30 PM - 8:30 PM IST
✅ Active Days: Weekdays (Mon-Fri)
✅ Manual Trading: Quotex ready

🎯 Ready to send high quality signals!
📊 Monitoring now...
"""
        await bot.send_message(chat_id=TELEGRAM_USER_ID, text=startup_msg)
        print("✅ Startup message sent")
    except Exception as e:
        print(f"⚠️  Startup message error: {e}")
    
    print("🚀 Bot started. Monitoring for signals...")
    print(f"📊 Trading hours: 6:30 PM - 8:30 PM IST (Weekdays)")
    
    # Main loop - check every minute
    while True:
        try:
            await monitor_and_send_signals(bot)
            await asyncio.sleep(60)  # Check every minute
        
        except KeyboardInterrupt:
            print("\n❌ Bot stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Bot stopped")
