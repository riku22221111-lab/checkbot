import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import asyncio
from datetime import datetime

# ===== 設定 =====
PREFIX = "!"
DATA_FILE = "voice_data.json"

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True  # 招待リンク検出に必須（Developer PortalでもONにすること）

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Discord招待リンクを検出する正規表現
INVITE_PATTERN = re.compile(
    r"(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite|discord\.com/invite)/[a-zA-Z0-9-]+",
    re.IGNORECASE
)


# ===== データ読み書き =====
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"データ読み込みエラー: {e}")
            return {}
    return {}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"データ保存エラー: {e}")


voice_data = load_data()


# ===== 起動時処理 =====
@bot.event
async def on_ready():
    print(f"✅ Bot起動: {bot.user}")

    # コマンドを確実に同期
    try:
        synced = await bot.tree.sync()
        print(f"✅ スラッシュコマンド同期完了: {len(synced)}個")
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"❌ 同期エラー: {e}")

# ===== VC参加時刻の記録 =====
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    guild_id = str(member.guild.id)
    user_id = str(member.id)

    if guild_id not in voice_data:
        voice_data[guild_id] = {}

    if after.channel is not None and (before.channel is None or before.channel.id != after.channel.id):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        voice_data[guild_id][user_id] = now
        save_data(voice_data)
        print(f"{member.display_name} がVCに参加 → {now}")


# ===== /check コマンド =====
@bot.hybrid_command(name="check", description="指定ユーザーの最終VC参加時刻を表示")
@app_commands.describe(member="調べたいユーザー")
async def check(ctx, member: discord.Member):
    guild_id = str(ctx.guild.id)
    user_id = str(member.id)
    data = voice_data.get(guild_id, {}).get(user_id)

    if data:
        await ctx.send(f"**{member.display_name}** は、最後に **{data}** に通話にいたよ")
    else:
        await ctx.send(f"**{member.display_name}** のVC参加履歴がねえぞ浮上しろ")


# ===== 起動 =====
if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        print("❌ TOKEN が設定されていません！")
        exit(1)
    print("🚀 Botを起動します...")
    bot.run(TOKEN)
