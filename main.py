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
import hashlib
import secrets

# Load environment variables from .env file
load_dotenv()

# Bot setup with necessary intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
OWNER_ID = 447812883158532106
NOTIFICATION_USERS = [447812883158532106, 778645525499084840, 581677161006497824, 1285269152474464369]
NOTIFICATION_CHANNEL_ID = 1431308135091671132  # General channel for notifications
ROLL_COOLDOWN_HOURS = 2
STATS_USER = os.getenv('STATS_USER', 'admin')
STATS_PASS = os.getenv('STATS_PASS', 'changeme')

# Supabase Database Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL not found in environment variables!")
    print("Please add your Supabase connection URL to your environment variables.")
    exit(1)

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

def get_db_connection():
    """Get a database connection from the pool"""
    return db_pool.getconn()

def return_db_connection(conn):
    """Return a connection to the pool"""
    db_pool.putconn(conn)

# Database setup
def init_database():
    """Initialize PostgreSQL database with required tables"""
    global db_pool
    
    try:
        # Create connection pool for Supabase
        # Using pooled connection (port 6543) for better performance
        db_pool = SimpleConnectionPool(1, 20, SUPABASE_URL)
        print("✅ Supabase connection pool created")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Users table
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT NOT NULL,
            total_rolls INTEGER DEFAULT 0,
            last_roll_time TIMESTAMP WITH TIME ZONE,
            next_roll_time TIMESTAMP WITH TIME ZONE,
            notifications_enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Rolls table
        cur.execute('''CREATE TABLE IF NOT EXISTS rolls (
            roll_id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            fruit_name TEXT NOT NULL,
            rolled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )''')
        
        # Command usage tracking
        cur.execute('''CREATE TABLE IF NOT EXISTS command_usage (
            id SERIAL PRIMARY KEY,
            command_name TEXT NOT NULL,
            user_id BIGINT NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create indexes for better performance
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_rolls_user_id ON rolls(user_id)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_rolls_rolled_at ON rolls(rolled_at)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_command_usage_used_at ON command_usage(used_at)''')
        cur.execute('''CREATE INDEX IF NOT EXISTS idx_users_next_roll_time ON users(next_roll_time)''')
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        print("✅ Supabase database initialized successfully")
        print("🦈 Connected to Supabase PostgreSQL")
        
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        print("Make sure your SUPABASE_URL is correct and the database is running.")
        raise

