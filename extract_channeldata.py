import discord
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define intents
intents = discord.Intents.default()
intents.guilds = True

client = discord.Client(intents=intents)

TOKEN = 'X'  # Replace with your actual token
GUILD_ID = 1169939685280337930  # Replace with your actual guild ID

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    
    if guild:
        channel_data = []
        for channel in guild.channels:
            channel_info = {
                'id': channel.id,
                'name': channel.name,
                'category': channel.category_id if channel.category else None,
                'type': 'voice' if isinstance(channel, discord.VoiceChannel) else 'text'
            }
            channel_data.append(channel_info)
            print(channel_info)
        
        # If you want to save it to a file
        with open('channel_data.txt', 'w', encoding='utf-8') as f:
            for channel in channel_data:
                f.write(f"{channel}\n")

    await client.close()

client.run(TOKEN)
