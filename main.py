import discord
from discord.ext import commands
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

TOKEN = os.getenv("BOT_TOKEN") or "your_token_here"  # Fallback for testing

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for slash commands to work properly

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def get_enchantments(rod_name):
    # Try different formatting variations
    variations = [
        rod_name,
        rod_name + " (Rod)",
        rod_name.replace(" rod", "").strip(),
        rod_name.replace(" rod", "").strip() + " (Rod)"
    ]
    
    for variant in variations:
        base_url = "https://fischipedia.org/wiki/"
        safe_name = urllib.parse.quote(variant.replace(" ", "_"))
        url = base_url + safe_name

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                enchant_header = soup.find("span", id="Enchantments")
                if not enchant_header:
                    return url, "❌ Couldn't find enchantments section on the page."
                    
                enchant_section = enchant_header.find_parent("h2").find_next_sibling()
                text = enchant_section.get_text(separator="\n").strip() if enchant_section else ""
                
                return url, text or "❌ No enchantments listed."
        except requests.RequestException:
            continue
    
    return None, f"❌ Couldn't find page for any variation of '{rod_name}'."

@tree.command(name="enchant", description="Get recommended enchantments for a rod")
@app_commands.describe(rod_name="Name of the rod to search for")
async def enchant(interaction: discord.Interaction, rod_name: str):
    await interaction.response.defer()
    url, data = get_enchantments(rod_name)

    if url:
        embed = discord.Embed(
            title=f"🎣 Enchantments for {rod_name}",
            description=data[:4000],
            color=discord.Color.blue()
        )
        embed.set_footer(text="From Fischipedia", icon_url="https://fischipedia.org/favicon.ico")
        embed.url = url
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(data)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# Run the bot
if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: No bot token found. Please set BOT_TOKEN environment variable.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Error: Invalid bot token. Please check your token.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
