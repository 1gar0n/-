import discord
from discord.ext import commands
import re

# 봇 기본 권한(Intents) 설정
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 📌 설정값
AUTH_CHANNEL_ID = 1531159294223843428  # 인증 전용 채널 ID
AUTH_ROLE_ID = 1513603622846599238     # 인증 시 지급할 역할 ID
SERVER_TAG = "푸씨갱"                  # 칭호 및 태그 키워드

# 💾 유저의 인증 전 기존 닉네임을 저장할 메모리 공간 (유저 ID: 이전 닉네임)
previous_nicknames = {}

@bot.event
async def on_ready():
    print(f"✅ {bot.user.name} 봇이 성공적으로 로그인했습니다!")

# ------------------------------------------------------------------
# 🔑 !인증 명령어
# ------------------------------------------------------------------
@bot.command(name="인증")
async def verify_user(ctx):
    # 1. 지정된 채널 확인
    if ctx.channel.id != AUTH_CHANNEL_ID:
        await ctx.send("해당 채널에서는 인증할 수 없습니다. 지정된 인증 채널을 이용해 주세요.")
        return

    # 지급할 역할 가져오기
    role = ctx.guild.get_role(AUTH_ROLE_ID)
    if role is None:
        await ctx.send("❌ 설정된 역할 ID를 찾을 수 없습니다. 관리자에게 문의해 주세요.")
        return

    # 2. 인증 직전의 현재 닉네임 상태 저장 (이전 칭호 복원용)
    original_nickname = ctx.author.nick if ctx.author.nick else ctx.author.name
    previous_nicknames[ctx.author.id] = original_nickname

    # 기존 『 칭호 』 형태가 있다면 제거 후 순수 이름만 추출
    clean_name = re.sub(r"^『\s*.*?\s*』\s*", "", original_nickname).strip()

    # 새 닉네임 설정: 『 푸씨갱 』 바꿀이름
    new_nickname = f"『 {SERVER_TAG} 』 {clean_name}"

    try:
        # 역할 부여
        await ctx.author.add_roles(role)
        
        # 칭호 자동 변경
        await ctx.author.edit(nick=new_nickname)
        
        await ctx.send(f"🎉 **{ctx.author.mention}** 님, 인증이 완료되어 **{role.name}** 역할이 지급되고 칭호가 **『 {SERVER_TAG} 』**으로 변경되었습니다!")
    except discord.Forbidden:
        await ctx.send("❌ 봇에게 권한이 부족합니다. 서버 설정에서 봇의 역할(Role) 순위를 최상단으로 올려주세요!")
    except Exception as e:
        await ctx.send(f"오류가 발생했습니다: {e}")


# ------------------------------------------------------------------
# 🔄 태그 제거 시 자동 역할 수거 및 이전 칭호/닉네임 복원
# ------------------------------------------------------------------
@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # 유저의 닉네임/디스플레이 이름 변경 감지
    if before.display_name != after.display_name:
        role = after.guild.get_role(AUTH_ROLE_ID)
        if role is None:
            return

        # 닉네임에 태그("푸씨갱")가 남아있는지 확인
        has_tag = SERVER_TAG in after.display_name

        # 태그를 떼었고, 정식 역할을 가지고 있는 경우
        if not has_tag and role in after.roles:
            try:
                # 1. 역할 자동 수거
                await after.remove_roles(role)
                
                # 2. 인증 직전의 닉네임으로 복원
                restore_nick = previous_nicknames.pop(after.id, None)

                if restore_nick:
                    # 저장된 이전 닉네임/칭호가 있으면 해당 이름으로 복원
                    await after.edit(nick=restore_nick)
                else:
                    # 저장된 기록이 없는 경우 『 푸씨갱 』 괄호만 지운 순수 이름으로 복원
                    clean_name = re.sub(r"^『\s*.*?\s*』\s*", "", after.display_name).strip()
                    await after.edit(nick=clean_name if clean_name else None)

                print(f"🗑️ {after.display_name} 님의 태그가 제거되어 역할 수거 및 이전 칭호로 복원되었습니다.")
            except discord.Forbidden:
                print("❌ 봇의 권한이 부족하여 역할을 수거하거나 닉네임을 변경할 수 없습니다.")
            except Exception as e:
                print(f"오류 발생: {e}")

# ⚠️ 여기에 발급받으신 봇 토큰을 붙여넣어 주세요!
bot.run('MTUzODE1MjU1MjI3NTkxMDcxNg.GE6YPX.gpgpC-A6iOYnoqLAttwTYMGYFcFQsWBGrfJ7pM')
