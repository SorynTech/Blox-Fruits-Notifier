# Blox Fruits Roll Tracker - SorynTech Bot Suite 🎲🦈

A comprehensive Discord bot for tracking Blox Fruits rolls with automatic reminders, statistics tracking, and a beautiful underwater-themed stats dashboard.

## 🌊 Features Overview

### 🎲 Roll Tracking System
- **Personal Roll Logging**: Each user tracks their own fruit rolls
- **Rarity System**: All fruits categorized by rarity (Common → Mythic)
- **Multiple Sorting Options**: Browse alphabetically or by rarity
- **2-Hour Cooldown**: Matches Blox Fruits' actual cooldown system
- **Automatic Reminders**: Get pinged when your next roll is ready
- **Roll History**: View all your past fruit rolls with rarity statistics
- **Public Announcements**: Share your rolls with the server (includes rarity)

### 📊 Stats Dashboard
The bot includes two web interfaces:

#### Public Health Check (`/health` or `/`)
- **Publicly accessible** for uptime monitoring (perfect for UptimeRobot)
- Shows basic bot statistics
- Underwater shark theme
- Real-time status display

#### Protected Stats Page (`/stats`)
- **HTTP Basic Authentication** required
- Comprehensive statistics dashboard
- Features:
  - **24-Hour Command Usage Graph**: Track when users are most active
  - **User Roll List**: See all users organized by next roll time
  - **Recent Rolls**: View each user's most recent fruit roll
  - **Notification Status**: See who has reminders enabled/disabled
  - **Real-time Updates**: Auto-refreshes every 30 seconds
- Beautiful animated underwater theme with swimming sharks 🦈
- Responsive design for mobile and desktop

### 🔔 Smart Notification System
- **Sleep Mode**: Disable reminders when you're not playing (`/sleep`)
- **Awake Mode**: Re-enable reminders when you're back (`/awake`)
- **Automatic Pings**: Get notified via DM when your roll is ready
- **Cooldown Tracking**: Bot keeps track of your next available roll

---

## 🎮 Commands

### 📝 User Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/fruit-roll` | Log your fruit roll | Opens interactive fruit selector |
| `/fruits` | View your roll history | Shows all your rolled fruits (most recent first) |
| `/sleep` | Disable roll reminders | Stops the bot from pinging you |
| `/awake` | Enable roll reminders | Re-enables roll notifications |

### 👑 Owner Commands

| Command | Description | Access Level |
|---------|-------------|--------------|
| `/stats-link` | Get stats page credentials | Owner Only (ID: 447812883158532106) |

---

## 🎯 How It Works

### First-Time Setup
1. Bot automatically notifies designated users on startup
2. Initial message includes all basic commands and instructions
3. Users are ready to start logging rolls immediately

### Logging a Roll
1. User runs `/fruit-roll`
2. Bot checks if user is on cooldown
   - ✅ **If available**: Shows sorting options (Alphabetical or By Rarity)
   - ❌ **If on cooldown**: Shows time remaining until next roll
3. User chooses sorting method:
   - **📝 Alphabetical**: Browse all fruits A-Z (3 pages of 20 fruits each)
   - **✨ By Rarity**: Select a rarity tier (Common, Uncommon, Rare, Legendary, Mythic)
4. User selects their rolled fruit from buttons
5. Bot announces: `@User just rolled [rarity emoji] [Fruit] [fruit emoji] ([Rarity])!`
6. Bot starts 2-hour countdown for next reminder

### Automatic Reminders
- Bot checks every minute for users whose cooldown is complete
- Sends DM with embedded reminder
- Only sends to users with notifications enabled
- Clears cooldown timer after sending

### Viewing Roll History
- `/fruits` command shows all your rolled fruits
- **Rarity Statistics**: Shows count of each rarity you've rolled
- Displays up to 25 most recent rolls with rarity indicators
- Shows timestamp for each roll (relative time)
- Color-coded by rarity with emoji indicators
- Total roll count at the top

---

## 🍎 Available Fruits

The bot includes all current Blox Fruits (41 total) organized by rarity:

### ⚪ Common (8 fruits)
Rocket, Spin, Blade, Spring, Bomb, Smoke, Spike, Flame

### 🔵 Uncommon (8 fruits)
Ice, Sand, Dark, Eagle, Diamond, Light, Rubber, Ghost

### 🟣 Rare (8 fruits)
Magma, Quake, Buddha, Love, Creation, Spider, Sound, Phoenix

