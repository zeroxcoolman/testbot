import discord
from discord.ext import commands
from discord import app_commands
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os

TOKEN = os.getenv("DISCORD_TOKEN")  # Make sure this matches your environment variable name

# Enable necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Required for slash commands

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

def get_enchantments(rod_name):
    base_url = "https://fischipedia.org/wiki/"
    search_url = "https://fischipedia.org/w/index.php?search="
    
    # Try these variations in order
    variations = [
        rod_name,
        f"{rod_name} (Rod)",
        rod_name.replace(" Rod", ""),
        f"{rod_name.replace(' Rod', '')} (Rod)",
        f"{rod_name} Rod",
        f"{rod_name} Rod (Rod)"
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    variations = [v for v in variations if not (v in seen or seen.add(v))]
    
    for variant in variations:
        safe_name = urllib.parse.quote(variant.replace(" ", "_"))
        url = base_url + safe_name
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Check if this is a real page or just search results
                if soup.find("div", class_="noarticletext"):
                    continue
                
                # More flexible enchantment finding
                enchant_header = soup.find(lambda tag: tag.name in ["h2", "h3"] and 
                                         "enchant" in tag.text.lower())
                
                if not enchant_header:
                    return url, "❌ Page exists but no enchantments section found."
                    
                content = []
                next_tag = enchant_header.find_next_sibling()
                while next_tag and next_tag.name not in ["h2", "h3"]:
                    content.append(next_tag.get_text(separator="\n", strip=True))
                    next_tag = next_tag.find_next_sibling()
                
                text = "\n".join(filter(None, content)) or "❌ No enchantments listed."
                return url, text
                
        except requests.RequestException as e:
            print(f"Error checking {url}: {e}")
            continue
    
    # If no page found, try searching
    try:
        search_response = requests.get(f"{search_url}{urllib.parse.quote(rod_name)}&go=Go", timeout=10)
        if search_response.status_code == 200:
            search_soup = BeautifulSoup(search_response.text, "html.parser")
            first_result = search_soup.find("ul", class_="mw-search-results")
            if first_result:
                result_link = first_result.find("a")["href"]
                if result_link.startswith("/wiki/"):
                    result_url = "https://fischipedia.org" + result_link
                    response = requests.get(result_url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        enchant_header = soup.find(lambda tag: tag.name in ["h2", "h3"] and 
                                                 "enchant" in tag.text.lower())
                        if enchant_header:
                            content = []
                            next_tag = enchant_header.find_next_sibling()
                            while next_tag and next_tag.name not in ["h2", "h3"]:
                                content.append(next_tag.get_text(separator="\n", strip=True))
                                next_tag = next_tag.find_next_sibling()
                            text = "\n".join(filter(None, content)) or "❌ No enchantments listed."
                            return result_url, text
    except requests.RequestException as e:
        print(f"Error during search: {e}")
    
    # Final fallback
    safe_search = urllib.parse.quote(rod_name)
    return None, (f"❌ Couldn't find enchantments for '{rod_name}'.\n"
                 f"🔍 Try searching manually:\n"
                 f"https://fischipedia.org/w/index.php?search={safe_search}&title=Special:Search&go=Go")

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
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: No bot token found. Please set DISCORD_TOKEN environment variable.")
    else:
        try:
            bot.run(TOKEN)
        except discord.LoginFailure:
            print("❌ Invalid token. Please check your DISCORD_TOKEN.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
