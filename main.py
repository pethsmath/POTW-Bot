import discord
import gspread
from discord.ext import commands as cmd
from oauth2client.service_account import ServiceAccountCredentials
from alive import suffer

# Google Sheets BS
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDENTIAL = ServiceAccountCredentials.from_json_keyfile_name('cert.json', SCOPE) # cert.json is not committed :innocent:
CLIENT = gspread.authorize(CREDENTIAL)

def log(obj): print('[LOG]', obj)

# Discord Bot Stuff
bot = cmd.Bot('!')
ADMIN_ROLE = 'POTW Admin'
WEEK = 1
LIMIT = 5

PROBLEM_SHEET = CLIENT.open('Problems POTW')
STORE_SHEET = CLIENT.open('Leaderboard POTW')
PROBLEM = PROBLEM_SHEET.worksheet('Problems')
HINT = PROBLEM_SHEET.worksheet('Hints')
STORE = STORE_SHEET.worksheet('Counts')
CORRECT = STORE_SHEET.worksheet('Correct')
FINAL = STORE_SHEET.worksheet('Final')

@bot.event
async def on_ready():
	await bot.change_presence(activity = discord.Game(name = 'the problem of the week'))
	log('Bot Running')

#ADMIN COMMANDS

#RUN THESE IN THE ADMIN CHANNEL

# HIDE COMMANDS

@bot.command(
	name = 'back',
	brief = 'Moves back a week. Syntax: !back',
	pass_context = True
)
@cmd.has_role(ADMIN_ROLE)
async def back(ctx: cmd.Context):
	global WEEK
	if WEEK == 1: await ctx.send("You can't go back beyond Week 1.")
	else:
		WEEK -= 1
		await ctx.send('You have moved back a week.')
@back.error
async def back_error(ctx: cmd.Context, error):
	if isinstance(error, cmd.MissingRole):
		await ctx.send("You don't have the perms to run this command!")

@bot.command(
	name = 'next',
	brief = 'Moves forward a week. Syntax: !next',
	pass_context = True
)
@cmd.has_role(ADMIN_ROLE)
async def next(ctx: cmd.Context):
	global WEEK
	WEEK += 1
	await ctx.send('You have moved forward a week.')
@next.error
async def next_error(ctx: cmd.Context, error):
	if isinstance(error, cmd.MissingRole):
		await ctx.send("You don't have the perms to run this command!")

"""
@bot.command(
	name = 'admin',
	brief = 'Sets the Admin channel to dump messages. Syntax: !admin',
	pass_context = True
)
@cmd.has_role(ADMIN_ROLE)
async def admin(ctx: cmd.Context):
	global ADMIN
	ADMIN = ctx.message.channel
	await ctx.send('You have set this as the admin channel!')
@admin.error
async def admin_error(ctx: cmd.Context, error):
	if isinstance(error, cmd.MissingRole):
		await ctx.send("You don't have the perms to run this command!")
"""

@bot.command(
	name = 'problem',
	brief = 'Add POTW problems. Syntax: !problem',
	pass_context = True
)
@cmd.has_role(ADMIN_ROLE)
async def problem(ctx: cmd.Context):
	await dm.send('Add problems here:\nhttps://docs.google.com/spreadsheets/d/1j-gutdV2Iasw9w2d2G__Iw66GBTJo-3trF7Q8qiIEzI/edit?ts=5ef102de#gid=0')
@problem.error
async def problem_error(ctx: cmd.Context, error):
	if isinstance(error, cmd.MissingRole):
		await dm.send("You don't have the perms to run this command!")

@bot.command(
	name = 'limit',
	brief = 'Sets the limit of tries you get per problem. Syntax: !limit',
	pass_context = True
)
@cmd.has_role(ADMIN_ROLE)
async def limit(ctx: cmd.Context, v: int):
	global LIMIT
	LIMIT = v
	await ctx.send(f'Set your limit to {v}')
@limit.error
async def limit_error(ctx: cmd.Context, error):
	if isinstance(error, cmd.MissingRole):
		await ctx.send("You don't have the perms to run this command!")

# USER COMMANDS

class User:
	def __init__(self, name):
		self.rrow, self.row = None, None
		try:
			self.row = STORE.find(name).row
		except:
			STORE.insert_row([name])
			self.row = STORE.find(name).row
		finally:
			try:
				self.rrow = CORRECT.find(name).row
			except:
				CORRECT.append_row([name])
				self.rrow = CORRECT.find(name).row

def strint(s: str):
	if '.' in s: return float(s)
	else: return int(s)

