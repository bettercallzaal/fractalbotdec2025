import discord
import logging
import asyncio
import random
from typing import Optional, List, Dict
from utils.web_integration import web_integration
from .speaking_queue import SpeakingQueue, VoiceTimer

class FractalGroup:
    """Core class for managing a fractal voting group"""
    
    def __init__(self, thread: discord.Thread, members: List[discord.Member], facilitator: discord.Member, cog, voice_channel=None, speaking_time=120, original_channel=None):
        """Initialize a new fractal group"""
        self.thread = thread
        self.facilitator = facilitator
        self.members = members
        self.original_channel = original_channel or thread  # Use original channel for timer notifications
        self.active_candidates = members.copy()  # Members currently in voting pool
        self.votes = {}  # Dict mapping voter_id to candidate_id
        self.winners = {}  # Dict mapping level to winner
        self.current_level = 6  # Start at level 6
        self.current_voting_message = None
        
        # Voice phase attributes
        self.voice_channel = voice_channel
        self.speaking_time = speaking_time
        self.voice_phase_active = voice_channel is not None
        self.speaking_queue = SpeakingQueue(members) if voice_channel else None
        self.voice_timer = VoiceTimer(speaking_time) if voice_channel else None
        self.voice_control_message = None
        self.display_update_task = None
        self.cog = cog
        self.logger = logging.getLogger('bot')
        
        self.logger.info(f"Created fractal group '{thread.name}' with facilitator {facilitator.display_name} and {len(members)} members")
        
        # Error recovery state
        self.error_count = 0
        self.last_error_time = None
        self.recovery_attempts = 0
    
    async def handle_error(self, error: Exception, context: str = "Unknown"):
        """Handle errors with recovery mechanisms"""
        import time
        current_time = time.time()
        
        self.error_count += 1
        self.last_error_time = current_time
        
        self.logger.error(f"Error in fractal {self.thread.name} ({context}): {error}", exc_info=True)
        
        # Check if we're getting too many errors
        if self.error_count > 5:
            self.logger.critical(f"Fractal {self.thread.name} has {self.error_count} errors - may need intervention")
            await self._emergency_notification(f"⚠️ **Fractal experiencing multiple errors** ({self.error_count})\n**Context:** {context}\n**Error:** {str(error)[:100]}")
        
        # Attempt recovery based on error type
        try:
            if "thread" in str(error).lower() or "channel" in str(error).lower():
                await self._recover_thread_issues()
            elif "permission" in str(error).lower():
                await self._recover_permission_issues()
            elif "member" in str(error).lower():
                await self._recover_member_issues()
            else:
                await self._generic_recovery()
        except Exception as recovery_error:
            self.logger.error(f"Recovery attempt failed: {recovery_error}")
    
    async def _emergency_notification(self, message: str):
        """Send emergency notification to facilitator or fallback channel"""
        try:
            # Try to notify facilitator
            if self.facilitator:
                try:
                    await self.facilitator.send(f"🚨 **Fractal Emergency - {self.thread.name}**\n{message}")
                    return
                except:
                    pass
            
            # Try to send to thread if accessible
            if self.thread and not self.thread.archived:
                try:
                    await self.thread.send(f"🚨 **System Alert**\n{message}")
                    return
                except:
                    pass
            
            # Try original channel
            if hasattr(self, 'original_channel') and self.original_channel:
                try:
                    await self.original_channel.send(f"🚨 **Fractal Alert - {self.thread.name}**\n{message}")
                    return
                except:
                    pass
                    
        except Exception as e:
            self.logger.critical(f"Failed to send emergency notification: {e}")
    
    async def _recover_thread_issues(self):
        """Attempt to recover from thread-related issues"""
        self.recovery_attempts += 1
        self.logger.info(f"Attempting thread recovery #{self.recovery_attempts}")
        
        try:
            # Check if thread still exists
            if not self.thread:
                raise Exception("Thread object is None")
            
            # Try to refresh thread
            await self.thread.fetch()
            
            # Check if archived
            if self.thread.archived:
                self.logger.warning(f"Thread {self.thread.name} is archived - cannot recover")
                await self._emergency_notification("Thread has been archived - fractal cannot continue")
                return False
            
            # Test permissions
            if not self.thread.permissions_for(self.thread.guild.me).send_messages:
                await self._emergency_notification("Bot lost permissions to thread - please check permissions")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Thread recovery failed: {e}")
            return False
    
    async def _recover_permission_issues(self):
        """Attempt to recover from permission issues"""
        self.logger.info("Attempting permission recovery")
        
        try:
            # Check thread permissions
            if self.thread:
                perms = self.thread.permissions_for(self.thread.guild.me)
                missing_perms = []
                
                if not perms.send_messages:
                    missing_perms.append("Send Messages")
                if not perms.embed_links:
                    missing_perms.append("Embed Links")
                if not perms.add_reactions:
                    missing_perms.append("Add Reactions")
                
                if missing_perms:
                    await self._emergency_notification(f"Missing permissions: {', '.join(missing_perms)}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Permission recovery failed: {e}")
            return False
    
    async def _recover_member_issues(self):
        """Attempt to recover from member-related issues"""
        self.logger.info("Attempting member recovery")
        
        try:
            # Check if members are still valid
            valid_members = []
            invalid_members = []
            
            for member in self.members:
                try:
                    # Try to access member properties
                    _ = member.display_name
                    _ = member.guild
                    valid_members.append(member)
                except:
                    invalid_members.append(member)
            
            if invalid_members:
                self.logger.warning(f"Found {len(invalid_members)} invalid members")
                # Remove invalid members
                for invalid_member in invalid_members:
                    if invalid_member in self.members:
                        self.members.remove(invalid_member)
                    if invalid_member in self.active_candidates:
                        self.active_candidates.remove(invalid_member)
                    # Remove their votes
                    self.votes = {k: v for k, v in self.votes.items() if k != invalid_member.id}
                
                await self._emergency_notification(f"Removed {len(invalid_members)} invalid members from fractal")
            
            # Check if we still have enough members
            if len(valid_members) < 2:
                await self._emergency_notification("Not enough valid members remaining - fractal may need to end")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Member recovery failed: {e}")
            return False
    
    async def _generic_recovery(self):
        """Generic recovery attempt"""
        self.logger.info("Attempting generic recovery")
        
        try:
            # Basic health check
            if not self.thread:
                return False
            
            # Try a simple operation
            await self.thread.fetch()
            
            # Reset error count if we've recovered
            if self.recovery_attempts > 0:
                self.error_count = max(0, self.error_count - 1)
                self.logger.info("Generic recovery successful - reduced error count")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Generic recovery failed: {e}")
            return False
    
    async def handle_member_disconnect(self, member: discord.Member):
        """Handle when a member leaves voice channel during fractal"""
        if member not in self.members:
            return  # Not part of this fractal
        
        self.logger.info(f"Member {member.display_name} disconnected from voice during fractal")
        
        # If it's during voice phase and they're the current speaker
        if self.voice_phase_active and self.speaking_queue and self.speaking_queue.current_speaker == member:
            await self.original_channel.send(
                f"⚠️ **{member.mention} disconnected while speaking**\n"
                f"🎙️ Moving to next speaker..."
            )
            # Move to next speaker
            await self.start_next_speaker()
        
        # Remove their vote if they had one
        if member.id in self.votes:
            del self.votes[member.id]
            await self.thread.send(
                f"⚠️ **{member.mention} disconnected** - their vote has been removed\n"
                f"📊 **Progress:** {len(self.votes)}/{len(self.members)} votes cast"
            )
        
        # If they were the facilitator, transfer to first remaining member
        if member == self.facilitator and len(self.members) > 1:
            new_facilitator = next((m for m in self.members if m != member), None)
            if new_facilitator:
                self.facilitator = new_facilitator
                await self.thread.send(
                    f"👑 **Facilitator transferred** to {new_facilitator.mention} due to disconnect"
                )
        
        # Check if we still have enough members to continue
        remaining_members = [m for m in self.members if m.voice and m.voice.channel == self.voice_channel] if self.voice_channel else self.members
        if len(remaining_members) < 2:
            await self.thread.send(
                f"⚠️ **Not enough members remaining** to continue fractal\n"
                f"💡 Fractal will be paused. Use admin commands to add members or end the fractal."
            )
            # Pause the fractal
            if hasattr(self, 'paused'):
                self.paused = True
    
    async def start_fractal(self):
        """Initialize the fractal group (doesn't automatically start voice or voting)"""
        self.logger.info(f"Fractal group '{self.thread.name}' initialized with {len(self.members)} members")
        
        # Notify web app that fractal started (don't let this break the fractal)
        try:
            await web_integration.notify_fractal_started(self)
        except Exception as e:
            self.logger.warning(f"Web integration notification failed: {e}")
    
    async def start_voting_only(self):
        """Start voting without voice phase"""
        self.logger.info(f"Starting voting-only fractal for '{self.thread.name}'")
        
        # Enhanced welcome message for voting-only fractal
        welcome_msg = (
            f"# 🗳️ **Welcome to {self.thread.name}!** 🗳️\n\n"
            f"**Facilitator:** {self.facilitator.mention}\n"
            f"**Members ({len(self.members)}):** {', '.join([m.mention for m in self.members])}\n\n"
            f"🎯 **Fractal Voting Process Starting**\n"
            f"📊 **How it works:** Vote through levels 6→1 until we have a winner\n"
            f"🏆 **Goal:** Democratic consensus through progressive elimination\n"
            f"⚡ **Each round:** Vote for who should advance to the next level\n\n"
            f"**Let's begin with Level 6 voting!**"
        )
        await self.thread.send(welcome_msg)
        
        # Start voting immediately
        await self.start_new_round()
    
    async def start_voice_phase(self):
        """Start the voice speaking phase"""
        # Enhanced welcome message with clearer instructions
        welcome_msg = (
            f"# 🎊 **Welcome to {self.thread.name}!** 🎊\n\n"
            f"**Facilitator:** {self.facilitator.mention}\n"
            f"**Members ({len(self.members)}):** {', '.join([m.mention for m in self.members])}\n\n"
            f"🎙️ **Voice Speaking Phase Starting in {self.voice_channel.mention}**\n"
            f"⏱️ **Speaking Time:** {self.speaking_time//60} minutes per person\n"
            f"🎛️ **Timer Controls:** Available in {self.voice_channel.mention} text chat\n"
            f"📋 **Speaking Order:** Will be announced as we go\n\n"
            f"🗳️ **After Speaking:** We'll return here for fractal voting (6→1 elimination)\n"
            f"🎯 **Goal:** Democratic consensus through structured discussion + voting\n\n"
            f"**Ready to begin! First speaker will be announced shortly...**"
        )
        await self.thread.send(welcome_msg)
        
        # Create voice control panel in original channel
        from .views import VoiceFractalControlView
        control_view = VoiceFractalControlView(self)
        
        self.voice_control_message = await self.original_channel.send(
            self.format_voice_status(), 
            view=control_view
        )
        
        # Start first speaker
        await self.start_next_speaker()
    
    async def start_next_speaker(self):
        """Start the next speaker in the queue"""
        self.logger.info(f"start_next_speaker called, speaking_queue exists: {self.speaking_queue is not None}")
        if not self.speaking_queue:
            self.logger.warning("No speaking queue available")
            return
        
        next_speaker = self.speaking_queue.next_speaker()
        self.logger.info(f"Next speaker from queue: {next_speaker.display_name if next_speaker else 'None'}")
        if not next_speaker:
            # All speakers done, transition to voting
            self.logger.info("All speakers done, transitioning to voting")
            await self.transition_to_voting()
            return
        
        # Update control panel
        await self.update_voice_control_display()
        
        # Start timer for this speaker
        self.logger.info(f"Starting timer for {next_speaker.display_name} with {self.speaking_time} seconds")
        
        # Send immediate confirmation that timer started to original channel
        self.logger.info(f"Sending timer notification to channel: {self.original_channel.name} (ID: {self.original_channel.id})")
        await self.original_channel.send(f"🎙️ **{next_speaker.mention} is now speaking** ({self.speaking_time//60} minutes)")
        
        await self.voice_timer.start_timer(
            next_speaker,
            self.original_channel,  # Send timer notifications to original channel
            warning_callback=self.speaker_warning,
            complete_callback=self.speaker_time_up
        )
        
        # Start display update task for live countdown
        self.start_display_update_task()
    
    async def speaker_warning(self, speaker: discord.Member, seconds_remaining: int):
        """Called when speaker has limited time remaining"""
        await self.original_channel.send(f"⏰ {speaker.mention} - {seconds_remaining} seconds remaining!")
    
    async def speaker_time_up(self, speaker: discord.Member):
        """Called when speaker's time is up"""
        await self.original_channel.send(f"⏱️ Time's up {speaker.mention}!")
        # Auto-advance to next speaker
        await self.start_next_speaker()
    
    async def skip_current_speaker(self):
        """Skip current speaker and add them back to queue"""
        if not self.speaking_queue:
            return
        
        current = self.speaking_queue.current_speaker
        if current:
            self.voice_timer.stop_timer()
            next_speaker = self.speaking_queue.skip_and_return()
            
            await self.thread.send(f"⏸️ {current.display_name} skipped - will return later")
            
            if next_speaker:
                await self.start_next_speaker()
            else:
                await self.transition_to_voting()
    
    async def advance_speaker(self):
        """Manually advance to next speaker"""
        if self.voice_timer:
            self.voice_timer.stop_timer()
        await self.start_next_speaker()
    
    async def extend_speaking_time(self, seconds: int):
        """Add time to current speaker"""
        if self.voice_timer:
            self.voice_timer.extend_time(seconds)
            await self.update_voice_control_display()
    
    async def transition_to_voting(self):
        """Transition from voice phase to voting phase"""
        # Enhanced transition message with detailed summary
        if self.speaking_queue:
            completed_speakers = [speaker.display_name for speaker in self.speaking_queue.completed_speakers]
            skipped_speakers = [speaker.display_name for speaker in self.speaking_queue.skipped_speakers]
            
            speaking_summary = f"**Completed speakers:** {', '.join(completed_speakers) if completed_speakers else 'None'}\n"
            if skipped_speakers:
                speaking_summary += f"**Speakers who skipped:** {', '.join(skipped_speakers)}\n"
            
            total_speaking_time = len(completed_speakers) * (self.speaking_time // 60)
            speaking_summary += f"**Total speaking time:** ~{total_speaking_time} minutes\n"
        else:
            speaking_summary = "**All participants had the opportunity to speak**\n"
        
        await self.thread.send(
            f"🎙️ **Speaking Phase Complete!**\n"
            f"{speaking_summary}\n"
            f"🗳️ **Now transitioning to Fractal Voting...**\n"
            f"📊 **Process:** Vote through levels 6→1 until we have a winner!\n"
            f"🎯 **Remember:** Consider what you heard during the speaking phase\n"
            f"💡 **Voting tip:** Choose who you think should advance to the next level\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Stop timer, display updates and voice controls
        if self.voice_timer:
            self.voice_timer.stop_timer()
        self.stop_display_updates()
        if self.voice_control_message:
            await self.voice_control_message.edit(view=None)
        
        # Switch to voting mode
        self.voice_phase_active = False
        
        # Add a brief pause before starting voting to let people process
        await asyncio.sleep(2)
        
        await self.start_new_round()
    
    def format_voice_status(self) -> str:
        """Format current voice phase status"""
        if not self.speaking_queue:
            return "Voice phase not active"
        
        status_lines = [f"🎙️ **ZAO Fractal - Level {self.current_level} Speaking Phase**"]
        
        current = self.speaking_queue.current_speaker
        if current:
            time_remaining = self.voice_timer.get_time_remaining_formatted() if self.voice_timer else "Unknown"
            status_lines.append(f"**Current Speaker:** {current.mention} ({time_remaining} remaining)")
        
        queue_display = self.speaking_queue.format_queue_display()
        if queue_display != "No speakers in queue":
            status_lines.append(queue_display)
        
        return "\n".join(status_lines)
    
    async def update_voice_control_display(self):
        """Update the voice control panel display"""
        if self.voice_control_message:
            try:
                await self.voice_control_message.edit(content=self.format_voice_status())
            except discord.NotFound:
                pass  # Message was deleted
        
    async def add_member(self, member: discord.Member):
        """Add a member to the fractal group"""
        if member not in self.members:
            self.members.append(member)
            self.active_candidates.append(member)
            await self.thread.add_user(member)
            self.logger.info(f"Added {member.display_name} to fractal group '{self.thread.name}'")

    async def start_new_round(self, winner: Optional[discord.Member] = None):
        """Start a new voting round, optionally recording a previous winner"""
        # Process previous winner if exists
        if winner:
            self.winners[self.current_level] = winner
            self.active_candidates.remove(winner)  # Remove from active candidates
            self.current_level -= 1  # Move to next level
            
            # Send prominent winner announcement like the second image
            await self.thread.send(
                f"🎊 **LEVEL {self.current_level + 1} WINNER: {winner.mention}!** 🎊\n\n"
                f"Moving to Level {self.current_level}..."
            )
        
        # Check if we've reached the end
        if self.current_level < 1 or len(self.active_candidates) <= 1:
            await self.end_fractal()
            return
            
        # Reset votes for new round
        self.votes = {}
        
        # Log active candidates
        candidate_names = ", ".join([c.display_name for c in self.active_candidates])
        self.logger.info(f"Starting level {self.current_level} with {len(self.active_candidates)} candidates: {candidate_names}")
        
        try:
            # Import here to avoid circular import
            from .views import ZAOFractalVotingView
            
            # Create voting view with buttons
            view = ZAOFractalVotingView(self)
            
            # Create enhanced voting message with speaking phase context
            votes_needed = self.get_vote_threshold()
            candidates_list = ", ".join([c.mention for c in self.active_candidates])
            
            # Add speaking phase context if this was a voice fractal
            speaking_context = ""
            if self.voice_channel and hasattr(self, 'speaking_queue') and self.speaking_queue:
                speaking_context = f"💭 **Consider what you heard** during the speaking phase in {self.voice_channel.mention}\n"
            
            voting_message = (
                f"🗳️ **Voting for Level {self.current_level}**\n\n"
                f"**Candidates:** {candidates_list}\n"
                f"**Votes Needed to Win:** {votes_needed} ({votes_needed}/{len(self.members)} members)\n\n"
                f"{speaking_context}"
                f"🎯 **Vote for who should advance** to the next level\n"
                f"📢 **Your vote will be announced publicly**\n"
                f"🔄 **You can change your vote** by clicking a different button"
            )
            
            message = await self.thread.send(voting_message, view=view)
            self.current_voting_message = message
            
        except Exception as e:
            self.logger.error(f"Error creating voting UI: {e}", exc_info=True)
            await self.thread.send("❌ Error setting up voting buttons. Please try again.")

    def get_vote_threshold(self):
        """Calculate votes needed to win (50% or more)"""
        return max(1, len(self.members) // 2 + len(self.members) % 2)  # Ceiling division

    async def process_vote(self, voter: discord.Member, candidate: discord.Member):
        """Process a vote and announce it publicly"""
        try:
            self.logger.debug(f"Processing vote: {voter.display_name} → {candidate.display_name}")
            previous_vote = self.votes.get(voter.id)
            previous_candidate = None
            changed_vote = False
            
            if previous_vote:
                previous_candidate = discord.utils.get(self.active_candidates + [m for m in self.members if m.id in [w.id for w in self.winners.values()]], id=previous_vote)
                changed_vote = True
            
            # Update vote
            self.votes[voter.id] = candidate.id
            
            # Notify web app of vote (don't let this break the fractal)
            try:
                await web_integration.notify_vote_cast(self, voter, candidate)
            except Exception as e:
                self.logger.warning(f"Web integration vote notification failed: {e}")
            
            # Enhanced public announcement with vote progress
            votes_cast = len(self.votes)
            total_members = len(self.members)
            votes_needed = self.get_vote_threshold()
            
            if previous_candidate:
                await self.thread.send(
                    f"🔄 **Vote Changed:** {voter.mention} changed vote from {previous_candidate.mention} to {candidate.mention}\n"
                    f"📊 **Progress:** {votes_cast}/{total_members} votes cast • {votes_needed} needed to win"
                )
            else:
                await self.thread.send(
                    f"✅ **New Vote:** {voter.mention} voted for {candidate.mention}\n"
                    f"📊 **Progress:** {votes_cast}/{total_members} votes cast • {votes_needed} needed to win"
                )
            
            # Check if this vote caused a winner
            await self.check_for_winner()
            
            # Return information about the vote for enhanced feedback
            return {
                'changed_vote': changed_vote,
                'votes_cast': votes_cast,
                'total_members': total_members,
                'votes_needed': votes_needed
            }
            
        except Exception as e:
            self.logger.error(f"Error processing vote: {e}", exc_info=True)
            await self.handle_error(e, "process_vote")
            # Return basic info even on error
            return {
                'changed_vote': False,
                'votes_cast': len(self.votes),
                'total_members': len(self.members),
                'votes_needed': self.get_vote_threshold()
            }

    async def check_for_winner(self):
        """Check if any candidate has reached the vote threshold"""
        vote_counts = {}
        
        # Count votes for each candidate
        for candidate_id in self.votes.values():
            vote_counts[candidate_id] = vote_counts.get(candidate_id, 0) + 1
        
        threshold = self.get_vote_threshold()
        
        # Check for a winner
        max_votes = max(vote_counts.values()) if vote_counts else 0
        
        if max_votes >= threshold:
            # Find all candidates with max votes (for tie-breaking)
            winners_with_max_votes = [
                candidate_id for candidate_id, count in vote_counts.items() 
                if count == max_votes
            ]
            
            # Handle ties with random selection
            if len(winners_with_max_votes) > 1:
                await self.thread.send(
                    f"🎲 **Tie detected!** {len(winners_with_max_votes)} candidates tied with {max_votes} votes. Selecting randomly..."
                )
                winner_id = random.choice(winners_with_max_votes)
            else:
                winner_id = winners_with_max_votes[0]
            
            winner = discord.utils.get(self.active_candidates, id=winner_id)
            if winner:
                # Log winner info
                self.logger.info(f"Winner for level {self.current_level}: {winner.display_name} with {max_votes}/{len(self.members)} votes")
                
                # Notify web app of round completion
                await web_integration.notify_round_complete(self, winner)
                
                await self.start_new_round(winner)
                return

    async def end_fractal(self):
        """End the fractal process and show final results"""
        # Add final remaining candidate as last place
        if len(self.active_candidates) == 1:
            self.winners[self.current_level] = self.active_candidates[0]
        
        # Create final ranking
        final_ranking = []
        for level in sorted(self.winners.keys(), reverse=True):
            final_ranking.append(self.winners[level])
        
        # Show results in fractal thread
        results_text = "# 🏆 **FRACTAL COMPLETE!** 🏆\n\n**Final Rankings:**\n"
        for i, winner in enumerate(final_ranking, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            results_text += f"{medal} {winner.mention}\n"
        
        await self.thread.send(results_text)
        
        # Notify web app that fractal is complete
        await web_integration.notify_fractal_complete(self)
        
        # Post simple results to general channel
        try:
            # Find a general channel to post results
            general_channel = None
            for channel in self.thread.guild.channels:
                if isinstance(channel, discord.TextChannel) and (
                    'general' in channel.name.lower() or 
                    'main' in channel.name.lower() or
                    channel.name.lower() in ['chat', 'lobby']
                ):
                    general_channel = channel
                    break
            
            if not general_channel:
                # Fallback to first available text channel
                general_channel = next(
                    (ch for ch in self.thread.guild.channels if isinstance(ch, discord.TextChannel)),
                    None
                )
            
            if general_channel:
                simple_results = f"🏆 **{self.thread.name} Results:** "
                simple_results += ", ".join([f"{i+1}. {winner.display_name}" for i, winner in enumerate(final_ranking)])
                await general_channel.send(simple_results)
        
        except Exception as e:
            self.logger.error(f"Failed to post results to general channel: {e}")
        
        # Remove from active groups
        if hasattr(self.cog, 'active_groups') and self.thread.id in self.cog.active_groups:
            del self.cog.active_groups[self.thread.id]
        
        self.logger.info(f"Fractal group '{self.thread.name}' completed")
    
    def start_display_update_task(self):
        """Start task to update voice control display every 5 seconds"""
        if self.display_update_task:
            self.display_update_task.cancel()
        
        self.display_update_task = asyncio.create_task(self._update_display_loop())
    
    async def _update_display_loop(self):
        """Update the voice control display every 5 seconds"""
        try:
            while self.voice_phase_active and self.voice_timer and self.voice_timer.is_running:
                await asyncio.sleep(5)  # Update every 5 seconds
                await self.update_voice_control_display()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Display update error: {e}")
    
    def stop_display_updates(self):
        """Stop the display update task"""
        if self.display_update_task:
            self.display_update_task.cancel()
            self.display_update_task = None
