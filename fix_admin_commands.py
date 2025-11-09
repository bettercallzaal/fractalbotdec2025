#!/usr/bin/env python3
"""
Script to fix all admin command interaction handling
"""

import re

def fix_admin_commands():
    file_path = "/Users/zaalpanthaki/Documents/ZTalent Files/CodingAI/fractalbotnov2025/cogs/fractal/cog.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the problematic admin permission checks
    pattern = r'(async def admin_\w+\([^)]+\):\s*"""[^"]*"""\s*)if not interaction\.user\.guild_permissions\.administrator:\s*await interaction\.response\.send_message\([^)]+\)\s*return\s*await interaction\.response\.defer\(ephemeral=True\)'
    
    # Replace with correct pattern
    def replacement(match):
        func_def = match.group(1)
        return f'{func_def}await interaction.response.defer(ephemeral=True)\n        \n        if not interaction.user.guild_permissions.administrator:\n            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)\n            return'
    
    # Apply the fix
    fixed_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
    
    # Also fix cases where defer comes after permission check
    pattern2 = r'if not interaction\.user\.guild_permissions\.administrator:\s*await interaction\.response\.send_message\("❌ You need administrator permissions to use this command\.", ephemeral=True\)\s*return\s*await interaction\.response\.defer\(ephemeral=True\)'
    
    replacement2 = 'await interaction.response.defer(ephemeral=True)\n        \n        if not interaction.user.guild_permissions.administrator:\n            await interaction.followup.send("❌ You need administrator permissions to use this command.", ephemeral=True)\n            return'
    
    fixed_content = re.sub(pattern2, replacement2, fixed_content, flags=re.MULTILINE)
    
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print("Fixed admin command interaction handling")

if __name__ == "__main__":
    fix_admin_commands()
