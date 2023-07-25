import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
import datetime
from dotenv import load_dotenv
load_dotenv()
import os
import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi  

TOKEN=os.environ['TOKEN']
bot = commands.Bot(command_prefix="!", help_command=None, intents=discord.Intents.all())

uri=os.environ['URI']

client = MongoClient(uri, server_api=ServerApi('1'))
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client["moderationlogs"]
col = db["database"]


@bot.event
async def on_ready():
  print(f'{bot.user} has connected to Discord!')
  try:
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")
  except Exception as e:
    print(e)

@bot.tree.command(name="shutdown", description="Shutsdown the bot")
async def shutdown(interaction = discord.interactions):
  user = interaction.user.id
  if user == 690634329591906316:
    print(f"{interaction.user.id} has shutdown the bot")
    await interaction.response.send_message("Bot Shutting Down", ephemeral = True)
    await bot.close()
    print(f'{bot.user} has been shutdown')
  else:
    await interaction.response.send_message(f"You do not have permission to use this command <@{user}>", ephemeral = True)


   
@bot.tree.command(name="ping", description="Returns the Bot's Ping")
async def ping(interaction: discord.interactions):
  try:
    embed = discord.Embed (title="Bot Connaction Status:", description=f"Bot Latency: {round(bot.latency * 1000)}ms", timestamp= datetime.datetime.now())
    embed.set_footer(text=f"Ran By {interaction.user}")
    await interaction.response.send_message(embed=embed)
  except:
    await interaction.response.send_message('Failed to get the bots current ping', ephemeral = True)
    
@bot.tree.command(name="userinfo", description="Get info of the target user")
async def userinfo(interaction: discord.integrations, target: discord.User = None):
  if target == None:
    target = interaction.user
  embed = discord.Embed(title=f"UserInfo", description=f"Mention: {target.mention}", timestamp= datetime.datetime.now())
  embed.add_field(name="Name", value=target.name)
  try: 
    embed.add_field(name="Nickname", value=target.nick)
  except:
    embed.add_field(name="Nickname", value="None")
  embed.add_field(name="ID", value=target.id)
  try: 
    embed.add_field(name="Join Date", value=target.joined_at.strftime("%a, %B %#d, %Y, %I:%M %p "))
  except:
    embed.add_field(name="Join Date", value="Never")
  embed.add_field(name="Account Creation Date", value=target.created_at.strftime("%a, %B %#d, %Y, %I:%M %p"))
  embed.set_footer(text=f"Called By {interaction.user}")
  await interaction.response.send_message(embed=embed)

@bot.tree.command(name="purge", description="purges an ammount of messages")
async def purge(interaction: discord.integrations, amount: int):
  try:
    await interaction.channel.purge(limit=amount+1)
    await interaction.response.send_message(f"Succesfully deleted {amount} message(s)")
  except:
    await interaction.response.send_message("Please provide the amount of messages to purge.", ephemeral = True)


@bot.tree.command(name="warn", description="Warns the targeted user")
@commands.has_permissions(kick_members=True)
async def warn(interaction: discord.integrations, target: discord.Member, *, reason: str):
  try:
    author = interaction.user
    log = { "UserID": target.id, "Type": "Warn", "Reason": reason, "Moderator": f"<@{author.id}> ({author.id})" }
    x = col.insert_one(log)
    try:
      ude = discord.Embed(title=f"You were infracted in {interaction.guild.name}:", description=f"{reason}", color=discord.Color.brand_red(), timestamp= datetime.datetime.now())
      ude.add_field(name="Infraction ID", value=x.inserted_id, inline=True)
      ude.add_field(name="Type", value='Warn', inline=True)
      ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
      await target.send(embed=ude)
    except:
      pass
    await interaction.response.send_message(f"Succesfully warned {target.name}")
  except:
    await interaction.response.send_message(f"Target user not found", ephemeral = True)

@app_commands.choices(type = [
  Choice(name="Mute(Voice)", value='voicemute'),
  Choice(name="Mute(Timeout)", value='timeout')
])
@bot.tree.command(name="mute", description="Mutes the targeted user")
@commands.has_permissions(moderate_members=True)
async def mute(interaction: discord.integrations, target: discord.Member, time: str, type: str ,*, reason: str):

    if "s" in time:
      gettime = time.strip('s')
      newtime = datetime.timedelta(seconds=int(gettime))
    elif "min" in time:
      gettime = time.strip('min')
      newtime = datetime.timedelta(minutes=int(gettime))
    elif "h" in time:
      gettime = time.strip('h')
      newtime = datetime.timedelta(hours=int(gettime))
    elif "d" in time:
      gettime = time.strip('d')
      newtime = datetime.timedelta(days=int(gettime))
    elif "w" in time:
      gettime = time.strip('w')
      newtime = datetime.timedelta(weeks=int(gettime))
    else:
      return await interaction.response.send_message(f"**{time}** is not a valid time, please use a valid time", ephemeral = True)
    if type == 'timeout':
      await target.edit(timed_out_until=discord.utils.utcnow() + newtime)
    else:
      return await interaction.response.send_message("This does not currently work", ephemeral = True)
    author = interaction.user
    log = { "UserID": target.id, "Type": type, "Reason": reason, "Time": time, "Moderator": f"<@{author.id}> ({author.id})" }
    x = col.insert_one(log)
    try:
      ude = discord.Embed(title=f"You were muted in {interaction.guild.name}:", description=f"{reason}", color=discord.Color.brand_red(), timestamp= datetime.datetime.now())
      ude.add_field(name="Infraction ID", value=x.inserted_id, inline=True)
      ude.add_field(name="Type", value=f'Mute - {type}', inline=True)
      ude.add_field(name="Mute Time", value=time, inline=True)
      ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
      await target.send(embed=ude)
    except:
      pass  
    await interaction.response.send_message(f"Succesfully muted {target.name}")

    