# Database helper functions
def get_user(user_id: int) -> Optional[Dict]:
    """Get user from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        row = cur.fetchone()
        cur.close()
        return_db_connection(conn)
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Error in get_user: {e}")
        return None

def create_or_update_user(user_id: int, username: str):
    """Create or update user in database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute('SELECT total_rolls, notifications_enabled FROM users WHERE user_id = %s', (user_id,))
        existing = cur.fetchone()
        
        if existing:
            # Update username
            cur.execute('UPDATE users SET username = %s WHERE user_id = %s', (username, user_id))
        else:
            # Insert new user
            cur.execute('''INSERT INTO users (user_id, username, total_rolls, notifications_enabled)
                         VALUES (%s, %s, 0, TRUE)''', (user_id, username))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
    except Exception as e:
        print(f"Error in create_or_update_user: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)

def log_roll(user_id: int, username: str, fruit_name: str):
    """Log a fruit roll in the database"""
    now = datetime.now(timezone.utc)
    next_roll = now + timedelta(hours=ROLL_COOLDOWN_HOURS)
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update user
        cur.execute('''UPDATE users 
                     SET total_rolls = total_rolls + 1,
                         last_roll_time = %s,
                         next_roll_time = %s,
                         username = %s
                     WHERE user_id = %s''',
                  (now, next_roll, username, user_id))
        
        # Log the roll
        cur.execute('INSERT INTO rolls (user_id, fruit_name, rolled_at) VALUES (%s, %s, %s)',
                  (user_id, fruit_name, now))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        stats['total_rolls'] += 1
    except Exception as e:
        print(f"Error in log_roll: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)

def get_user_rolls(user_id: int) -> List[Dict]:
    """Get all rolls for a user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''SELECT fruit_name, rolled_at FROM rolls 
                     WHERE user_id = %s 
                     ORDER BY rolled_at DESC''', (user_id,))
        rows = cur.fetchall()
        cur.close()
        return_db_connection(conn)
        
        return [{'fruit': row['fruit_name'], 'time': row['rolled_at']} for row in rows]
    except Exception as e:
        print(f"Error in get_user_rolls: {e}")
        return []

def get_all_users() -> List[Dict]:
    """Get all users from database"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''SELECT user_id, username, total_rolls, last_roll_time, 
                            next_roll_time, notifications_enabled 
                     FROM users''')
        rows = cur.fetchall()
        cur.close()
        return_db_connection(conn)
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return []

def toggle_notifications(user_id: int, enabled: bool):
    """Toggle notifications for a user"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET notifications_enabled = %s WHERE user_id = %s',
                  (enabled, user_id))
        conn.commit()
        cur.close()
        return_db_connection(conn)
    except Exception as e:
        print(f"Error in toggle_notifications: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)

def log_command_usage(command_name: str, user_id: int):
    """Log command usage for statistics"""
    try:
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
    except Exception as e:
        print(f"Error in log_command_usage: {e}")
        if conn:
            conn.rollback()
            return_db_connection(conn)

def get_command_usage_stats() -> Dict:
    """Get command usage statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get usage by hour for last 24 hours
        cur.execute('''SELECT 
                        EXTRACT(HOUR FROM used_at) as hour,
                        COUNT(*) as count
                     FROM command_usage
                     WHERE used_at >= NOW() - INTERVAL '24 hours'
                     GROUP BY EXTRACT(HOUR FROM used_at)
                     ORDER BY hour''')
        
        hourly_data = {}
        for row in cur.fetchall():
            hourly_data[str(int(row[0])).zfill(2)] = row[1]
        
        cur.close()
        return_db_connection(conn)
        return hourly_data
    except Exception as e:
        print(f"Error in get_command_usage_stats: {e}")
        return {}

# Fruit list with rarities (Blox Fruits)
# Rarity: Common (gray), Uncommon (blue), Rare (purple), Legendary (pink), Mythic (red)
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
    "Flame": {"rarity": "Uncommon", "color": 0x808080, "emoji": "🔥"},
    
    # Rare (Purple)
    "Magma": {"rarity": "Rare", "color": 0x9333ea, "emoji": "🌋"},
    "Light": {"rarity": "Rare", "color": 0x3b82f6, "emoji": "💡"},
    "Rubber": {"rarity": "Rare", "color": 0x3b82f6, "emoji": "🎈"},
    "Ghost": {"rarity": "Rare", "color": 0x3b82f6, "emoji": "👻"},
    
    # Legendary (Pink/Magenta)
    "Portal": {"rarity": "Legendary", "color": 0xec4899, "emoji": "🌀"},
    "Lightning": {"rarity": "Legendary", "color": 0xec4899, "emoji": "⚡"},
    "Pain": {"rarity": "Legendary", "color": 0xec4899, "emoji": "💢"},
    "Blizzard": {"rarity": "Legendary", "color": 0xec4899, "emoji": "❄️"},
    "Quake": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "⚡"},
    "Buddha": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "🙏"},
    "Love": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "💖"},
    "Creation": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "🎨"},
    "Spider": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "🕷️"},
    "Sound": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "🔊"},
    "Phoenix": {"rarity": "Legendary", "color": 0x9333ea, "emoji": "🔥"},
    
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

# Fruit selection view with buttons - supports multiple pages
class FruitSelectionView(discord.ui.View):
    def __init__(self, user_id: int, fruits_list: List[str], page_name: str, total_pages: int, current_page: int):
        super().__init__(timeout=180)  # 3 minute timeout
        self.user_id = user_id
        self.selected_fruit = None
        self.page_name = page_name
        self.total_pages = total_pages
        self.current_page = current_page
        
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
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
                return
            
            self.selected_fruit = fruit_name
            self.stop()
            
            # Get fruit data
            fruit_data = FRUITS_DATA[fruit_name]
            
            # Log the roll
            log_roll(self.user_id, str(interaction.user), fruit_name)
            
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
            
            await channel.send(f"🎲 <@{self.user_id}> just rolled {rarity_display} **{fruit_name}** {fruit_data['emoji']} ({fruit_data['rarity']})!")
            
            # Update ephemeral message
            next_roll_time = datetime.now(timezone.utc) + timedelta(hours=ROLL_COOLDOWN_HOURS)
            await interaction.response.edit_message(
                content=f"✅ Logged your roll: {fruit_data['emoji']} **{fruit_name}** ({fruit_data['rarity']})\n⏰ Next roll available <t:{int(next_roll_time.timestamp())}:R>",
                view=None
            )
        
        return callback

class PageSelectionView(discord.ui.View):
    """Initial view to select sorting method"""
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
    
    @discord.ui.button(label="📝 Alphabetical Order", style=discord.ButtonStyle.primary, row=0)
    async def alphabetical(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
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
    
    @discord.ui.button(label="✨ Sort by Rarity", style=discord.ButtonStyle.secondary, row=0)
    async def by_rarity(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
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

class AlphabeticalPagesView(discord.ui.View):
    """View for alphabetical pagination"""
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        
        # Split fruits into pages of 20
        self.pages = []
        fruits_sorted = sorted(FRUITS)
        for i in range(0, len(fruits_sorted), 20):
            self.pages.append(fruits_sorted[i:i+20])
    
    @discord.ui.button(label="Page 1 (Blade-Gas)", style=discord.ButtonStyle.primary, row=0)
    async def page1(self, interaction: discord.Interaction, button: discord.ui.Button):
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
    
    @discord.ui.button(label="⚪ Common", style=discord.ButtonStyle.secondary, emoji="⚪", row=0)
    async def common(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        
        await self.show_rarity_fruits(interaction, "Common")
    
    @discord.ui.button(label="🔵 Uncommon", style=discord.ButtonStyle.primary, emoji="🔵", row=0)
    async def uncommon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        
        await self.show_rarity_fruits(interaction, "Uncommon")
    
    @discord.ui.button(label="🟣 Rare", style=discord.ButtonStyle.primary, emoji="🟣", row=1)
    async def rare(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        
        await self.show_rarity_fruits(interaction, "Rare")
    
    @discord.ui.button(label="🔮 Legendary", style=discord.ButtonStyle.primary, emoji="🔮", row=1)
    async def legendary(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        
        await self.show_rarity_fruits(interaction, "Legendary")
    
    @discord.ui.button(label="🔴 Mythic", style=discord.ButtonStyle.danger, emoji="🔴", row=2)
    async def mythic(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This selection is not for you!", ephemeral=True)
            return
        
        await self.show_rarity_fruits(interaction, "Mythic")
    
    @discord.ui.button(label="🔙 Back to Sort Options", style=discord.ButtonStyle.secondary, row=3)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
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

@bot.event
async def on_ready():
    stats['bot_start_time'] = datetime.now(timezone.utc)
    stats['guilds_count'] = len(bot.guilds)
    
    # Initialize database
    init_database()
    
    # Update active users count
    stats['active_users'] = len(get_all_users())
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')
    
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guild(s)')
    print(f'🍎 Fruit Roll Tracker Ready!')
    
    # Start notification checker
    if not notification_checker.is_running():
        notification_checker.start()
    
    # Notify initial users
    await notify_initial_users()

async def notify_initial_users():
    """Send initial notification to designated users in the notification channel"""
    await asyncio.sleep(5)  # Wait for bot to be fully ready
    
    try:
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if not channel:
            print(f"❌ Could not find notification channel with ID {NOTIFICATION_CHANNEL_ID}")
            return
        
        # Create mentions string
        mentions = " ".join([f"<@{user_id}>" for user_id in NOTIFICATION_USERS])
        
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
        
        await channel.send(content=mentions, embed=embed)
        print(f"✅ Sent startup notification to channel {channel.name}")
    except Exception as e:
        print(f"❌ Failed to send startup notification: {e}")

# Notification checker task
@tasks.loop(minutes=1)
async def notification_checker():
    """Check for users who need roll reminders"""
    now = datetime.now(timezone.utc)
    users = get_all_users()
    
    # Get notification channel
    channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
    if not channel:
        print(f"❌ Could not find notification channel with ID {NOTIFICATION_CHANNEL_ID}")
        return
    
    for user_data in users:
        if not user_data['notifications_enabled']:
            continue
        
        if user_data['next_roll_time'] and user_data['next_roll_time'] <= now:
            try:
                embed = discord.Embed(
                    title="🎲 Fruit Roll Ready!",
                    description=f"<@{user_data['user_id']}>'s fruit roll cooldown is complete!",
                    color=discord.Color.gold()
                )
                embed.add_field(
                    name="📝 Log Your Roll",
                    value="Use `/fruit-roll` to log your next fruit roll!",
                    inline=False
                )
                embed.set_footer(text="Use /sleep to disable these reminders")
                
                await channel.send(content=f"<@{user_data['user_id']}>", embed=embed)
                
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
                    print(f"Error updating next_roll_time: {e}")
                
                print(f"✅ Sent roll reminder to {user_data['username']} in channel")
            except Exception as e:
                print(f"❌ Failed to send reminder to {user_data['user_id']}: {e}")

@notification_checker.before_loop
async def before_notification_checker():
    await bot.wait_until_ready()

# Slash Commands
@bot.tree.command(name='fruit-roll', description='Log your fruit roll')
async def fruit_roll(interaction: discord.Interaction):
    """Log a fruit roll"""
    log_command_usage('fruit-roll', interaction.user.id)
    
    # Check if user exists, create if not
    user_data = get_user(interaction.user.id)
    if not user_data:
        create_or_update_user(interaction.user.id, str(interaction.user))
        user_data = get_user(interaction.user.id)
    
    # Check if user can roll (cooldown)
    if user_data and user_data['next_roll_time']:
        now = datetime.now(timezone.utc)
        if user_data['next_roll_time'] > now:
            time_left = user_data['next_roll_time'] - now
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
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
            return
    
    # Show fruit selection options
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

@bot.tree.command(name='fruits', description='View all your rolled fruits')
async def fruits(interaction: discord.Interaction):
    """View all rolled fruits for the user"""
    log_command_usage('fruits', interaction.user.id)
    
    rolls = get_user_rolls(interaction.user.id)
    
    if not rolls:
        embed = discord.Embed(
            title="📊 Your Fruit Rolls",
            description="You haven't logged any fruit rolls yet!\n\nUse `/fruit-roll` to log your first roll.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Count fruits by rarity
    rarity_counts = {"Common": 0, "Uncommon": 0, "Rare": 0, "Legendary": 0, "Mythic": 0}
    for roll in rolls:
        fruit_name = roll['fruit']
        if fruit_name in FRUITS_DATA:
            rarity = FRUITS_DATA[fruit_name]["rarity"]
            rarity_counts[rarity] += 1
    
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

@bot.tree.command(name='sleep', description='Disable fruit roll reminders')
async def sleep_mode(interaction: discord.Interaction):
    """Disable roll reminders"""
    log_command_usage('sleep', interaction.user.id)
    
    user_data = get_user(interaction.user.id)
    if not user_data:
        create_or_update_user(interaction.user.id, str(interaction.user))
    
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

@bot.tree.command(name='awake', description='Enable fruit roll reminders')
async def awake_mode(interaction: discord.Interaction):
    """Enable roll reminders"""
    log_command_usage('awake', interaction.user.id)
    
    user_data = get_user(interaction.user.id)
    if not user_data:
        create_or_update_user(interaction.user.id, str(interaction.user))
    
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

# Owner Commands
@bot.tree.command(name='stats-link', description='[OWNER] Get the stats page link')
async def stats_link(interaction: discord.Interaction):
    """Get stats page credentials"""
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ Owner only command", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📊 Stats Page Access",
        description="Here are your stats page credentials:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Username", value=f"`{STATS_USER}`", inline=False)
    embed.add_field(name="Password", value=f"`{STATS_PASS}`", inline=False)
    embed.add_field(name="URL", value="Go to `/stats` on your bot URL", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
            height: 300px;
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
            <div class="chart-title">📈 /fruit-roll Command Usage (24h)</div>
            <div class="chart-container">
                <canvas id="usageChart"></canvas>
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
        const usageData = {usage_data};
        
        const ctx = document.getElementById('usageChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: usageData.labels,
                datasets: [{{
                    label: 'Command Uses',
                    data: usageData.data,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#94a3b8',
                            font: {{ size: 14 }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(59, 130, 246, 0.1)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    x: {{
                        grid: {{ color: 'rgba(59, 130, 246, 0.1)' }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

async def handle_health(request):
    """Public health check endpoint"""
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
    if not check_auth(request):
        return get_auth_response()
    
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
    
    # Get command usage data
    usage_stats = get_command_usage_stats()
    labels = []
    data = []
    
    for hour in range(24):
        hour_str = f"{hour:02d}"
        labels.append(f"{hour_str}:00")
        data.append(usage_stats.get(hour_str, 0))
    
    usage_data = {
        'labels': labels,
        'data': data
    }
    
    html = STATS_PAGE.format(
        uptime=uptime,
        total_rolls=stats['total_rolls'],
        active_users=len(users),
        guilds_count=stats['guilds_count'],
        users_list=users_html,
        usage_data=json.dumps(usage_data),
        current_time=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    )
    
    return web.Response(text=html, content_type='text/html')

async def handle_root(request):
    """Root redirects to health"""
    return await handle_health(request)

async def start_web_server():
    """Start the web server"""
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/stats', handle_stats)
    
    port = int(os.getenv('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f'🌐 Web server started on port {port}')
    print(f'🏥 Health check: http://0.0.0.0:{port}/')
    print(f'📊 Stats page: http://0.0.0.0:{port}/stats (Protected)')

async def main():
    """Main function"""
    await start_web_server()
    
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in .env file!")
        return
    
    print("✅ Discord token loaded")
    
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot shutting down...")
    finally:
        if db_pool:
            db_pool.closeall()
            print("✅ Supabase connections closed")
