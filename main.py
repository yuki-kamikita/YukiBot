import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import random
import requests
import pandas as pd
from io import StringIO
import pytz
import re

load_dotenv()
TOKEN = os.getenv('TOKEN')
CHANNEL = os.getenv('CHANNEL')

# Intentsの設定
intents = discord.Intents.all()
intents.messages = True  # メッセージイベントに反応させる
bot = discord.Bot(intents=intents)


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
  # await bot.process_commands(message)


##########################################
# 名言bot
##########################################

# スプレッドシートから名言を読み込む関数
async def load_quotes():
    # スクリプトのあるディレクトリのパスを取得
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # CSVファイルへのフルパスを構築
    csv_path = os.path.join(dir_path, 'meigen.csv')

    # CSVファイルを読み込む
    df = pd.read_csv(csv_path, usecols=[2, 4])  # C列とE列のデータを読み込む
    return df

# カスタム絵文字の名前を検出し、対応する絵文字に置き換える関数
def replace_custom_emojis(text):
    emoji_pattern = re.compile(r":([a-zA-Z0-9_]+):")

    def replace(match):
        emoji_name = match.group(1)
        emoji = discord.utils.get(bot.emojis, name=emoji_name)
        return str(emoji) if emoji else match.group(0)

    return emoji_pattern.sub(replace, text)

# 名言を一つ取得する
def get_quote(quotes_df, line=None):
  quotes = quotes_df.iloc[:, 0]  # C列のデータ
  additional_info = quotes_df.iloc[:, 1]  # E列のデータ

  if line is not None and 2 <= line <= len(quotes):
      # 引数で指定された行の名言を取得
      quote = quotes[line - 2]
      info = additional_info[line - 2]
  else:
      # ランダムな名言を選択
      index = random.randrange(len(quotes))
      quote = quotes[index]
      info = additional_info[index]
      line = index + 2  # 実際の行番号を設定

  # カスタム絵文字の置き換え（前述の関数を使用）
  quote = replace_custom_emojis(quote)
  info = replace_custom_emojis(info) if pd.notna(info) else None

  return quote, info, line

# ランダムな名言とその行番号をEmbedで送信するコマンド
@bot.slash_command(name="名言", description="数字入れると指定できるよ")
async def send_quote(interaction: discord.Interaction, line: int = None):
    await interaction.response.defer()
    quotes_df = await load_quotes()
    quote, info, actual_line = get_quote(quotes_df, line)

    embed_title = f"名言 {actual_line}"
    embed = discord.Embed(title=embed_title, description=quote, color=0x2f4f4f)

    # infoがNoneでないかつフッターに🥇が含まれるかチェック
    if info and "🥇" in info:
        # カスタム絵文字を取得
        gold_coin_emoji = discord.utils.get(bot.emojis, name="gold_coin")
        if gold_coin_emoji:
            # タイトルの先頭にカスタム絵文字を追加
            embed.title = f"{gold_coin_emoji} {embed.title}"

    # フッターの設定
    if pd.notna(info):
        embed.set_footer(text=info)

    await interaction.followup.send(embed=embed)


##########################################
# のくのくた語bot
##########################################
def load_list_from_file(filename):
    # meigen.py のあるディレクトリのパスを取得
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # ファイルへのフルパスを構築
    full_path = os.path.join(dir_path, filename)
    
    with open(full_path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file]

LIST1 = load_list_from_file("nokunokutaString/list1.txt")
LIST2 = load_list_from_file("nokunokutaString/list2.txt")
LIST3 = load_list_from_file("nokunokutaString/list3.txt")
LIST4 = load_list_from_file("nokunokutaString/list4.txt")


@bot.slash_command(name="のくのくた語", description="ランダムなのくのくた語を生成")
async def nokunokuta(interaction: discord.Interaction):
  await interaction.response.defer()
  random_words = random.choice(LIST1) + random.choice(LIST2) + random.choice(
      LIST3) + random.choice(LIST4)
  embed = discord.Embed(title="のくのくた語",
                        description=random_words,
                        color=0x2f4f4f)
  await interaction.respond(embed=embed)

##########################################
# イベント転記
##########################################
async def send_event_embed(event, color, content):
  print(event)
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


# トークンを使ってボットを実行
try:
  bot.run(TOKEN)
except:
  os.system("kill 1")

# 参考URL
# https://docs.pycord.dev/en/stable/api/events.html#scheduled-events
# https://discord.com/developers/docs/resources/channel#embed-object
# https://discord.com/developers/docs/resources/user#users-resource
# https://docs.pycord.dev/en/stable/api/models.html#discord.ScheduledEvent
# https://materialui.co/colors/
# https://discordjs.guide/slash-commands/response-methods.html#ephemeral-responses