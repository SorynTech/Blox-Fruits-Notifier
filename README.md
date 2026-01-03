# Blox Fruits Roll Tracker - SorynTech Bot Suite 🎲🦈

A comprehensive Discord bot for tracking Blox Fruits rolls with automatic reminders, statistics tracking, and a beautiful underwater-themed stats dashboard.

## 🌊 Features Overview

### 🎲 Roll Tracking System
- **Personal Roll Logging**: Each user tracks their own fruit rolls
- **Rarity System**: All fruits categorized by rarity (Common → Mythic)
- **Multiple Sorting Options**: Browse alphabetically or by rarity
- **2-Hour Cooldown**: Matches Blox Fruits' actual cooldown system
- **Automatic Reminders**: Get pinged in a designated channel when your next roll is ready
- **Roll History**: View all your past fruit rolls with rarity statistics
- **Public Announcements**: Share your rolls with the server (includes rarity)

### 📊 Stats Dashboard
The bot includes two web interfaces:

#### Public Health Check (`/health` or `/`)
- **Publicly accessible** for uptime monitoring (perfect for UptimeRobot)
- Shows basic bot statistics
- Underwater shark theme
- Real-time status display
- Custom favicon support

#### Protected Stats Page (`/stats`)
- **HTTP Basic Authentication** required
- Comprehensive statistics dashboard
- Features:
  - **Fruit Rarity Distribution Chart**: Visual bar chart showing rolls by rarity
  - **User Roll List**: See all users organized by next roll time
  - **Recent Rolls**: View each user's most recent fruit roll
  - **Notification Status**: See who has reminders enabled/disabled
  - **Real-time Updates**: Auto-refreshes every 30 seconds
- Beautiful animated underwater theme with swimming sharks 🦈
- Responsive design for mobile and desktop
- Custom favicon support

### 🔔 Smart Notification System
- **Sleep Mode**: Disable reminders when you're not playing (`/sleep`)
- **Awake Mode**: Re-enable reminders when you're back (`/awake`)
- **Channel Notifications**: Get notified in a designated channel when your roll is ready
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
| `/stats-link` | Get stats page credentials | Owner Only (ID: USER_ID_HERE) |

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
5. Bot announces in the channel: `@User just rolled [rarity emoji] [Fruit] [fruit emoji] ([Rarity])!`
6. Bot starts 2-hour countdown for next reminder

### Automatic Reminders
- Bot checks every minute for users whose cooldown is complete
- Sends notification to designated channel with user mention
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

The bot includes all current Blox Fruits (46 total) organized by rarity:

### ⚪ Common (7 fruits)
Rocket, Spin, Blade, Spring, Bomb, Smoke, Spike

### 🔵 Uncommon (6 fruits)
Ice, Sand, Dark, Eagle, Diamond, Flame

### 🟣 Rare (4 fruits)
Magma, Light, Rubber, Ghost

### 🔮 Legendary (11 fruits)
Portal, Lightning, Pain, Blizzard, Quake, Buddha, Love, Creation, Spider, Sound, Phoenix

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
- **Stats Dashboard**: Bar chart showing distribution of rolls by rarity

---

## 🛠️ Technical Details

### Built With
- **discord.py** - Discord API wrapper
- **aiohttp** - Async HTTP server for web dashboard
- **Supabase PostgreSQL** - Cloud-hosted database for persistent storage
- **psycopg2** - PostgreSQL adapter with connection pooling
- **Chart.js** - Interactive charts for stats dashboard
- **Python 3.8+** - Programming language

### Database Schema

The bot uses Supabase PostgreSQL with three main tables:

```sql
-- Users table
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    total_rolls INTEGER DEFAULT 0,
    last_roll_time TIMESTAMP WITH TIME ZONE,
    next_roll_time TIMESTAMP WITH TIME ZONE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rolls table (NOW INCLUDES RARITY)
CREATE TABLE rolls (
    roll_id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    fruit_name TEXT NOT NULL,
    fruit_rarity TEXT NOT NULL,
    rolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

-- Command usage tracking
CREATE TABLE command_usage (
    id SERIAL PRIMARY KEY,
    command_name TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_rolls_user_id ON rolls(user_id);
CREATE INDEX IF NOT EXISTS idx_rolls_rolled_at ON rolls(rolled_at);
CREATE INDEX IF NOT EXISTS idx_rolls_rarity ON rolls(fruit_rarity);
CREATE INDEX IF NOT EXISTS idx_command_usage_used_at ON command_usage(used_at);
CREATE INDEX IF NOT EXISTS idx_users_next_roll_time ON users(next_roll_time);
```

