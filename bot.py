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

# ----------------- Configuration Loading -----------------
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Erreur: Le fichier 'config/config.json' n'a pas été trouvé. Veuillez le créer dans votre dépôt GitHub.")
    exit()

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
        await button_channel.send(
            "CHECK THE CURRENT STOCK",
            view=MainStockButton()
        )

    await bot.tree.sync()
    print("✅ Commandes slash synchronisées.")

# ------------------ /serverinfo command ------------------
@bot.tree.command(name="serverinfo", description="Show information about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message("❌ This command must be used inside a server.", ephemeral=True)
        return

    name = guild.name
    id_ = guild.id
    owner = guild.owner
    member_count = guild.member_count
    created_at = guild.created_at.strftime("%d/%m/%Y %H:%M:%S")
    region = guild.region if hasattr(guild, 'region') else "N/A"

    embed = discord.Embed(title=f"Information about {name}", color=discord.Color.blue())
    embed.add_field(name="Server ID", value=str(id_), inline=False)
    embed.add_field(name="Owner", value=str(owner), inline=False)
    embed.add_field(name="Member Count", value=str(member_count), inline=False)
    embed.add_field(name="Created On", value=created_at, inline=False)
    embed.set_footer(text="Obscur Market")

    await interaction.response.send_message(embed=embed)

# ------------------ /join command ------------------
@bot.tree.command(name="join", description="Fait rejoindre le bot dans ton salon vocal")
async def join(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    SERVEUR_PRINCIPAL_ID = 1315005427150225458
    AUTRE_SERVEUR_ID = 1325503567397912627

    if guild_id == SERVEUR_PRINCIPAL_ID:
        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            await interaction.response.send_message("❌ Tu dois être dans un salon vocal pour utiliser cette commande.", ephemeral=True)
            return
        channel = voice_state.channel
    elif guild_id == AUTRE_SERVEUR_ID:
        guild = bot.get_guild(AUTRE_SERVEUR_ID)
        channel = guild.get_channel(1325521098510700636)
        if not channel:
            await interaction.response.send_message("❌ Le salon vocal n'a pas été trouvé.", ephemeral=True)
            return
    else:
        await interaction.response.send_message("❌ Ce serveur n'est pas supporté pour cette commande.", ephemeral=True)
        return

    permissions = channel.permissions_for(interaction.guild.me)
    if not permissions.connect:
        await interaction.response.send_message("❌ Je n'ai pas la permission de me connecter à ce salon vocal.", ephemeral=True)
        return

    await interaction.response.defer()

    try:
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur lors de la connexion : {e}", ephemeral=True)
        return

    await interaction.followup.send(f"✅ Connecté à {channel.name}")

# ------------------ /leave command ------------------
@bot.tree.command(name="leave", description="Déconnecte le bot du salon vocal")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Déconnecté du salon vocal.")
    else:
        await interaction.response.send_message("❌ Je ne suis pas connecté en vocal.")

# ------------------ /paypal command ------------------
@bot.tree.command(name="paypal", description="Show PayPal address with the desired amount")
@app_commands.describe(amount="Amount to send (e.g. 25€)")
async def paypal(interaction: discord.Interaction, amount: str):
    message = f"**{amount}**\n`ewenn.larequie@gmail.com`\nFriends & Family"
    await interaction.response.send_message(message)

# ------------------ /offer command ------------------
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
    def __init__(self):
        self.client = tls_client.Session(
            client_identifier="chrome112",
            random_tls_extension_order=True
        )

    def get_cookies(self):
        cookies = {}
        try:
            response = self.client.get('https://discord.com')
            for cookie in response.cookies:
                if cookie.name.startswith('__') and cookie.name.endswith('uid'):
                    cookies[cookie.name] = cookie.value
            return cookies
        except Exception:
            return cookies

    def headers(self, token: str):
        headers = {
            'authority': 'discord.com',
            'accept': '*/*',
            'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'authorization': token,
            'content-type': 'application/json',
            'origin': 'https://discord.com',
            'referer': 'https://discord.com/channels/@me',
            'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'x-context-properties': 'eyJsb2NhdGlvbiI6IkpvaW4gR3VpbGQiLCJsb2NhdGlvbl9ndWlsZF9pZCI6IjExMDQzNzg1NDMwNzg2Mzc1OTEiLCJsb2NhdGlvbl9jaGFubmVsX2lkIjoiMTEwNzI4NDk3MTkwMDYzMzIzMCIsImxvY2F0aW9uX2NoYW5uZWxfdHlwZSI6MH0=',
            'x-debug-options': 'bugReporterEnabled',
            'x-discord-locale': 'en-GB',
            'x-super-properties': 'eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6Iml0LUlUIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzExMi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTEyLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwIiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjE5MzkwNiwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiZGVzaWduX2lkIjowfQ==',
        }
        return headers

    def get_tokens_from_file(self, filename: str):
        tokens = []
        try:
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        if ":" in line:
                            parts = line.split(":")
                            if len(parts) >= 3:
                                tokens.append(parts[2])
                        else:
                            tokens.append(line)
        except FileNotFoundError:
            return []
        return tokens

    def boost_server(self, token, guild_id, success_list, failed_list):
        try:
            headers = self.headers(token)
            
            slots_response = httpx.get(
                "https://discord.com/api/v9/users/@me/guilds/premium/subscription-slots",
                headers=headers,
            )

            if slots_response.status_code == 401:
                logging.error(f"Token invalid or no Nitro: {token}")
                failed_list.append(token)
                return

            slots_json = slots_response.json()
            boosts_list = [boost["id"] for boost in slots_json]

            payload = {"user_premium_guild_subscription_slot_ids": boosts_list}

            boosted_response = self.client.put(
                f"https://discord.com/api/v9/guilds/{guild_id}/premium/subscriptions",
                json=payload,
                headers=headers,
                cookies=self.get_cookies()
            )

            if boosted_response.status_code == 201:
                success_list.append(token)
                logging.info(f"Successfully boosted server {guild_id} with token: {token}")
            else:
                logging.error(f"Failed to boost server {guild_id} with token: {token} - Status code: {boosted_response.status_code}")
                failed_list.append(token)

        except Exception as e:
            logging.error(f"An error occurred while boosting with token {token}: {e}")
            failed_list.append(token)

@bot.tree.command(name="boost", description="Boost a server using tokens from 3m.txt")
@app_commands.describe(guild_id="The ID of the server to boost")
async def boost_command(interaction: discord.Interaction, guild_id: str):
    await interaction.response.defer(ephemeral=False)
    
    booster = Booster()
    tokens = booster.get_tokens_from_file("data/3m.txt")
    
    if not tokens:
        await interaction.followup.send("❌ No tokens found in data/3m.txt. Make sure the file exists in your repository.")
        return

    success_list = []
    failed_list = []
    threads = []
    
    await interaction.followup.send(f"🚀 Starting to boost server with ID `{guild_id}` using {len(tokens)} tokens...")
    
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
    embed.set_footer(text="Boosts provided by Obscur Market")
    
    await interaction.followup.send(embed=embed)

    # ------------------ Vinted Monitor System ------------------

def create_vinted_embed(item: dict) -> Embed:
    """Crée un message Discord 'Embed' formaté pour un article Vinted."""
    embed = Embed(
        title=f"✨ Nouvelle Annonce : {item['title']}",
        url=item['url'],
        color=0x007788  # Couleur bleu-vert Vinted
    )
    if item.get('photo') and item['photo'].get('url'):
        embed.set_image(url=item['photo']['url'])
    
    embed.add_field(name="Prix", value=f"**{item['price']} €**", inline=True)
    embed.add_field(name="Taille", value=item.get('size_title', 'N/A'), inline=True)
    embed.add_field(name="Marque", value=item.get('brand_title', 'N/A'), inline=True)
    
    if item.get('user'):
         embed.set_footer(text=f"Vendu par {item['user']['login']}")
    return embed
    
# Dans bot.py (à vérifier)
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
        options = [
            discord.SelectOption(label=prod, description=f"View stock for {prod}")
            for prod in produits
        ]
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

        await interaction.response.send_message(
            f"📦 **{produit}** → Remaining stock: **{stock_value}**",
            ephemeral=True
        )

class StockView(discord.ui.View):
    def __init__(self, produits):
        super().__init__()
        self.add_item(StockSelect(produits))

class MainStockButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📦 View Stock", style=discord.ButtonStyle.primary)
    async def show_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Select a product to check its stock:",
            view=StockView(produits),
            ephemeral=True
        )

# Lancer le keep-alive avant le bot
keep_alive()
bot.run(TOKEN)


