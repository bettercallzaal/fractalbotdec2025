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
        
        # For button interactions, we need to defer differently
        try:
            await interaction.response.defer()
        except discord.InteractionResponded:
            # Interaction already responded to, continue
            pass
        
        # Generate group name
        group_name = self.cog._get_next_group_name(interaction.guild.id)
        
        # Look for fractal-bot channel first, then fall back to current channel
        channel = interaction.channel
        fractal_bot_channel = discord.utils.get(interaction.guild.text_channels, name="fractal-bot")
        
        # Try to use fractal-bot channel if it exists and bot has permissions
        if fractal_bot_channel:
            try:
                # Check if bot can create threads in fractal-bot channel
                bot_permissions = fractal_bot_channel.permissions_for(interaction.guild.me)
                if bot_permissions.create_public_threads:
                    channel = fractal_bot_channel
                    self.cog.logger.info(f"Using fractal-bot channel for thread creation")
                else:
                    self.cog.logger.warning(f"No thread creation permissions in fractal-bot channel, using fallback")
            except Exception as e:
                self.cog.logger.error(f"Error checking fractal-bot channel permissions: {e}")
        
        # Get the parent channel (in case we're in a thread)
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
        
        # Get the actual original channel (not thread)
        original_channel = interaction.channel
        if isinstance(interaction.channel, discord.Thread):
            original_channel = interaction.channel.parent
        
        # Create and start fractal group
        fractal_group = FractalGroup(
            thread=thread,
            members=self.members,
            facilitator=self.facilitator,
            cog=self.cog,
            original_channel=original_channel
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


class VoiceMemberConfirmationView(discord.ui.View):
    """Extended confirmation view for voice fractals with two button options"""
    
    def __init__(self, cog, members, facilitator, voice_channel, speaking_time):
        super().__init__(timeout=60)
        self.cog = cog
        self.members = members
        self.facilitator = facilitator
        self.voice_channel = voice_channel
        self.speaking_time = speaking_time
        self.awaiting_modification = False
    
    @discord.ui.button(label="🗳️ Start Fractal", style=discord.ButtonStyle.success, row=0)
    async def start_fractal_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start fractal with voting only (no speaking phase)"""
        self.cog.logger.info(f"Start Fractal (voting only) called by {interaction.user.display_name}")
        
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can start the fractal.", ephemeral=True)
            return
        
        await self._create_fractal_group(interaction, start_speaking=False)
    
    @discord.ui.button(label="⏱️ Start Timer Only", style=discord.ButtonStyle.primary, row=0)
    async def start_timer_only(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start timer in voice channel without creating thread"""
        self.cog.logger.info(f"Start Timer Only (no thread) called by {interaction.user.display_name}")
        
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can start the fractal.", ephemeral=True)
            return
        
        await self._start_timer_only(interaction)
    
    @discord.ui.button(label="⏱️ Start Timer + Voting", style=discord.ButtonStyle.secondary, row=1)
    async def start_with_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start fractal with speaking phase and timers"""
        self.cog.logger.info(f"Start Timer + Voting called by {interaction.user.display_name}")
        
        if interaction.user != self.facilitator:
            await interaction.response.send_message("Only the facilitator can start the fractal.", ephemeral=True)
            return
        
        await self._create_fractal_group(interaction, start_speaking=True)
    
    async def _start_timer_only(self, interaction: discord.Interaction):
        """Start timer system in voice channel without creating any threads"""
        self.cog.logger.info("Starting timer-only mode (no threads)")
        
        try:
            await interaction.response.defer()
            self.cog.logger.info("Interaction deferred successfully")
        except discord.InteractionResponded:
            self.cog.logger.info("Interaction already responded, continuing")
            pass
        except Exception as e:
            self.cog.logger.error(f"Error deferring interaction: {e}")
            return
        
        # Create a simple timer system without FractalGroup or threads
        from .speaking_queue import SpeakingQueue, VoiceTimer
        
        # Create speaking queue and timer
        speaking_queue = SpeakingQueue(self.members)
        voice_timer = VoiceTimer(self.speaking_time)
        
        # Store timer info in a simple way (not using FractalGroup)
        timer_data = {
            'speaking_queue': speaking_queue,
            'voice_timer': voice_timer,
            'voice_channel': self.voice_channel,
            'facilitator': self.facilitator,
            'members': self.members,
            'speaking_time': self.speaking_time
        }
        
        # Store in a simple way for cleanup later
        self.cog.active_timers = getattr(self.cog, 'active_timers', {})
        self.cog.active_timers[self.voice_channel.id] = timer_data
        
        # Update interaction response
        try:
            await interaction.edit_original_response(
                content=f"⏱️ **Timer started in {self.voice_channel.mention}!**\n"
                        f"🎙️ Each person gets {self.speaking_time//60} minutes to speak",
                view=None
            )
            self.cog.logger.info("Interaction response updated successfully")
        except Exception as e:
            self.cog.logger.error(f"Failed to update interaction response: {e}")
        
        # Start first speaker
        await self._start_next_timer_speaker(timer_data)
    
    async def _start_next_timer_speaker(self, timer_data):
        """Start the next speaker in timer-only mode"""
        speaking_queue = timer_data['speaking_queue']
        voice_timer = timer_data['voice_timer']
        voice_channel = timer_data['voice_channel']
        
        next_speaker = speaking_queue.next_speaker()
        if not next_speaker:
            # All speakers done
            await voice_channel.send("🎉 **All speakers have finished!**")
            # Clean up
            if hasattr(self.cog, 'active_timers') and voice_channel.id in self.cog.active_timers:
                del self.cog.active_timers[voice_channel.id]
            return
        
        # Send speaker announcement
        await voice_channel.send(f"🎙️ **{next_speaker.mention} is now speaking** ({timer_data['speaking_time']//60} minutes)")
        
        # Start timer with callbacks
        async def warning_callback(speaker, seconds):
            await voice_channel.send(f"⏰ {speaker.mention} - {seconds} seconds remaining!")
        
        async def complete_callback(speaker):
            await self._timer_complete(speaker, timer_data)
        
        await voice_timer.start_timer(
            next_speaker,
            voice_channel,
            warning_callback=warning_callback,
            complete_callback=complete_callback
        )
    
    async def _timer_complete(self, speaker, timer_data):
        """Called when timer completes in timer-only mode"""
        voice_channel = timer_data['voice_channel']
        await voice_channel.send(f"⏱️ Time's up {speaker.mention}!")
        # Auto-advance to next speaker
        await self._start_next_timer_speaker(timer_data)
    
    async def _create_fractal_group(self, interaction: discord.Interaction, start_speaking: bool):
        """Create fractal group and optionally start speaking phase"""
        self.cog.logger.info(f"Creating fractal group, start_speaking={start_speaking}")
        
        # For button interactions, we need to defer differently
        self.cog.logger.info("Attempting to defer interaction")
        try:
            await interaction.response.defer()
            self.cog.logger.info("Interaction deferred successfully")
        except discord.InteractionResponded:
            # Interaction already responded to, continue
            self.cog.logger.info("Interaction already responded, continuing")
            pass
        except Exception as e:
            self.cog.logger.error(f"Error deferring interaction: {e}")
            return
        
        # Use existing thread creation logic
        self.cog.logger.info("Generating group name")
        group_name = self.cog._get_next_group_name(interaction.guild.id)
        self.cog.logger.info(f"Generated group name: {group_name}")
        
        # Look for fractal-bot channel first, then fall back to current channel
        channel = interaction.channel
        self.cog.logger.info(f"Initial channel: {channel.name} (type: {type(channel).__name__})")
        fractal_bot_channel = discord.utils.get(interaction.guild.text_channels, name="fractal-bot")
        
        # Try to use fractal-bot channel if it exists and bot has permissions
        if fractal_bot_channel:
            self.cog.logger.info("Found fractal-bot channel, checking permissions")
            try:
                # Check if bot can create threads in fractal-bot channel
                bot_permissions = fractal_bot_channel.permissions_for(interaction.guild.me)
                if bot_permissions.create_public_threads:
                    channel = fractal_bot_channel
                    self.cog.logger.info(f"Using fractal-bot channel for thread creation")
                else:
                    self.cog.logger.warning(f"No thread creation permissions in fractal-bot channel, using fallback")
            except Exception as e:
                self.cog.logger.error(f"Error checking fractal-bot channel permissions: {e}")
        else:
            self.cog.logger.info("No fractal-bot channel found, using current channel")
        
        # Ensure we have a text channel that can create threads
        if isinstance(channel, discord.Thread):
            self.cog.logger.info("Channel is a thread, using parent")
            channel = channel.parent
        elif isinstance(channel, discord.VoiceChannel):
            self.cog.logger.info("Channel is voice channel, finding text channel")
            # If somehow we're in a voice channel, find a suitable text channel
            channel = interaction.guild.system_channel or interaction.guild.text_channels[0]
        
        self.cog.logger.info(f"Creating thread '{group_name}' in channel {channel.name}")
        try:
            thread = await channel.create_thread(
                name=group_name,
                type=discord.ChannelType.public_thread,
                reason="ZAO Fractal Group"
            )
            self.cog.logger.info(f"Thread created successfully: {thread.name} (ID: {thread.id})")
        except Exception as e:
            self.cog.logger.error(f"Failed to create thread: {e}")
            await interaction.edit_original_response(
                content=f"❌ **Failed to create fractal thread:** {str(e)}",
                view=None
            )
            return
        
        # Add members (existing logic)
        for member in self.members:
            try:
                await thread.add_user(member)
            except discord.HTTPException:
                pass
        
        # Create VOICE-ENABLED fractal group
        self.cog.logger.info(f"Creating FractalGroup with {len(self.members)} members, voice_channel={self.voice_channel.name}, speaking_time={self.speaking_time}")
        # Use voice channel for timer notifications since that's where people are
        timer_channel = self.voice_channel
        
        self.cog.logger.info(f"Voice channel for timer notifications: {timer_channel.name} (ID: {timer_channel.id})")
        self.cog.logger.info(f"Thread for voting: {thread.name} (ID: {thread.id})")
        try:
            fractal_group = FractalGroup(
                thread=thread,
                members=self.members,
                facilitator=self.facilitator,
                cog=self.cog,
                voice_channel=self.voice_channel,
                speaking_time=self.speaking_time,
                original_channel=timer_channel  # Send timer notifications to voice channel
            )
            self.cog.logger.info("FractalGroup created successfully")
        except Exception as e:
            self.cog.logger.error(f"Failed to create FractalGroup: {e}")
            await interaction.edit_original_response(
                content=f"❌ **Failed to create fractal group:** {str(e)}",
                view=None
            )
            return
        
        # Store and start (existing pattern)
        self.cog.logger.info(f"Storing fractal group with thread ID {thread.id}")
        self.cog.active_groups[thread.id] = fractal_group
        
        self.cog.logger.info("Updating interaction response")
        try:
            await interaction.edit_original_response(
                content=f"✅ **Voice Fractal started!** Check {thread.mention}",
                view=None
            )
            self.cog.logger.info("Interaction response updated successfully")
        except Exception as e:
            self.cog.logger.error(f"Failed to update interaction response: {e}")
        
        # Start the appropriate phase based on user choice
        self.cog.logger.info(f"Starting fractal, speaking phase: {start_speaking}")
        try:
            if start_speaking:
                # Start with speaking phase
                await fractal_group.start_voice_phase()
                self.cog.logger.info("Speaking phase started successfully")
            else:
                # Start with voting only
                await fractal_group.start_voting_only()
                self.cog.logger.info("Voting phase started successfully")
        except Exception as e:
            self.cog.logger.error(f"Failed to start fractal phase: {e}")
            await thread.send(f"❌ **Error starting fractal:** {str(e)}")


class FractalOptionsView(discord.ui.View):
    """View for choosing how to proceed with the fractal"""
    
    def __init__(self, fractal_group):
        super().__init__(timeout=300)  # 5 minute timeout
        self.fractal_group = fractal_group
    
    @discord.ui.button(label="🎙️ Start Speaking Phase", style=discord.ButtonStyle.primary, row=0)
    async def start_speaking(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Start the timed speaking phase"""
        if interaction.user != self.fractal_group.facilitator:
            await interaction.response.send_message("Only the facilitator can control the fractal.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Start the voice phase
            await self.fractal_group.start_voice_phase()
            
            # Update the message to remove buttons
            await interaction.edit_original_response(
                content=f"{interaction.message.content}\n\n✅ **Speaking phase started!**",
                view=None
            )
            
        except Exception as e:
            await interaction.followup.send(f"❌ **Error starting speaking phase:** {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🗳️ Skip to Voting", style=discord.ButtonStyle.secondary, row=0)
    async def skip_to_voting(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Skip speaking phase and go directly to voting"""
        if interaction.user != self.fractal_group.facilitator:
            await interaction.response.send_message("Only the facilitator can control the fractal.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Skip voice phase and start voting
            self.fractal_group.voice_phase_active = False
            await self.fractal_group.start_voting_only()
            
            # Update the message to remove buttons
            await interaction.edit_original_response(
                content=f"{interaction.message.content}\n\n✅ **Skipped to voting phase!**",
                view=None
            )
            
        except Exception as e:
            await interaction.followup.send(f"❌ **Error starting voting:** {str(e)}", ephemeral=True)
