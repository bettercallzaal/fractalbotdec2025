# ZAO Fractal Voting System

A comprehensive Discord bot and web application for structured group decision-making through fractal voting. Create transparent, democratic voting processes with automatic group management, real-time results, and a beautiful web dashboard for tracking participation and progress.

## Overview

The ZAO Fractal Voting System streamlines group consensus-building with these core features:

- **Simplified Setup**: One command creates everything - no complex forms or setup
- **Auto-Generated Groups**: Smart naming with daily counters per server
- **Progressive Elimination**: Vote through rounds until one winner emerges
- **Public & Transparent**: All votes and results visible to everyone
- **Tie-Breaking**: Automatic random selection for tied votes
- **Multi-Channel Results**: Results posted to both fractal thread and general channel
- **Web Dashboard**: Beautiful Next.js web app for tracking participation and progress
- **Discord OAuth**: Seamless sign-in with Discord for personalized experience
- **Admin Controls**: Full management tools for moderators

## Key Features

### **🚀 Streamlined User Experience**
- **One-Command Setup**: `/zaofractal` does everything automatically
- **Smart Member Detection**: Pulls members from your current voice channel
- **Quick Confirmation**: Simple ✅/❌ buttons to start or modify participants
- **Auto-Naming**: Groups named "Fractal Group 1 - Nov 2, 2025" with daily counters

### **🎯 Transparent Voting Process**
- **Public Threads**: Everyone can see the voting process for full transparency
- **Real-Time Updates**: Live vote announcements as they happen
- **Vote Changes Allowed**: Participants can modify votes during each round
- **50% Threshold**: Requires majority support to advance (not just plurality)
- **Tie-Breaking**: Random selection when candidates tie with equal votes

### **📊 Comprehensive Results**
- **Round-by-Round Winners**: Clear announcements after each level
- **Final Rankings**: Complete 1st, 2nd, 3rd place results
- **Dual Distribution**: Results in fractal thread + summary in general channel
- **Persistent Archives**: Completed groups remain for future reference

### **🌐 Web Dashboard**
- **Discord OAuth Integration**: Sign in with your Discord account
- **Personal Statistics**: Track your fractal participation and wins
- **Real-Time Updates**: Live sync with Discord bot activities
- **Beautiful UI**: Modern, responsive design with Tailwind CSS
- **Database Integration**: PostgreSQL with Neon for reliable data storage

### **🛠️ Admin Management**
- **Complete Process Control**: Force round progression, pause/resume, restart fractals
- **Dynamic Member Management**: Add/remove members, change facilitators mid-fractal
- **Advanced Monitoring**: Detailed stats, server analytics, data export
- **Comprehensive Oversight**: 15 powerful admin commands for total control
- **Robust Error Handling**: All commands include validation and clear feedback

## Installation

### **Discord Bot Setup**

1. **Clone this repository:**
   ```bash
   git clone https://github.com/bettercallzaal/fractalbotnov2025.git
   cd fractalbotnov2025
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   # Edit .env and add your Discord bot token
   DISCORD_TOKEN=your_bot_token_here
   DEBUG=FALSE
   ```

4. **Run the bot:**
   ```bash
   python3 main.py
   ```

5. **Invite to your server:**
   Use the invite link shown in the console output with proper permissions.

### **Web Dashboard Setup**

