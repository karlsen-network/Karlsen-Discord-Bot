import discord
from discord.ext import commands
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
import time

# Configure OpenAI API key and bot token
OPENAI_API_KEY = "XXXXXXXXXXXXXXXXXX"  # Replace with your OpenAI API key
ASSISTANT_ID = "XXXXXXXXXXXXXXXXXX"  # Replace with your Assistant ID
TOKEN = "XXXXXXXXXXXXXXXXXX"  # Replace with your bot token

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# intents with all access
intents = discord.Intents.all()

# command prefix
bot = commands.Bot(command_prefix="/", intents=intents)

# Guild ID
GUILD_ID = XXXXXXXXXXXXXXXXXX

# Channel and role IDs
OFFTOPIC_CHAT_ID = XXXXXXXXXXXXXXXXXX
CATEGORY_ID = XXXXXXXXXXXXXXXXXX
ROLE_ID = XXXXXXXXXXXXXXXXXX
MEMBER_COUNT_CHANNEL_ID = XXXXXXXXXXXXXXXXXX
VERIFICATION_CHANNEL_ID = XXXXXXXXXXXXXXXXXX
VERIFIED_ROLE_ID = XXXXXXXXXXXXXXXXXX
VERIFICATION_MESSAGE_ID = XXXXXXXXXXXXXXXXXX
LOG_CHANNEL_ID = XXXXXXXXXXXXXXXXXX
COMMAND_LOG_CHANNEL_ID = XXXXXXXXXXXXXXXXXX
EXCLUDED_SPAM_CHECK_CHANNEL_ID = XXXXXXXXXXXXXXXXXX

# Anti-spam settings
ACCOUNT_AGE_LIMIT = timedelta(days=X)
SPAM_THRESHOLD = X
SPAM_TIMEOUT = timedelta(minutes=X)

# Keywords for checking display names and message content
FLAGGED_DISPLAY_NAME_KEYWORDS = ["Name1", "Name2", "Name3", "Name4", "Name5"]
BANNED_MESSAGE_KEYWORDS = ["Word1", "Word2", "Word3", "Word4", "Word5"]

# Initialize tracking variables
message_count = defaultdict(int)
user_message_history = defaultdict(lambda: deque(maxlen=SPAM_THRESHOLD))
user_warned = {}

# Channel IDs for various metrics
CHANNEL_IDS = {
    "Price:": XXXXXXXXXXXXXXXXXX,
    "Max Supply:": XXXXXXXXXXXXXXXXXX,
    "Mined KLS:": XXXXXXXXXXXXXXXXXX,
    "Mined %:": XXXXXXXXXXXXXXXXXX,
    "mcap:": XXXXXXXXXXXXXXXXXX,
    "Nethash:": XXXXXXXXXXXXXXXXXX,
    "cBlock:": XXXXXXXXXXXXXXXXXX,
    "nBlock": XXXXXXXXXXXXXXXXXX,
    "nReduction:": XXXXXXXXXXXXXXXXXX,
    "24h Volume:": XXXXXXXXXXXXXXXXXX,
}

# Initialize max supply
MAX_SUPPLY = None


# Rest API
async def get_data(url, headers={"accept": "application/json"}, as_json=True):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json() if as_json else await response.text()
            else:
                logging.error(f"Failed to fetch data from {url}: {response.status}")
                return None


async def get_max_supply():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/coinsupply/max",
            headers={"accept": "text/plain"},
        ) as response:
            max_supply = float(await response.text())
            logging.info(f"Max supply fetched: {max_supply}")
            return max_supply


async def get_circulating_supply():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/coinsupply/circulating?in_billion=false",
            headers={"accept": "text/plain"},
        ) as response:
            circulating_supply = float(await response.text())
            logging.info(f"Circulating supply fetched: {circulating_supply}")
            return circulating_supply


async def get_hashrate():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/hashrate?stringOnly=false",
            headers={"accept": "application/json"},
        ) as response:
            hashrate = (await response.json())["hashrate"]
            logging.info(f"Hashrate fetched: {hashrate}")
            return hashrate


async def get_blockreward():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/blockreward?stringOnly=false",
            headers={"accept": "application/json"},
        ) as response:
            blockreward = (await response.json())["blockreward"]
            logging.info(f"Blockreward fetched: {blockreward}")
            return blockreward


async def get_halving_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/halving",
            headers={"accept": "application/json"},
        ) as response:
            halving_data = await response.json()
            logging.info(f"Halving data fetched: {halving_data}")
            return halving_data


