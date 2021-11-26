from math import floor
import api
from nextcord.embeds import Embed
from nextcord.ext import commands
from nextcord.activity import ActivityType, Activity
from yaml import load as load_yaml, Loader
import re
import asyncio

from nextcord.message import Message

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
    return re.sub(emoj, '', data).strip()

def load_config():
    with open('config.yml') as file:
        data = file.read()
        parsed_data = load_yaml(data, Loader=Loader)
    return parsed_data

def divide_chunks(l, n):
    for i in range(0, len(l), n): 
        yield l[i:i + n]

config = load_config()

bot = commands.Bot(command_prefix=config['prefix'])

@commands.cooldown(1, 5, commands.BucketType.user)
@bot.command()
async def ping(ctx):
    await ctx.reply('Pong! `{}ms`'.format(floor(bot.latency * 1000)))

@commands.cooldown(1, 10, commands.BucketType.channel)
@bot.command(name='valorant')
async def val_giveaways(ctx):
    res_tweets = api.get_valorant_giveaways()
    fetched_tweets = sorted(res_tweets, key= lambda d: d['publicMetrics']['retweet_count'])
    tweets_chunks = divide_chunks(fetched_tweets, 20)
    percentage_chances = []
    embed_pages = []
    current_page = 0
    total_pages = floor(len(fetched_tweets) / 20) - 1 if len(fetched_tweets) % 20 == 0 else floor(len(fetched_tweets) / 20)

    pg = 0
    for tweets in tweets_chunks:
        pg += 1
        text = ''

        for tweet in tweets:
            if not 'authorUser' in tweet:
                continue

            stats = tweet['publicMetrics']
            title = tweet['title'].strip()

            if not float(stats['retweet_count']) == 0:
                percentage_chances.append((1 - (1 / (float(stats['retweet_count']) + 1))))
            else:
                percentage_chances.append(1)

            text = text + '**[`🔗 Go to tweet`](https://twitter.com/{}/status/{}) │ [`{}`](https://twitter.com/{})** │ *`{}`* │ `{:<6}🔁`\n'.format(tweet['authorUser'].replace('@', ''), tweet['id'], '{:<16}'.format(tweet['authorUser']), tweet['authorUser'].replace('@', ''), '{:<20}'.format(de_emojify(title[:17].strip()).replace('*', '') + '...'), stats['retweet_count'])
        
        embed_pages.append(text)

    embed = Embed(title='VALORANT Giveaways Page [{}/{}]'.format(current_page + 1, total_pages + 1), description=embed_pages[0], color=0xFF4454)
    embed.set_footer(text='Giveaways all sourced from twitter | Updated every 12h at UTC time | Data from the last 7 days')
    info_message: Message = await ctx.channel.send(embed=embed)

    chance = 1

    for percentage in percentage_chances:
        chance *= percentage 
    
    embed = Embed(title='Chance of winning', description='```fix\n{:.5}%```'.format(100 - chance * 100), color=0xFF4454)
    embed.set_footer(text='Chance of winning once | Assumes that every giveaway only has 1 winner | Uses the retweet statistic')
    await ctx.channel.send(embed=embed)

    await info_message.add_reaction('⬅️')
    await info_message.add_reaction('➡️')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️']

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=90, check=check)

            if str(reaction.emoji) == '➡️' and current_page != total_pages:
                await info_message.remove_reaction(reaction, user)
                current_page += 1
                embed = Embed(title='VALORANT Giveaways Page [{}/{}]'.format(current_page + 1, total_pages + 1), description=embed_pages[current_page], color=0xFF4454)
                embed.set_footer(text='Giveaways all sourced from twitter | Updated every 12h at UTC time | Data from the last 7 days')
                await info_message.edit(embed=embed)
            elif str(reaction.emoji) == '⬅️' and current_page > 0:
                await info_message.remove_reaction(reaction, user)
                current_page -= 1
                embed = Embed(title='VALORANT Giveaways Page [{}/{}]'.format(current_page + 1, total_pages + 1), description=embed_pages[current_page], color=0xFF4454)
                embed.set_footer(text='Giveaways all sourced from twitter | Updated every 12h at UTC time | Data from the last 7 days')
                await info_message.edit(embed=embed)
            else:
                await info_message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await info_message.clear_reactions()



# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.CommandOnCooldown):
#         embed = Embed(title='You cannot use this command yet! ⌚',description='Try again in **{:.2f} seconds**'.format(error.retry_after), color=0x001b3b)
#         await ctx.send(embed=embed)
#     else:
#         print(error)

@bot.event
async def on_ready():
    print('Ready!')
    await bot.change_presence(activity=Activity(type=ActivityType.listening, name='{}help'.format(config['prefix'])))

bot.run(config['token'])