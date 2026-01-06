import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from aiohttp import web
import asyncio
from dotenv import load_dotenv
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from typing import Optional, List, Dict
import logging
import sys

# ============================================================================
# LOGGING CONFIGURATION - VERBOSE MODE
# ============================================================================

# Configure logging with colors and detailed format
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[38;5;46m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s [%(levelname)s] %(name)s: %(message)s" + reset,
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Set up root logger
logger = logging.getLogger('BloxFruitsBot')
logger.setLevel(logging.DEBUG)

# Console handler with colors
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

# Discord.py library logging
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
discord_handler = logging.StreamHandler(sys.stdout)
discord_handler.setFormatter(ColoredFormatter())
discord_logger.addHandler(discord_handler)

logger.info("=" * 80)
logger.info("🦈 BLOX FRUITS ROLL TRACKER - STARTING UP")
logger.info("=" * 80)

# Load environment variables from .env file
logger.info("📂 Loading environment variables...")
load_dotenv()
logger.info("✅ Environment variables loaded")

# Bot setup with necessary intents
logger.info("🤖 Configuring Discord bot intents...")
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
logger.info("✅ Bot intents configured: message_content=True, guilds=True, members=True")

bot = commands.Bot(command_prefix='!', intents=intents)
logger.info("✅ Bot instance created with prefix '!'")

# Configuration
OWNER_ID = 447812883158532106
DAD_USER_ID = 447812883158532106  # Special display name for this user
NOTIFICATION_USERS = [447812883158532106, 778645525499084840]
NOTIFICATION_CHANNEL_ID = 1431308135091671132
ROLL_COOLDOWN_HOURS = 2
STATS_USER = os.getenv('STATS_USER', 'admin')
STATS_PASS = os.getenv('STATS_PASS', 'changeme')

logger.info(f"⚙️  Configuration loaded:")
logger.info(f"   - Owner ID: {OWNER_ID}")
logger.info(f"   - Notification Users: {len(NOTIFICATION_USERS)} users")
logger.info(f"   - Notification Channel: {NOTIFICATION_CHANNEL_ID}")
logger.info(f"   - Roll Cooldown: {ROLL_COOLDOWN_HOURS} hours")
logger.info(f"   - Stats Auth: {STATS_USER}:{'*' * len(STATS_PASS)}")
logger.info(f"   - Dad User ID: {DAD_USER_ID}")

# Ignored user IDs
IGNORED_ALTS = [1364903422129733654, 1454897720610521251, 1127038223013658694]  # Added to DB but suspended
IGNORED_BOTS = [1455626479940538533, 1451606115249815663, 443545183997657120, 762217899355013120]  # Completely skipped
IGNORED_USERS = set(IGNORED_ALTS + IGNORED_BOTS)  # Combined set for reference
logger.info(f"   - Alt Accounts (suspended): {len(IGNORED_ALTS)}")
logger.info(f"   - Bot Accounts (skipped): {len(IGNORED_BOTS)}")

# Supabase Database Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    logger.critical("❌ SUPABASE_URL not found in environment variables!")
    logger.critical("Please add your Supabase connection URL to your environment variables.")
    exit(1)
else:
    logger.info("✅ Supabase URL found in environment")

# Connection pool for Supabase
db_pool = None

# Statistics tracking
stats = {
    'bot_start_time': None,
    'total_rolls': 0,
    'guilds_count': 0,
    'active_users': 0,
    'command_usage': {}
}

logger.info("📊 Statistics tracking initialized")


def get_display_name(user_id: int, username: str = None) -> str:
    """Get display name for user (Daddy for special user, otherwise username)"""
    if user_id == DAD_USER_ID:
        return "Daddy"
    return username if username else f"User {user_id}"


def get_db_connection():
    """Get a database connection from the pool"""
    logger.debug("🔌 Acquiring database connection from pool...")
    return db_pool.getconn()


def return_db_connection(conn):
    """Return a connection to the pool"""
    logger.debug("🔌 Returning database connection to pool...")
    db_pool.putconn(conn)


# Database setup
def init_database():
    """Initialize Supabase database with required tables"""
    global db_pool
    
    logger.info("=" * 80)
    logger.info("🗄️  INITIALIZING DATABASE")
    logger.info("=" * 80)

    try:
        # Create connection pool for Supabase
        logger.info("🔄 Creating Supabase connection pool...")
        db_pool = SimpleConnectionPool(1, 20, SUPABASE_URL)
        logger.info("✅ Supabase connection pool created (min=1, max=20)")

        logger.info("🔌 Testing database connection...")
        conn = get_db_connection()
        cur = conn.cursor()
        logger.info("✅ Database connection successful")

        # Users table
        logger.info("📋 Creating 'users' table if not exists...")
        cur.execute('''CREATE TABLE IF NOT EXISTS users
                       (
                           user_id
                           BIGINT
                           PRIMARY
                           KEY,
                           username
                           TEXT
                           NOT
                           NULL,
                           total_rolls
                           INTEGER
                           DEFAULT
                           0,
                           last_roll_time
                           TIMESTAMP
                           WITH
                           TIME
                           ZONE,
                           next_roll_time
                           TIMESTAMP
                           WITH
                           TIME
                           ZONE,
                           notifications_enabled
                           BOOLEAN
                           DEFAULT
                           TRUE,
                           created_at
                           TIMESTAMP
                           WITH
                           TIME
                           ZONE
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )''')
        logger.info("✅ 'users' table ready")
        
        # Add suspended column if it doesn't exist
        try:
            cur.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS suspended BOOLEAN DEFAULT FALSE')
            logger.info("✅ 'suspended' column added/verified")
        except Exception as e:
            logger.debug(f"Suspended column may already exist: {e}")

        # Rolls table - NOW INCLUDES RARITY
        logger.info("📋 Creating 'rolls' table if not exists...")
        cur.execute('''CREATE TABLE IF NOT EXISTS rolls
        (
            roll_id
            SERIAL
            PRIMARY
            KEY,
            user_id
            BIGINT
            NOT
            NULL,
            fruit_name
            TEXT
            NOT
            NULL,
            fruit_rarity
            TEXT
            NOT
            NULL,
            rolled_at
            TIMESTAMP
            WITH
            TIME
            ZONE
            DEFAULT
            CURRENT_TIMESTAMP,
            FOREIGN
            KEY
                       (
            user_id
                       ) REFERENCES users
                       (
                           user_id
                       )
            )''')
        logger.info("✅ 'rolls' table ready")

        # Command usage tracking
        logger.info("📋 Creating 'command_usage' table if not exists...")
        cur.execute('''CREATE TABLE IF NOT EXISTS command_usage
                       (
                           id
                           SERIAL
                           PRIMARY
                           KEY,
                           command_name
                           TEXT
                           NOT
                           NULL,
                           user_id
                           BIGINT
                           NOT
                           NULL,
                           used_at
                           TIMESTAMP
                           WITH
                           TIME
                           ZONE
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )''')
        logger.info("✅ 'command_usage' table ready")

        # Create indexes for better performance
        logger.info("📊 Creating database indexes...")
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_rolls_user_id ON rolls(user_id)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_rolls_rolled_at ON rolls(rolled_at)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_rolls_rarity ON rolls(fruit_rarity)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_command_usage_used_at ON command_usage(used_at)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_users_next_roll_time ON users(next_roll_time)''')
        logger.info("✅ All indexes created")

        conn.commit()
        logger.info("✅ Database changes committed")
        cur.close()
        return_db_connection(conn)

        logger.info("=" * 80)
        logger.info("✅ SUPABASE DATABASE INITIALIZED SUCCESSFULLY")
        logger.info("🦈 Connected to Supabase PostgreSQL")
        logger.info("=" * 80)

    except Exception as e:
        logger.critical(f"❌ Supabase connection error: {e}")
        logger.critical("Make sure your SUPABASE_URL is correct and the database is running.")
        raise


# Database helper functions
def get_user(user_id: int) -> Optional[Dict]:
    """Get user from database"""
    try:
        logger.debug(f"👤 Fetching user data for ID: {user_id}")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        cur.close()
        return_db_connection(conn)

        if row:
            logger.debug(f"✅ User found: {dict(row).get('username')}")
            return dict(row)
        logger.debug(f"⚠️  User not found: {user_id}")
        return None
    except Exception as e:
        logger.error(f"❌ Error in get_user: {e}")
        return None


def create_or_update_user(user_id: int, username: str):
    """Create or update user in database"""
    try:
        logger.info(f"👤 Creating/updating user: {username} (ID: {user_id})")
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if user exists
        cur.execute('SELECT total_rolls, notifications_enabled FROM users WHERE user_id = %s', (user_id,))
        existing = cur.fetchone()

        if existing:
            logger.debug(f"📝 Updating existing user: {username}")
            cur.execute('UPDATE users SET username = %s WHERE user_id = %s', (username, user_id))
        else:
            logger.info(f"✨ Creating new user: {username}")
            cur.execute('''INSERT INTO users (user_id, username, total_rolls, notifications_enabled)
                           VALUES (%s, %s, 0, TRUE)''', (user_id, username))

        conn.commit()
        cur.close()
        return_db_connection(conn)
        logger.debug(f"✅ User operation complete: {username}")
    except Exception as e:
        logger.error(f"❌ Error in create_or_update_user: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)


def log_roll(user_id: int, username: str, fruit_name: str):
    """Log a fruit roll in the database"""
    now = datetime.now(timezone.utc)
    next_roll = now + timedelta(hours=ROLL_COOLDOWN_HOURS)

    # Get fruit rarity
    fruit_rarity = FRUITS_DATA.get(fruit_name, {}).get('rarity', 'Unknown')
    
    display_name = get_display_name(user_id, username)
    logger.info(f"🎲 Logging roll: {display_name} ({username}) -> {fruit_name} ({fruit_rarity})")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Update user
        logger.debug(f"📝 Updating user stats for {display_name} ({username})")
        cur.execute('''UPDATE users
                       SET total_rolls    = total_rolls + 1,
                           last_roll_time = %s,
                           next_roll_time = %s,
                           username       = %s
                       WHERE user_id = %s''',
                    (now, next_roll, username, user_id))

        # Log the roll WITH RARITY
        logger.debug(f"📝 Inserting roll record")
        cur.execute('INSERT INTO rolls (user_id, fruit_name, fruit_rarity, rolled_at) VALUES (%s, %s, %s, %s)',
                    (user_id, fruit_name, fruit_rarity, now))

        conn.commit()
        cur.close()
        return_db_connection(conn)

        stats['total_rolls'] += 1
        logger.info(f"✅ Roll logged successfully! Total rolls: {stats['total_rolls']}")
        logger.info(f"⏰ Next roll for {display_name}: {next_roll.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    except Exception as e:
        logger.error(f"❌ Error in log_roll: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)


def get_user_rolls(user_id: int) -> List[Dict]:
    """Get all rolls for a user"""
    try:
        logger.debug(f"📊 Fetching roll history for user ID: {user_id}")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''SELECT fruit_name, rolled_at
                       FROM rolls
                       WHERE user_id = %s
                       ORDER BY rolled_at DESC''', (user_id,))
        rows = cur.fetchall()
        cur.close()
        return_db_connection(conn)

        logger.debug(f"✅ Found {len(rows)} rolls for user")
        return [{'fruit': row['fruit_name'], 'time': row['rolled_at']} for row in rows]
    except Exception as e:
        logger.error(f"❌ Error in get_user_rolls: {e}")
        return []