async def get_price():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/price?stringOnly=false",
            headers={"accept": "application/json"},
        ) as response:
            price = (await response.json())["price"]
            logging.info(f"Price fetched: {price}")
            return price


async def get_marketcap():
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.karlsencoin.com/info/marketcap?stringOnly=false",
            headers={"accept": "application/json"},
        ) as response:
            marketcap = (await response.json())["marketcap"]
            logging.info(f"Marketcap fetched: {marketcap}")
            return marketcap


async def get_24h_volume():
    url = "https://api.coingecko.com/api/v3/coins/karlsen"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"accept": "application/json"}) as response:
            data = await response.json()
            volume_24h = data["market_data"]["total_volume"]["usd"]
            logging.info(f"24h volume fetched: {volume_24h}")
            return volume_24h


# Update channel names with api data
async def update_or_create_channel(guild, channel_id, channel_name, new_name):
    try:
        if channel := guild.get_channel(channel_id):
            await channel.edit(name=new_name)
            logging.info(f"Updated channel {channel_name} to {new_name}")
        else:
            logging.warning(
                f"Channel ID {channel_id} not found for {channel_name}. Skipping creation."
            )
    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = int(e.response.headers.get("Retry-After", 60))
            logging.warning(f"Rate limited. Retrying in {retry_after} seconds.")
            await asyncio.sleep(retry_after)
            await update_or_create_channel(guild, channel_id, channel_name, new_name)
    except Exception as e:
        logging.error(f"Error creating/updating channel {channel_name}: {e}")


async def update_channel(guild, channel_name, api_call, **kwargs):
    try:
        data = await api_call()
        if data is None:
            logging.error(f"Received None data for channel {channel_name}")
            return

        new_name = generate_channel_name(channel_name, data, **kwargs)
        if new_name:
            await update_or_create_channel(
                guild, CHANNEL_IDS.get(channel_name), channel_name, new_name
            )
    except Exception as e:
        logging.error(f"Error updating channel {channel_name}: {e}")


def generate_channel_name(
    channel_name,
    data,
    calculate_supply_percentage=False,
    supply_percentage=False,
    next_reward=False,
    next_reduction=False,
    convert_hashrate=False,
    marketcap=False,
):
    if calculate_supply_percentage or supply_percentage:
        circulating_supply = data
        mined_supply_percentage = (circulating_supply / MAX_SUPPLY) * 100
    if convert_hashrate:
        return f"Hashrate: {round(data, 1):.1f} Th/s"
    if next_reward:
        return f"nBlock: {data['nextHalvingAmount']:.3f}⏬"
    if next_reduction:
        return f"{data['nextHalvingDate']}"
    if supply_percentage:
        return f"Mined %: {mined_supply_percentage:.2f}%"
    if marketcap:
        return f"mcap: {round(data / 1e6, 1)} mio"
    if channel_name == "Mined KLS:":
        return f"{channel_name} {data / 1e9:.4f} billion"
    if channel_name == "cBlock:":
        return f"{channel_name} {data:.3f}"
    if channel_name == "Price:":
        return f"{channel_name} {data:.6f} $"
    if channel_name == "24h Volume:":
        return f"{channel_name} {data:.1f} $"
    return (
        f"{channel_name} {data:.3e}"
        if isinstance(data, float)
        else f"{channel_name} {data}"
    )


# Background tasks
async def set_category_name():
    await bot.wait_until_ready()
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        category = discord.utils.get(guild.categories, id=CATEGORY_ID)
        if category:
            await category.edit(name="--Karlsen Network Stats--")
            logging.info("Category name set to --Karlsen Network Stats--")


async def set_max_supply():
    global MAX_SUPPLY
    MAX_SUPPLY = await get_max_supply()
    await bot.wait_until_ready()
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild and MAX_SUPPLY:
        channel_id = CHANNEL_IDS.get("Max Supply:")
        new_name = f"Max Supply: {MAX_SUPPLY / 1e9:.3f} billion"
        await update_or_create_channel(guild, channel_id, "Max Supply:", new_name)