### Environment Variables

Create a `.env` file with the following:

```env
DISCORD_TOKEN=your_bot_token_here
SUPABASE_URL=postgresql://user:pass@host:port/database
STATS_USER=your_stats_username
STATS_PASS=your_stats_password
PORT=10000
```

**Important:**
- `DISCORD_TOKEN` - **Required** for bot to function
- `SUPABASE_URL` - **Required** PostgreSQL connection string from Supabase
- `STATS_USER` - Username for stats page (default: `admin`)
- `STATS_PASS` - Password for stats page (default: `changeme`)
- `PORT` - Web server port (default: `10000`)

### Supabase Setup
1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Project Settings → Database
4. Copy the connection string (URI format)
5. Add it to your `.env` file as `SUPABASE_URL`
6. The bot will automatically create all required tables on first run

### Bot Permissions Required
- Send Messages
- Embed Links
- Use Slash Commands
- Read Message History
- Mention @everyone, @here, and All Roles (for notifications)

---

## 📊 Statistics Tracking

### What Gets Tracked
- **Total Rolls**: Global count of all fruit rolls
- **Per-User Rolls**: Individual roll counts with rarity breakdown
- **Rarity Distribution**: Chart showing how many of each rarity have been rolled
- **Active Users**: Number of users who have logged at least one roll
- **Next Roll Times**: Countdown timers for each user
- **Notification Status**: Who has reminders enabled/disabled
- **Command Usage**: Tracking of all command executions

### Stats Page Access
1. Navigate to `http://your-bot-url/stats`
2. Enter credentials from `/stats-link` command
3. View comprehensive dashboard with:
   - Real-time statistics
   - Fruit rarity distribution chart (Common → Mythic)
   - User list sorted by next roll time
   - Recent roll information
   - Notification status for each user

---

## 🔄 Automatic Systems

### Notification Loop
- Runs every 1 minute
- Checks all users' `next_roll_time`
- Sends channel notifications to eligible users with mentions
- Automatically clears cooldown after reminder sent
- Only notifies users with notifications enabled

### Database Connection Pooling
- Connection pool (1-20 connections) for optimal performance
- Automatic connection management
- Graceful error handling
- Connection cleanup on shutdown

### Web Server
- Always-on HTTP server for monitoring
- `/health` endpoint responds to all requests (for UptimeRobot)
- `/stats` endpoint protected by HTTP Basic Auth
- `/favicon.ico` endpoint for custom favicon support
- Auto-refresh every 30 seconds on stats page

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
- **Custom favicon support** for browser tabs

### Color Palette
- Primary: `#06b6d4` (Cyan)
- Background: `#0a1929` → `#1a2f42` → `#0d3a5c` (Gradient)
- Cards: `rgba(13, 58, 92, 0.4)` (Translucent blue)
- Accents: `#3b82f6` (Blue), `#10b981` (Green)
- Text: `#fff` (White), `#94a3b8` (Gray)

### Rarity Colors
- Common: `#808080` (Gray)
- Uncommon: `#3b82f6` (Blue)
- Rare: `#9333ea` (Purple)
- Legendary: `#ec4899` (Pink/Magenta)
- Mythic: `#dc2626` (Red)

---

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install discord.py aiohttp python-dotenv psycopg2-binary

# Create .env file with your credentials
cat > .env << EOF
DISCORD_TOKEN=your_token
SUPABASE_URL=your_supabase_url
STATS_USER=admin
STATS_PASS=changeme
PORT=10000
EOF

