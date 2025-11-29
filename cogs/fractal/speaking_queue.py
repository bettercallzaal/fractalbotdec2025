import discord
import asyncio
import logging
from typing import List, Optional

class SpeakingQueue:
    """Manages the speaking order and queue for voice fractals"""
    
    def __init__(self, participants: List[discord.Member]):
        self.active_queue = participants.copy()
        self.completed_speakers = []
        self.skipped_speakers = []
        self.current_speaker = None
        self.logger = logging.getLogger('bot')
    
    def next_speaker(self) -> Optional[discord.Member]:
        """Move to next person, current speaker goes to completed"""
        if self.current_speaker:
            self.completed_speakers.append(self.current_speaker)
            self.logger.info(f"Moved {self.current_speaker.display_name} to completed speakers")
        
        if self.active_queue:
            self.current_speaker = self.active_queue.pop(0)
            self.logger.info(f"Next speaker: {self.current_speaker.display_name}")
            return self.current_speaker
        elif self.skipped_speakers:
            # Cycle skipped speakers back to active queue
            self.cycle_skipped_speakers()
            return self.next_speaker()
        else:
            self.current_speaker = None
            return None
    
    def skip_and_return(self) -> Optional[discord.Member]:
        """Skip current speaker, add to end of queue"""
        if self.current_speaker:
            self.skipped_speakers.append(self.current_speaker)
            self.logger.info(f"Skipped {self.current_speaker.display_name} - will return later")
            self.current_speaker = None
        
        return self.next_speaker()
    
    def cycle_skipped_speakers(self):
        """Move skipped speakers back to active queue"""
        if self.skipped_speakers:
            self.active_queue.extend(self.skipped_speakers)
            self.skipped_speakers.clear()
            self.logger.info("Cycled skipped speakers back to active queue")
    
    def get_remaining_speakers(self) -> List[discord.Member]:
        """Get all speakers who haven't completed speaking"""
        remaining = []
        if self.current_speaker:
            remaining.append(self.current_speaker)
        remaining.extend(self.active_queue)
        remaining.extend(self.skipped_speakers)
        return remaining
    
    def is_complete(self) -> bool:
        """Check if all speakers have completed"""
        return (not self.current_speaker and 
                not self.active_queue and 
                not self.skipped_speakers)
    
    def format_queue_display(self) -> str:
        """Generate formatted display of current queue status"""
        lines = []
        
        if self.current_speaker:
            lines.append(f"**Current:** {self.current_speaker.display_name}")
        
        if self.active_queue:
            queue_names = " → ".join([user.display_name for user in self.active_queue[:3]])
            if len(self.active_queue) > 3:
                queue_names += f" → +{len(self.active_queue) - 3} more"
            lines.append(f"**Queue:** {queue_names}")
        
        if self.skipped_speakers:
            skipped_names = ", ".join([user.display_name for user in self.skipped_speakers])
            lines.append(f"**Skipped (will return):** {skipped_names}")
        
        if self.completed_speakers:
            completed_names = ", ".join([user.display_name for user in self.completed_speakers])
            lines.append(f"**Completed:** {completed_names}")
        
        return "\n".join(lines) if lines else "No speakers in queue"


class VoiceTimer:
    """Manages speaking timers with warnings and notifications"""
    
    def __init__(self, speaking_time: int = 120):
        self.speaking_time = speaking_time  # seconds
        self.current_task = None
        self.time_remaining = 0
        self.is_running = False
        self.logger = logging.getLogger('bot')
    
    async def start_timer(self, speaker: discord.Member, callback_channel, warning_callback=None, complete_callback=None):
        """Start timer for a speaker with optional callbacks"""
        if self.current_task:
            self.current_task.cancel()
        
        self.is_running = True
        self.time_remaining = self.speaking_time
        
        # Start the timer task but don't await it (non-blocking)
        self.current_task = asyncio.create_task(
            self._run_timer(speaker, callback_channel, warning_callback, complete_callback)
        )
        
        self.logger.info(f"Started timer for {speaker.display_name} ({self.speaking_time} seconds)")
    
    async def _run_timer(self, speaker, callback_channel, warning_callback, complete_callback):
        """Internal timer logic"""
        try:
            # Wait until 1 minute remaining
            if self.speaking_time > 60:
                await asyncio.sleep(self.speaking_time - 60)
                self.time_remaining = 60
                
                # Send 1-minute warning
                if warning_callback:
                    await warning_callback(speaker, 60)
                else:
                    await callback_channel.send(f"⏰ {speaker.mention} - 1 minute remaining!")
            
            # Wait for final minute
            await asyncio.sleep(min(60, self.speaking_time))
            self.time_remaining = 0
            
            # Time's up notification
            if complete_callback:
                await complete_callback(speaker)
            else:
                await callback_channel.send(f"⏱️ Time's up {speaker.mention}!")
                
        except asyncio.CancelledError:
            self.logger.info(f"Timer cancelled for {speaker.display_name}")
            raise
        finally:
            self.is_running = False
    
    def extend_time(self, seconds: int):
        """Add time to current timer"""
        if self.is_running:
            self.time_remaining += seconds
            self.speaking_time += seconds
            self.logger.info(f"Extended timer by {seconds} seconds")
    
    def stop_timer(self):
        """Stop the current timer"""
        if self.current_task:
            self.current_task.cancel()
            self.current_task = None
        self.is_running = False
    
    def get_time_remaining_formatted(self) -> str:
        """Get formatted time remaining"""
        if not self.is_running:
            return "Not running"
        
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        return f"{minutes}:{seconds:02d}"
