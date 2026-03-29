# 🎯 Multi-Database Admin Panel

Complete admin panel for managing users across 5 PostgreSQL databases simultaneously.

## 📱 Tech Stack

**Frontend:** Expo React Native (Web + Mobile compatible)
**Backend:** FastAPI (Python)
**Databases:** PostgreSQL (5 databases on Neon.tech)

---

## 🌟 Features

### ⭐ Priority Databases
1. **LDB App Users (neondb)** - Main application users
2. **IDPass Users** - ID and password management

### 📊 Other Databases
3. **PMFBY Users** - PMFBY scheme users
4. **KRP Users** - KRP scheme users  
5. **Byaj Anudan Users** - Interest subsidy users

### 🔥 Core Features
- ✅ **User Approval System** - Approve/Reject pending users
- ✅ **Status Management** - Active/Inactive user status
- ✅ **Multi-tab Interface** - Pending, Approved, Inactive tabs
- ✅ **Real-time Counts** - Live count badges for all statuses
- ✅ **Bulk Operations** - Approve, Reject, Deactivate, Delete, Reactivate
- ✅ **Confirmation Dialogs** - Safety for destructive actions
- ✅ **Toast Notifications** - Success/Error messages
- ✅ **Mobile Responsive** - Works on all devices
- ✅ **Sidebar Navigation** - Easy database switching
- ✅ **Pull to Refresh** - Update data instantly

---

## 🗄️ Database Schema

### DB1: neondb
**Tables:**
- `pending_users` - New registration requests
- `app_users` - Approved users (with active/inactive status)

**Fields:**
- sr, userid, user_pass_hash, pacs_name, created_on, approved_on, active, last_access_time

### DB2-4: pmfby_idpass, krp_idpass, byajanudan_idpass
**Tables:**
- `pending_ipws` - New requests
- `ipws` - Approved users

**Fields:**
- sr, user_id, pass, name, pacs_name, branch, dist, state, mobile, approved_on, last_access_time

### DB5: IDPass
**Same structure as DB2-4 but uses:**
- `user_name` field instead of `user_id`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Yarn package manager

### Installation

```bash
# Backend Setup
cd backend
pip install -r requirements.txt
python server.py

# Frontend Setup
cd frontend
yarn install
yarn start
```

### Access URLs
- **Web Preview:** https://record-keeper-35.preview.emergentagent.com
- **Backend API:** Port 8001
- **Frontend Dev:** Port 3000

---

## 📡 API Endpoints

### Health & Status
```
GET  /              - API health check
GET  /api/health    - Database connection status
GET  /api/counts    - Get counts for all databases
```

### Database Operations
```
GET    /api/{dbkey}/pending        - Get pending users
GET    /api/{dbkey}/approved       - Get approved users
GET    /api/neondb/inactive        - Get inactive users (DB1 only)

POST   /api/{dbkey}/approve/{sr}   - Approve user
POST   /api/{dbkey}/reject/{sr}    - Reject user
POST   /api/{dbkey}/deactivate/{sr}- Deactivate user
DELETE /api/{dbkey}/delete/{sr}    - Delete user permanently
POST   /api/neondb/reactivate/{sr} - Reactivate user (DB1 only)
```

**Database Keys (dbkey):**
- `neondb` - LDB App Users
- `pmfby` - PMFBY Users
- `krp` - KRP Users
- `byajanudan` - Byaj Anudan Users
- `idpass` - IDPass Users

---

## 🎨 UI/UX Features

### Design
- **Dark Sidebar** - Professional look with #1a1a2e background
- **Clean Content Area** - White background for readability
- **Color-coded Badges:**
  - 🟠 Amber - Pending count
  - 🟢 Green - Approved count
  - 🔴 Red - Inactive count

### Mobile Features
- Hamburger menu for sidebar
- Responsive tables with horizontal scroll
- Touch-optimized buttons
- Pull-to-refresh functionality
- Toast notifications (auto-dismiss in 3s)

### Desktop Features
- Persistent sidebar
- Large data tables
- Hover effects
- Keyboard navigation support

---

## 🔐 Security Features