### 🔮 Legendary (4 fruits)
Portal, Lightning, Pain, Blizzard

### 🔴 Mythic (13 fruits)
Gravity, Mammoth, T-Rex, Dough, Shadow, Venom, Gas, Spirit, Tiger, Yeti, Kitsune, Control, Dragon

---

## 🎨 Rarity System

### Visual Indicators
- **⚪ Common** - Gray background
- **🔵 Uncommon** - Blue background
- **🟣 Rare** - Purple background
- **🔮 Legendary** - Pink/Magenta background
- **🔴 Mythic** - Red background

### In Commands
- **Roll Announcements**: Show rarity emoji and color
- **`/fruits` History**: Color-coded by rarity with statistics
- **Selection Menu**: Choose to browse alphabetically or by rarity

---

## 🛠️ Technical Details

### Built With
- **discord.py** - Discord API wrapper
- **aiohttp** - Async HTTP server for web dashboard
- **sqlite3** - Local database for persistent storage
- **Python 3.8+** - Programming language

### Database Schema

The bot uses SQLite with three main tables:

```sql
-- Users table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    total_rolls INTEGER DEFAULT 0,
    last_roll_time TIMESTAMP,
    next_roll_time TIMESTAMP,
    notifications_enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rolls table
CREATE TABLE rolls (
    roll_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fruit_name TEXT NOT NULL,
    rolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Command usage tracking
CREATE TABLE command_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Environment Variables

Create a `.env` file with the following:

```env
DISCORD_TOKEN=your_bot_token_here
STATS_USER=your_stats_username
STATS_PASS=your_stats_password
PORT=10000
```

**Important:**
- `DISCORD_TOKEN` - Required for bot to function
- `STATS_USER` - Username for stats page (default: `admin`)
- `STATS_PASS` - Password for stats page (default: `changeme`)
- `PORT` - Web server port (default: `10000`)

### Bot Permissions Required
- Send Messages
- Embed Links
- Use Slash Commands
- Read Message History
- Send Messages in DMs

---

## 📊 Statistics Tracking

### What Gets Tracked
- **Total Rolls**: Global count of all fruit rolls
- **Per-User Rolls**: Individual roll counts
- **Command Usage**: 24-hour graph of `/fruit-roll` usage
- **Active Users**: Number of users who have logged at least one roll
- **Next Roll Times**: Countdown timers for each user
- **Notification Status**: Who has reminders enabled/disabled

### Stats Page Access
1. Navigate to `http://your-bot-url/stats`
2. Enter credentials from `/stats-link` command
3. View comprehensive dashboard with:
   - Real-time statistics
   - Command usage graph
   - User list sorted by next roll time
   - Recent roll information
   - Notification status for each user

---

## 🔄 Automatic Systems

### Notification Loop
- Runs every 1 minute
- Checks all users' `next_roll_time`
- Sends DM reminders to eligible users
- Automatically clears cooldown after reminder sent

### Database Cleanup
- SQLite database stored in `fruit_rolls.db`
- Automatic indexing for fast queries
- Timestamps stored in ISO format
- Foreign key constraints maintain data integrity

### Web Server
- Always-on HTTP server for monitoring
- `/health` endpoint responds to all requests (for UptimeRobot)
- `/stats` endpoint protected by HTTP Basic Auth
- Auto-refresh every 30 seconds

---

## 🎨 Visual Theme

### Underwater Shark Theme
All web pages feature:
- **Deep ocean blue gradients**
- **Animated swimming sharks** 🦈 crossing the screen
- **Glassmorphism effects** with backdrop blur
- **Glowing neon accents** in cyan/blue
- **Responsive design** for all screen sizes
- **Smooth animations** and transitions

### Color Palette
- Primary: `#06b6d4` (Cyan)
- Background: `#0a1929` → `#1a2f42` → `#0d3a5c` (Gradient)
- Cards: `rgba(13, 58, 92, 0.4)` (Translucent blue)
- Accents: `#3b82f6` (Blue), `#10b981` (Green)
- Text: `#fff` (White), `#94a3b8` (Gray)

---

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your token
echo "DISCORD_TOKEN=your_token" > .env

# Run the bot
python main.py
```

### Production (Render.com)
1. Fork this repository
2. Create new Web Service on Render
3. Connect your GitHub repository
4. Set environment variables:
   - `DISCORD_TOKEN`
   - `STATS_USER`
   - `STATS_PASS`
5. Deploy!

### UptimeRobot Setup
1. Add new monitor
2. Monitor Type: HTTP(s)
3. URL: `https://your-bot-url.onrender.com/health`
4. Monitoring Interval: 5 minutes
5. This keeps your Render instance alive 24/7

