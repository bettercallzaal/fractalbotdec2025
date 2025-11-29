# ZAO Fractal Voting System

A comprehensive Discord bot and web application for structured group decision-making through fractal voting. Features **voice-enabled speaking rounds** followed by silent voting, creating transparent, democratic processes with automatic group management, real-time results, and a beautiful web dashboard.

## What's New in December 2025

### Integrated Voice-Enabled Fractals
**Major Update**: Voice speaking rounds are now built into the main fractal experience!

- **Enhanced Command**: `/fractaltimer [speaking_time]` now includes voice speaking rounds by default
- **Smart Timer System**: Automatic warnings, speaker transitions, and queue management
- **Voice Control Panel**: Real-time controls for facilitators and speakers
- **Seamless Flow**: Speaking rounds → Auto-transition to voting → Results
- **Customizable**: Optional speaking time parameter (1-10 minutes, default: 2)

## Integrated Fractal Experience

Every fractal now combines structured speaking rounds with voting for the ultimate democratic experience!

### Unified Fractal Process
**`/fractaltimer [speaking_time]`**: Voice speaking rounds → Auto-transition to voting → Results

## Overview

The ZAO Fractal Voting System streamlines group consensus-building with these core features:

- **Voice Speaking Rounds**: Timed speaking phases with queue management
- **Smart Timer System**: Automatic warnings and speaker transitions
- **Voice Control Panel**: Next speaker, skip & return, time extensions
- **Silent Voting Phase**: Traditional button voting after discussions
- **Progressive Elimination**: Vote through rounds until one winner emerges
- **Public & Transparent**: All phases visible to everyone
- **Tie-Breaking**: Automatic random selection for tied votes
- **Multi-Channel Results**: Results posted to both fractal thread and general channel
- **Web Dashboard**: Beautiful Next.js web app for tracking participation and progress
- **Discord OAuth**: Seamless sign-in with Discord for personalized experience
- **Admin Controls**: Full management tools for moderators
- **🎙️ Voice Speaking Rounds**: Timed speaking phases with queue management
- **⏱️ Smart Timer System**: Automatic warnings and speaker transitions
- **🎛️ Voice Control Panel**: Next speaker, skip & return, time extensions
- **🗳️ Silent Voting Phase**: Traditional button voting after discussions
- **📊 Progressive Elimination**: Vote through rounds until one winner emerges
- **🔍 Public & Transparent**: All phases visible to everyone
- **🎲 Tie-Breaking**: Automatic random selection for tied votes
- **📱 Multi-Channel Results**: Results posted to both fractal thread and general channel
- **🌐 Web Dashboard**: Beautiful Next.js web app for tracking participation and progress
- **🔐 Discord OAuth**: Seamless sign-in with Discord for personalized experience
- **⚙️ Admin Controls**: Full management tools for moderators

## Key Features

### **🎙️ Voice-Enabled Fractals (NEW)**
- **Timed Speaking Rounds**: Each participant gets equal speaking time (1-10 minutes)
- **Smart Queue Management**: Automatic speaker progression with skip/return options
- **Real-Time Control Panel**: Facilitator controls for managing speaking flow
- **Voice Channel Integration**: Seamlessly works with Discord voice channels
- **Flexible Timing**: Extend speaking time on-the-fly (+30s, +1m buttons)
- **Early Termination**: Skip remaining speakers and jump to voting
- **Automatic Transition**: Seamlessly moves from speaking to voting phase

### **🎛️ Voice Control System**
- **⏭️ Next Speaker**: Advance to next person (facilitator or current speaker)
- **⏸️ Skip & Return**: Skip unavailable speaker, add them back to queue
- **🗳️ Skip to Voting**: End speaking phase early and start voting
- **⏱️ Time Extensions**: Add 30 seconds or 1 minute to current speaker
- **📊 Real-Time Display**: Live queue status with remaining speakers and time

### **🚀 Streamlined User Experience**
- **Simple Command**: `/fractaltimer` - integrated voice and voting experience
- **Smart Member Detection**: Pulls members from your current voice channel
- **Quick Confirmation**: Simple ✅/❌ buttons to start or modify participants
- **Auto-Naming**: Groups named "Fractal Group 1 - Dec 1, 2025" with daily counters
- **Flexible Setup**: Works in any text channel, creates dedicated threads

### **🎯 Transparent Voting Process**
- **Public Threads**: Everyone can see the entire process for full transparency
- **Real-Time Updates**: Live announcements for speaking and voting phases
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
   git clone https://github.com/bettercallzaal/fractalbotdec2025.git
   cd fractalbotdec2025
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

### **🎙️ Main Fractal Command**

#### **`/fractaltimer [speaking_time]`**
Create a fractal with integrated voice speaking rounds followed by voting.

**Parameters:**
- `speaking_time` (optional): Minutes each person gets to speak (1-10, default: 2)

**Example Usage:**
```
/fractaltimer
/fractaltimer speaking_time:3
/fractaltimer speaking_time:1
```

**Integrated Process Flow:**
1. **Setup**: Bot detects members in your voice channel, shows confirmation
2. **Speaking Phase**: Each person gets timed speaking rounds with control panel
3. **Auto-Transition**: Seamlessly moves to voting after everyone speaks
4. **Voting Phase**: Silent voting with traditional button system
5. **Results**: Winner announcements and level progression

