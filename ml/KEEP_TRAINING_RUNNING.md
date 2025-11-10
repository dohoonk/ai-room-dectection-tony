# Keeping Training Running When Laptop Closes

## ⚠️ Important: Closing Laptop = Sleep = Training Pauses

When you close your MacBook, it goes to sleep and **all processes pause**, including your training.

---

## ✅ Solutions to Keep Training Running

### Option 1: Prevent Sleep (Recommended)

**Keep laptop open but prevent it from sleeping:**

```bash
# Prevent sleep (runs until you cancel with Ctrl+C)
caffeinate -d

# Or prevent sleep indefinitely (until you manually stop it)
caffeinate -d &
```

**What this does:**
- Keeps display awake (prevents sleep)
- Training continues running
- You can close the lid (but keep it plugged in)
- Press Ctrl+C or `killall caffeinate` to stop

**Best practice:**
- Keep laptop plugged in
- Run `caffeinate -d` in a separate terminal
- Training will continue even if you close the lid

---

### Option 2: Keep Laptop Open

**Simplest solution:**
- Keep laptop open (don't close the lid)
- Plug it in to power
- Adjust sleep settings:
  - System Settings → Battery → Options
  - Set "Prevent automatic sleeping when display is off" to ON
  - Or set sleep to "Never" while plugged in

---

### Option 3: Use Screen/Tmux (Advanced)

**Create a persistent session:**

```bash
# Install screen (if not installed)
brew install screen

# Start a screen session
screen -S training

# Run training inside screen
yolo segment train ...

# Detach: Press Ctrl+A, then D
# Reattach later: screen -r training
```

**Benefits:**
- Session survives disconnections
- Can reconnect later to check progress
- Still need to prevent sleep though

---

### Option 4: Run as Background Service (Most Robust)

**Create a launchd service (macOS native):**

This is more complex but most reliable. Not recommended for beginners.

---

## 🎯 Recommended Approach

**For your current training:**

1. **Keep laptop open and plugged in** (simplest)
2. **OR run caffeinate:**
   ```bash
   caffeinate -d
   ```
   Then you can close the lid (but keep plugged in)

3. **Check progress later:**
   ```bash
   # See how many epochs completed
   wc -l ml/runs/room_detection_gpu/results.csv
   
   # View latest results
   tail ml/runs/room_detection_gpu/results.csv
   ```

---

## ⏱️ Current Training Status

Your training is currently running. If you want to keep it going:

1. **Right now:** Keep laptop open or run `caffeinate -d`
2. **If you close laptop:** Training will pause (but can resume when you wake it)
3. **Best practice:** Keep it open/plugged in for the ~15 hours

---

## 🔄 If Training Gets Paused

**If your laptop goes to sleep:**
- Training process pauses
- When you wake it, training may continue OR may need restart
- **Good news:** Best model is saved automatically, so you won't lose progress
- You can resume from the last checkpoint if needed

---

## 💡 Quick Command

**To prevent sleep right now:**
```bash
caffeinate -d
```

Run this in a separate terminal window. Your training will continue even if you close the lid (as long as it's plugged in).