---

## 🔒 Security Features

### Stats Page Protection
- HTTP Basic Authentication required
- Credentials stored in environment variables
- No unauthorized access to user data
- 401 response with auth challenge if credentials invalid

### Database Security
- SQLite file stored locally
- No external database connections
- Foreign key constraints prevent orphaned data
- Parameterized queries prevent SQL injection

### User Privacy
- Roll history only visible to the user
- DM reminders only go to the user
- Stats page requires authentication
- No public exposure of user IDs

---

## 📋 Planned Features

### Future Enhancements
- [ ] Weekly roll statistics per user
- [ ] Rarity tracking (Common, Rare, Legendary fruits)
- [ ] Server leaderboards (most rolls)
- [ ] Export roll history to CSV
- [ ] Custom notification timing (user preference)
- [ ] Integration with other Blox Fruits features
- [ ] Role rewards for milestone rolls (10, 50, 100, etc.)

---

## 🐛 Troubleshooting

### Bot Not Responding
1. Check bot is online in Discord
2. Verify token in `.env` file
3. Check bot has required permissions
4. Run `/stats-link` to verify bot is functioning

### Notifications Not Working
1. Check DMs are enabled for the bot
2. Verify you're not in sleep mode (`/awake`)
3. Check you've logged at least one roll
4. Ensure 2 hours have passed since last roll

### Stats Page Not Loading
1. Verify `STATS_USER` and `STATS_PASS` in `.env`
2. Check HTTP Basic Auth credentials
3. Try clearing browser cache
4. Ensure web server is running (check logs)

### Database Issues
1. Delete `fruit_rolls.db` to reset (will lose data)
2. Check file permissions on database
3. Ensure sufficient disk space
4. Restart bot to reinitialize database

---

## 🔗 SorynTech Bot Suite

This bot is part of the **SorynTech Bot Suite**, a collection of Discord bots with unified underwater shark theming.

### Other Bots in the Suite

#### 🦈 Shark Moderation Bot
A comprehensive Discord moderation bot with powerful features and the same beautiful underwater theme.

**Repository**: [github.com/SorynTech/Discord-Moderation-Bot](https://github.com/SorynTech/Discord-Moderation-Bot-)

**Features:**
- 33+ moderation commands
- Advanced tracking system
- Moderation history
- Voice moderation
- Server lockdown
- Role management
- Beautiful status page with multiple modes
- Emergency shutdown system

**Learn More**: Check out the full README in the repository for detailed documentation.

---

## 📊 Project Statistics

- **Commands**: 5 total (4 user + 1 owner)
- **Database Tables**: 3
- **Tracked Fruits**: 39
- **Auto-Notifications**: Yes (2-hour intervals)
- **Web Endpoints**: 3 (`/`, `/health`, `/stats`)
- **Lines of Code**: ~1000+

---

## 🤝 Contributing

This is a personal project by SorynTech. If you have suggestions or find bugs, feel free to:
- Open an issue on GitHub
- Submit a pull request
- Contact the developer directly

**Note**: This bot is designed specifically for Blox Fruits and may require updates when the game updates fruit lists or cooldown timers.

---

## 📄 License

MIT License

Copyright (c) 2025 SorynTech

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## 🙏 Acknowledgments

- **Blox Fruits** - For the amazing game that inspired this bot
- **discord.py** - For the excellent Discord API wrapper
- **SorynTech Community** - For testing and feedback

---

**Made with 💙 by SorynTech** 🦈

*Part of the SorynTech Bot Suite - Professional Discord automation with style*

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/SorynTech/Blox-Fruits-Notifier/issues)
- **Discord**: Coming soon
- **Documentation**: This README + in-code comments

---

## ⚙️ Configuration Reference

### Startup Notification Recipients
Edit these user IDs in `main.py`:
```python
NOTIFICATION_USERS = [
    447812883158532106,   # User 1
    778645525499084840,   # User 2
    581677161006497824,   # User 3
    1285269152474464369   # User 4
]
```

### Cooldown Duration
Modify in `main.py`:
```python
ROLL_COOLDOWN_HOURS = 2  # Change this value
```

### Owner ID
Set your Discord user ID:
```python
OWNER_ID = 447812883158532106  # Your ID here
```

---

**🦈 Swim with the sharks, roll with the best 🎲**