1. **Navigate to web directory:**
   ```bash
   cd web
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # Copy example and edit with your values
   cp .env.example .env.local
   
   # Required variables:
   DISCORD_CLIENT_ID=your_discord_app_client_id
   DISCORD_CLIENT_SECRET=your_discord_app_client_secret
   NEXTAUTH_URL=http://localhost:3000
   NEXTAUTH_SECRET=your_nextauth_secret_key
   DATABASE_URL=your_postgresql_connection_string
   WEBHOOK_SECRET=your_webhook_secret
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

5. **Visit the dashboard:**
   Open [http://localhost:3000](http://localhost:3000) in your browser

### **Production Deployment**

The web dashboard is deployed on Vercel with Neon PostgreSQL:
- **Live URL**: [https://fractalbotnov2025.vercel.app](https://fractalbotnov2025.vercel.app)
- **Database**: Neon PostgreSQL with automatic scaling
- **Environment**: All variables configured via Vercel dashboard

## Usage

### **User Commands**
- **`/zaofractal`** - Create a new fractal voting group from your voice channel
- **`/status`** - Show current status of an active fractal group (use in fractal threads)
- **`/endgroup`** - End an active fractal group (facilitator only)

### **Admin Commands** (Requires Administrator permissions)

#### **Basic Management**
- **`/admin_end_fractal [thread_id]`** - Force end any fractal group
- **`/admin_list_fractals`** - List all active fractal groups with details
- **`/admin_cleanup`** - Remove old/stuck fractal groups

#### **Force Round Progression**
- **`/admin_force_round <thread_id>`** - Skip current voting and move to next level
- **`/admin_reset_votes <thread_id>`** - Clear all votes in current round
- **`/admin_declare_winner <thread_id> <user>`** - Manually declare a round winner

#### **Member Management**
- **`/admin_add_member <thread_id> <user>`** - Add someone to an active fractal
- **`/admin_remove_member <thread_id> <user>`** - Remove someone from active fractal
- **`/admin_change_facilitator <thread_id> <user>`** - Transfer facilitator role

#### **Group Control**
- **`/admin_pause_fractal <thread_id>`** - Temporarily pause voting
- **`/admin_resume_fractal <thread_id>`** - Resume paused fractal
- **`/admin_restart_fractal <thread_id>`** - Restart from beginning with same members

#### **Advanced Monitoring**
- **`/admin_fractal_stats <thread_id>`** - Detailed stats for specific group
- **`/admin_server_stats`** - Overall server fractal statistics
- **`/admin_export_data [thread_id]`** - Export fractal data as JSON file

### **Simplified Voting Process**

1. **Join a voice channel** with 2-6 members
2. **Run `/zaofractal`** in any text channel
3. **Confirm members** with ✅ or modify with ❌
4. **Public thread created** automatically (e.g., "Fractal Group 1 - Nov 2, 2025")
5. **Vote in rounds** by clicking candidate buttons
6. **Winners announced** after each round (requires 50%+ votes)
7. **Ties broken randomly** when candidates have equal votes
8. **Final results** posted to fractal thread and general channel
9. **Thread archived** but remains accessible for reference

## Project Structure

```
fractalbotnov2025/
├── main.py                  # Discord bot entry point and startup
├── .env                     # Environment variables (tokens, database)
├── requirements.txt         # Python dependencies
├── config/
│   ├── config.py           # Configuration parameters
│   └── .env.template       # Environment template
├── cogs/
│   ├── base.py             # Base cog with utility methods
│   └── fractal/
│       ├── __init__.py     # Package initialization
│       ├── cog.py          # Slash commands and admin tools
│       ├── group.py        # FractalGroup core voting logic
│       └── views.py        # UI components and member confirmation
├── utils/
│   └── logging.py          # Logging configuration
├── web/                     # Next.js Web Dashboard
│   ├── pages/              # Next.js pages and API routes
│   │   ├── index.tsx       # Main dashboard page
│   │   ├── _app.tsx        # App wrapper with NextAuth
│   │   └── api/            # API endpoints
│   │       ├── auth/       # NextAuth Discord OAuth
│   │       ├── fractals/   # Fractal data endpoints
│   │       ├── health.ts   # Health check endpoint
│   │       └── webhook.ts  # Discord bot webhook integration
│   ├── utils/              # Database and utility functions
│   │   ├── database.ts     # Neon PostgreSQL connection
│   │   └── schema.ts       # Database schema definitions
│   ├── types/              # TypeScript type definitions
│   ├── public/             # Static assets
│   ├── package.json        # Node.js dependencies
│   └── .env.example        # Web app environment template
└── vercel.json             # Vercel deployment configuration
```

## Recent Improvements (v4 - November 2025)

### **🌐 Web Dashboard Integration**
- **Next.js Web Application**: Beautiful, responsive dashboard for tracking participation
- **Discord OAuth**: Seamless sign-in with Discord accounts
- **Real-Time Sync**: Live integration between Discord bot and web dashboard
- **PostgreSQL Database**: Neon-hosted database for reliable data persistence
- **Vercel Deployment**: Production-ready hosting with automatic scaling

### **🎯 Enhanced User Experience**
- **Personal Statistics**: Track individual fractal participation and wins
- **Modern UI**: Tailwind CSS with beautiful, accessible design
- **Mobile Responsive**: Works perfectly on all device sizes
- **TypeScript**: Full type safety throughout the web application

### **🔧 Technical Architecture**
- **Database Schema**: Comprehensive tables for users, fractals, participants, voting rounds, and votes
- **API Integration**: RESTful endpoints for Discord bot webhook integration
- **Environment Management**: Secure configuration via Vercel and Neon integration
- **Migration Scripts**: Automated database setup and maintenance

### **📊 Previous Improvements (v3)**
- Removed complex modal forms - everything is now button-based
- Auto-generated group names eliminate user input requirements
- One-click member confirmation with modification options
- Public threads for full transparency
- Fixed "Unknown Interaction" errors with proper View/Modal patterns
- Added tie-breaking logic with random selection
- Implemented dual results posting (thread + general channel)
- Added 15 comprehensive admin management commands
- Advanced monitoring with detailed statistics and data export

## Configuration

### **Environment Variables**

**Discord Bot (.env):**
```bash
DISCORD_TOKEN=your_bot_token_here    # Required: Your Discord bot token
DEBUG=FALSE                          # Optional: Enable debug logging
```

**Web Dashboard (web/.env.local):**
```bash
# Discord OAuth
DISCORD_CLIENT_ID=your_discord_app_client_id
DISCORD_CLIENT_SECRET=your_discord_app_client_secret

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000  # or your production URL
NEXTAUTH_SECRET=your_nextauth_secret_key

