import discord
from discord.ext import commands
import random
import requests
import pandas as pd
from io import StringIO
import pytz
from keep_alive import keep_alive


##########################################
# ボット初期化
##########################################

TOKEN = os.environ['DISCORD_TOKEN']
CSV_URL = os.environ['CSV_URL']
CHANNEL = os.environ['CHANNEL_ID']

# Intentsの設定
intents = discord.Intents.all()
intents.messages = True  # メッセージイベントに反応させる

# ボットの定義（Intentsを含む）
# bot = discord.Client(intents=discord.Intents.all())
bot = commands.Bot(command_prefix='!', intents=intents)

# ボットが準備完了したときに実行されるイベント
@bot.event
async def on_ready():
    print('接続しました')

@bot.event
async def on_message(message):
    # ボット自身のメッセージは無視する
    if message.author == bot.user:
        return

    print(f"メッセージ受信: {message.content}")

    # コマンドを処理するために必要
    await bot.process_commands(message)


##########################################
# 名言bot
##########################################

# スプレッドシートから名言を読み込む関数
async def load_quotes():
  response = requests.get(CSV_URL)
  data = response.content.decode('utf-8')
  df = pd.read_csv(StringIO(data), usecols=[2])  # C列のインデックスは2
  return df.iloc[:, 0]  # C列のデータ


# ランダムな名言とその行番号をEmbedで送信するコマンド
@bot.command(name='名言')
async def send_quote(ctx, line: int = None):
  quotes = await load_quotes()
  if line is not None:
    # 引数で指定された行の名言を取得
    if 1 <= line <= len(quotes):
      quote = quotes[line - 2]
      embed_title = f"名言 {line}"
      embed = discord.Embed(title=embed_title,
                            description=quote,
                            color=0x2f4f4f)
      await ctx.send(embed=embed)
    else:
      await ctx.send('にゃーん')
  else:
    # ランダムな名言を選択
    index = random.randrange(len(quotes))
    quote = quotes[index]
    embed_title = f"名言 {index + 2}"  # なんか2行ずれてる
    embed = discord.Embed(title=embed_title, description=quote, color=0x2f4f4f)
    await ctx.send(embed=embed)

##########################################
# のくのくた語bot
##########################################
def load_list_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

LIST1 = load_list_from_file("nokunokutaString/list1.txt")
LIST2 = load_list_from_file("nokunokutaString/list2.txt")
LIST3 = load_list_from_file("nokunokutaString/list3.txt")
LIST4 = load_list_from_file("nokunokutaString/list4.txt")

@bot.command(name='のくのくた語')
async def nokunokuta(ctx):
    random_words = random.choice(LIST1) + random.choice(LIST2) + random.choice(LIST3) + random.choice(LIST4)
    embed = discord.Embed(title="のくのくた語", description=random_words, color=0x2f4f4f)
    await ctx.send(embed=embed)

##########################################
# イベント転記
##########################################
async def send_event_embed(event, color, content):
  jst = pytz.timezone('Asia/Tokyo')
  start_time = event.start_time.astimezone(jst).strftime("%Y-%m-%d %H:%M")
  channel = bot.get_channel(CHANNEL)
  embed = discord.Embed(title=event.name,
                        description=event.description,
                        color=color)
  embed.add_field(name="開始日時", value=start_time)
  embed.add_field(name="開催場所", value=event.location)
  embed.set_author(name=event.creator.global_name,
                   icon_url=event.creator.avatar)
  await channel.send(content=content, embed=embed)

@bot.event
async def on_scheduled_event_create(event):
  await send_event_embed(event, 0x2196F3, "以下のイベントが作成されました🏁")

@bot.event
async def on_scheduled_event_update(before, after):
  await send_event_embed(after, 0x4CAF50, "以下のイベントが更新されました🔄")

##########################################
# ボット実行
##########################################

# 常時稼働
keep_alive()

# トークンを使ってボットを実行
bot.run(TOKEN)

# 参考URL
# https://docs.pycord.dev/en/stable/api/events.html#scheduled-events
# https://discord.com/developers/docs/resources/channel#embed-object
# https://discord.com/developers/docs/resources/user#users-resource
# https://docs.pycord.dev/en/stable/api/models.html#discord.ScheduledEvent
# https://materialui.co/colors/

# アップローダー
# https://www.utsuboublog.com/entry/discord-bot-replit