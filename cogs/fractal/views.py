import discord
import logging
from typing import Callable, Dict, List
from .group import FractalGroup

class ZAOFractalVotingView(discord.ui.View):
    """UI view with voting buttons for fractal rounds"""
    
    def __init__(self, fractal_group):
        super().__init__(timeout=None)  # No timeout for persistent buttons
        self.fractal_group = fractal_group
        self.logger = logging.getLogger('bot')
        
        # Create voting buttons
        self.create_voting_buttons()
    
    def create_voting_buttons(self):
        """Create a button for each active candidate"""
        # Clear any existing buttons
        self.clear_items()
        
        # List of button styles to cycle through
        styles = [
            discord.ButtonStyle.primary,    # Blue
            discord.ButtonStyle.success,    # Green
            discord.ButtonStyle.danger,     # Red 
            discord.ButtonStyle.secondary   # Grey
        ]
        
        # Create a button for each candidate
        for i, candidate in enumerate(self.fractal_group.active_candidates):
            # Cycle through button styles
            style = styles[i % len(styles)]
            
            # Create button with candidate name
            button = discord.ui.Button(
                style=style,
                label=candidate.display_name,
                custom_id=f"vote_{candidate.id}"
            )
            
            # Create and assign callback
            button.callback = self.create_vote_callback(candidate)
            self.add_item(button)
            
        self.logger.info(f"Created {len(self.fractal_group.active_candidates)} voting buttons")
    
    def create_vote_callback(self, candidate):
        """Create a callback function for voting buttons"""
        async def vote_callback(interaction):
            # Always defer response immediately to avoid timeout
            await interaction.response.defer(ephemeral=True)
            
            try:
                # Process the vote (public announcement happens in process_vote)
                await self.fractal_group.process_vote(interaction.user, candidate)
                
                # Confirm to the voter (private)
                await interaction.followup.send(
                    f"You voted for {candidate.display_name}",
                    ephemeral=True
                )
                
            except Exception as e:
                self.logger.error(f"Error processing vote: {e}", exc_info=True)
                await interaction.followup.send(
                    "❌ Error recording your vote. Please try again.",
                    ephemeral=True
                )
                
        return vote_callback


class MemberConfirmationView(discord.ui.View):
    """A view for confirming fractal group members"""
    def __init__(self, cog, members, facilitator):
        super().__init__(timeout=60)
        self.cog = cog
        self.members = members
        self.facilitator = facilitator
        self.awaiting_modification = False
    
    @discord.ui.button(label="✅ Start Fractal", style=discord.ButtonStyle.success)
    async def confirm_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the fractal with current members"""
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can start the fractal.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Generate group name
        group_name = self.cog._get_next_group_name(interaction.guild.id)
        
        # Look for fractal-bot channel first, then fall back to current channel
        fractal_bot_channel = discord.utils.get(interaction.guild.text_channels, name="fractal-bot")
        if fractal_bot_channel:
            channel = fractal_bot_channel
        else:
            # Get the parent channel (in case we're in a thread)
            channel = interaction.channel
            if isinstance(channel, discord.Thread):
                channel = channel.parent
            elif isinstance(channel, discord.VoiceChannel):
                # If somehow we're in a voice channel, find a suitable text channel
                channel = interaction.guild.system_channel or interaction.guild.text_channels[0]
        
        # Create public thread
        thread = await channel.create_thread(
            name=group_name,
            type=discord.ChannelType.public_thread,
            reason="ZAO Fractal Group"
        )
        
        # Add all members to thread
        for member in self.members:
            try:
                await thread.add_user(member)
            except discord.HTTPException:
                pass  # Member might already be in thread or have permissions issues
        
        # Create and start fractal group
        fractal_group = FractalGroup(
            thread=thread,
            members=self.members,
            facilitator=self.facilitator,
            cog=self.cog
        )
        
        # Store active group
        self.cog.active_groups[thread.id] = fractal_group
        
        # Update original message first to avoid timeout
        try:
            await interaction.edit_original_response(
                content=f"✅ **Fractal started!** Check {thread.mention}",
                view=None
            )
        except:
            pass  # Interaction might have timed out, but continue anyway
        
        # Start the fractal (this might take a moment)
        try:
            await fractal_group.start_fractal()
        except Exception as e:
            # If fractal start fails, send error to thread
            await thread.send(f"❌ Error starting fractal: {str(e)}")
            raise
    
    @discord.ui.button(label="❌ Modify Members", style=discord.ButtonStyle.secondary)
    async def modify_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Allow modification of member list"""
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can modify members.", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "**To modify members:**\n"
            "• Remove people: `@username @username`\n"
            "• Add people: `@username @username`\n"
            "• Then click ✅ to start",
            ephemeral=True
        )
        self.awaiting_modification = True