# Run the bot
python main.py
```

### Production (Render.com)

#### Step 1: Prepare Your Repository
1. Fork or push this repository to GitHub
2. Ensure `main.py` and `requirements.txt` are in the root directory
3. Make sure `.env` is in your `.gitignore` (never commit secrets!)

#### Step 2: Create Supabase Database
1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Choose an organization and set project details:
   - **Name**: blox-fruits-bot-db (or your choice)
   - **Database Password**: Generate a strong password (save this!)
   - **Region**: Choose closest to your users
4. Wait for project to initialize (~2 minutes)
5. Go to **Project Settings** → **Database**
6. Copy the **Connection String** (URI format):
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
7. Save this for later - you'll need it!

#### Step 3: Create Render Web Service
1. Go to [render.com](https://render.com) and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository from the list
5. Configure the service:
   - **Name**: `blox-fruits-bot` (or your choice)
   - **Region**: Choose same as Supabase if possible
   - **Branch**: `main`
   - **Root Directory**: Leave blank (unless code is in subfolder)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Instance Type**: `Free` (or paid for better performance)

#### Step 4: Add Environment Variables
In the Render dashboard, scroll to **Environment Variables** and add:

| Key | Value | Notes |
|-----|-------|-------|
| `DISCORD_TOKEN` | `your_bot_token_here` | From Discord Developer Portal |
| `SUPABASE_URL` | `postgresql://postgres:...` | Your Supabase connection string |
| `STATS_USER` | `admin` | Username for stats page |
| `STATS_PASS` | `your_secure_password` | Strong password for stats page |
| `PORT` | `10000` | Web server port (Render auto-assigns) |

**Getting Your Discord Token:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application (or create one)
3. Go to **Bot** section
4. Click **"Reset Token"** and copy it
5. Paste into Render environment variables

#### Step 5: Deploy
1. Click **"Create Web Service"**
2. Render will automatically deploy your bot
3. Watch the logs for:
   ```
   ✅ Supabase connection pool created
   ✅ Supabase database initialized successfully
   🦈 Connected to Supabase PostgreSQL
   ✅ Synced X slash command(s)
   🍎 Fruit Roll Tracker Ready!
   ```
4. Your bot should now be online in Discord!

#### Step 6: Get Your Bot URL
1. After deployment, Render assigns you a URL:
   ```
   https://blox-fruits-bot-xxxx.onrender.com
   ```
2. Test the health check:
   ```
   https://your-bot-url.onrender.com/health
   ```
3. You should see the underwater-themed health page!

#### Step 7: Invite Bot to Discord
1. Go to Discord Developer Portal → Your App → **OAuth2** → **URL Generator**
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
3. Select bot permissions:
   - ✅ Send Messages
   - ✅ Embed Links
   - ✅ Read Message History
   - ✅ Mention Everyone
   - ✅ Use Slash Commands
4. Copy the generated URL and open it in browser
5. Select your server and authorize

#### Step 8: Configure Bot Settings
1. Update `main.py` with your server details:
   ```python
   OWNER_ID = YOUR_DISCORD_USER_ID
   NOTIFICATION_CHANNEL_ID = YOUR_CHANNEL_ID
   NOTIFICATION_USERS = [USER_ID_1, USER_ID_2, ...]
   ```
2. Commit and push changes to GitHub
3. Render will automatically redeploy

#### Step 9: Keep It Alive (Optional but Recommended)
Render free tier spins down after 15 minutes of inactivity. Set up UptimeRobot:

