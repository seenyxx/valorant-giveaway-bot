from math import floor
import api
from nextcord.embeds import Embed
from nextcord.ext import commands
from nextcord.activity import ActivityType, Activity
from yaml import load as load_yaml, Loader
import re

def de_emojify(data):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
    "]+", re.UNICODE)
    return re.sub(emoj, '', data)

def load_config():
    with open('config.yml') as file:
        data = file.read()
        parsed_data = load_yaml(data, Loader=Loader)
    return parsed_data

config = load_config()

bot = commands.Bot(command_prefix=config['prefix'])

@commands.cooldown(1, 5, commands.BucketType.user)
@bot.command()
async def ping(ctx):
    await ctx.reply('Pong! `{}ms`'.format(floor(bot.latency * 1000)))

@commands.cooldown(1, 10, commands.BucketType.channel)
@bot.command(name='valorant')
async def val_giveaways(ctx):
    tweets = api.get_valorant_giveaways()
    for i in range(0, len(tweets) - 50):
        tweets.pop()

    text = ''

    for tweet in tweets:
        
        title = tweet['title']
        text = text + '**[`🔗 Go to tweet`](https://twitter.com/{}/status/{}) │ [`{}`](https://twitter.com/{})** *`{}`*\n'.format(tweet['authorUser'].replace('@', ''), tweet['id'], '{:<16}'.format(tweet['authorUser']), tweet['authorUser'].replace('@', ''), '{:<35}'.format(de_emojify(title[:30].strip()) + '...'))

    embed = Embed(title='VALORANT Giveaways', description=text, color=0xFF4454)
    embed.set_footer(text='Updated every 12h at UTC time | Data from the last 7 days')
    await ctx.reply(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        embed = Embed(title='You cannot use this command yet! ⌚',description='Try again in **{:.2f} seconds**'.format(error.retry_after), color=0x001b3b)
        await ctx.send(embed=embed)
    else:
        print(error)

@bot.event
async def on_ready():
    print('Ready!')
    await bot.change_presence(activity=Activity(type=ActivityType.listening, name='{}help'.format(config['prefix'])))

bot.run(config['token'])