class VoiceFractalControlView(discord.ui.View):
    """Control panel for voice fractal speaking phase"""
    
    def __init__(self, fractal_group):
        super().__init__(timeout=None)
        self.fractal = fractal_group
    
    def is_facilitator(self, user: discord.Member) -> bool:
        """Check if user is the facilitator"""
        return user == self.fractal.facilitator
    
    def can_control_speaking(self, user: discord.Member) -> bool:
        """Check if user can control speaking (facilitator or current speaker)"""
        return (user == self.fractal.facilitator or 
                (self.fractal.speaking_queue and user == self.fractal.speaking_queue.current_speaker))
    
    @discord.ui.button(label="⏭️ Next Speaker", style=discord.ButtonStyle.primary)
    async def next_speaker(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Advance to next speaker"""
        if not self.can_control_speaking(interaction.user):
            await interaction.response.send_message(
                "Only facilitator or current speaker can advance.", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        await self.fractal.advance_speaker()
    
    @discord.ui.button(label="⏸️ Skip & Return", style=discord.ButtonStyle.secondary)
    async def skip_speaker(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip current speaker, add them back to queue"""
        if not self.is_facilitator(interaction.user):
            await interaction.response.send_message(
                "Only facilitator can skip speakers.", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        await self.fractal.skip_current_speaker()
    
    @discord.ui.button(label="🗳️ Skip to Voting", style=discord.ButtonStyle.success)
    async def skip_to_voting(self, interaction: discord.Interaction, button: discord.ui.Button):
        """End speaking phase and go to voting"""
        if not self.is_facilitator(interaction.user):
            await interaction.response.send_message(
                "Only facilitator can skip to voting.", 
                ephemeral=True
            )
            return
        
        # Show confirmation if there are remaining speakers
        remaining = self.fractal.speaking_queue.get_remaining_speakers()
        if len(remaining) > 1:  # More than just current speaker
            view = ConfirmEndEarlyView(self.fractal, remaining)
            remaining_names = ", ".join([u.display_name for u in remaining[1:]])  # Skip current speaker
            await interaction.response.send_message(
                f"⚠️ **End speaking phase early?**\n"
                f"**{len(remaining)-1} speakers** haven't spoken yet: {remaining_names}",
                view=view, 
                ephemeral=True
            )
        else:
            await interaction.response.defer()
            await self.fractal.transition_to_voting()
    
    @discord.ui.button(label="⏱️ +30s", style=discord.ButtonStyle.success)
    async def extend_30s(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add 30 seconds to current speaker"""
        if not self.is_facilitator(interaction.user):
            await interaction.response.send_message(
                "Only facilitator can extend time.", 
                ephemeral=True
            )
            return
        
        await self.fractal.extend_speaking_time(30)
        await interaction.response.send_message("⏱️ Added 30 seconds", ephemeral=True)
    
    @discord.ui.button(label="⏱️ +1m", style=discord.ButtonStyle.success)
    async def extend_1m(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add 1 minute to current speaker"""
        if not self.is_facilitator(interaction.user):
            await interaction.response.send_message(
                "Only facilitator can extend time.", 
                ephemeral=True
            )
            return
        
        await self.fractal.extend_speaking_time(60)
        await interaction.response.send_message("⏱️ Added 1 minute", ephemeral=True)


class ConfirmEndEarlyView(discord.ui.View):
    """Confirmation dialog for ending speaking phase early"""
    
    def __init__(self, fractal_group, remaining_speakers):
        super().__init__(timeout=30)
        self.fractal = fractal_group
        self.remaining_speakers = remaining_speakers
    
    @discord.ui.button(label="✅ End Early", style=discord.ButtonStyle.danger)
    async def confirm_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm ending speaking phase early"""
        await interaction.response.defer()
        await self.fractal.transition_to_voting()
        
        # Edit original message to show confirmation
        try:
            await interaction.edit_original_response(
                content="✅ Speaking phase ended early - moving to voting!",
                view=None
            )
        except:
            pass
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_end(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel ending early"""
        await interaction.response.edit_message(
            content="❌ Cancelled - continuing speaking phase",
            view=None
        )


class VoiceMemberConfirmationView(MemberConfirmationView):
    """Extended confirmation view for voice fractals"""
    
    def __init__(self, cog, members, facilitator, voice_channel, speaking_time):
        super().__init__(cog, members, facilitator)
        self.voice_channel = voice_channel
        self.speaking_time = speaking_time
    
    async def confirm_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start voice-enabled fractal"""
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can start the fractal.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Use existing thread creation logic
        group_name = self.cog._get_next_group_name(interaction.guild.id)
        
        # Look for fractal-bot channel first, then fall back to current channel
        fractal_bot_channel = discord.utils.get(interaction.guild.text_channels, name="fractal-bot")
        if fractal_bot_channel:
            channel = fractal_bot_channel
        else:
            channel = interaction.channel
            
            # Ensure we have a text channel that can create threads
            if isinstance(channel, discord.Thread):
                channel = channel.parent
            elif isinstance(channel, discord.VoiceChannel):
                # If somehow we're in a voice channel, find a suitable text channel
                channel = interaction.guild.system_channel or interaction.guild.text_channels[0]
        
        thread = await channel.create_thread(
            name=group_name,
            type=discord.ChannelType.public_thread,
            reason="ZAO Fractal Group"
        )
        
        # Add members (existing logic)
        for member in self.members:
            try:
                await thread.add_user(member)
            except discord.HTTPException:
                pass
        
        # Create VOICE-ENABLED fractal group
        fractal_group = FractalGroup(
            thread=thread,
            members=self.members,
            facilitator=self.facilitator,
            cog=self.cog,
            voice_channel=self.voice_channel,  # NEW!
            speaking_time=self.speaking_time   # NEW!
        )
        
        # Store and start (existing pattern)
        self.cog.active_groups[thread.id] = fractal_group
        
        await interaction.edit_original_response(
            content=f"✅ **Voice Fractal started!** Check {thread.mention}",
            view=None
        )
        
        # This will start voice phase first, then transition to voting
        await fractal_group.start_fractal()