1. Go to [uptimerobot.com](https://uptimerobot.com) and sign up
2. Click **"Add New Monitor"**
3. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Blox Fruits Bot
   - **URL**: `https://your-bot-url.onrender.com/health`
   - **Monitoring Interval**: 5 minutes
4. Click **"Create Monitor"**
5. Your bot will now stay awake 24/7!

#### Troubleshooting Render Deployment

**Build Failed:**
- Check `requirements.txt` includes all dependencies
- Verify Python version compatibility
- Check build logs for specific errors

**Bot Not Starting:**
- Verify all environment variables are set correctly
- Check `DISCORD_TOKEN` is valid
- Ensure `SUPABASE_URL` connection string is correct
- Review runtime logs in Render dashboard

**Database Connection Errors:**
- Verify Supabase project is running (not paused)
- Check connection string format is correct
- Ensure IP restrictions aren't blocking Render
- Test connection string with a local Python script first

**Bot Goes Offline:**
- Set up UptimeRobot to prevent spin-down
- Consider upgrading to paid Render plan for always-on
- Check Render service logs for crashes

**Commands Not Syncing:**
- Wait up to 1 hour for Discord to sync globally
- Try kicking and re-inviting the bot
- Check bot has proper permissions in server
- Verify bot has `applications.commands` scope

---

## 🔒 Security Features

### Stats Page Protection
- HTTP Basic Authentication required
- Credentials stored in environment variables
- No unauthorized access to user data
- 401 response with auth challenge if credentials invalid

### Database Security
- Supabase PostgreSQL with built-in security
- Connection pooling with proper cleanup
- Parameterized queries prevent SQL injection
- Foreign key constraints prevent orphaned data
- Indexed columns for optimal performance

### User Privacy
- Roll history only visible to the user
- Channel notifications only ping the specific user
- Stats page requires authentication
- No public exposure of sensitive user data

---

## 📋 Planned Features

### Future Enhancements
- [ ] Weekly roll statistics per user
- [ ] Server leaderboards (most rolls, best luck)
- [ ] Export roll history to CSV
- [ ] Custom notification timing (user preference)
- [ ] Integration with other Blox Fruits features
- [ ] Role rewards for milestone rolls (10, 50, 100, etc.)
- [ ] Streak tracking (consecutive daily rolls)
- [ ] Trading system integration

---

## 🐛 Troubleshooting

### Bot Not Responding
1. Check bot is online in Discord
2. Verify `DISCORD_TOKEN` in `.env` file
3. Check bot has required permissions
4. Run `/stats-link` to verify bot is functioning
5. Check Supabase database connection

### Notifications Not Working
1. Check you're in the notification channel
2. Verify you're not in sleep mode (`/awake`)
3. Check you've logged at least one roll
4. Ensure 2 hours have passed since last roll
5. Verify `NOTIFICATION_CHANNEL_ID` is correct in code

### Stats Page Not Loading
1. Verify `STATS_USER` and `STATS_PASS` in `.env`
2. Check HTTP Basic Auth credentials
3. Try clearing browser cache
4. Ensure web server is running (check logs)
5. Check favicon route is responding

### Database Issues
1. Verify `SUPABASE_URL` is correct
2. Check Supabase project is running
3. Ensure connection pool isn't exhausted
4. Check Supabase logs for errors
5. Verify tables were created (check startup logs)

### Supabase Connection Errors
```
❌ Supabase connection error: ...
```
**Solutions:**
1. Double-check your `SUPABASE_URL` format
2. Ensure your Supabase project isn't paused
3. Check if you've exceeded free tier limits
4. Verify network connectivity
5. Try recreating the connection string from Supabase dashboard

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
- **Database Tables**: 3 (users, rolls, command_usage)
- **Tracked Fruits**: 46 across 5 rarity tiers
- **Auto-Notifications**: Yes (2-hour intervals)
- **Web Endpoints**: 4 (`/`, `/health`, `/stats`, `/favicon.ico`)
- **Lines of Code**: ~1800+
- **Database**: Supabase PostgreSQL (Cloud-hosted)

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
- **Supabase** - For the reliable PostgreSQL hosting
- **Chart.js** - For beautiful data visualization
- **SorynTech Community** - For testing and feedback

---

**Made with 💙 by SorynTech** 🦈

*Part of the SorynTech Bot Suite - Professional Discord automation with style*

---

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/SorynTech/Blox-Fruits-Notifier/issues)
- **Discord**: ✉️ soryntech | Server: Coming soon
- **Documentation**: This README + in-code comments

---

## ⚙️ Configuration Reference

### Notification Channel
Edit the channel ID in `main.py`:
```python
NOTIFICATION_CHANNEL_ID = USER_ID_HERE  # Your channel ID
```

### Startup Notification Recipients
Edit these user IDs in `main.py`:
```python
NOTIFICATION_USERS = [
    USER_ID_HERE,   # User 1
    USER_ID_HERE,   # User 2
    USER_ID_HERE,   # User 3
    USER_ID_HERE    # User 4
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
OWNER_ID = USER_ID_HERE  # Your ID here
```

### Database Connection Pool
Adjust pool size in `main.py`:
```python
db_pool = SimpleConnectionPool(1, 20, SUPABASE_URL)  # Min 1, Max 20
```

---

## 🆕 Recent Updates

### v2.0 - Supabase Migration
- ✅ Migrated from SQLite to Supabase PostgreSQL
- ✅ Added connection pooling for better performance
- ✅ Added rarity tracking to rolls table
- ✅ Added rarity distribution chart to stats page
- ✅ Added favicon support to all web pages
- ✅ Improved error handling for database operations
- ✅ Added comprehensive indexing for faster queries

### v1.0 - Initial Release
- 🎲 Full fruit roll tracking system
- 🔔 Automatic notification system
- 📊 Stats dashboard with authentication
- 🦈 Beautiful underwater theme
- 📝 Complete command suite

---

**🦈 Swim with the sharks, roll with the best 🎲**