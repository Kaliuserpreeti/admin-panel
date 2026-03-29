# Build Your APK - Super Easy Guide

## Option 1: EAS Build via Terminal (Recommended)

Since you have Expo credentials, here's what YOU need to run on YOUR computer:

### Windows PowerShell/CMD:

```cmd
# Install EAS CLI (one time only)
npm install -g eas-cli

# Login with your credentials
eas login
# Enter: IT_Infotec
# Enter: HPVerma@1999

# Now you need the project code on your computer
# Download from Emergent or clone from GitHub
```

---

## Option 2: Build via Expo Website (EASIEST!)

1. Go to: https://expo.dev/login
   - Login: IT_Infotec
   - Pass: HPVerma@1999

2. Click: "Create a new project"

3. Upload your project OR connect GitHub

4. Click: "New Build" → Android → APK

5. Wait 15-20 mins → Download APK!

---

## Option 3: I'll Create a Build Script for You

Run this from the project directory:

```bash
#!/bin/bash
# This needs to run from /app/frontend directory

export EXPO_TOKEN="your-expo-token-here"
eas build --platform android --profile preview --non-interactive
```

---

## What You Need:

Your project code needs to be either:
- A. On your local Windows machine
- B. In a GitHub repository
- C. Uploaded to Expo directly

Current code is on Emergent server at `/app/frontend` - not accessible from Windows.

---

## FASTEST METHOD FOR YOU:

Since you're on Windows and code is on Emergent server, best option:

1. **Download code from Emergent** (use export/download feature)
2. **Extract to your computer** (e.g., C:\MyProjects\admin-panel)
3. **Open PowerShell in that folder**
4. **Run:**
   ```cmd
   npm install -g eas-cli
   eas login
   eas build --platform android --profile preview
   ```

Would you like me to create a downloadable ZIP of your project?
