import discord
import logging
from discord.ext import commands

class BaseCog(commands.Cog):
    """Base cog with utility methods for all cogs"""
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('bot')

    async def check_voice_state(self, user):
        """Check if user is in a voice channel and return eligible members"""
        # Validate user is in voice channel
        if not user.voice or not user.voice.channel:
            return {
                'success': False,
                'message': '❌ **You must be in a voice channel** to create a fractal group.\n💡 Join a voice channel and try again!',
                'members': [],
                'channel': None
            }
        
        voice_channel = user.voice.channel
        
        # Check if bot has permissions in voice channel
        bot_permissions = voice_channel.permissions_for(user.guild.me)
        if not bot_permissions.view_channel:
            return {
                'success': False,
                'message': f'❌ **Bot cannot access voice channel** {voice_channel.mention}\n💡 Please check bot permissions!',
                'members': [],
                'channel': voice_channel
            }
        
        # Get non-bot members (with additional validation)
        try:
            all_members = voice_channel.members
            members = [m for m in all_members if not m.bot and m.guild_permissions.send_messages]
        except Exception as e:
            self.logger.error(f"Error getting voice channel members: {e}")
            return {
                'success': False,
                'message': '❌ **Error accessing voice channel members.** Please try again.',
                'members': [],
                'channel': voice_channel
            }
        
        # Enhanced member count validation
        if len(members) < 1:
            return {
                'success': False,
                'message': f'❌ **No eligible members found** in {voice_channel.mention}\n💡 Make sure members have text permissions!',
                'members': [],
                'channel': voice_channel
            }
        
        if len(members) < 2:
            member_list = ", ".join([m.display_name for m in members])
            return {
                'success': False,
                'message': f'❌ **Need at least 2 members** for a fractal group.\n**Current:** {member_list}\n💡 Invite more people to join the voice channel!',
                'members': members,
                'channel': voice_channel
            }
        
        if len(members) > 6:
            return {
                'success': False,
                'message': f'❌ **Too many members** ({len(members)}/6 max) in {voice_channel.mention}\n💡 Fractal groups work best with 2-6 people for optimal discussion time.',
                'members': members[:6],  # Return first 6 for reference
                'channel': voice_channel
            }
        
        return {
            'success': True,
            'message': f'✅ **Found {len(members)} eligible members** in {voice_channel.mention}',
            'members': members,
            'channel': voice_channel
        }

async def setup(bot):
    await bot.add_cog(BaseCog(bot))