- Confirmation dialogs for destructive actions (Delete, Reject, Deactivate)
- Transaction-based database operations
- Proper error handling with user-friendly messages
- Connection pooling for database efficiency
- CORS configured for secure API access

---

## 📊 Current Database Status

```
neondb:      10 active users, 0 pending
pmfby:       58 approved, 4 pending
krp:         67 approved, 0 pending  
byajanudan:  24 approved, 0 pending
idpass:      58 approved, 0 pending
```

---

## 🛠️ Development

### Backend Tech
- FastAPI for async API handling
- asyncpg for PostgreSQL async connections
- Connection pooling (2-10 connections per DB)
- Automatic reconnection handling
- Structured logging

### Frontend Tech
- Expo Router for file-based routing
- Axios for API calls
- React Native Safe Area Context
- Platform-specific optimizations
- TypeScript for type safety

---

## 📱 Mobile App (APK)

See [APK_BUILD_GUIDE.md](./APK_BUILD_GUIDE.md) for:
- Expo Go app testing
- Native APK build instructions
- EAS Build setup
- APK signing process

**Quick Test:**
1. Install Expo Go from Play Store
2. Scan QR code from preview URL
3. Test all features on your mobile

---

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check backend logs
sudo supervisorctl tail -f backend

# Restart backend
sudo supervisorctl restart backend
```

### Frontend Issues
```bash
# Check frontend logs
sudo supervisorctl tail -f expo

# Restart frontend
sudo supervisorctl restart expo

# Clear cache
cd frontend && yarn start --clear
```

### Database Connection Issues
- Check Neon.tech database status
- Verify connection strings in server.py
- Check network connectivity
- Review backend startup logs for connection errors

---

## 📈 Performance

- **Response Time:** < 500ms for most operations
- **Database Pools:** 5 pools x 10 max connections = 50 total
- **Frontend Bundle:** Optimized with Metro bundler
- **API Calls:** Async/await for non-blocking operations

---

## 🎯 User Workflows

### Approve New User
1. Select database from sidebar
2. Click "Pending" tab
3. Review user details
4. Click "Approve" button
5. User moves to Approved tab
6. Count badges update automatically

### Deactivate User
1. Go to "Approved" tab
2. Find user to deactivate
3. Click "Deactivate" button
4. Confirm action
5. User moves back to Pending
6. For neondb: User moves to Inactive tab

### Delete User Permanently
1. Navigate to Approved/Inactive tab
2. Locate user
3. Click "Delete" button
4. Confirm permanent deletion
5. User removed from database
6. Counts update

---

## 📝 Database Operations Logic

### DB1 (neondb) - Special Logic
```
Pending → [Approve] → Active (app_users, active=true)
Active → [Deactivate] → Inactive (app_users, active=false) + adds to pending_users
Inactive → [Reactivate] → Active (sets active=true)
Inactive → [Delete] → Permanently removed
```

### DB2-5 (Standard Logic)
```
Pending (pending_ipws) → [Approve] → Approved (ipws)
Approved → [Deactivate] → Pending (back to pending_ipws)
Approved → [Delete] → Permanently removed
```

---

## 🌐 Browser Compatibility

- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS/Android)

---

## 💡 Tips

1. **Regular Refresh:** Use pull-to-refresh to get latest counts
2. **Confirmation:** Always read confirmation dialogs carefully
3. **Toast Messages:** Watch for success/error notifications
4. **Mobile Use:** Swipe tables horizontally to see all fields
5. **Sidebar:** Click database name to expand/collapse tabs

---

## 👨‍💻 Support

For issues or questions:
1. Check backend/frontend logs
2. Verify database connections
3. Review API endpoint responses
4. Check browser console for errors

---

## 📄 License

Proprietary - All rights reserved

---

## 🎉 Credits

**Built with:**
- FastAPI
- Expo React Native
- PostgreSQL (Neon.tech)
- Python asyncpg
- React Navigation
- Axios

**Powered by:** Emergent AI Platform

---

**Last Updated:** March 2026
**Version:** 1.0.0
**Status:** ✅ Production Ready