@bot.command(
	name = 'solve',
	brief = 'Solves the problem. Syntax: !solve answer',
	pass_context = True
)
async def solve(ctx: cmd.Context, answer):
	#global ADMIN
	#if not ADMIN:
		#ctx.send("Please set an admin channel.")
	try:
		answer = strint(answer)
	except ValueError:
		await dm.send('Please enter an number.')
		await ctx.message.delete()
		return False
	dm = ctx.author.dm_channel
	if not dm: dm = await ctx.author.create_dm()
	user = User(ctx.author.name)
	await ctx.message.delete()
	solved = int('0' if CORRECT.cell(user.rrow, WEEK + 1).value == '' else CORRECT.cell(user.rrow, WEEK + 1).value)
	if solved == 1: 
		await dm.send('You have already solved this problem.')
	else:
		curr = int('0' if STORE.cell(user.row, WEEK + 2).value == '' else STORE.cell(user.row, WEEK + 2).value) + 1
		if curr <= LIMIT:
			if answer == strint(PROBLEM.acell(f'B{WEEK}').value):
				# Correct Answer Inputted
				CORRECT.update_cell(user.rrow, WEEK + 1, '1')
				address = STORE.cell(user.row, WEEK + 2).address
				STORE.format(f'{address}:{address}', {'backgroundColor': {'red': 0.0, 'green': 125.0, 'blue': 0.0}})
				STORE.update_acell(address, str(LIMIT - (curr - 1)))
				try: final_row = FINAL.find(STORE.cell(user.row, 1).value).row
				except:
					FINAL.insert_row([STORE.cell(user.row, 1).value])
					final_row = 1
				finally:
					FINAL.update_cell(final_row, WEEK + 2, STORE.acell(address).value)
				await ADMIN.send(f'<@!{ctx.author.id}> had a Correct Answer!')
				await dm.send(f'Correct Answer! You have received {LIMIT - (curr - 1)} points.')
			else:
				# Incorrect Answer Inputted
				CORRECT.update_cell(user.rrow, WEEK + 1, '0')
				address = STORE.cell(user.row, WEEK + 2).address
				STORE.format(f'{address}:{address}', {'backgroundColor': {'red': 125.0, 'green': 0.0, 'blue': 0.0}})
				STORE.update_acell(address, str(curr))
				await ADMIN.send(f'<@!{ctx.author.id}> had an Incorrect Answer!')
				await dm.send(f'Incorrect Answer! You have {LIMIT - curr} tries remaining.')
				if curr == LIMIT: STORE.update_acell(address, '0')
		else:
			await dm.send('You have already passed the limit of tries you can make for this problem.')

@bot.command(
	name = 'hint',
	brief = 'Gives a hint. This will cost 1 point. Syntax: !hint',
	pass_context = True
)
async def hint(ctx: cmd.Context):
	dm = ctx.author.dm_channel
	if not dm: dm = await ctx.author.create_dm()
	hints = HINT.acell(f'A{WEEK}').value
	user = User(ctx.author.name)
	await ctx.message.delete()
	if hints == "":
		dm.send("There is no hint for this week.")
		await ctx.message.delete()
		return False
	curr = int('0' if STORE.cell(user.row, WEEK + 2).value == '' else STORE.cell(user.row, WEEK + 2).value) + 1
	if LIMIT - curr == 0: # You lost a try
		await dm.send(hints + "\nYou have one try left! Good luck.")
		return
	elif LIMIT - curr < 0:
		await dm.send(hints + "\nYou ran out of tries to this problem.")
	else:
		await dm.send(hints + f'\n You have {LIMIT - curr} tries remaining.')
	# Same as an wrong answer
	CORRECT.update_cell(user.rrow, WEEK + 1, '0')
	address = STORE.cell(user.row, WEEK + 2).address
	STORE.format(f'{address}:{address}', {'backgroundColor': {'red': 125.0, 'green': 0.0, 'blue': 0.0}})
	STORE.update_acell(address, str(curr))
	if curr == LIMIT: STORE.update_acell(address, '0')

@bot.command(
	name = 'potw',
	brief = 'Displays the POTW. Syntax: !potw',
	pass_context = True
)
async def potw(ctx: cmd.Context):
	dm = ctx.author.dm_channel
	if not dm: dm = await ctx.author.create_dm()
	embed = discord.Embed(title = f'Problem of Week {WEEK}', color = discord.Color.blurple(), description = PROBLEM.acell(f'C{WEEK}').value)
	embed.set_image(url = PROBLEM.acell(f'A{WEEK}').value)
	await dm.send(embed = embed)

@bot.command(
	name = 'leaderboard',
	brief = 'Shows the leaderboard. Syntax: !leaderboard',
	pass_context = True
)
async def leaderboard(ctx: cmd.Context):
	dm = ctx.author.dm_channel
	if not dm: dm = await ctx.author.create_dm()
	embed = discord.Embed(title = f'Problem of Week Leaderboard', color = discord.Color.blurple(), description = 'https://docs.google.com/spreadsheets/d/1ffDocLKYnE9ub2EGJRlX8bnUBHFAMf6EgDhUNDZ5UJA/edit?usp=sharing')
	await dm.send(embed = embed)

@bot.command( 
	name = 'starfanclub',
	brief = 'Join the Star Fan Club! Syntax: !starfanclub',
	pass_context = True
)
async def starfanclub(ctx: cmd.Context):
	dm = ctx.author.dm_channel
	if not dm: 
		dm = await ctx.author.create_dm()
	await dm.send("Xie Xie Star")
	member = ctx.message.author
	# get emoji info from R.Danny or emojipedia/emoji_name
	emoji = "⭐"
	await ctx.message.add_reaction(emoji)
	role = discord.utils.get(member.guild.roles, name = "star simp")
	await member.add_roles(role) 

suffer()
bot.run(__import__('os').getenv('DISCORD'))