def get_all_users() -> List[Dict]:
    """Get all users from database"""
    try:
        logger.debug("👥 Fetching all users from database")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''SELECT user_id,
                              username,
                              total_rolls,
                              last_roll_time,
                              next_roll_time,
                              notifications_enabled
                       FROM users''')
        rows = cur.fetchall()
        cur.close()
        return_db_connection(conn)

        logger.debug(f"✅ Fetched {len(rows)} users")
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Error in get_all_users: {e}")
        return []


def toggle_notifications(user_id: int, enabled: bool):
    """Toggle notifications for a user"""
    try:
        status = "ENABLED" if enabled else "DISABLED"
        logger.info(f"🔔 Setting notifications {status} for user ID: {user_id}")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET notifications_enabled = %s WHERE user_id = %s',
                    (enabled, user_id))
        conn.commit()
        cur.close()
        return_db_connection(conn)
        logger.debug(f"✅ Notifications toggled successfully")
    except Exception as e:
        logger.error(f"❌ Error in toggle_notifications: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)


def log_command_usage(command_name: str, user_id: int):
    """Log command usage for statistics"""
    try:
        logger.debug(f"📊 Logging command usage: /{command_name} by user {user_id}")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO command_usage (command_name, user_id) VALUES (%s, %s)',
                    (command_name, user_id))
        conn.commit()
        cur.close()
        return_db_connection(conn)

        if command_name not in stats['command_usage']:
            stats['command_usage'][command_name] = 0
        stats['command_usage'][command_name] += 1
        logger.debug(f"✅ Command logged (total for /{command_name}: {stats['command_usage'][command_name]})")
    except Exception as e:
        logger.error(f"❌ Error in log_command_usage: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)


def get_rarity_distribution() -> Dict:
    """Get distribution of fruit rarities rolled"""
    try:
        logger.debug("📊 Fetching rarity distribution")
        conn = get_db_connection()
        cur = conn.cursor()

        # Get count of rolls by rarity
        cur.execute('''SELECT fruit_rarity,
                              COUNT(*) as count
                       FROM rolls
                       GROUP BY fruit_rarity
                       ORDER BY
                           CASE fruit_rarity
                           WHEN 'Common' THEN 1
                           WHEN 'Uncommon' THEN 2
                           WHEN 'Rare' THEN 3
                           WHEN 'Legendary' THEN 4
                           WHEN 'Mythic' THEN 5
                           ELSE 6
        END''')

        rarity_data = {}
        for row in cur.fetchall():
            rarity_data[row[0]] = row[1]

        cur.close()
        return_db_connection(conn)
        logger.debug(f"✅ Rarity distribution: {rarity_data}")
        return rarity_data
    except Exception as e:
        logger.error(f"❌ Error in get_rarity_distribution: {e}")
        return {}


def sync_guild_members_to_db(guild):
    """Sync all guild members to database (bots excluded, alts added as suspended)"""
    logger.info(f"🔄 Syncing members from guild: {guild.name}")
    
    synced_count = 0
    skipped_count = 0
    
    for member in guild.members:
        # Skip bots completely
        if member.bot:
            skipped_count += 1
            continue
        
        # Alts are added but suspended
        is_alt = member.id in IGNORED_ALTS
        
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT user_id FROM users WHERE user_id = %s', (member.id,))
            exists = cur.fetchone()
            
            if not exists:
                # Add user - alts are suspended, regular users are not
                cur.execute('''INSERT INTO users (user_id, username, total_rolls, notifications_enabled, suspended)
                               VALUES (%s, %s, 0, TRUE, %s)''', (member.id, member.name, is_alt))
                conn.commit()
                synced_count += 1
                if is_alt:
                    logger.info(f"✨ Added ALT member (suspended): {member.name} (ID: {member.id})")
                else:
                    logger.info(f"✨ Added new member: {member.name} (ID: {member.id})")
            else:
                cur.execute('UPDATE users SET username = %s WHERE user_id = %s', (member.name, member.id))
                conn.commit()
            
            cur.close()
            return_db_connection(conn)
        except Exception as e:
            logger.error(f"❌ Error syncing member {member.name}: {e}")
            if 'conn' in locals():
                try:
                    conn.rollback()
                    return_db_connection(conn)
                except:
                    pass
    
    logger.info(f"✅ Member sync complete: {synced_count} added, {skipped_count} skipped (bots)")
    return synced_count, skipped_count


def suspend_user(user_id: int, suspend: bool = True):
    """Suspend or unsuspend a user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT username FROM users WHERE user_id = %s', (user_id,))
        user = cur.fetchone()
        
        if not user:
            cur.close()
            return_db_connection(conn)
            return False, "User not found in database"
        
        cur.execute('UPDATE users SET suspended = %s WHERE user_id = %s', (suspend, user_id))
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        status = "SUSPENDED" if suspend else "UNSUSPENDED"
        logger.info(f"✅ User {user[0]} (ID: {user_id}) {status}")
        return True, f"User {user[0]} {status.lower()}"
    except Exception as e:
        logger.error(f"❌ Error in suspend_user: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
                return_db_connection(conn)
            except:
                pass
        return False, f"Error: {str(e)}"


def get_suspended_users():
    """Get all suspended users"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''SELECT user_id, username, total_rolls, last_roll_time, created_at
                       FROM users WHERE suspended = TRUE ORDER BY username''')
        rows = cur.fetchall()
        cur.close()
        return_db_connection(conn)
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"❌ Error getting suspended users: {e}")
        return []