async def update_channels():
    await bot.wait_until_ready()
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        while True:
            try:
                logging.info("Starting channel updates")
                await update_channel(
                    guild,
                    "Mined KLS:",
                    get_circulating_supply,
                    calculate_supply_percentage=True,
                )
                await update_channel(
                    guild, "Mined %:", get_circulating_supply, supply_percentage=True
                )
                await update_channel(
                    guild, "Nethash:", get_hashrate, convert_hashrate=True
                )
                await update_channel(guild, "cBlock:", get_blockreward)
                await update_channel(
                    guild, "nBlock", get_halving_data, next_reward=True
                )
                await update_channel(
                    guild, "nReduction:", get_halving_data, next_reduction=True
                )
                await update_channel(guild, "Price:", get_price)
                await update_channel(guild, "mcap:", get_marketcap, marketcap=True)
                await update_channel(guild, "24h Volume:", get_24h_volume)
                await update_member_count(guild, ROLE_ID, MEMBER_COUNT_CHANNEL_ID)
                logging.info("Finished channel updates")
            except Exception as e:
                logging.error(f"Error updating channels: {e}")
            await asyncio.sleep(600)


async def update_member_count(guild, role_id, channel_id):
    logging.info("Updating member count")
    role = guild.get_role(role_id)
    if role:
        member_count = len(role.members)
        new_name = f"Members: {member_count}"
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.edit(name=new_name)
            logging.info(f"Updated member count channel to {new_name}")


async def background_task():
    await set_category_name()
    await set_max_supply()
    await update_channels()


# Event handlers and commands
@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user}")
    bot.loop.create_task(background_task())


@bot.event
async def on_raw_reaction_add(payload):
    if (
        payload.channel_id == VERIFICATION_CHANNEL_ID
        and payload.message_id == VERIFICATION_MESSAGE_ID
    ):
        if str(payload.emoji) == "👍":
            guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)
            if guild:
                role = guild.get_role(VERIFIED_ROLE_ID)
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.add_roles(role)
                    logging.info(f"Assigned verified role to {member.name}")
                    await log_action(guild, f"Assigned verified role to {member.name}")


@bot.event
async def on_member_join(member):
    logging.info(f"Member joined: {member.name} (ID: {member.id})")
    account_age = datetime.now(timezone.utc) - member.created_at
    minimum_age = ACCOUNT_AGE_LIMIT

    # log member joining along with account age and minimum required useraccount age
    await log_action(
        member.guild,
        f"Member joined: {member.name} (ID: {member.id}), "
        f"Account age: {account_age}, Minimum required account age: {minimum_age}",
    )

    if account_age < ACCOUNT_AGE_LIMIT:
        await handle_suspicious_user(member, "Account age less than required minimum")


async def handle_suspicious_user(member, reason):
    now = datetime.now(timezone.utc)
    account_age = now - member.created_at

    if account_age < ACCOUNT_AGE_LIMIT:
        await send_dm(
            member, "You have been kicked from the server due to suspicious activity."
        )
        await asyncio.sleep(1)
        await member.kick(reason=reason)
        logging.warning(f"Kicked {member.name} due to {reason} (ID: {member.id})")
        await log_action(
            member.guild, f"Kicked {member.name} due to {reason} (ID: {member.id})"
        )
    else:
        await send_dm(
            member, "You have been banned from the server due to suspicious activity."
        )
        await asyncio.sleep(1)
        await member.ban(reason=reason)
        logging.warning(f"Banned {member.name} due to {reason} (ID: {member.id})")
        await log_action(
            member.guild, f"Banned {member.name} due to {reason} (ID: {member.id})"
        )

    await delete_recent_messages(member.guild, member.id, timedelta(days=7))


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # debug logging
    logging.debug(
        f"Received message from {message.author.name} (ID: {message.author.id}): {message.content}"
    )
    logging.debug(f"Message author's display name: {message.author.display_name}")

    # check flagged keywords in display name
    detected_keyword = next(
        (
            keyword
            for keyword in FLAGGED_DISPLAY_NAME_KEYWORDS
            if keyword.lower() in message.author.display_name.lower()
        ),
        None,
    )
    if detected_keyword:
        logging.debug(
            f"Flagged keyword '{detected_keyword}' found in display name: {message.author.display_name}"
        )
        await handle_banned_user(
            message.author,
            "Display name contains inappropriate content that violates our guidelines.",
            detected_keyword,
        )

    # check banned keywords in message content
    detected_keyword = next(
        (
            banned_word
            for banned_word in BANNED_MESSAGE_KEYWORDS
            if banned_word.lower() in message.content.lower()
        ),
        None,
    )
    if detected_keyword:
        await message.delete()
        logging.debug(
            f"Banned keyword '{detected_keyword}' found in message content: {message.content}"
        )
        await handle_banned_user(
            message.author,
            "Message contains inappropriate content that violates our guidelines.",
            detected_keyword,
        )

    await handle_spam(message)

    # Respond to every 500th message in the off-topic chat
    if message.channel.id == OFFTOPIC_CHAT_ID:
        message_count[OFFTOPIC_CHAT_ID] += 1
        if message_count[OFFTOPIC_CHAT_ID] % 500 == 0:
            response = await ask_openai_assistant(message.content)
            await message.reply(response)

    await bot.process_commands(message)


