# FitApp — Android Project
## Your Nippard PPL + PRAMS Cardio app

---

## What's inside

- **Workout tab** — Full Nippard PPL programme (Phase 1/2/3, all 6 sessions)
- **Cardio tab** — All 5 PRAMS cardio modules (Tabata, Gym circuits, Bleep test, Rowing, Outdoor)
- **Timer tab** — Cardio interval timer (Tabata / AMRAP / Intervals / Bleep)
- **History tab** — PR tracker + session log

### New features (vs original HTML files)
- ✅ **Rest timer** — tap REST after any set; configurable duration (default 90s), counts down with beeps
- ✅ **Previous session data** — when logging a workout, shows your last weights for each exercise as grey placeholder
- ✅ **PR tracking** — automatically records personal bests by exercise
- ✅ **All data persists** — localStorage keeps everything between sessions

---

## How to build the APK

### Step 1 — Install Android Studio
Download free from: https://developer.android.com/studio

### Step 2 — Open the project
- Open Android Studio
- Click **File → Open**
- Select this `FitApp` folder
- Wait for Gradle sync (2–5 minutes first time, needs internet)

### Step 3 — Build debug APK
- Click **Build → Build Bundle(s) / APK(s) → Build APK(s)**
- Wait ~1 minute
- Click the notification "locate" link — the APK will be at:
  `app/build/outputs/apk/debug/app-debug.apk`

### Step 4 — Install on your phone
Option A — USB cable:
- Enable Developer Options on your phone (Settings → About → tap Build Number 7 times)
- Enable USB Debugging
- Plug in phone → click "Run" (▶) in Android Studio

Option B — Copy APK:
- Transfer `app-debug.apk` to your phone
- Open it from Files app
- Allow "install from unknown sources" when prompted

---

## Requirements
- Android 7.0+ (API 24+)
- ~5MB storage

---

## Customising
The entire app is in one HTML file:
`app/src/main/assets/index.html`

You can edit it directly — change exercises, rest durations, add new workouts, etc.
After editing, just rebuild the APK.