# Fruit list with rarities (Blox Fruits)
logger.info("🍎 Loading fruit database...")
FRUITS_DATA = {
    # Common (Gray)
    "Rocket": {"rarity": "Common", "color": 0x808080, "emoji": "🚀"},
    "Spin": {"rarity": "Common", "color": 0x808080, "emoji": "🌀"},
    "Blade": {"rarity": "Common", "color": 0x808080, "emoji": "⚔️"},
    "Spring": {"rarity": "Common", "color": 0x808080, "emoji": "🌸"},
    "Bomb": {"rarity": "Common", "color": 0x808080, "emoji": "💣"},
    "Smoke": {"rarity": "Common", "color": 0x808080, "emoji": "💨"},
    "Spike": {"rarity": "Common", "color": 0x808080, "emoji": "🦔"},

    # Uncommon (Blue)
    "Ice": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "🧊"},
    "Sand": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "🏖️"},
    "Dark": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "🌑"},
    "Eagle": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "🦅"},
    "Diamond": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "💎"},
    "Flame": {"rarity": "Uncommon", "color": 0x3b82f6, "emoji": "🔥"},

    # Rare (Purple)
    "Magma": {"rarity": "Rare", "color": 0x9333ea, "emoji": "🌋"},
    "Light": {"rarity": "Rare", "color": 0x9333ea, "emoji": "💡"},
    "Rubber": {"rarity": "Rare", "color": 0x9333ea, "emoji": "🎈"},
    "Ghost": {"rarity": "Rare", "color": 0x9333ea, "emoji": "👻"},

    # Legendary (Pink/Magenta)
    "Portal": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🌀"},
    "Lightning": {"rarity": "Legendary", "color": 0xec4899, "emoji": "⚡"},
    "Pain": {"rarity": "Legendary", "color": 0xec4899, "emoji": "💢"},
    "Blizzard": {"rarity": "Legendary", "color": 0xec4899, "emoji": "❄️"},
    "Quake": {"rarity": "Legendary", "color": 0xec4899, "emoji": "⚡"},
    "Buddha": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🙏"},
    "Love": {"rarity": "Legendary", "color": 0xec4899, "emoji": "💖"},
    "Creation": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🎨"},
    "Spider": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🕷️"},
    "Sound": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🔊"},
    "Phoenix": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🔥"},

    # Mythic (Red)
    "Gravity": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🌌"},
    "Mammoth": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🦣"},
    "T-Rex": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🦖"},
    "Dough": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🍩"},
    "Shadow": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "👤"},
    "Venom": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "☠️"},
    "Gas": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "☁️"},
    "Spirit": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "👻"},
    "Tiger": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🐯"},
    "Yeti": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "❄️"},
    "Kitsune": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🦊"},
    "Control": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🎮"},
    "Dragon": {"rarity": "Mythic", "color": 0xdc2626, "emoji": "🐉"}
}

# Get sorted list of fruits
FRUITS = list(FRUITS_DATA.keys())

# Rarity groups for organized display
RARITY_GROUPS = {
    "Common": [name for name, data in FRUITS_DATA.items() if data["rarity"] == "Common"],
    "Uncommon": [name for name, data in FRUITS_DATA.items() if data["rarity"] == "Uncommon"],
    "Rare": [name for name, data in FRUITS_DATA.items() if data["rarity"] == "Rare"],
    "Legendary": [name for name, data in FRUITS_DATA.items() if data["rarity"] == "Legendary"],
    "Mythic": [name for name, data in FRUITS_DATA.items() if data["rarity"] == "Mythic"]
}

# Rarity colors for Discord embeds
RARITY_COLORS = {
    "Common": 0x808080,
    "Uncommon": 0x3b82f6,
    "Rare": 0x9333ea,
    "Legendary": 0xec4899,
    "Mythic": 0xdc2626
}

logger.info(f"✅ Loaded {len(FRUITS_DATA)} fruits across {len(RARITY_GROUPS)} rarity tiers")


# Fruit selection view with buttons - supports multiple pages
class FruitSelectionView(discord.ui.View):
    def __init__(self, user_id: int, fruits_list: List[str], page_name: str, total_pages: int, current_page: int):
        super().__init__(timeout=180)  # 3 minute timeout
        self.user_id = user_id
        self.selected_fruit = None
        self.page_name = page_name
        self.total_pages = total_pages
        self.current_page = current_page
        
        logger.debug(f"🎮 Created FruitSelectionView for user {user_id}: {page_name}")

        # Create buttons for fruits (up to 20 buttons per page, 4 rows of 5)
        for i, fruit in enumerate(fruits_list[:20]):
            fruit_data = FRUITS_DATA[fruit]
            button = discord.ui.Button(
                label=fruit,
                style=discord.ButtonStyle.primary,
                custom_id=f"fruit_{fruit}",
                emoji=fruit_data["emoji"],
                row=i // 5  # 5 buttons per row
            )
            button.callback = self.create_callback(fruit)
            self.add_item(button)

    def create_callback(self, fruit_name: str):
        async def callback(interaction: discord.Interaction):
            logger.info(f"🎲 Fruit button clicked: {fruit_name} by {interaction.user} (ID: {interaction.user.id})")
            
            if interaction.user.id != self.user_id:
                logger.warning(f"⚠️  Unauthorized button click by {interaction.user.id}, expected {self.user_id}")
                await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
                return

            self.selected_fruit = fruit_name
            self.stop()

            # Get fruit data
            fruit_data = FRUITS_DATA[fruit_name]
            
            logger.info(f"✅ Valid fruit selection: {fruit_name} ({fruit_data['rarity']})")

            # Log the roll
            log_roll(self.user_id, interaction.user.name, fruit_name)

            # Send public message
            channel = interaction.channel
            rarity_emoji = {
                "Common": "⚪",
                "Uncommon": "🔵",
                "Rare": "🟣",
                "Legendary": "🟣",
                "Mythic": "🔴"
            }
            rarity_display = rarity_emoji.get(fruit_data["rarity"], "⚪")

            # Get display name for public message
            display_name = get_display_name(self.user_id, interaction.user.name)

            logger.info(f"📢 Broadcasting roll to channel: {channel.name}")
            await channel.send(
                f"🎲 **{display_name}** just rolled {rarity_display} **{fruit_name}** {fruit_data['emoji']} ({fruit_data['rarity']})!")

            # Update ephemeral message
            next_roll_time = datetime.now(timezone.utc) + timedelta(hours=ROLL_COOLDOWN_HOURS)
            logger.debug(f"📝 Updating ephemeral message for user")
            await interaction.response.edit_message(
                content=f"✅ Logged your roll: {fruit_data['emoji']} **{fruit_name}** ({fruit_data['rarity']})\n⏰ Next roll available <t:{int(next_roll_time.timestamp())}:R>",
                view=None
            )
            logger.info(f"✅ Roll complete for {interaction.user}")

        return callback


