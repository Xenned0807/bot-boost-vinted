import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import threading
import os
import aiohttp
import json
import httpx
import tls_client
import random
import string
import logging
import asyncio
from discord import Embed
from vinted_client import VintedClient

# ----------------- Configuration Loading (Optionnel) -----------------
# Ce bloc n'est pas utilisé par le reste du code, vous pouvez le supprimer pour simplifier
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Info: Le fichier optionnel 'config/config.json' n'a pas été trouvé.")
    pass # On continue car la config principale vient du .env

# ----------------- KEEP ALIVE -----------------
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ----------------- DISCORD BOT -----------------
TOKEN = os.getenv("DISCORD_TOKEN")

STOCK_CHANNEL_ID = 1403423722509172886
BUTTON_CHANNEL_ID = 1403435686937366669
GUILD_ID = 1315005427150225458

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
vinted_task = None

@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Game(name="Best Market")
    )
    print(f"Bot connected as {bot.user}")

    button_channel = bot.get_channel(BUTTON_CHANNEL_ID)
    if button_channel:
        # Note : MainStockButton est défini plus bas, le bot doit être prêt.
        # Pour éviter les problèmes, on s'assure que la vue est prête
        try:
            await button_channel.send(
                "CHECK THE CURRENT STOCK",
                view=MainStockButton()
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi du bouton de stock : {e}")

    await bot.tree.sync()
    print("✅ Commandes slash synchronisées.")

# ------------------ Slash Commands ------------------
@bot.tree.command(name="serverinfo", description="Show information about the server")
async def serverinfo(interaction: discord.Interaction):
    # ... (code de la commande inchangé)
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command must be used inside a server.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Information about {guild.name}", color=discord.Color.blue())
    embed.add_field(name="Server ID", value=str(guild.id), inline=False)
    embed.add_field(name="Owner", value=str(guild.owner), inline=False)
    embed.add_field(name="Member Count", value=str(guild.member_count), inline=False)
    embed.add_field(name="Created On", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="join", description="Fait rejoindre le bot dans ton salon vocal")
async def join(interaction: discord.Interaction):
    # ... (code de la commande inchangé)
    # Note : ce code est complexe et peut avoir des cas limites
    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        await interaction.response.send_message("❌ Tu dois être dans un salon vocal.", ephemeral=True)
        return
    channel = voice_state.channel
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f"✅ Connecté à {channel.name}")


@bot.tree.command(name="leave", description="Déconnecte le bot du salon vocal")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Déconnecté du salon vocal.")
    else:
        await interaction.response.send_message("❌ Je ne suis pas connecté en vocal.")


@bot.tree.command(name="paypal", description="Show PayPal address with the desired amount")
@app_commands.describe(amount="Amount to send (e.g. 25€)")
async def paypal(interaction: discord.Interaction, amount: str):
    message = f"**{amount}**\n`ewenn.larequie@gmail.com`\nFriends & Family"
    await interaction.response.send_message(message)


@bot.tree.command(name="offer", description="Show a special offer with the desired price")
@app_commands.describe(price="Offer price (e.g. 50)")
async def offer(interaction: discord.Interaction, price: str):
    embed = discord.Embed(
        title="<a:BlackHeartSpin:1315323757576978532> SPECIAL OFFER <a:BlackHeartSpin:1315323757576978532>",
        description="*Only today!*",
        color=discord.Color.purple()
    )
    embed.add_field(name="💰 Price", value=f"**{price}€**", inline=False)
    embed.set_footer(text="Obscur Market")
    await interaction.response.send_message(content="@everyone", embed=embed)

# ------------------ /boost command ------------------
class Booster:
    # ... (le code de la classe Booster reste inchangé)
    def __init__(self):
        self.client = tls_client.Session(client_identifier="chrome112", random_tls_extension_order=True)
    def get_cookies(self):
        # ...
        return {}
    def headers(self, token: str):
        # ...
        return {}
    def get_tokens_from_file(self, filename: str):
        # ...
        return []
    def boost_server(self, token, guild_id, success_list, failed_list):
        # ...
        pass

@bot.tree.command(name="boost", description="Boost a server using tokens from 3m.txt")
@app_commands.describe(guild_id="The ID of the server to boost")
async def boost_command(interaction: discord.Interaction, guild_id: str):
    await interaction.response.defer(ephemeral=False)
    
    booster = Booster()
    tokens = booster.get_tokens_from_file("data/3m.txt")
    
    if not tokens:
        await interaction.followup.send("❌ No tokens found in data/3m.txt.")
        return

    success_list = []
    failed_list = []
    threads = []
    
    await interaction.followup.send(f"🚀 Starting to boost server `{guild_id}` with {len(tokens)} tokens...")
    
    for token in tokens:
        thread = threading.Thread(target=booster.boost_server, args=(token, guild_id, success_list, failed_list))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    success_count = len(success_list)
    failed_count = len(failed_list)
    
    embed = discord.Embed(
        title="Boost Operation Complete",
        description=f"Summary for server ID `{guild_id}`",
        color=discord.Color.green() if success_count > 0 else discord.Color.red()
    )
    embed.add_field(name="✅ Successful Boosts", value=success_count, inline=False)
    embed.add_field(name="❌ Failed Boosts", value=failed_count, inline=False)
    await interaction.followup.send(embed=embed)