# Database
DATABASE_URL=postgresql://username:password@host:5432/database

# Webhook Security
WEBHOOK_SECRET=your_webhook_secret_for_discord_bot
```

### **Bot Permissions Required**
- Send Messages
- Embed Links
- Attach Files
- Read Messages
- Manage Messages
- Manage Threads
- Create Public Threads
- Read Message History
- Add Reactions

## Admin Guide

### **Getting Thread IDs**
Most admin commands require a `thread_id` parameter:
1. **Right-click** on the fractal thread name
2. **Select "Copy ID"** (requires Developer Mode enabled)
3. **Use the ID** in admin commands

### **Common Admin Scenarios**
- **Stuck voting**: Use `/admin_force_round` to advance to next level
- **Member left mid-fractal**: Use `/admin_remove_member` to continue
- **Need to add spectator**: Use `/admin_add_member` to include them
- **Facilitator disconnected**: Use `/admin_change_facilitator` to transfer role
- **Process needs pause**: Use `/admin_pause_fractal` and `/admin_resume_fractal`
- **Start over**: Use `/admin_restart_fractal` to begin fresh

### **Monitoring & Analytics**
- **Individual fractal stats**: `/admin_fractal_stats` shows detailed metrics
- **Server overview**: `/admin_server_stats` displays server-wide statistics
- **Data analysis**: `/admin_export_data` creates JSON export for external tools

## Troubleshooting

### **Common Issues**
- **"Unknown Interaction" errors**: Fixed in v3 - update to latest version
- **Missing permissions**: Ensure bot has thread management permissions
- **Stuck fractals**: Use `/admin_force_round` or `/admin_cleanup`
- **No general channel found**: Bot will use first available text channel as fallback
- **Paused fractals**: Check with `/admin_fractal_stats` and resume if needed

### **Support**
- Check console logs for detailed error information
- Use `/admin_list_fractals` to see all active groups
- Use `/admin_server_stats` for server-wide overview
- Export data with `/admin_export_data` for analysis
- Restart bot if experiencing persistent issues

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the terms of the MIT License - see the LICENSE file for details.

---

**Version 4.0 (November 2025)** - Now with beautiful web dashboard and Discord OAuth integration! 🌐

**Full-Stack Solution** - Discord bot + Next.js web app + PostgreSQL database! 🚀

**Live Demo**: [https://fractalbotnov2025.vercel.app](https://fractalbotnov2025.vercel.app) ⚡
