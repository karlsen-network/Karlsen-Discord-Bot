import discord
from discord.ext import commands
import aiohttp
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Ensure this is enabled

# Set the command prefix
bot = commands.Bot(command_prefix='/', intents=intents)

TOKEN = 'X'  # Replace with your bot token
COMMAND_LOG_CHANNEL_ID = 1249031011371843669  # Channel to log /b commands

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')

@bot.command(name='b')
async def check_balance(ctx, *, address: str):
    logging.info(f"Processing /b command: {address}")
    balance = await get_wallet_balance(address)
    if balance is not None:
        await ctx.send(f"The wallet `{address}` has a balance of {balance / 1e8:.8f} KLS")
        logging.info(f"Sent balance for address {address}: {balance / 1e8:.8f} KLS")
    else:
        await ctx.send("Failed to retrieve the wallet balance. Please check the address and try again.")
        logging.error("Balance retrieval failed, balance is None.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    logging.debug(f"Raw message data: {message}")
    logging.debug(f"Message content: '{message.content}'")
    logging.debug(f"Received message: '{message.content}' from {message.author} in channel {message.channel.id}")

    await bot.process_commands(message)

async def get_wallet_balance(address):
    try:
        url = f'https://api.karlsencoin.com/addresses/{address}/balance'
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'accept': 'application/json'}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['balance']
                else:
                    logging.error(f"Failed to fetch balance for address {address}: {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Exception in get_wallet_balance: {e}")
        return None

bot.run(TOKEN)