#### **Voice Control Panel** (Available during speaking phase)
- **⏭️ Next Speaker**: Advance to next person (facilitator or current speaker can use)
- **⏸️ Skip & Return**: Skip current speaker, add them back to queue (facilitator only)
- **🗳️ Skip to Voting**: End speaking phase early and start voting (facilitator only)
- **⏱️ +30s / +1m**: Add time to current speaker (facilitator only)

### **📊 Status & Management Commands**
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

## 🎯 Complete Fractal Process Example

### **🎙️ Integrated Fractal Flow**

1. **Join a voice channel** with 2-6 members
2. **Run `/fractaltimer speaking_time:3`** in any text channel
3. **Confirm setup** - Bot shows voice channel, speaking time, and member list
4. **Click ✅ Start Fractal** - Public thread created automatically (e.g., "Fractal Group 1 - Dec 1, 2025")

#### **Speaking Phase**
5. **Speaking rounds begin** - Each person gets 3 minutes to speak
   ```
   🎙️ ZAO Fractal - Level 6 Speaking Phase
   Current Speaker: @alice (2:30 remaining)
   Queue: @bob → @charlie → @dave
   
   [⏭️ Next Speaker] [⏸️ Skip & Return] [🗳️ Skip to Voting] [⏱️ +30s] [⏱️ +1m]
   ```
6. **Timer warnings** - "⏰ @alice - 1 minute remaining!"
7. **Auto-advance** - "⏱️ Time's up @alice!" → Next speaker starts
8. **Flexible control** - Skip unavailable speakers, extend time, or end early

#### **Automatic Transition to Voting**
9. **Seamless transition** - "🗣️ Speaking phase complete! 🗳️ Now starting silent voting phase..."
10. **Vote in rounds** by clicking candidate buttons
11. **Winners announced** after each round (requires 50%+ votes)
12. **Ties broken randomly** when candidates have equal votes
13. **Final results** posted to fractal thread and general channel
14. **Thread archived** but remains accessible for reference

### **🎛️ Voice Control Examples**

#### **Normal Flow:**
```
🎙️ Current: @alice (1:30 remaining)
Queue: @bob → @charlie → @dave
[User clicks "Next Speaker"]
🎙️ Current: @bob (3:00 remaining)  
Queue: @charlie → @dave → @alice
```

#### **Skip & Return Flow:**
```
🎙️ Current: @bob (1:45 remaining)
[Facilitator clicks "Skip & Return" - @bob is AFK]
⏸️ @bob skipped - will return later
🎙️ Current: @charlie (3:00 remaining)
Queue: @dave → @alice → @bob
```

#### **Early End Flow:**
```
[Facilitator clicks "Skip to Voting"]
⚠️ End speaking phase early?
2 speakers haven't spoken yet: @dave, @alice
[✅ End Early] [❌ Cancel]
[If confirmed] 🗳️ Moving to voting phase...
```

## Project Structure

```
fractalbotdec2025/
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
│       ├── cog.py          # Slash commands (/fractaltimer) and admin tools
│       ├── group.py        # FractalGroup with voice phase and voting logic
│       ├── speaking_queue.py # Voice queue management and timer system (NEW)
│       └── views.py        # UI components, voice controls, and confirmations
├── utils/
│   ├── logging.py          # Logging configuration
│   └── web_integration.py  # Webhook integration for web dashboard
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

## **🎉 DEPLOYMENT STATUS - FULLY OPERATIONAL**

### **✅ Production Deployment Complete:**
- **Web Dashboard**: [https://fractalbotnov2025.vercel.app](https://fractalbotnov2025.vercel.app) - **LIVE & WORKING** 🟢
- **Discord OAuth**: Fully functional authentication flow ✅
- **Database**: Neon PostgreSQL with all tables created and operational ✅
- **API Endpoints**: All routes working (`/api/health`, `/api/auth/*`, `/api/fractals`) ✅
- **Environment Variables**: All configured in Vercel dashboard ✅

### **🔧 Technical Stack Deployed:**
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Authentication**: NextAuth.js with Discord OAuth provider
- **Database**: Neon PostgreSQL with Drizzle ORM
- **Hosting**: Vercel with automatic deployments from GitHub
- **Environment**: Production-ready with proper error handling

### **🚀 Ready for Use:**
1. **Discord Bot**: Deploy the Python bot to start fractal voting sessions
2. **Web Dashboard**: Users can sign in and track their participation
3. **Database Integration**: All user data and fractal results are stored
4. **Real-Time Sync**: Bot and web app share the same database

### **🔍 Deployment Verification:**
- **Health Check**: [https://fractalbotnov2025.vercel.app/api/health](https://fractalbotnov2025.vercel.app/api/health)
- **Session Check**: [https://fractalbotnov2025.vercel.app/api/auth/session](https://fractalbotnov2025.vercel.app/api/auth/session)
- **Fractals API**: [https://fractalbotnov2025.vercel.app/api/fractals](https://fractalbotnov2025.vercel.app/api/fractals)

### **📋 Deployment Checklist Completed:**
- ✅ Environment variables configured in Vercel
- ✅ Database tables created in Neon console
- ✅ Discord OAuth redirect URLs added
- ✅ Vercel routing configuration fixed
- ✅ Database schema columns added (`wallet_type`, `total_votes`)
- ✅ All API endpoints returning proper responses
- ✅ Discord sign-in flow working end-to-end

---

**Version 4.0 (November 2025)** - Now with beautiful web dashboard and Discord OAuth integration! 🌐

**Full-Stack Solution** - Discord bot + Next.js web app + PostgreSQL database! 🚀

**Live Demo**: [https://fractalbotnov2025.vercel.app](https://fractalbotnov2025.vercel.app) ⚡
