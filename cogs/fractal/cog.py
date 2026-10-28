import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
from datetime import datetime
from ..base import BaseCog
from .views import MemberConfirmationView, VoiceMemberConfirmationView
from .group import FractalGroup

class FractalCog(BaseCog):
    """Cog for handling ZAO Fractal voting commands and logic"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.logger = logging.getLogger('bot')
        self.active_groups = {}  # Dict mapping thread_id to FractalGroup
        self.daily_counters = {}  # Dict mapping guild_id -> {date: counter}
        
        # Create admin command group
        self.admin_group = app_commands.Group(name="admin", description="Admin commands for fractal management")
    
    def _get_next_group_name(self, guild_id: int) -> str:
        """Generate auto-incremented group name for the day"""
        today = datetime.now().strftime("%b %d, %Y")
        
        if guild_id not in self.daily_counters:
            self.daily_counters[guild_id] = {}
        
        if today not in self.daily_counters[guild_id]:
            self.daily_counters[guild_id][today] = 0
        
        self.daily_counters[guild_id][today] += 1
        counter = self.daily_counters[guild_id][today]
        
        return f"Fractal Group {counter} - {today}"
    
    @app_commands.command(
        name="fractaltimer",
        description="Create a fractal with timed speaking rounds followed by voting"
    )
    @app_commands.describe(
        speaking_time="Minutes each person gets to speak (default: 2, range: 1-10)"
    )
    async def fractaltimer(self, interaction: discord.Interaction, speaking_time: int = 2):
        """Create a fractal with timed speaking phase followed by voting"""
        # Check if interaction has already been responded to
        if interaction.response.is_done():
            return
        
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            # Interaction expired or invalid, try to send a regular message
            return
        except discord.InteractionResponded:
            # Already responded, continue with followup
            pass
        
        # Validate speaking time
        if speaking_time < 1 or speaking_time > 10:
            await interaction.followup.send(
                "❌ Speaking time must be between 1-10 minutes!", 
                ephemeral=True
            )
            return
        
        # Check user's voice state
        voice_check = await self.check_voice_state(interaction.user)
        if not voice_check['success']:
            try:
                await interaction.followup.send(voice_check['message'], ephemeral=True)
            except (discord.NotFound, discord.HTTPException) as e:
                # If followup fails, try regular channel message
                self.logger.warning(f"Followup failed, using channel message: {e}")
                try:
                    await interaction.channel.send(f"{interaction.user.mention} {voice_check['message']}")
                except discord.HTTPException as e2:
                    self.logger.error(f"Failed to send voice check error message: {e2}")
            return
        
        members = voice_check['members']
        voice_channel = interaction.user.voice.channel
        
        # Create voice-enabled confirmation view
        view = VoiceMemberConfirmationView(
            cog=self, 
            members=members, 
            facilitator=interaction.user,
            voice_channel=voice_channel,
            speaking_time=speaking_time * 60  # Convert to seconds
        )
        
        member_list = "\n".join([f"• {member.display_name}" for member in members])
        
        # Enhanced setup message with better formatting
        setup_message = (
            f"🎙️ **ZAO Fractal Setup**\n"
            f"**Voice Channel:** {voice_channel.mention}\n"
            f"**Speaking Time:** {speaking_time} minutes each\n"
            f"**Members ({len(members)}):**\n{member_list}\n\n"
            f"**Choose your fractal type:**\n"
            f"• 🗳️ **Start Fractal** - Voting only (no speaking)\n"
            f"• ⏱️ **Start Timer Only** - Speaking rounds only (no voting)\n"
            f"• ⏱️ **Start Timer + Voting** - Full fractal with speaking then voting"
        )
        
        try:
            message = await interaction.followup.send(setup_message, view=view, ephemeral=True)
            view.message = message  # Store message for timeout handling
        except (discord.NotFound, discord.HTTPException) as e:
            # Fallback to channel message with better error handling
            self.logger.warning(f"Followup failed, using channel message: {e}")
            try:
                message = await interaction.channel.send(
                    f"{interaction.user.mention}\n{setup_message}",
                    view=view
                )
                view.message = message  # Store message for timeout handling
            except discord.HTTPException as e2:
                self.logger.error(f"Failed to send setup message: {e2}")
                # Last resort - send without view
                try:
                    await interaction.channel.send(
                        f"{interaction.user.mention}\n❌ **Error setting up fractal.** Please try again."
                    )
                except discord.HTTPException as e3:
                    self.logger.critical(f"Complete failure to send any message: {e3}")


    @app_commands.command(
        name="zaofractal",
        description="Create a voting-only fractal (no voice timer)"
    )
    @app_commands.describe(
        member1="Member 1 (required)",
        member2="Member 2 (required)",
        member3="Member 3 (optional)",
        member4="Member 4 (optional)",
        member5="Member 5 (optional)",
        member6="Member 6 (optional)"
    )
    async def zaofractal(
        self,
        interaction: discord.Interaction,
        member1: discord.Member,
        member2: discord.Member,
        member3: discord.Member | None = None,
        member4: discord.Member | None = None,
        member5: discord.Member | None = None,
        member6: discord.Member | None = None,
    ):
        if interaction.response.is_done():
            return

        try:
            await interaction.response.defer(ephemeral=True)
        except (discord.NotFound, discord.InteractionResponded):
            pass

        members = [m for m in [member1, member2, member3, member4, member5, member6] if m is not None]
        members = [m for m in members if not m.bot]

        unique_members: list[discord.Member] = []
        seen_ids: set[int] = set()
        for m in members:
            if m.id not in seen_ids:
                unique_members.append(m)
                seen_ids.add(m.id)
        members = unique_members

        if interaction.user not in members:
            members.insert(0, interaction.user)

        if len(members) < 2:
            await interaction.followup.send("❌ Need at least 2 human members.", ephemeral=True)
            return

        if len(members) > 6:
            await interaction.followup.send("❌ Fractal groups are limited to 6 members.", ephemeral=True)
            return

        view = MemberConfirmationView(
            cog=self,
            members=members,
            facilitator=interaction.user
        )

        member_list = "\n".join([f"- {m.display_name}" for m in members])
        setup_message = (
            "🗳️ **ZAO Fractal (Voting Only) Setup**\n"
            f"**Facilitator:** {interaction.user.mention}\n"
            f"**Members ({len(members)}):**\n{member_list}\n\n"
            "Press **✅ Start Fractal** to create the voting thread + buttons."
        )

        try:
            await interaction.followup.send(setup_message, view=view, ephemeral=True)
        except (discord.NotFound, discord.HTTPException) as e:
            self.logger.warning(f"Voting-only setup followup failed, using channel message: {e}")
            try:
                await interaction.channel.send(f"{interaction.user.mention}\n{setup_message}", view=view)
            except discord.HTTPException as e2:
                self.logger.error(f"Failed to send voting-only setup message: {e2}")
                return
    
    @app_commands.command(
        name="endgroup",
        description="End an active fractal group (facilitator only)"
    )
    async def end_group(self, interaction: discord.Interaction):
        """End an active fractal group"""
        await interaction.response.defer(ephemeral=True)
        
        # Check if in a fractal thread
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("❌ This command can only be used in a fractal group thread.", ephemeral=True)
            return
        
        # Check if this is an active fractal group
        group = self.active_groups.get(interaction.channel.id)
        if not group:
            await interaction.followup.send("❌ This thread is not an active fractal group.", ephemeral=True)
            return
        
        # Check if user is facilitator
        if interaction.user.id != group.facilitator.id:
            await interaction.followup.send("❌ Only the group facilitator can end the fractal group.", ephemeral=True)
            return
        
        # End the fractal group
        await group.end_fractal()
        del self.active_groups[interaction.channel.id]
        
        await interaction.followup.send("✅ Fractal group ended successfully.", ephemeral=True)
    
    @app_commands.command(
        name="status",
        description="Show the current status of an active fractal group"
    )
    async def status(self, interaction: discord.Interaction):
        """Show the status of an active fractal group"""
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.NotFound:
            return
        except discord.InteractionResponded:
            pass
        
        # Check if in a fractal thread
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.followup.send("❌ This command can only be used in a fractal group thread.", ephemeral=True)
            return
        
        # Check if this is an active fractal group
        group = self.active_groups.get(interaction.channel.id)
        if not group:
            # Debug: show what threads we have
            active_thread_ids = list(self.active_groups.keys())
            await interaction.followup.send(f"❌ This thread is not an active fractal group.\nActive threads: {active_thread_ids}\nCurrent thread: {interaction.channel.id}", ephemeral=True)
            return
        
        # Build status message
        status = f"# ZAO Fractal Status\n\n"
        status += f"**Group:** {interaction.channel.name}\n"
        status += f"**Facilitator:** {group.facilitator.mention}\n"
        status += f"**Current Level:** {group.current_level}\n"
        status += f"**Members:** {len(group.members)}\n"
        status += f"**Active Candidates:** {len(group.active_candidates)}\n"
        status += f"**Votes Cast:** {len(group.votes)}/{len(group.members)}\n\n"
        
        # Winners so far
        if group.winners:
            status += "**Winners:**\n"
            for level, winner in sorted(group.winners.items(), reverse=True):
                status += f"Level {level}: {winner.mention}\n"
        
        await interaction.followup.send(status, ephemeral=True)
    
    # Admin Commands
    @app_commands.command(
        name="admin_end_fractal",
        description="[ADMIN] Force end any active fractal group"
    )
    @app_commands.describe(thread_id="ID of the thread to end (optional)")
    async def admin_end_fractal(self, interaction: discord.Interaction, thread_id: str = None):
        """Admin command to force end fractals"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        if thread_id:
            # End specific fractal
            try:
                thread_id_int = int(thread_id)
                if thread_id_int in self.active_groups:
                    group = self.active_groups[thread_id_int]
                    await group.end_fractal()
                    await interaction.followup.send(f"✅ Ended fractal in {group.thread.mention}", ephemeral=True)
                else:
                    await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
            except ValueError:
                await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        else:
            # Show list of active fractals to choose from
            if not self.active_groups:
                await interaction.followup.send("❌ No active fractals to end.", ephemeral=True)
                return
            
            status = "**Active Fractals:**\n"
            for thread_id, group in self.active_groups.items():
                status += f"• {group.thread.mention} (ID: {thread_id}) - Level {group.current_level}\n"
            status += "\nUse `/admin_end_fractal thread_id:<ID>` to end a specific one."
            
            await interaction.followup.send(status, ephemeral=True)
    
    @app_commands.command(
        name="admin_list_fractals",
        description="[ADMIN] List all active fractal groups"
    )
    async def admin_list_fractals(self, interaction: discord.Interaction):
        """Admin command to list all active fractals"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        if not self.active_groups:
            await interaction.followup.send(
                "✅ **No active fractal groups**\n"
                "💡 Use `/fractaltimer` to create a new fractal group!",
                ephemeral=True
            )
            return
        
        # Enhanced status with better formatting and more info
        status = f"# 📊 **Active Fractal Groups ({len(self.active_groups)})**\n\n"
        
        for thread_id, group in self.active_groups.items():
            # Determine phase and status
            if hasattr(group, 'voice_phase_active') and group.voice_phase_active:
                phase = f"🎙️ Speaking Phase"
                if group.speaking_queue and group.speaking_queue.current_speaker:
                    phase += f" (Current: {group.speaking_queue.current_speaker.display_name})"
            else:
                phase = f"🗳️ Voting Phase (Level {group.current_level})"
            
            # Check if paused
            paused_status = ""
            if hasattr(group, 'paused') and group.paused:
                paused_status = " ⏸️ **PAUSED**"
            
            # Voice channel info
            voice_info = ""
            if hasattr(group, 'voice_channel') and group.voice_channel:
                voice_info = f"🎙️ **Voice:** {group.voice_channel.mention}\n"
            
            status += f"## **{group.thread.name}**{paused_status}\n"
            status += f"📍 **Thread:** {group.thread.mention}\n"
            status += f"{voice_info}"
            status += f"👑 **Facilitator:** {group.facilitator.mention}\n"
            status += f"📊 **Phase:** {phase}\n"
            status += f"👥 **Members:** {len(group.members)} total, {len(group.active_candidates)} active candidates\n"
            status += f"🗳️ **Votes:** {len(group.votes)}/{len(group.members)} cast\n"
            
            if group.winners:
                winners_text = ", ".join([f"L{level}: {winner.display_name}" for level, winner in sorted(group.winners.items(), reverse=True)])
                status += f"🏆 **Winners:** {winners_text}\n"
            
            status += f"🆔 **Thread ID:** `{thread_id}`\n\n"
        
        await interaction.followup.send(status, ephemeral=True)
    
    @app_commands.command(
        name="admin_cleanup",
        description="[ADMIN] Clean up old/stuck fractal groups"
    )
    async def admin_cleanup(self, interaction: discord.Interaction):
        """Admin command to cleanup stuck fractals"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        if not self.active_groups:
            await interaction.followup.send(
                "✅ **No fractal groups to clean up**\n"
                "All fractal groups are already clean!",
                ephemeral=True
            )
            return
        
        cleaned_count = 0
        to_remove = []
        cleanup_details = []
        
        for thread_id, group in self.active_groups.items():
            try:
                # Check if thread still exists and is accessible
                thread = self.bot.get_channel(thread_id)
                if not thread:
                    to_remove.append(thread_id)
                    cleanup_details.append(f"• **{group.thread.name}** - Thread no longer exists")
                    cleaned_count += 1
                elif thread.archived:
                    to_remove.append(thread_id)
                    cleanup_details.append(f"• **{group.thread.name}** - Thread archived")
                    cleaned_count += 1
                elif not thread.permissions_for(interaction.guild.me).send_messages:
                    to_remove.append(thread_id)
                    cleanup_details.append(f"• **{group.thread.name}** - No bot permissions")
                    cleaned_count += 1
            except Exception as e:
                to_remove.append(thread_id)
                cleanup_details.append(f"• **{getattr(group, 'thread', {}).get('name', 'Unknown')}** - Error: {str(e)[:50]}")
                cleaned_count += 1
        
        # Remove invalid groups
        for thread_id in to_remove:
            try:
                del self.active_groups[thread_id]
            except KeyError:
                pass  # Already removed
        
        if cleaned_count == 0:
            await interaction.followup.send(
                "✅ **All fractal groups are healthy!**\n"
                f"Checked {len(self.active_groups)} active groups - no cleanup needed.",
                ephemeral=True
            )
        else:
            cleanup_summary = "\n".join(cleanup_details[:10])  # Limit to 10 items
            if len(cleanup_details) > 10:
                cleanup_summary += f"\n... and {len(cleanup_details) - 10} more"
            
            await interaction.followup.send(
                f"🧹 **Cleanup Complete!**\n"
                f"**Removed:** {cleaned_count} inactive fractal groups\n"
                f"**Remaining:** {len(self.active_groups)} active groups\n\n"
                f"**Cleaned up:**\n{cleanup_summary}",
                ephemeral=True
            )
    
    # Force Round Progression Commands
    @app_commands.command(
        name="admin_force_round",
        description="[ADMIN] Skip current voting and move to next level"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_force_round(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to force move to next round"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ **Admin permissions required** to use this command.", ephemeral=True)
            return
        
        # Enhanced validation
        if not thread_id.strip():
            await interaction.followup.send(
                "❌ **Thread ID required**\n"
                "💡 Use `/admin_list_fractals` to see active fractal thread IDs",
                ephemeral=True
            )
            return
        
        try:
            thread_id_int = int(thread_id.strip())
        except ValueError:
            await interaction.followup.send(
                f"❌ **Invalid thread ID format:** `{thread_id}`\n"
                "💡 Thread ID must be a number. Use `/admin_list_fractals` to see valid IDs.",
                ephemeral=True
            )
            return
        
        if thread_id_int not in self.active_groups:
            available_ids = ", ".join([f"`{tid}`" for tid in list(self.active_groups.keys())[:5]])
            await interaction.followup.send(
                f"❌ **No active fractal found** with thread ID `{thread_id_int}`\n"
                f"💡 **Available IDs:** {available_ids if available_ids else 'None'}\n"
                f"Use `/admin_list_fractals` to see all active fractals.",
                ephemeral=True
            )
            return
        
        group = self.active_groups[thread_id_int]
        
        # Check if fractal is in voting phase
        if hasattr(group, 'voice_phase_active') and group.voice_phase_active:
            await interaction.followup.send(
                f"❌ **Cannot force round during speaking phase**\n"
                f"💡 Wait for speaking phase to complete or use voice controls to skip to voting.",
                ephemeral=True
            )
            return
        
        try:
            # Find candidate with most votes or pick randomly if tie
            vote_counts = {}
            for candidate_id in group.votes.values():
                vote_counts[candidate_id] = vote_counts.get(candidate_id, 0) + 1
            
            if vote_counts:
                max_votes = max(vote_counts.values())
                winners = [cid for cid, count in vote_counts.items() if count == max_votes]
                winner_id = winners[0] if len(winners) == 1 else random.choice(winners)
                winner = discord.utils.get(group.active_candidates, id=winner_id)
            else:
                # No votes cast, pick random candidate
                winner = random.choice(group.active_candidates)
            
            await group.thread.send(f"⚡ **ADMIN OVERRIDE:** Forcing round completion. Winner: {winner.mention}")
            await group.start_new_round(winner)
            
            await interaction.followup.send(
                f"✅ **Round forced successfully!**\n"
                f"**Fractal:** {group.thread.mention}\n"
                f"**Winner:** {winner.mention}\n"
                f"**Level:** {group.current_level + 1} → {group.current_level}",
                ephemeral=True
            )
            
        except Exception as e:
            self.logger.error(f"Error forcing round: {e}", exc_info=True)
            await interaction.followup.send(
                f"❌ **Error forcing round:** {str(e)}\n"
                f"💡 Check logs for details or try `/admin_list_fractals` to verify fractal status.",
                ephemeral=True
            )
    
    @app_commands.command(
        name="admin_reset_votes",
        description="[ADMIN] Clear all votes in current round"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_reset_votes(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to reset votes in current round"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            old_vote_count = len(group.votes)
            group.votes = {}
            
            await group.thread.send(f"⚡ **ADMIN RESET:** All votes cleared. Voting restarted for Level {group.current_level}.")
            
            await interaction.followup.send(f"✅ Reset {old_vote_count} votes in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error resetting votes: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_declare_winner",
        description="[ADMIN] Manually declare a round winner"
    )
    @app_commands.describe(thread_id="ID of the fractal thread", user="User to declare as winner")
    async def admin_declare_winner(self, interaction: discord.Interaction, thread_id: str, user: discord.Member):
        """Admin command to manually declare a winner"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            if user not in group.active_candidates:
                await interaction.followup.send(f"❌ {user.mention} is not an active candidate in this fractal.", ephemeral=True)
                return
            
            await group.thread.send(f"⚡ **ADMIN DECLARATION:** {user.mention} declared winner of Level {group.current_level}!")
            await group.start_new_round(user)
            
            await interaction.followup.send(f"✅ Declared {user.mention} as winner in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error declaring winner: {str(e)}", ephemeral=True)
    
    # Member Management Commands
    @app_commands.command(
        name="admin_add_member",
        description="[ADMIN] Add someone to an active fractal"
    )
    @app_commands.describe(thread_id="ID of the fractal thread", user="User to add to the fractal")
    async def admin_add_member(self, interaction: discord.Interaction, thread_id: str, user: discord.Member):
        """Admin command to add member to active fractal"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            if user in group.members:
                await interaction.followup.send(f"❌ {user.mention} is already in this fractal.", ephemeral=True)
                return
            
            # Add to members and active candidates
            group.members.append(user)
            group.active_candidates.append(user)
            
            # Add to thread
            try:
                await group.thread.add_user(user)
            except discord.HTTPException:
                pass
            
            await group.thread.send(f"⚡ **ADMIN ADD:** {user.mention} has been added to the fractal!")
            
            await interaction.followup.send(f"✅ Added {user.mention} to {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding member: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_remove_member",
        description="[ADMIN] Remove someone from active fractal"
    )
    @app_commands.describe(thread_id="ID of the fractal thread", user="User to remove from the fractal")
    async def admin_remove_member(self, interaction: discord.Interaction, thread_id: str, user: discord.Member):
        """Admin command to remove member from active fractal"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            if user not in group.members:
                await interaction.followup.send(f"❌ {user.mention} is not in this fractal.", ephemeral=True)
                return
            
            # Remove from members and active candidates
            if user in group.members:
                group.members.remove(user)
            if user in group.active_candidates:
                group.active_candidates.remove(user)
            
            # Remove their vote if they had one
            if user.id in group.votes:
                del group.votes[user.id]
            
            await group.thread.send(f"⚡ **ADMIN REMOVE:** {user.mention} has been removed from the fractal.")
            
            await interaction.followup.send(f"✅ Removed {user.mention} from {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error removing member: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_change_facilitator",
        description="[ADMIN] Transfer facilitator role to another member"
    )
    @app_commands.describe(thread_id="ID of the fractal thread", user="New facilitator")
    async def admin_change_facilitator(self, interaction: discord.Interaction, thread_id: str, user: discord.Member):
        """Admin command to change facilitator"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            old_facilitator = group.facilitator
            
            if user not in group.members:
                await interaction.followup.send(f"❌ {user.mention} must be a member of the fractal to become facilitator.", ephemeral=True)
                return
            
            group.facilitator = user
            
            await group.thread.send(f"⚡ **FACILITATOR CHANGE:** {old_facilitator.mention} → {user.mention}")
            
            await interaction.followup.send(f"✅ Changed facilitator from {old_facilitator.mention} to {user.mention} in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error changing facilitator: {str(e)}", ephemeral=True)
    
    # Group Control Commands
    @app_commands.command(
        name="admin_pause_fractal",
        description="[ADMIN] Temporarily pause voting in a fractal"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_pause_fractal(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to pause fractal voting"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            # Add paused flag to group
            if not hasattr(group, 'paused'):
                group.paused = False
            
            if group.paused:
                await interaction.followup.send("❌ Fractal is already paused.", ephemeral=True)
                return
            
            group.paused = True
            
            await group.thread.send("⏸️ **FRACTAL PAUSED** by admin. Voting is temporarily suspended.")
            
            await interaction.followup.send(f"✅ Paused fractal in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error pausing fractal: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_resume_fractal",
        description="[ADMIN] Resume paused fractal voting"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_resume_fractal(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to resume paused fractal"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            if not hasattr(group, 'paused') or not group.paused:
                await interaction.followup.send("❌ Fractal is not paused.", ephemeral=True)
                return
            
            group.paused = False
            
            await group.thread.send("▶️ **FRACTAL RESUMED** by admin. Voting continues!")
            
            await interaction.followup.send(f"✅ Resumed fractal in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error resuming fractal: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_restart_fractal",
        description="[ADMIN] Restart fractal from beginning with same members"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_restart_fractal(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to restart fractal from beginning"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            # Reset fractal state
            group.current_level = 6
            group.votes = {}
            group.winners = {}
            group.active_candidates = group.members.copy()
            if hasattr(group, 'paused'):
                group.paused = False
            
            await group.thread.send("🔄 **FRACTAL RESTARTED** by admin. Starting fresh from Level 6!")
            
            # Start new round
            await group.start_new_round()
            
            await interaction.followup.send(f"✅ Restarted fractal in {group.thread.mention}", ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error restarting fractal: {str(e)}", ephemeral=True)
    
    # Advanced Monitoring Commands
    @app_commands.command(
        name="admin_fractal_stats",
        description="[ADMIN] Detailed stats for a specific fractal group"
    )
    @app_commands.describe(thread_id="ID of the fractal thread")
    async def admin_fractal_stats(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to get detailed fractal stats"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            thread_id_int = int(thread_id)
            if thread_id_int not in self.active_groups:
                await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                return
            
            group = self.active_groups[thread_id_int]
            
            # Calculate detailed stats
            total_members = len(group.members)
            active_candidates = len(group.active_candidates)
            votes_cast = len(group.votes)
            vote_percentage = (votes_cast / total_members * 100) if total_members > 0 else 0
            
            # Vote distribution
            vote_counts = {}
            for candidate_id in group.votes.values():
                candidate = discord.utils.get(group.active_candidates, id=candidate_id)
                if candidate:
                    vote_counts[candidate.display_name] = vote_counts.get(candidate.display_name, 0) + 1
            
            stats = f"# 📊 **Detailed Fractal Stats**\n\n"
            stats += f"**Thread:** {group.thread.mention}\n"
            stats += f"**Facilitator:** {group.facilitator.mention}\n"
            stats += f"**Current Level:** {group.current_level}\n"
            stats += f"**Status:** {'⏸️ Paused' if hasattr(group, 'paused') and group.paused else '▶️ Active'}\n\n"
            
            stats += f"**Members:** {total_members}\n"
            stats += f"**Active Candidates:** {active_candidates}\n"
            stats += f"**Votes Cast:** {votes_cast}/{total_members} ({vote_percentage:.1f}%)\n"
            stats += f"**Votes Needed to Win:** {group.get_vote_threshold()}\n\n"
            
            if vote_counts:
                stats += "**Current Vote Distribution:**\n"
                for candidate, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
                    stats += f"• {candidate}: {count} votes\n"
                stats += "\n"
            
            if group.winners:
                stats += "**Winners So Far:**\n"
                for level in sorted(group.winners.keys(), reverse=True):
                    winner = group.winners[level]
                    stats += f"• Level {level}: {winner.display_name}\n"
            
            await interaction.followup.send(stats, ephemeral=True)
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting fractal stats: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_server_stats",
        description="[ADMIN] Overall server fractal statistics"
    )
    async def admin_server_stats(self, interaction: discord.Interaction):
        """Admin command to get server-wide fractal stats"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            guild_id = interaction.guild.id
            
            # Count active fractals for this server
            server_fractals = [group for group in self.active_groups.values() if group.thread.guild.id == guild_id]
            
            total_active = len(server_fractals)
            total_participants = sum(len(group.members) for group in server_fractals)
            total_votes_cast = sum(len(group.votes) for group in server_fractals)
            
            # Daily counter stats
            today = datetime.now().strftime("%b %d, %Y")
            daily_count = 0
            if guild_id in self.daily_counters and today in self.daily_counters[guild_id]:
                daily_count = self.daily_counters[guild_id][today]
            
            stats = f"# 📈 **Server Fractal Statistics**\n\n"
            stats += f"**Server:** {interaction.guild.name}\n"
            stats += f"**Active Fractals:** {total_active}\n"
            stats += f"**Total Participants:** {total_participants}\n"
            stats += f"**Total Votes Cast:** {total_votes_cast}\n"
            stats += f"**Groups Created Today:** {daily_count}\n\n"
            
            if server_fractals:
                stats += "**Active Groups:**\n"
                for group in server_fractals:
                    status = "⏸️ Paused" if hasattr(group, 'paused') and group.paused else "▶️ Active"
                    stats += f"• {group.thread.name} - Level {group.current_level} ({status})\n"
            else:
                stats += "No active fractals currently running.\n"
            
            await interaction.followup.send(stats, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error getting server stats: {str(e)}", ephemeral=True)
    
    @app_commands.command(
        name="admin_export_data",
        description="[ADMIN] Export fractal data for analysis"
    )
    @app_commands.describe(thread_id="ID of the fractal thread (optional - exports all if not specified)")
    async def admin_export_data(self, interaction: discord.Interaction, thread_id: str = None):
        """Admin command to export fractal data"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            import json
            from datetime import datetime
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "server_id": interaction.guild.id,
                "server_name": interaction.guild.name,
                "fractals": []
            }
            
            if thread_id:
                # Export specific fractal
                thread_id_int = int(thread_id)
                if thread_id_int not in self.active_groups:
                    await interaction.followup.send("❌ No active fractal found with that thread ID.", ephemeral=True)
                    return
                groups_to_export = [self.active_groups[thread_id_int]]
            else:
                # Export all fractals for this server
                groups_to_export = [group for group in self.active_groups.values() if group.thread.guild.id == interaction.guild.id]
            
            for group in groups_to_export:
                fractal_data = {
                    "thread_id": group.thread.id,
                    "thread_name": group.thread.name,
                    "facilitator": {
                        "id": group.facilitator.id,
                        "name": group.facilitator.display_name
                    },
                    "current_level": group.current_level,
                    "paused": hasattr(group, 'paused') and group.paused,
                    "members": [{"id": m.id, "name": m.display_name} for m in group.members],
                    "active_candidates": [{"id": m.id, "name": m.display_name} for m in group.active_candidates],
                    "votes": {str(voter_id): candidate_id for voter_id, candidate_id in group.votes.items()},
                    "winners": {str(level): {"id": winner.id, "name": winner.display_name} for level, winner in group.winners.items()}
                }
                export_data["fractals"].append(fractal_data)
            
            # Create JSON file content
            json_content = json.dumps(export_data, indent=2)
            
            # Create file and send
            import io
            file_buffer = io.StringIO(json_content)
            file = discord.File(file_buffer, filename=f"fractal_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            await interaction.followup.send(
                f"📁 **Data Export Complete**\n"
                f"Exported {len(export_data['fractals'])} fractal(s) from {interaction.guild.name}",
                file=file,
                ephemeral=True
            )
            
        except ValueError:
            await interaction.followup.send("❌ Invalid thread ID format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error exporting data: {str(e)}", ephemeral=True)
    
    # Debug and Health Check Commands
    @app_commands.command(
        name="admin_debug_fractal",
        description="[ADMIN] Detailed debug information for a specific fractal"
    )
    @app_commands.describe(thread_id="ID of the fractal thread to debug")
    async def admin_debug_fractal(self, interaction: discord.Interaction, thread_id: str):
        """Admin command to get detailed debug info for a fractal"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ **Admin permissions required** to use this command.", ephemeral=True)
            return
        
        # Validate thread ID
        try:
            thread_id_int = int(thread_id.strip())
        except ValueError:
            await interaction.followup.send(
                f"❌ **Invalid thread ID format:** `{thread_id}`\n"
                "💡 Thread ID must be a number.",
                ephemeral=True
            )
            return
        
        if thread_id_int not in self.active_groups:
            await interaction.followup.send(
                f"❌ **No active fractal found** with thread ID `{thread_id_int}`\n"
                f"💡 Use `/admin_list_fractals` to see active fractals.",
                ephemeral=True
            )
            return
        
        group = self.active_groups[thread_id_int]
        
        # Comprehensive debug information
        debug_info = f"# 🔍 **Debug Info: {group.thread.name}**\n\n"
        
        # Basic Info
        debug_info += f"## 📊 **Basic Information**\n"
        debug_info += f"**Thread ID:** `{thread_id_int}`\n"
        debug_info += f"**Thread Name:** {group.thread.name}\n"
        debug_info += f"**Thread Mention:** {group.thread.mention}\n"
        debug_info += f"**Facilitator:** {group.facilitator.mention} (`{group.facilitator.id}`)\n"
        debug_info += f"**Current Level:** {group.current_level}\n"
        debug_info += f"**Created:** <t:{int(group.thread.created_at.timestamp())}:R>\n\n"
        
        # Members Info
        debug_info += f"## 👥 **Members ({len(group.members)})**\n"
        for i, member in enumerate(group.members, 1):
            voice_status = "🎙️ In Voice" if member.voice and member.voice.channel else "❌ Not in Voice"
            debug_info += f"{i}. {member.mention} (`{member.id}`) - {voice_status}\n"
        debug_info += "\n"
        
        # Active Candidates
        debug_info += f"## 🎯 **Active Candidates ({len(group.active_candidates)})**\n"
        for i, candidate in enumerate(group.active_candidates, 1):
            debug_info += f"{i}. {candidate.mention} (`{candidate.id}`)\n"
        debug_info += "\n"
        
        # Voting Info
        debug_info += f"## 🗳️ **Voting Status**\n"
        debug_info += f"**Votes Cast:** {len(group.votes)}/{len(group.members)}\n"
        debug_info += f"**Votes Needed:** {group.get_vote_threshold()}\n"
        if group.votes:
            debug_info += f"**Vote Details:**\n"
            for voter_id, candidate_id in group.votes.items():
                voter = discord.utils.get(group.members, id=voter_id)
                candidate = discord.utils.get(group.active_candidates, id=candidate_id)
                voter_name = voter.display_name if voter else f"Unknown ({voter_id})"
                candidate_name = candidate.display_name if candidate else f"Unknown ({candidate_id})"
                debug_info += f"  • {voter_name} → {candidate_name}\n"
        debug_info += "\n"
        
        # Voice Phase Info
        if hasattr(group, 'voice_channel') and group.voice_channel:
            debug_info += f"## 🎙️ **Voice Phase Information**\n"
            debug_info += f"**Voice Channel:** {group.voice_channel.mention} (`{group.voice_channel.id}`)\n"
            debug_info += f"**Speaking Time:** {group.speaking_time // 60} minutes\n"
            debug_info += f"**Voice Phase Active:** {'✅ Yes' if getattr(group, 'voice_phase_active', False) else '❌ No'}\n"
            
            if hasattr(group, 'speaking_queue') and group.speaking_queue:
                debug_info += f"**Current Speaker:** {group.speaking_queue.current_speaker.display_name if group.speaking_queue.current_speaker else 'None'}\n"
                debug_info += f"**Completed Speakers:** {len(group.speaking_queue.completed_speakers)}\n"
                debug_info += f"**Remaining Speakers:** {len(group.speaking_queue.queue)}\n"
            debug_info += "\n"
        
        # Winners Info
        if group.winners:
            debug_info += f"## 🏆 **Winners by Level**\n"
            for level in sorted(group.winners.keys(), reverse=True):
                winner = group.winners[level]
                debug_info += f"**Level {level}:** {winner.mention} (`{winner.id}`)\n"
            debug_info += "\n"
        
        # System Status
        debug_info += f"## ⚙️ **System Status**\n"
        debug_info += f"**Thread Accessible:** {'✅ Yes' if group.thread else '❌ No'}\n"
        debug_info += f"**Thread Archived:** {'❌ Yes' if group.thread and group.thread.archived else '✅ No'}\n"
        debug_info += f"**Bot Permissions:** {'✅ Good' if group.thread.permissions_for(interaction.guild.me).send_messages else '❌ Missing'}\n"
        debug_info += f"**Paused:** {'⏸️ Yes' if getattr(group, 'paused', False) else '✅ Active'}\n"
        
        # Memory usage info
        import sys
        debug_info += f"**Memory Usage:** ~{sys.getsizeof(group)} bytes\n"
        
        await interaction.followup.send(debug_info, ephemeral=True)
    
    @app_commands.command(
        name="admin_health_check",
        description="[ADMIN] System health check and diagnostics"
    )
    async def admin_health_check(self, interaction: discord.Interaction):
        """Admin command to check system health"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ **Admin permissions required** to use this command.", ephemeral=True)
            return
        
        health_report = f"# 🏥 **System Health Check**\n\n"
        
        # Bot Status
        health_report += f"## 🤖 **Bot Status**\n"
        health_report += f"**Bot Online:** ✅ Yes\n"
        health_report += f"**Latency:** {round(self.bot.latency * 1000)}ms\n"
        health_report += f"**Guilds:** {len(self.bot.guilds)}\n"
        health_report += f"**Active Fractals:** {len(self.active_groups)}\n\n"
        
        # Memory and Performance
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        health_report += f"## 📊 **Performance Metrics**\n"
        health_report += f"**Memory Usage:** {memory_mb:.1f} MB\n"
        health_report += f"**CPU Usage:** {process.cpu_percent():.1f}%\n"
        health_report += f"**Threads:** {process.num_threads()}\n\n"
        
        # Fractal Health
        healthy_fractals = 0
        problematic_fractals = []
        
        for thread_id, group in self.active_groups.items():
            try:
                # Check thread accessibility
                if not group.thread or group.thread.archived:
                    problematic_fractals.append(f"Thread {thread_id}: Archived/Deleted")
                    continue
                
                # Check permissions
                if not group.thread.permissions_for(interaction.guild.me).send_messages:
                    problematic_fractals.append(f"Thread {thread_id}: No permissions")
                    continue
                
                # Check member validity
                invalid_members = [m for m in group.members if not m.guild or m.guild != interaction.guild]
                if invalid_members:
                    problematic_fractals.append(f"Thread {thread_id}: {len(invalid_members)} invalid members")
                    continue
                
                healthy_fractals += 1
                
            except Exception as e:
                problematic_fractals.append(f"Thread {thread_id}: Error - {str(e)[:50]}")
        
        health_report += f"## 🎯 **Fractal Health**\n"
        health_report += f"**Healthy Fractals:** {healthy_fractals}/{len(self.active_groups)}\n"
        
        if problematic_fractals:
            health_report += f"**Issues Found:**\n"
            for issue in problematic_fractals[:10]:  # Limit to 10 issues
                health_report += f"  • {issue}\n"
            if len(problematic_fractals) > 10:
                health_report += f"  • ... and {len(problematic_fractals) - 10} more\n"
            health_report += f"\n💡 **Recommendation:** Run `/admin_cleanup` to fix issues\n"
        else:
            health_report += f"**Status:** ✅ All fractals healthy!\n"
        
        health_report += f"\n## 🔧 **Quick Actions**\n"
        health_report += f"• `/admin_cleanup` - Clean up problematic fractals\n"
        health_report += f"• `/admin_list_fractals` - View all active fractals\n"
        health_report += f"• `/admin_debug_fractal` - Debug specific fractal\n"
        
        await interaction.followup.send(health_report, ephemeral=True)
    
    @app_commands.command(
        name="admin_debug_mode",
        description="[ADMIN] Toggle debug mode for verbose logging"
    )
    @app_commands.describe(enabled="Enable or disable debug mode")
    async def admin_debug_mode(self, interaction: discord.Interaction, enabled: bool):
        """Admin command to toggle debug mode"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ **Admin permissions required** to use this command.", ephemeral=True)
            return
        
        # Toggle debug logging level
        import logging
        logger = logging.getLogger('bot')
        
        if enabled:
            logger.setLevel(logging.DEBUG)
            # Also set debug for fractal-specific loggers
            for handler in logger.handlers:
                handler.setLevel(logging.DEBUG)
            
            await interaction.followup.send(
                "🔍 **Debug Mode Enabled**\n"
                "• Verbose logging is now active\n"
                "• All fractal operations will be logged in detail\n"
                "• Use `/admin_debug_mode enabled:False` to disable",
                ephemeral=True
            )
        else:
            logger.setLevel(logging.INFO)
            for handler in logger.handlers:
                handler.setLevel(logging.INFO)
            
            await interaction.followup.send(
                "✅ **Debug Mode Disabled**\n"
                "• Logging returned to normal level\n"
                "• Only important events will be logged",
                ephemeral=True
            )
        
        self.logger.info(f"Debug mode {'enabled' if enabled else 'disabled'} by {interaction.user.display_name}")
    
    @app_commands.command(
        name="admin_emergency_stop",
        description="[ADMIN] Emergency stop all fractals and clear system"
    )
    async def admin_emergency_stop(self, interaction: discord.Interaction):
        """Emergency command to stop all fractals"""
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ **Admin permissions required** to use this command.", ephemeral=True)
            return
        
        # Confirmation check
        if not hasattr(self, '_emergency_confirmed'):
            self._emergency_confirmed = False
        
        if not self._emergency_confirmed:
            self._emergency_confirmed = True
            await interaction.followup.send(
                "⚠️ **EMERGENCY STOP CONFIRMATION**\n"
                "This will immediately stop ALL active fractals and clear the system.\n"
                "**This action cannot be undone!**\n\n"
                "Run this command again within 30 seconds to confirm.",
                ephemeral=True
            )
            
            # Reset confirmation after 30 seconds
            import asyncio
            await asyncio.sleep(30)
            self._emergency_confirmed = False
            return
        
        # Execute emergency stop
        stopped_count = len(self.active_groups)
        
        # Notify all active fractals
        for thread_id, group in list(self.active_groups.items()):
            try:
                await group.thread.send(
                    "🚨 **EMERGENCY STOP**\n"
                    "This fractal has been stopped by an administrator.\n"
                    "Contact server staff if you have questions."
                )
            except:
                pass  # Thread might be inaccessible
        
        # Clear all active groups
        self.active_groups.clear()
        
        # Reset confirmation
        self._emergency_confirmed = False
        
        self.logger.critical(f"EMERGENCY STOP executed by {interaction.user.display_name} - stopped {stopped_count} fractals")
        
        await interaction.followup.send(
            f"🚨 **EMERGENCY STOP COMPLETE**\n"
            f"**Stopped:** {stopped_count} active fractals\n"
            f"**System Status:** Clean\n"
            f"**Action logged:** Yes\n\n"
            f"All fractals have been terminated and the system has been reset.",
            ephemeral=True
        )
