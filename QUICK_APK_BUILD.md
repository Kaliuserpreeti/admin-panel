# 🚀 APK Build - Step by Step Guide

Bhai, **Expo Go mein sab kaam kar raha hai** - ab APK banana bahut easy hai! 

## ✅ Method 1: EAS Build (RECOMMENDED - Sabse Easy!)

### Step 1: EAS CLI Install Karo

```bash
npm install -g eas-cli
```

### Step 2: Expo Account Banao (Free hai!)

```bash
eas login
```

**Agar account nahi hai:**
- Username: kuch bhi unique (jaise: yourname123)
- Email: aapka email
- Password: strong password

### Step 3: Project Configure Karo

```bash
cd /app/frontend
eas build:configure
```

Ye `eas.json` file bana dega automatically.

### Step 4: APK Build Karo 🎯

```bash
eas build --platform android --profile preview
```

**Kya hoga:**
- Cloud pe build hoga (15-20 minutes)
- Terminal mein link milega
- Build complete hone ke baad APK download link milega

### Step 5: APK Download Karo

Build complete hone ke baad:
```
✅ Build finished!
📱 Download: https://expo.dev/accounts/[your-account]/projects/[project]/builds/[build-id]
```

Is link se APK download karo!

---

## 📦 Method 2: Local APK Build (Advanced)

Agar cloud build nahi karna to local build karo:

### Prerequisites:
- Android Studio installed
- Java JDK 17+
- 15GB+ free space

### Steps:

```bash
# Step 1: Android native project generate karo
cd /app/frontend
npx expo prebuild --platform android --clean

# Step 2: Build APK
cd android
./gradlew assembleRelease

# APK Location:
# android/app/build/outputs/apk/release/app-release.apk
```

---

## 🎯 Quick Commands Summary

```bash
# EAS Build (Easiest!)
npm install -g eas-cli
eas login
cd /app/frontend
eas build --platform android --profile preview

# Wait 15-20 mins
# Download APK from link
```

---

## ⚡ APK Install Kaise Karein

APK download hone ke baad:

1. **APK ko mobile mein transfer karo**
   - USB cable se
   - Ya Google Drive/WhatsApp se

2. **Mobile mein install karo**
   - File Manager open karo
   - APK file pe tap karo
   - "Install from Unknown Sources" allow karo
   - Install button press karo

3. **App open karo**
   - Installed apps mein dikhai dega
   - Open karo aur use karo!

---

## 🔧 Troubleshooting

### "eas: command not found"
```bash
npm install -g eas-cli
# Terminal restart karo
```

### "Login failed"
```bash
# Expo website pe signup karo pehle:
# https://expo.dev/signup
# Phir eas login try karo
```

### "Build failed"
```bash
# Logs check karo
eas build:list
# Last build ka detail dekho
```

### APK install nahi ho raha
- Settings → Security → "Install from Unknown Sources" enable karo
- Ya Settings → Apps → Special Access → Install Unknown Apps → File Manager ko allow karo

---

## 📱 APK File Size

**Expected Size:** 40-60 MB
**First Install:** Thoda time lagega (2-3 mins)

---

## 🎉 Success!

APK install hone ke baad:

✅ App icon home screen pe dikhega
✅ Offline bhi chalega (data fetch ke liye internet chahiye)
✅ Notifications support (agar add karo to)
✅ Full native experience

---

## 💡 Pro Tips

1. **Development APK:**
   - `eas build --profile preview` use karo
   - Testing ke liye perfect

2. **Production APK:**
   - `eas build --profile production` use karo
   - Google Play Store upload ke liye

3. **Debug APK (Local):**
   ```bash
   cd android
   ./gradlew assembleDebug
   # Faster build, larger size
   ```

4. **Check Build Status:**
   ```bash
   eas build:list
   ```

---

## 🆘 Need Help?

Agar koi problem aaye to:

1. EAS Build logs check karo
2. `eas build:list` command se status dekho
3. Expo documentation: https://docs.expo.dev/build/setup/

---

**Happy Building! 🚀**

Bhai, **EAS Build sabse easy hai!** Just 4 commands aur APK ready! 💪