class PageSelectionView(discord.ui.View):
    """Initial view to select sorting method"""

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        logger.debug(f"🎮 Created PageSelectionView for user {user_id}")

    @discord.ui.button(label="📝 Alphabetical Order", style=discord.ButtonStyle.primary, row=0)
    async def alphabetical(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"📝 Alphabetical sorting selected by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            logger.warning(f"⚠️  Unauthorized button click")
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        # Show alphabetical pages
        view = AlphabeticalPagesView(self.user_id)
        embed = discord.Embed(
            title="🎲 Select Your Fruit Roll - Alphabetical",
            description="Choose a page to view fruits in alphabetical order:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        logger.debug("✅ Switched to alphabetical pages view")

    @discord.ui.button(label="✨ Sort by Rarity", style=discord.ButtonStyle.secondary, row=0)
    async def by_rarity(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"✨ Rarity sorting selected by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            logger.warning(f"⚠️  Unauthorized button click")
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        # Show rarity pages
        view = RaritySelectionView(self.user_id)
        embed = discord.Embed(
            title="🎲 Select Your Fruit Roll - By Rarity",
            description="Choose a rarity category:",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        logger.debug("✅ Switched to rarity selection view")


class AlphabeticalPagesView(discord.ui.View):
    """View for alphabetical pagination"""

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

        # Split fruits into pages of 20
        self.pages = []
        fruits_sorted = sorted(FRUITS)
        for i in range(0, len(fruits_sorted), 20):
            self.pages.append(fruits_sorted[i:i + 20])
        
        logger.debug(f"📄 Created {len(self.pages)} alphabetical pages")

    @discord.ui.button(label="Page 1 (Blade-Gas)", style=discord.ButtonStyle.primary, row=0)
    async def page1(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"📄 Page 1 selected by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        fruits_list = self.pages[0] if len(self.pages) > 0 else []
        view = FruitSelectionView(self.user_id, fruits_list, "Alphabetical Page 1", len(self.pages), 1)

        embed = discord.Embed(
            title="🎲 Select Your Fruit - Page 1",
            description="Choose the fruit you rolled:",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"⏱️ You have 3 minutes • Page 1/{len(self.pages)}")

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Page 2 (Gravity-Portal)", style=discord.ButtonStyle.primary, row=0)
    async def page2(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"📄 Page 2 selected by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        fruits_list = self.pages[1] if len(self.pages) > 1 else []
        view = FruitSelectionView(self.user_id, fruits_list, "Alphabetical Page 2", len(self.pages), 2)

        embed = discord.Embed(
            title="🎲 Select Your Fruit - Page 2",
            description="Choose the fruit you rolled:",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"⏱️ You have 3 minutes • Page 2/{len(self.pages)}")

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Page 3 (Quake-Yeti)", style=discord.ButtonStyle.primary, row=1)
    async def page3(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"📄 Page 3 selected by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        fruits_list = self.pages[2] if len(self.pages) > 2 else []
        view = FruitSelectionView(self.user_id, fruits_list, "Alphabetical Page 3", len(self.pages), 3)

        embed = discord.Embed(
            title="🎲 Select Your Fruit - Page 3",
            description="Choose the fruit you rolled:",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"⏱️ You have 3 minutes • Page 3/{len(self.pages)}")

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔙 Back to Sort Options", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🔙 Back button clicked by {interaction.user}")
        
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        view = PageSelectionView(self.user_id)
        embed = discord.Embed(
            title="🎲 Select Your Fruit Roll",
            description="How would you like to browse fruits?",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)


class RaritySelectionView(discord.ui.View):
    """View for selecting by rarity"""

    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        logger.debug(f"🎮 Created RaritySelectionView for user {user_id}")

    @discord.ui.button(label="⚪ Common", style=discord.ButtonStyle.secondary, emoji="⚪", row=0)
    async def common(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"⚪ Common rarity selected by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        await self.show_rarity_fruits(interaction, "Common")

    @discord.ui.button(label="🔵 Uncommon", style=discord.ButtonStyle.primary, emoji="🔵", row=0)
    async def uncommon(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🔵 Uncommon rarity selected by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        await self.show_rarity_fruits(interaction, "Uncommon")

    @discord.ui.button(label="🟣 Rare", style=discord.ButtonStyle.primary, emoji="🟣", row=1)
    async def rare(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🟣 Rare rarity selected by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        await self.show_rarity_fruits(interaction, "Rare")

    @discord.ui.button(label="🔮 Legendary", style=discord.ButtonStyle.primary, emoji="🔮", row=1)
    async def legendary(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🔮 Legendary rarity selected by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        await self.show_rarity_fruits(interaction, "Legendary")

    @discord.ui.button(label="🔴 Mythic", style=discord.ButtonStyle.danger, emoji="🔴", row=2)
    async def mythic(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🔴 Mythic rarity selected by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        await self.show_rarity_fruits(interaction, "Mythic")

    @discord.ui.button(label="🔙 Back to Sort Options", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.info(f"🔙 Back button clicked by {interaction.user}")
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return

        view = PageSelectionView(self.user_id)
        embed = discord.Embed(
            title="🎲 Select Your Fruit Roll",
            description="How would you like to browse fruits?",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def show_rarity_fruits(self, interaction: discord.Interaction, rarity: str):
        """Show fruits of a specific rarity"""
        fruits_list = RARITY_GROUPS[rarity]
        view = FruitSelectionView(self.user_id, fruits_list, f"{rarity} Fruits", 1, 1)

        rarity_emoji = {
            "Common": "⚪",
            "Uncommon": "🔵",
            "Rare": "🟣",
            "Legendary": "🔮",
            "Mythic": "🔴"
        }

        embed = discord.Embed(
            title=f"🎲 {rarity_emoji[rarity]} {rarity} Fruits",
            description=f"Choose your {rarity.lower()} fruit roll:\n\n" + ", ".join(fruits_list),
            color=RARITY_COLORS[rarity]
        )
        embed.set_footer(text=f"⏱️ You have 3 minutes • {len(fruits_list)} {rarity} fruits")

        await interaction.response.edit_message(embed=embed, view=view)
        logger.debug(f"✅ Showing {len(fruits_list)} {rarity} fruits")


@bot.event
async def on_ready():
    logger.info("=" * 80)
    logger.info("🎉 BOT READY EVENT TRIGGERED")
    logger.info("=" * 80)
    
    stats['bot_start_time'] = datetime.now(timezone.utc)
    stats['guilds_count'] = len(bot.guilds)

    logger.info(f"🤖 Logged in as: {bot.user.name}")
    logger.info(f"🆔 Bot ID: {bot.user.id}")
    logger.info(f"🌐 Connected to {len(bot.guilds)} guild(s):")
    
    for guild in bot.guilds:
        logger.info(f"   - {guild.name} (ID: {guild.id}, Members: {guild.member_count})")

    # Initialize database
    init_database()

    # Sync guild members to database
    logger.info("=" * 80)
    logger.info("👥 SYNCING GUILD MEMBERS")
    logger.info("=" * 80)
    for guild in bot.guilds:
        synced, skipped = sync_guild_members_to_db(guild)
    logger.info("✅ Member sync complete")
    logger.info("=" * 80)

    # Update active users count
    stats['active_users'] = len(get_all_users())
    logger.info(f"👥 Active users in database: {stats['active_users']}")

    # Sync slash commands
    logger.info("🔄 Syncing slash commands with Discord...")
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Successfully synced {len(synced)} slash command(s):")
        for cmd in synced:
            logger.info(f"   - /{cmd.name}")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

    logger.info("=" * 80)
    logger.info("✅ BOT FULLY INITIALIZED AND READY")
    logger.info("🍎 Fruit Roll Tracker is now ONLINE!")
    logger.info("=" * 80)

    # Start notification checker
    if not notification_checker.is_running():
        logger.info("⏰ Starting notification checker task...")
        notification_checker.start()
        logger.info("✅ Notification checker task started")

    # Notify initial users
    logger.info("📢 Sending startup notifications...")
    await notify_initial_users()


async def notify_initial_users():
    """Send initial notification to designated users in the notification channel"""
    logger.info("⏳ Waiting 5 seconds before sending notifications...")
    await asyncio.sleep(5)

    try:
        logger.info(f"🔍 Looking for notification channel ID: {NOTIFICATION_CHANNEL_ID}")
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not channel:
            logger.error(f"❌ Could not find notification channel with ID {NOTIFICATION_CHANNEL_ID}")
            return

        logger.info(f"✅ Found channel: {channel.name} in guild: {channel.guild.name}")

        # Create mentions string
        mentions = " ".join([f"<@{user_id}>" for user_id in NOTIFICATION_USERS])
        logger.info(f"📝 Mentioning {len(NOTIFICATION_USERS)} users")

        embed = discord.Embed(
            title="🎲 Blox Fruits Roll Tracker is Online!",
            description="Log your fruit rolls and get reminded when your next roll is ready!",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📝 Get Started",
            value="Use `/fruit-roll` to log your first fruit roll!",
            inline=False
        )
        embed.add_field(
            name="⏰ Reminders",
            value="You'll be pinged in this channel every 2 hours when your next roll is ready!",
            inline=False
        )
        embed.add_field(
            name="💤 Sleep Mode",
            value="`/sleep` - Disable roll reminders\n`/awake` - Enable roll reminders",
            inline=False
        )
        embed.add_field(
            name="📊 View Your Rolls",
            value="Use `/fruits` to see all your rolled fruits!",
            inline=False
        )
        embed.set_footer(text="SorynTech Blox Fruits Bot | 🦈 Part of the SorynTech Bot Suite")

        logger.info("📤 Sending startup notification embed...")
        await channel.send(content=mentions, embed=embed)
        logger.info(f"✅ Sent startup notification to channel: {channel.name}")
    except Exception as e:
        logger.error(f"❌ Failed to send startup notification: {e}", exc_info=True)


# Notification checker task
@tasks.loop(minutes=1)
async def notification_checker():
    """Check for users who need roll reminders"""
    logger.debug("⏰ Notification checker running...")
    now = datetime.now(timezone.utc)
    users = get_all_users()

    # Get notification channel
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        logger.error(f"❌ Could not find notification channel with ID {NOTIFICATION_CHANNEL_ID}")
        return

    notifications_sent = 0
    for user_data in users:
        if not user_data['notifications_enabled']:
            continue

        if user_data['next_roll_time'] and user_data['next_roll_time'] <= now:
            try:
                display_name = get_display_name(user_data['user_id'], user_data['username'])
                logger.info(f"🔔 Sending roll reminder to {display_name} ({user_data['username']}, ID: {user_data['user_id']})")
                
                # Special embed for Dad
                if user_data['user_id'] == DAD_USER_ID:
                    embed = discord.Embed(
                        title="🎲 Fruity rolly ready!",
                        description=f"Daddy's fruit rolly cooldown is all doney woney :3",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="📝 Log your rolly",
                        value="Use `/fruit-roll` to loggy your next fruit roll!",
                        inline=False
                    )
                    embed.set_footer(text="Use /sleep to disable able these reminders tee hee :3c")
                    mention_text = f"**Blox Fruits Notifier:** Daddy Lucian Your fruit roll is weddy when you are :3c ||<@{user_data['user_id']}>||"
                else:
                    embed = discord.Embed(
                        title="🎲 Fruit Roll Ready!",
                        description=f"**{display_name}**'s fruit roll cooldown is complete!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="📝 Log Your Roll",
                        value="Use `/fruit-roll` to log your next fruit roll!",
                        inline=False
                    )
                    embed.set_footer(text="Use /sleep to disable these reminders")
                    mention_text = f"<@{user_data['user_id']}>"

                await channel.send(content=mention_text, embed=embed)
                notifications_sent += 1

                # Clear next_roll_time so we don't spam
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute('UPDATE users SET next_roll_time = NULL WHERE user_id = %s',
                                (user_data['user_id'],))
                    conn.commit()
                    cur.close()
                    return_db_connection(conn)
                except Exception as e:
                    logger.error(f"❌ Error updating next_roll_time: {e}")

                logger.info(f"✅ Sent roll reminder to {display_name}")
            except Exception as e:
                logger.error(f"❌ Failed to send reminder to {user_data['user_id']}: {e}")
    
    if notifications_sent > 0:
        logger.info(f"📬 Sent {notifications_sent} roll reminder(s) this cycle")
    else:
        logger.debug("✅ No reminders to send this cycle")


@notification_checker.before_loop
async def before_notification_checker():
    logger.info("⏰ Notification checker waiting for bot to be ready...")
    await bot.wait_until_ready()
    logger.info("✅ Notification checker ready to start")


# Slash Commands
@bot.tree.command(name='fruit-roll', description='Log your fruit roll')
async def fruit_roll(interaction: discord.Interaction):
    """Log a fruit roll"""
    logger.info("=" * 80)
    logger.info(f"🎲 /fruit-roll command invoked by {interaction.user} (ID: {interaction.user.id})")
    logger.info(f"   Guild: {interaction.guild.name if interaction.guild else 'DM'}")
    logger.info(f"   Channel: {interaction.channel.name if hasattr(interaction.channel, 'name') else 'DM'}")
    
    log_command_usage('fruit-roll', interaction.user.id)

    # Check if user exists, create if not
    logger.debug("👤 Checking if user exists in database...")
    user_data = get_user(interaction.user.id)
    if not user_data:
        logger.info("✨ User not found, creating new user entry...")
        create_or_update_user(interaction.user.id, interaction.user.name)
        user_data = get_user(interaction.user.id)

    # Check if user is suspended
    if user_data and user_data.get('suspended', False):
        logger.warning(f"🔒 Suspended user attempted to roll: {interaction.user}")
        await interaction.response.send_message(
            "Hey Soryntech Temporaily suspended your user ID dm him to fix this",
            ephemeral=True
        )
        return

    # Check if user can roll (cooldown)
    if user_data and user_data['next_roll_time']:
        now = datetime.now(timezone.utc)
        if user_data['next_roll_time'] > now:
            time_left = user_data['next_roll_time'] - now
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)

            logger.warning(f"⏰ User on cooldown! Time remaining: {hours}h {minutes}m")
            
            embed = discord.Embed(
                title="⏰ Roll On Cooldown",
                description=f"Your next roll is available <t:{int(user_data['next_roll_time'].timestamp())}:R>",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Time Remaining",
                value=f"{hours}h {minutes}m",
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            logger.info("✅ Cooldown message sent")
            return

    # Show fruit selection options
    logger.info("✅ User can roll! Showing fruit selection menu...")
    embed = discord.Embed(
        title="🎲 Log Your Fruit Roll",
        description="How would you like to browse fruits?",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="📝 Alphabetical Order",
        value="Browse fruits A-Z across multiple pages",
        inline=False
    )
    embed.add_field(
        name="✨ Sort by Rarity",
        value="⚪ Common • 🔵 Uncommon • 🟣 Rare • 🔮 Legendary • 🔴 Mythic",
        inline=False
    )
    embed.set_footer(text="⏱️ You have 3 minutes to select your fruit")

    view = PageSelectionView(interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    logger.info("✅ Fruit selection menu sent to user")
    logger.info("=" * 80)


@bot.tree.command(name='fruits', description='View all your rolled fruits')
async def fruits(interaction: discord.Interaction):
    """View all rolled fruits for the user"""
    logger.info(f"📊 /fruits command invoked by {interaction.user} (ID: {interaction.user.id})")
    log_command_usage('fruits', interaction.user.id)

    rolls = get_user_rolls(interaction.user.id)

    if not rolls:
        logger.info(f"⚠️  User {interaction.user} has no rolls yet")
        embed = discord.Embed(
            title="📊 Your Fruit Rolls",
            description="You haven't logged any fruit rolls yet!\n\nUse `/fruit-roll` to log your first roll.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    logger.info(f"📊 User has {len(rolls)} total rolls")

    # Count fruits by rarity
    rarity_counts = {"Common": 0, "Uncommon": 0, "Rare": 0, "Legendary": 0, "Mythic": 0}
    for roll in rolls:
        fruit_name = roll['fruit']
        if fruit_name in FRUITS_DATA:
            rarity = FRUITS_DATA[fruit_name]["rarity"]
            rarity_counts[rarity] += 1

    logger.debug(f"Rarity breakdown: {rarity_counts}")

    embed = discord.Embed(
        title="🍎 Your Fruit Roll History",
        description=f"**Total Rolls:** {len(rolls)}\n\n**By Rarity:**\n⚪ Common: {rarity_counts['Common']} | 🔵 Uncommon: {rarity_counts['Uncommon']} | 🟣 Rare: {rarity_counts['Rare']}\n🔮 Legendary: {rarity_counts['Legendary']} | 🔴 Mythic: {rarity_counts['Mythic']}",
        color=discord.Color.purple()
    )

    # Show up to 25 most recent rolls
    for i, roll in enumerate(rolls[:25], 1):
        fruit_name = roll['fruit']
        timestamp = int(roll['time'].timestamp())

        # Get fruit data
        if fruit_name in FRUITS_DATA:
            fruit_data = FRUITS_DATA[fruit_name]
            rarity_emoji = {
                "Common": "⚪",
                "Uncommon": "🔵",
                "Rare": "🟣",
                "Legendary": "🔮",
                "Mythic": "🔴"
            }
            emoji = rarity_emoji.get(fruit_data["rarity"], "⚪")
            display_name = f"{emoji} {fruit_data['emoji']} {fruit_name}"
        else:
            display_name = f"🍎 {fruit_name}"

        embed.add_field(
            name=f"{i}. {display_name}",
            value=f"<t:{timestamp}:R>",
            inline=True
        )

    if len(rolls) > 25:
        embed.set_footer(text=f"Showing 25 of {len(rolls)} rolls")
    else:
        embed.set_footer(text="SorynTech Blox Fruits Tracker")

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"✅ Sent roll history to {interaction.user}")


@bot.tree.command(name='sleep', description='Disable fruit roll reminders')
async def sleep_mode(interaction: discord.Interaction):
    """Disable roll reminders"""
    logger.info(f"💤 /sleep command invoked by {interaction.user} (ID: {interaction.user.id})")
    log_command_usage('sleep', interaction.user.id)

    user_data = get_user(interaction.user.id)
    if not user_data:
        create_or_update_user(interaction.user.id, interaction.user.name)

    toggle_notifications(interaction.user.id, False)

    embed = discord.Embed(
        title="💤 Sleep Mode Enabled",
        description="You will no longer receive fruit roll reminder pings.",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="Wake Up",
        value="Use `/awake` to re-enable reminder pings",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"✅ Sleep mode enabled for {interaction.user}")


@bot.tree.command(name='awake', description='Enable fruit roll reminders')
async def awake_mode(interaction: discord.Interaction):
    """Enable roll reminders"""
    logger.info(f"☀️ /awake command invoked by {interaction.user} (ID: {interaction.user.id})")
    log_command_usage('awake', interaction.user.id)

    user_data = get_user(interaction.user.id)
    if not user_data:
        create_or_update_user(interaction.user.id, interaction.user.name)

    toggle_notifications(interaction.user.id, True)

    embed = discord.Embed(
        title="☀️ Awake Mode Enabled",
        description="You will now receive fruit roll reminder pings!",
        color=discord.Color.green()
    )
    embed.add_field(
        name="Sleep Mode",
        value="Use `/sleep` to disable reminder pings",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)
    logger.info(f"✅ Awake mode enabled for {interaction.user}")


# Owner Commands
@bot.tree.command(name='stats-link', description='[OWNER] Get the stats page link')
async def stats_link(interaction: discord.Interaction):
    """Get stats page credentials"""
    logger.info(f"📊 /stats-link command invoked by {interaction.user} (ID: {interaction.user.id})")
    
    if interaction.user.id != OWNER_ID:
        logger.warning(f"⚠️  Unauthorized access attempt by {interaction.user}")
        await interaction.response.send_message("❌ Owner only command", ephemeral=True)
        return

    logger.info("✅ Owner authorized, sending stats credentials")
    
    embed = discord.Embed(
        title="📊 Stats Page Access",
        description="Here are your stats page credentials:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Username", value=f"`{STATS_USER}`", inline=False)
    embed.add_field(name="Password", value=f"`{STATS_PASS}`", inline=False)
    embed.add_field(name="URL", value="Go to `/stats` on your bot URL", inline=False)
    embed.add_field(name="LINK:", value="https://blox-fruits-notifier-msvi.onrender.com/stats", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='suspend', description='[OWNER] Suspend or unsuspend a user')
@app_commands.describe(user_id='The Discord user ID to suspend/unsuspend')
async def suspend_command(interaction: discord.Interaction, user_id: str):
    """Suspend or unsuspend a user from using the bot"""
    logger.info(f"🔒 /suspend command invoked by {interaction.user} (ID: {interaction.user.id})")
    log_command_usage('suspend', interaction.user.id)
    
    if interaction.user.id != OWNER_ID:
        logger.warning(f"⚠️  Unauthorized suspend attempt by {interaction.user}")
        await interaction.response.send_message("❌ Owner only command", ephemeral=True)
        return
    
    try:
        target_user_id = int(user_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid user ID format.", ephemeral=True)
        return
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT username, suspended FROM users WHERE user_id = %s', (target_user_id,))
        user_data = cur.fetchone()
        cur.close()
        return_db_connection(conn)
        
        if not user_data:
            await interaction.response.send_message(f"❌ User ID {target_user_id} not found in database.", ephemeral=True)
            return
        
        username, currently_suspended = user_data
        new_status = not currently_suspended
        
        success, message = suspend_user(target_user_id, new_status)
        
        if success:
            status_emoji = "🔒" if new_status else "🔓"
            status_text = "SUSPENDED" if new_status else "UNSUSPENDED"
            color = discord.Color.red() if new_status else discord.Color.green()
            
            embed = discord.Embed(
                title=f"{status_emoji} User {status_text}",
                description=f"User **{username}** (ID: {target_user_id}) has been {status_text.lower()}.",
                color=color
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Failed: {message}", ephemeral=True)
    except Exception as e:
        logger.error(f"❌ Error in suspend command: {e}")
        await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)


# Web server functions
def check_auth(request) -> bool:
    """Check HTTP Basic Auth"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return False

    import base64
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        return username == STATS_USER and password == STATS_PASS
    except:
        return False


def get_auth_response():
    """Return 401 with auth request"""
    return web.Response(
        text='Unauthorized',
        status=401,
        headers={'WWW-Authenticate': 'Basic realm="Stats Page"'}
    )


# HTML Templates
HEALTH_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blox Fruits Bot - Health Check</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a1929 0%, #1a2f42 50%, #0d3a5c 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(13, 58, 92, 0.4);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            border: 2px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        h1 {{
            font-size: 3em;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .status {{
            display: inline-block;
            padding: 15px 30px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 25px;
            font-size: 1.5em;
            margin: 20px 0;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
        }}
        .info {{
            margin-top: 20px;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .supabase-badge {{
            margin-top: 20px;
            padding: 10px 20px;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 10px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Blox Fruits Bot</h1>
        <div class="status">✅ Bot is Online</div>
        <div class="info">
            <p>Uptime: {uptime}</p>
            <p>Total Rolls: {total_rolls}</p>
            <p>Active Users: {active_users}</p>
        </div>
        <div class="supabase-badge">
            <p>🗄️ Powered by Supabase</p>
        </div>
    </div>
</body>
</html>
"""

STATS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SorynTech - Blox Fruits Stats</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a1929 0%, #1a2f42 50%, #0d3a5c 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
            position: relative;
            overflow-x: hidden;
        }}
        .shark-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }}
        .shark {{
            position: absolute;
            font-size: 40px;
            opacity: 0.15;
            animation: swim 30s linear infinite;
        }}
        .shark:nth-child(2) {{
            animation-delay: 10s;
            top: 60%;
            animation-duration: 40s;
        }}
        .shark:nth-child(3) {{
            animation-delay: 20s;
            top: 30%;
            animation-duration: 35s;
        }}
        @keyframes swim {{
            0% {{
                left: -100px;
                transform: scaleX(-1);
            }}
            100% {{
                left: calc(100% + 100px);
                transform: scaleX(-1);
            }}
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        .header {{
            text-align: center;
            padding: 40px 20px;
            background: rgba(13, 58, 92, 0.3);
            border-radius: 20px;
            border: 2px solid rgba(59, 130, 246, 0.3);
            margin-bottom: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .supabase-badge {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: rgba(59, 130, 246, 0.2);
            border-radius: 15px;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(13, 58, 92, 0.4);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border: 2px solid rgba(59, 130, 246, 0.2);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(59, 130, 246, 0.5);
        }}
        .stat-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.8;
            text-transform: uppercase;
            margin-bottom: 10px;
            color: #94a3b8;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #06b6d4;
        }}
        .chart-section {{
            background: rgba(13, 58, 92, 0.4);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border: 2px solid rgba(59, 130, 246, 0.2);
        }}
        .chart-title {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #06b6d4;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
        }}
        .users-section {{
            background: rgba(13, 58, 92, 0.4);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            border: 2px solid rgba(59, 130, 246, 0.2);
        }}
        .user-item {{
            background: rgba(13, 58, 92, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid rgba(59, 130, 246, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .user-info {{
            flex-grow: 1;
        }}
        .user-name {{
            font-weight: bold;
            color: #06b6d4;
        }}
        .user-stats {{
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        .next-roll {{
            text-align: right;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            opacity: 0.8;
            color: #94a3b8;
        }}
    </style>
    <script>
        setTimeout(function() {{
            location.reload();
        }}, 30000);
    </script>
</head>
<body>
    <div class="shark-container">
        <div class="shark" style="top: 20%;">🦈</div>
        <div class="shark" style="top: 60%;">🦈</div>
        <div class="shark" style="top: 30%;">🦈</div>
    </div>

    <div class="container">
        <div class="header">
            <h1>🦈 SorynTech Bot Suite</h1>
            <p style="font-size: 1.2em; color: #06b6d4;">🎲 Blox Fruits Roll Tracker</p>
            <div class="supabase-badge">🗄️ Powered by Supabase</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">⏱️</div>
                <div class="stat-label">Uptime</div>
                <div class="stat-value">{uptime}</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">🎲</div>
                <div class="stat-label">Total Rolls</div>
                <div class="stat-value">{total_rolls}</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-label">Active Users</div>
                <div class="stat-value">{active_users}</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">🌐</div>
                <div class="stat-label">Servers</div>
                <div class="stat-value">{guilds_count}</div>
            </div>
        </div>

        <div class="chart-section">
            <div class="chart-title">🍎 Fruit Rarity Distribution</div>
            <div class="chart-container">
                <canvas id="rarityChart"></canvas>
            </div>
        </div>

        <div class="users-section">
            <div class="chart-title">👥 Recent Rolls & Upcoming Notifications</div>
            {users_list}
        </div>

        <div class="footer">
            <p>🦈 SorynTech Bot Suite | 🗄️ Supabase PostgreSQL</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Auto-refresh every 30 seconds | Last Updated: {current_time}</p>
        </div>
    </div>

    <script>
        const rarityData = {rarity_data};

        const ctx = document.getElementById('rarityChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: rarityData.labels,
                datasets: [{{
                    label: 'Number of Rolls',
                    data: rarityData.data,
                    backgroundColor: rarityData.colors,
                    borderColor: rarityData.borderColors,
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.dataset.label || '';
                                if (label) {{
                                    label += ': ';
                                }}
                                label += context.parsed.y + ' rolls';
                                return label;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(59, 130, 246, 0.1)' }},
                        ticks: {{ 
                            color: '#94a3b8',
                            stepSize: 1
                        }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ 
                            color: '#94a3b8',
                            font: {{ size: 14, weight: 'bold' }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""


SUSPENDED_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SorynTech - Suspended Users</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a1929 0%, #1a2f42 50%, #0d3a5c 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
            position: relative;
            overflow-x: hidden;
        }}
        .shark-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            overflow: hidden;
        }}
        .shark {{
            position: absolute;
            font-size: 40px;
            opacity: 0.15;
            animation: swim 30s linear infinite;
        }}
        .shark:nth-child(2) {{
            animation-delay: 10s;
            top: 60%;
            animation-duration: 40s;
        }}
        .shark:nth-child(3) {{
            animation-delay: 20s;
            top: 30%;
            animation-duration: 35s;
        }}
        @keyframes swim {{
            0% {{ left: -100px; transform: scaleX(-1); }}
            100% {{ left: calc(100% + 100px); transform: scaleX(-1); }}
        }}
        .container {{ max-width: 1400px; margin: 0 auto; position: relative; z-index: 1; }}
        .header {{
            text-align: center;
            padding: 40px 20px;
            background: rgba(13, 58, 92, 0.3);
            border-radius: 20px;
            border: 2px solid rgba(220, 38, 38, 0.5);
            margin-bottom: 30px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats-box {{
            background: rgba(13, 58, 92, 0.4);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .user-card {{
            background: rgba(13, 58, 92, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border: 2px solid rgba(220, 38, 38, 0.2);
        }}
        .user-name {{ font-size: 1.2em; font-weight: bold; color: #ef4444; margin-bottom: 5px; }}
        .user-id {{ font-size: 0.9em; color: #94a3b8; font-family: monospace; }}
        .user-stats {{ margin-top: 10px; font-size: 0.9em; color: #cbd5e1; }}
        .empty {{ text-align: center; padding: 40px; opacity: 0.7; }}
        .nav-link {{
            display: inline-block;
            margin-top: 20px;
            padding: 12px 24px;
            background: rgba(59, 130, 246, 0.3);
            border-radius: 10px;
            text-decoration: none;
            color: #06b6d4;
            border: 1px solid rgba(59, 130, 246, 0.5);
        }}
    </style>
</head>
<body>
    <div class="shark-container">
        <div class="shark" style="top: 20%;">🦈</div>
        <div class="shark" style="top: 60%;">🦈</div>
        <div class="shark" style="top: 30%;">🦈</div>
    </div>

    <div class="container">
        <div class="header">
            <h1>🦈 SorynTech Bot Suite</h1>
            <p style="font-size: 1.2em; color: #ef4444;">🔒 Suspended Users</p>
        </div>

        <div class="stats-box">
            <h2 style="color: #ef4444;">Suspended: {suspended_count}</h2>
        </div>

        {users_list}

        <div style="text-align: center;">
            <a href="/stats" class="nav-link">← Back to Stats Dashboard</a>
        </div>
    </div>
</body>
</html>
"""


async def handle_health(request):
    """Public health check endpoint"""
    logger.debug("🏥 Health check endpoint accessed")
    
    uptime = "Not started"
    if stats['bot_start_time']:
        delta = datetime.now(timezone.utc) - stats['bot_start_time']
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m"

    html = HEALTH_PAGE.format(
        uptime=uptime,
        total_rolls=stats['total_rolls'],
        active_users=stats['active_users']
    )

    return web.Response(text=html, content_type='text/html')


async def handle_stats(request):
    """Protected stats page"""
    logger.debug("📊 Stats page accessed")
    
    if not check_auth(request):
        logger.warning("⚠️  Unauthorized stats page access attempt")
        return get_auth_response()

    logger.info("✅ Stats page access authorized")

    # Calculate uptime
    uptime = "Not started"
    if stats['bot_start_time']:
        delta = datetime.now(timezone.utc) - stats['bot_start_time']
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime = f"{days}d {hours}h {minutes}m"

    # Get all users sorted by next roll time
    users = get_all_users()
    users_sorted = sorted(
        [u for u in users if u['next_roll_time']],
        key=lambda x: x['next_roll_time']
    )

    # Build users list HTML
    users_html = ""
    for user in users_sorted:
        last_roll = user['last_roll_time']
        next_roll = user['next_roll_time']

        # Get their last fruit
        rolls = get_user_rolls(user['user_id'])
        last_fruit = rolls[0]['fruit'] if rolls else "None"

        next_roll_str = f"<t:{int(next_roll.timestamp())}:R>" if next_roll else "No upcoming roll"
        notif_status = "🔔 Enabled" if user['notifications_enabled'] else "🔕 Disabled"

        users_html += f"""
        <div class="user-item">
            <div class="user-info">
                <div class="user-name">{user['username']}</div>
                <div class="user-stats">
                    Last Roll: {last_fruit} | Total: {user['total_rolls']} | {notif_status}
                </div>
            </div>
            <div class="next-roll">
                <div style="font-weight: bold;">Next Roll</div>
                <div>{next_roll_str}</div>
            </div>
        </div>
        """

    if not users_html:
        users_html = "<p style='text-align: center; opacity: 0.7;'>No users have logged rolls yet</p>"

    # Get rarity distribution data
    rarity_dist = get_rarity_distribution()

    # Define rarity order and colors
    rarity_order = ['Common', 'Uncommon', 'Rare', 'Legendary', 'Mythic']
    rarity_colors_hex = {
        'Common': 'rgba(128, 128, 128, 0.8)',
        'Uncommon': 'rgba(59, 130, 246, 0.8)',
        'Rare': 'rgba(147, 51, 234, 0.8)',
        'Legendary': 'rgba(236, 72, 153, 0.8)',
        'Mythic': 'rgba(220, 38, 38, 0.8)'
    }
    rarity_border_colors = {
        'Common': 'rgba(128, 128, 128, 1)',
        'Uncommon': 'rgba(59, 130, 246, 1)',
        'Rare': 'rgba(147, 51, 234, 1)',
        'Legendary': 'rgba(236, 72, 153, 1)',
        'Mythic': 'rgba(220, 38, 38, 1)'
    }
    rarity_emoji = {
        'Common': '⚪',
        'Uncommon': '🔵',
        'Rare': '🟣',
        'Legendary': '🔮',
        'Mythic': '🔴'
    }

    labels = []
    data = []
    colors = []
    border_colors = []

    for rarity in rarity_order:
        labels.append(f"{rarity_emoji.get(rarity, '')} {rarity}")
        data.append(rarity_dist.get(rarity, 0))
        colors.append(rarity_colors_hex.get(rarity, 'rgba(128, 128, 128, 0.8)'))
        border_colors.append(rarity_border_colors.get(rarity, 'rgba(128, 128, 128, 1)'))

    rarity_data = {
        'labels': labels,
        'data': data,
        'colors': colors,
        'borderColors': border_colors
    }

    html = STATS_PAGE.format(
        uptime=uptime,
        total_rolls=stats['total_rolls'],
        active_users=len(users),
        guilds_count=stats['guilds_count'],
        users_list=users_html,
        rarity_data=json.dumps(rarity_data),
        current_time=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    )

    return web.Response(text=html, content_type='text/html')


async def handle_suspended(request):
    """Protected suspended users page"""
    logger.debug("🔒 Suspended users page accessed")
    
    if not check_auth(request):
        logger.warning("⚠️  Unauthorized suspended page access attempt")
        return get_auth_response()

    logger.info("✅ Suspended page access authorized")

    try:
        suspended_users = get_suspended_users()
        
        if suspended_users:
            users_html = ""
            for user in suspended_users:
                last_roll = user['last_roll_time'].strftime('%Y-%m-%d %H:%M UTC') if user['last_roll_time'] else 'Never'
                created = user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'Unknown'
                
                users_html += f"""
                <div class="user-card">
                    <div class="user-name">🔒 {user['username']}</div>
                    <div class="user-id">User ID: {user['user_id']}</div>
                    <div class="user-stats">
                        Total Rolls: {user['total_rolls']} | Last Roll: {last_roll} | Joined: {created}
                    </div>
                </div>
                """
        else:
            users_html = '<div class="empty">✅ No suspended users! All clear! 🎉</div>'
        
        html = SUSPENDED_PAGE.format(
            suspended_count=len(suspended_users),
            users_list=users_html
        )
        
        return web.Response(text=html, content_type='text/html')
    except Exception as e:
        logger.error(f"❌ Error in handle_suspended: {e}")
        return web.Response(text=f"Error: {str(e)}", status=500)


async def handle_root(request):
    """Root redirects to health"""
    logger.debug("🌐 Root endpoint accessed")
    return await handle_health(request)


async def handle_favicon(request):
    """Handle favicon requests"""
    import os.path
    favicon_path = os.path.join(os.path.dirname(__file__), 'favicon.ico')

    try:
        if os.path.exists(favicon_path):
            with open(favicon_path, 'rb') as f:
                favicon_data = f.read()
            return web.Response(
                body=favicon_data,
                content_type='image/x-icon',
                headers={
                    'Cache-Control': 'public, max-age=86400'  # Cache for 1 day
                }
            )
        else:
            return web.Response(status=404)
    except Exception as e:
        logger.error(f"Error serving favicon: {e}")
        return web.Response(status=404)


async def start_web_server():
    """Start the web server"""
    logger.info("=" * 80)
    logger.info("🌐 STARTING WEB SERVER")
    logger.info("=" * 80)
    
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/stats', handle_stats)
    app.router.add_get('/suspended', handle_suspended)
    app.router.add_get('/favicon.ico', handle_favicon)

    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    logger.info(f"✅ Web server started successfully on 0.0.0.0:{port}")
    logger.info(f"🏥 Health check: http://0.0.0.0:{port}/")
    logger.info(f"📊 Stats page: http://0.0.0.0:{port}/stats (Protected)")
    logger.info(f"🔒 Suspended page: http://0.0.0.0:{port}/suspended (Protected)")
    logger.info("=" * 80)


async def main():
    """Main function"""
    logger.info("🚀 MAIN FUNCTION STARTING...")
    
    await start_web_server()

    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        logger.critical("❌ DISCORD_TOKEN not found in .env file!")
        logger.critical("Please set the DISCORD_TOKEN environment variable")
        return

    logger.info("✅ Discord token loaded from environment")
    logger.info("🔐 Connecting to Discord...")

    async with bot:
        await bot.start(TOKEN)


if __name__ == "__main__":
    try:
        logger.info("=" * 80)
        logger.info("🦈 BLOX FRUITS BOT STARTING...")
        logger.info("=" * 80)
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("👋 SHUTDOWN SIGNAL RECEIVED")
        logger.info("=" * 80)
        logger.info("🛑 Bot shutting down gracefully...")
    finally:
        if db_pool:
            logger.info("🔌 Closing database connection pool...")
            db_pool.closeall()
            logger.info("✅ Supabase connections closed")
        logger.info("=" * 80)
        logger.info("✅ SHUTDOWN COMPLETE")
        logger.info("=" * 80)