# =======================================================
# == ICI EST LE BON ENDROIT POUR LE MONITEUR VINTED =====
# =======================================================

# ------------------ Vinted Monitor System ------------------
def create_vinted_embed(item: dict) -> Embed:
    """Crée un message Discord 'Embed' formaté pour un article Vinted."""
    embed = Embed(
        title=f"✨ Nouvelle Annonce : {item['title']}",
        url=item['url'],
        color=0x007788
    )
    if item.get('photo') and item['photo'].get('url'):
        embed.set_image(url=item['photo']['url'])
    
    embed.add_field(name="Prix", value=f"**{item['price']} €**", inline=True)
    embed.add_field(name="Taille", value=item.get('size_title', 'N/A'), inline=True)
    embed.add_field(name="Marque", value=item.get('brand_title', 'N/A'), inline=True)
    
    if item.get('user'):
        embed.set_footer(text=f"Vendu par {item['user']['login']}")
    return embed

async def vinted_monitor_task():
    """Tâche de fond qui surveille Vinted et poste les nouvelles annonces."""
    await bot.wait_until_ready()
    
    channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
    search_url = os.getenv("VINTED_SEARCH_URL")
    delay = int(os.getenv("VINTED_DELAY_SECONDS"))
    
    channel = bot.get_channel(channel_id)
    if not channel:
        print(f"ERREUR VINTED: Le salon avec l'ID {channel_id} est introuvable.")
        return

    vinted_client = VintedClient(search_url=search_url)
    
    if not await vinted_client.initialize_session():
        print("Échec de l'initialisation du client Vinted. Arrêt de la tâche.")
        await channel.send("❌ Impossible de se connecter à Vinted pour le moment. Le moniteur n'a pas pu démarrer.")
        return
    
    print(f"La surveillance Vinted va démarrer dans le salon #{channel.name}.")

    try:
        while not bot.is_closed():
            try:
                new_items = await vinted_client.search_new_items()
                if new_items:
                    for item in reversed(new_items):
                        embed = create_vinted_embed(item)
                        await channel.send(embed=embed)
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                print("La tâche de surveillance Vinted a été arrêtée.")
                break
            except Exception as e:
                print(f"ERREUR dans la boucle Vinted : {e}")
                await asyncio.sleep(delay * 2)
    finally:
        await vinted_client.close_session()
        print("Session Vinted fermée proprement.")

@bot.command()
async def start_vinted(ctx):
    """Lance la surveillance des annonces Vinted."""
    global vinted_task
    if vinted_task and not vinted_task.done():
        await ctx.send("✅ La surveillance Vinted est déjà active !")
        return
    
    vinted_task = bot.loop.create_task(vinted_monitor_task())
    await ctx.send("🚀 **Surveillance Vinted activée !**")

@bot.command()
async def stop_vinted(ctx):
    """Arrête la surveillance des annonces Vinted."""
    global vinted_task
    if vinted_task and not vinted_task.done():
        vinted_task.cancel()
        await ctx.send("🛑 **Surveillance Vinted arrêtée.**")
    else:
        await ctx.send("La surveillance Vinted n'est pas active.")


# ------------------ Stock system ------------------
produits = [
    "disney-plus", "prime-video", "spotify", "netflix", "capcut-pro",
    "chatgpt-plus", "canva", "youtube", "crunchyroll", "dazn",
    "nord-vpn", "paramount-plus", "nitro-boost", "nitro-basic",
    "spotify-generator", "boost-tool", "x14-server-boosts"
]

class StockSelect(discord.ui.Select):
    def __init__(self, produits):
        options = [discord.SelectOption(label=prod, description=f"View stock for {prod}") for prod in produits]
        super().__init__(placeholder="Select a product", options=options)

    async def callback(self, interaction: discord.Interaction):
        produit = self.values[0]
        stock_channel = interaction.client.get_channel(STOCK_CHANNEL_ID)
        stock_value = "Not found"

        async for msg in stock_channel.history(limit=50):
            lignes = msg.content.split("\n")
            for ligne in lignes:
                if ligne.lower().startswith(produit.lower()):
                    try:
                        stock_value = ligne.split(":")[1].strip()
                    except:
                        stock_value = "Invalid format"
                    break
            if stock_value != "Not found":
                break

        await interaction.response.send_message(f"📦 **{produit}** → Remaining stock: **{stock_value}**", ephemeral=True)


class StockView(discord.ui.View):
    def __init__(self, produits):
        super().__init__()
        self.add_item(StockSelect(produits))


class MainStockButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 View Stock", style=discord.ButtonStyle.primary)
    async def show_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select a product to check its stock:", view=StockView(produits), ephemeral=True)


# Lancer le keep-alive avant le bot
keep_alive()
bot.run(TOKEN)