async def handle_banned_user(member, reason, detected_keyword=None):
    # Send a DM to the user without revealing the detected keyword
    await send_dm(
        member,
        f"You have been banned from the server for the following reason: {reason}.",
    )

    await asyncio.sleep(1)  # Wait for the message to be sent before banning
    await member.guild.ban(member, reason=reason)

    # Log the detected keyword and reason internally
    if detected_keyword:
        logging.warning(
            f"Banned {member.name} due to {reason} (Detected keyword: {detected_keyword}) (ID: {member.id})"
        )
        await log_action(
            member.guild,
            f"Banned {member.name} due to {reason} (Detected keyword: {detected_keyword}) (ID: {member.id})",
        )
    else:
        logging.warning(f"Banned {member.name} due to {reason} (ID: {member.id})")
        await log_action(
            member.guild, f"Banned {member.name} due to {reason} (ID: {member.id})"
        )

    # Delete their messages from the past 7 days
    await delete_recent_messages(member.guild, member.id, timedelta(days=7))


async def handle_spam(message):
    if message.channel.id == EXCLUDED_SPAM_CHECK_CHANNEL_ID:
        return  # Skip spam check for the excluded channel

    user_history = user_message_history[message.author.id]
    user_history.append(message.content)
    now = datetime.now(timezone.utc)
    if len(user_history) == SPAM_THRESHOLD and all(
        msg == message.content for msg in user_history
    ):
        if (
            message.author.id not in user_warned
            or (now - user_warned[message.author.id]) > SPAM_TIMEOUT
        ):
            user_warned[message.author.id] = now
            user_message_history[message.author.id].clear()
            try:
                await message.author.timeout(
                    SPAM_TIMEOUT,
                    reason="Spamming the same message multiple times in a row.",
                )
                await message.channel.send(
                    f"{message.author.mention} has been timed out for 15 minutes for spamming the same message multiple times in a row."
                )
                logging.info(f"User {message.author} timed out for spamming.")
            except Exception as e:
                logging.error(f"Failed to timeout user {message.author}: {e}")


@bot.command(name="b")
async def check_balance(ctx, *, address: str):
    if ctx.channel.id != COMMAND_LOG_CHANNEL_ID:
        await ctx.send("This command can only be used in the designated channel.")
        return
    logging.info(f"Processing /b command: {address}")
    balance = await get_wallet_balance(address)
    if balance is not None:
        await ctx.send(
            f"The wallet `{address}` has a balance of {balance / 1e8:.8f} KLS"
        )
        logging.info(f"Sent balance for address {address}: {balance / 1e8:.8f} KLS")
    else:
        await ctx.send(
            "Failed to retrieve the wallet balance. Please check the address and try again."
        )


async def get_wallet_balance(address):
    try:
        url = f"https://api.karlsencoin.com/addresses/{address}/balance"
        data = await get_data(url)
        if data:
            return data["balance"]
    except Exception as e:
        logging.error(f"Exception in get_wallet_balance: {e}")
    return None


# OpenAi Assistant API (using GPT4o-mini)
async def ask_openai_assistant(user_input):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "OpenAI-Beta": "assistants=v1",
    }
    try:
        thread_id = await create_thread(headers)
        if not thread_id:
            return "Failed to create thread."
        await send_message_to_thread(headers, thread_id, user_input)
        run_id, status = await run_thread(headers, thread_id)
        if status != "completed":
            return f"Run did not complete successfully. Status: {status}"
        return await fetch_final_result(headers, thread_id, run_id)
    except Exception as e:
        logging.exception("An error occurred while interacting with the Assistant API.")
        return f"An error occurred: {str(e)}"


async def create_thread(headers):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/threads", headers=headers
        ) as response:
            if response.status == 200:
                thread_data = await response.json()
                logging.debug(
                    f"Thread created successfully with ID: {thread_data['id']}"
                )
                return thread_data["id"]
            else:
                logging.error(
                    f"Failed to create thread. Response: {await response.text()}"
                )
                return None