@app_commands.choices(type = [
  Choice(name="Mute(Voice)", value='voicemute'),
  Choice(name="Mute(Timeout)", value='timeout')
])   
@bot.tree.command(name="unmute", description="Unmutes a targeted user")
@commands.has_permissions(moderate_members=True)
async def mute(interaction: discord.integrations, target: discord.Member, type: str ,*, reason: str):
  if type == 'timeout':
      if not target.is_timed_out():
        return await interaction.response.send_message(f"{target.name} is not timedout", ephemeral = True)
      else:
        await target.timeout(None, reason=reason)
  elif type == 'voicemute':
    return await interaction.response.send_message("This does not currently work", ephemeral = True)
  try:
    author = interaction.user
    ude = discord.Embed(title=f"You were manually unmuted in {interaction.guild.name}:", description=f"{reason}", color=discord.Color.green(), timestamp= datetime.datetime.now())
    ude.add_field(name="Infraction ID", value='infid', inline=True)
    ude.add_field(name="Type", value=f'Unmute - {type}', inline=True)
    ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
    await target.send(embed=ude)
  except:
    pass
  return await interaction.response.send_message(f"Succesfully unmuted {target.name}")
  
@bot.tree.command(name="kick", description="Kicks the targeted user")
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.integrations, target: discord.Member, *, reason: str):
  try:
    author = interaction.user
    log = { "UserID": target.id, "Type": "Kick", "Reason": reason, "Moderator": f"<@{author.id}> ({author.id})" }
    x = col.insert_one(log)
    try:
      ude = discord.Embed(title=f"You were infracted in {interaction.guild.name}:", description=f"{reason}", color=discord.Color.brand_red(), timestamp= datetime.datetime.now())
      ude.add_field(name="Infraction ID", value=x.inserted_id, inline=True)
      ude.add_field(name="Type", value='Kick', inline=True)
      ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
      await target.send(embed=ude)
    except:
      pass
    await target.kick(reason=reason)
    await interaction.response.send_message(f"Succesfully Kicked {target.name}")
  except:
    await interaction.response.send_message(f"Target user not found", ephemeral = True) 
   
@bot.tree.command(name="ban", description="Bans the targeted user")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.integrations, target: discord.User, time: str, *, reason: str):
  if "perm" in time:
    author = interaction.user
    log = { "UserID": target.id, "Type": "Ban", "Reason": reason, "Time": time,"Moderator": f"<@{author.id}> ({author.id})" }
    x = col.insert_one(log)
    try:
      author = interaction.user
      ude = discord.Embed(title=f"You were banned from {interaction.guild.name}:", description=f"{reason}", color=discord.Color.brand_red(), timestamp= datetime.datetime.now())
      ude.add_field(name="Infraction ID", value=x.inserted_id, inline=True)
      ude.add_field(name="Type", value='Ban', inline=True)
      ude.add_field(name="Ban Time", value=time, inline=True)
      ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
      await target.send(embed=ude)
    except:
      pass
    await interaction.guild.ban(target, reason=reason)
    return await interaction.response.send_message(f"Succesfully banned {target.name}")  
  elif "s" in time:
    gettime = time.strip('s')
    newtime = datetime.timedelta(seconds=int(gettime))
  elif "min" in time:
    gettime = time.strip('min')
    newtime = datetime.timedelta(minutes=int(gettime))
  elif "h" in time:
    gettime = time.strip('h')
    newtime = datetime.timedelta(hours=int(gettime))
  elif "d" in time:
    gettime = time.strip('d')
    newtime = datetime.timedelta(days=int(gettime))
  elif "w" in time:
    gettime = time.strip('w')
    newtime = datetime.timedelta(weeks=int(gettime))
  else:
    return await interaction.response.send_message(f"**{time}** is not a valid time, please use a valid time", ephemeral = True)
  return await interaction.response.send_message("This does not currently work", ephemeral = True)
  #author = interaction.user
  #ude = discord.Embed(title=f"You were banned from {interaction.guild.name}:", description=f"{reason}", color=discord.Color.brand_red(), timestamp= datetime.datetime.now())
  #ude.add_field(name="Infraction ID", value='infid', inline=True)
  #ude.add_field(name="Type", value='Ban', inline=True)
  #ude.add_field(name="Ban Time", value=time, inline=True)
  #ude.add_field(name="Moderator", value=f'{author.mention} ({author.id})', inline=False)
  #await target.send(embed=ude)
  #await target.ban(reason=reason)
  #await interaction.response.send_message(f"Succesfully banned {target.name}")

@bot.tree.command(name="unban", description="Unbans the targeted user")
@commands.has_permissions(ban_members=True)
async def unban(interaction: discord.integrations, target: discord.User, *, reason: str):
  try:
    await interaction.guild.unban(target, reason=reason)
    await interaction.response.send_message(f"Succesfully unbanned {target}")
  except:
    await interaction.response.send_message(f"{target} is not banned")

    
    
bot.run(TOKEN)