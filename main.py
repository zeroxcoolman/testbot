import discord
from discord.ext import commands
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

TOKEN = os.environ["DISCORD_TOKEN"]
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def get_enchantments(rod_name):
    base_url = "https://fischipedia.org/wiki/"
    safe_name = urllib.parse.quote(rod_name.replace(" ", "_"))
    url = base_url + safe_name

    response = requests.get(url)
    if response.status_code != 200:
        return None, f"❌ Couldn't find page for '{rod_name}'."

    soup = BeautifulSoup(response.text, "html.parser")

    enchant_header = soup.find("span", id="Enchantments")
    if not enchant_header:
        return None, f"❌ Couldn't find enchantments section on the page."

    enchant_section = enchant_header.find_parent("h2").find_next_sibling()
    text = enchant_section.get_text(separator="\n").strip() if enchant_section else ""

    return url, text or "❌ No enchantments listed."

@tree.command(name="enchant", description="Get recommended enchantments for a rod")
@app_commands.describe(rod_name="Name of the rod to search for")
async def enchant(interaction: discord.Interaction, rod_name: str):
    await interaction.response.defer()
    url, data = get_enchantments(rod_name)

    if url:
        embed = discord.Embed(title=f"🎣 Enchantments for {rod_name}", description=data[:4000], color=discord.Color.blue())
        embed.set_footer(text="From Fischipedia", icon_url="https://fischipedia.org/favicon.ico")
        embed.url = url
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(data)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