async def send_message_to_thread(headers, thread_id, user_input):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.openai.com/v1/threads/{thread_id}/messages",
            headers=headers,
            json={"role": "user", "content": user_input},
        ) as response:
            if response.status != 200:
                logging.error(
                    f"Failed to send message. Response: {await response.text()}"
                )
            logging.debug("Message sent successfully to the thread.")


async def run_thread(headers, thread_id):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.openai.com/v1/threads/{thread_id}/runs",
            headers=headers,
            json={"assistant_id": ASSISTANT_ID},
        ) as response:
            if response.status == 200:
                run_data = await response.json()
                run_id = run_data["id"]
                status = run_data["status"]
                start_time = time.time()
                logging.debug(
                    f"Thread run initiated with ID: {run_id}, initial status: {status}"
                )
                while status in ["queued", "in_progress"]:
                    await asyncio.sleep(0.5)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}",
                            headers=headers,
                        ) as check_response:
                            status = (await check_response.json())["status"]
                            logging.debug(
                                f"Current status of run ID {run_id}: {status}"
                            )
                            if time.time() - start_time > 29:
                                logging.error(
                                    "Timeout waiting for the run to complete."
                                )
                                return run_id, "timeout"
                return run_id, status
            else:
                logging.error(
                    f"Failed to run thread. Response: {await response.text()}"
                )
                return None, "error"


async def fetch_final_result(headers, thread_id, run_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.openai.com/v1/threads/{thread_id}/messages", headers=headers
        ) as response:
            if response.status == 200:
                messages_data = await response.json()
                for message in reversed(messages_data["data"]):
                    if message["role"] == "assistant" and message["content"]:
                        content_item = next(
                            (c for c in message["content"] if c["type"] == "text"), None
                        )
                        if content_item and content_item["text"]["value"]:
                            return content_item["text"]["value"]
                logging.error("Assistant's final response not found.")
                return "Assistant's final response not found."
            else:
                logging.error(
                    f"Failed to fetch messages. Response: {await response.text()}"
                )
                return "Failed to fetch messages."


@bot.command(name="ask")
async def ask_kls(ctx, *, question: str):
    if ctx.channel.id != COMMAND_LOG_CHANNEL_ID:
        await ctx.send("This command can only be used in the designated channels.")
        return
    try:
        response = await ask_openai_assistant(question)
        await ctx.send(f"**Q:** {question}\n**A:** {response}")
    except Exception as e:
        logging.error(f"Error in Assistant API request: {e}")
        await ctx.send("Sorry, I couldn't process your request.")


@bot.command(name="commands")
async def commands_command(ctx):
    if ctx.channel.id != COMMAND_LOG_CHANNEL_ID:
        await ctx.send("This command can only be used in the designated channel.")
        return
    help_text = """
**Available Commands:**

1. **/b <wallet_address>**
   - Usage: `/b karlsen:qzrq7v5jhsc5znvtfdg6vxg7dz5x8dqe4wrh90jkdnwehp6vr8uj7csdss2l7`
   - Description: Retrieves and displays the balance for the specified wallet address.

2. **/ask <question>**
   - Usage: `/ask What is the Karlsen Network?`
   - Description: Provides an intelligent response to your question using OpenAI's Assistants API.
    """
    await ctx.send(help_text)


async def send_dm(member, message):
    for _ in range(3):
        try:
            await member.send(message)
            logging.info(f"Sent DM to {member.name}")
            return
        except discord.errors.Forbidden:
            logging.error(f"Cannot send message to {member.name}, retrying...")
            await asyncio.sleep(1)
    logging.error(f"Failed to send message to {member.name} after 3 attempts.")


async def log_action(guild, message):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(message)
    else:
        logging.warning(f"Log channel with ID {LOG_CHANNEL_ID} not found")


async def delete_recent_messages(guild, user_id, time_limit):
    now = datetime.now(timezone.utc)
    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=10000, after=now - time_limit):
                if message.author.id == user_id:
                    try:
                        await message.delete()
                        await asyncio.sleep(1)
                    except discord.errors.NotFound:
                        print(f"Message {message.id} not found, skipping.")
                    except discord.errors.Forbidden:
                        print(f"Missing permissions to delete message {message.id}.")
                    except discord.errors.HTTPException as e:
                        print(f"Failed to delete message {message.id}: {e}")
        except discord.errors.Forbidden:
            print(f"Missing permissions to read history in channel {channel.name}.")
        except discord.errors.HTTPException as e:
            print(f"Failed to retrieve history in channel {channel.name}: {e}")


bot.run(TOKEN)
