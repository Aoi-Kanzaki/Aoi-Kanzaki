import json
from quart import Quart, render_template, request, session, redirect, url_for
from quart_discord import DiscordOAuth2Session
from discord.ext.ipc import Client

with open("../config.json", "r") as config:
    config = json.load(config)

app = Quart(__name__)
ipc = Client(secret_key=config['secret_key'])
app.config["SECRET_KEY"] = config['secret_key']
app.config["DISCORD_CLIENT_ID"] = 834979964062662656
app.config["DISCORD_CLIENT_SECRET"] = "LTjg8Ognzdcmqj2L84EWtKLuIO9E3i7E"
app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback"
discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
	return await render_template("index.html", authorized=await discord.authorized)

@app.route("/login")
async def login():
	return await discord.create_session()

@app.route("/callback")
async def callback():
    try:
        await discord.callback()
    except:
        pass
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
async def dashboard():
	if not await discord.authorized:
		return redirect(url_for("login"))

	guild_ids = await ipc.request("get_guild_ids")
	user_guilds = await discord.fetch_guilds()
	user = await discord.fetch_user()
	favs = await ipc.request("get_favorites", user_id=user.id)

	spotify = await ipc.request("get_spotify", user_id=user.id)
	try:
		spotify = spotify['account']
	except KeyError:
		spotify = None

	guilds = []
	for guild in user_guilds:
		if guild.permissions.administrator:			
			guild.class_color = "green-border" if guild.id in guild_ids else "red-border"
			guilds.append(guild)

	guilds.sort(key = lambda x: x.class_color == "red-border")
	return await render_template("dashboard.html", guilds=guilds, user=user, favsongs=favs['songs'], spotify_account=spotify)

@app.route("/dashboard/<int:guild_id>")
async def dashboard_server(guild_id):
	if not await discord.authorized:
		return redirect(url_for("login"))

	guild = await ipc.request("get_guild", guild_id=guild_id)
	try:
		name = guild["name"]
		return await render_template("guildSettings.html", guild=guild)
	except KeyError:
		return redirect(f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=80)