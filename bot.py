import os
        now=time.time()
        last=gtn_cooldowns.get(message.author.id,0)
        if now-last<2:
            return
        gtn_cooldowns[message.author.id]=now
        guess=int(message.content)
        if guess==gtn_number:
            score=add_gtn_point(message.author.id)
            await message.channel.send(embed=embed_msg("🎉 Correct!",f"{message.author.mention} guessed **{gtn_number}** → {score} wins"))
            gtn_running=False
            gtn_number=None
            return
        diff=abs(guess-gtn_number)
        if diff>100: text="📉 Too Far"
        elif diff>70: text="📊 Far"
        elif diff>50: text="📈 Close"
        else: text="🔥 Very Close"
        hint="Higher" if guess<gtn_number else "Lower"
        await message.channel.send(embed=embed_msg(text,hint))

    # -------- MC QUIZ CHECK --------
    if quiz_running and message.channel.id==quiz_channel_id and quiz_answer:
        now=time.time()
        last=quiz_cooldowns.get(message.author.id,0)
        if now-last<2:
            return
        quiz_cooldowns[message.author.id]=now
        if message.content.lower().strip()==quiz_answer.lower().strip():
            score=add_quiz_point(message.author.id)
            await message.channel.send(embed=embed_msg("🎉 Correct!",f"{message.author.mention} → {score} points"))
            quiz_running=False
            quiz_question=None
            quiz_answer=None

    await bot.process_commands(message)

# ================= HELP =================
@bot.command()
async def help(ctx):
    embed=discord.Embed(title="🎮 NEXUS Game System", color=discord.Color.gold())
    if ctx.author.guild_permissions.administrator:
        embed.add_field(name="👑 Admin", value="""*givepointsmc @user amount
*removepointsmc @user amount
*bulkpointsmc amount @user1 @user2 ...
*givepointsgtn @user amount
*removepointsgtn @user amount
*bulkpointsgtn amount @user1 @user2 ...
*givepointquiz @user amount
*removepointquiz @user amount
*bulkpointquiz amount @user1 @user2 ...""", inline=False)
    if any(role.id==GAME_MANAGER_ROLE_ID for role in ctx.author.roles):
        embed.add_field(name="🎮 Manager", value="""*setmclines #channel
*setgtn #channel
*setquiz #channel
*srtgame
*stopgame
*lb
*clearlb
*gtnanswer
*giveanswerquiz""", inline=False)
    embed.add_field(name="🌍 Public", value="*help", inline=False)
    await ctx.send(embed=embed)

# ================= RUN BOT =================
bot.run(TOKEN)
