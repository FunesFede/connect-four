import discord
from pycord_rest import App, ApplicationAuthorizedEvent

from dotenv import load_dotenv
import os
import io

from views.game import Game
from helpers.manager import GameManager


load_dotenv()


app = App(default_command_integration_types=[
    discord.IntegrationType.user_install, discord.IntegrationType.guild_install])


@app.listen("on_application_authorized")
async def on_application_authorized(event: ApplicationAuthorizedEvent):
    print(f"Authorized: Guild={event.guild}, User={event.user}")


@app.slash_command(description="Challenge someone on a connect four game")
@discord.option("oppponent", discord.User, description="Choose your opponent for this game")
@discord.option("rows", int, description="The number of rows for the grid. Defaults to 6", default=6, min_value=4, max_value=24)
@discord.option("columns", int, description="The number of columns for the grid. Defaults to 7", defult=7, min_value=5, max_value=25)
@discord.option("spin_it", bool, description="Allow spinning columns? Defaults to True", defult=True)
async def play(ctx: discord.ApplicationContext, opponent: discord.User, rows: int = 6, columns: int = 7, spin_it: bool = True):
    if ctx.author.id == opponent.id or opponent.bot:
        return await ctx.respond(content="You cannot play against this user!", ephemeral=True)

    game_container: discord.ui.DesignerView = Game(
        GameManager(rows, columns, spin_it, ctx.author.id, opponent.id))
    image = game_container.get_grid()

    with io.BytesIO() as image_binary:
        image.save(image_binary, "PNG")
        image_binary.seek(0)
        grid = discord.File(fp=image_binary, filename="grid.png")
        await ctx.respond(view=game_container, files=[grid])

if __name__ == "__main__":
    app.run(
        token=os.environ["TOKEN"],
        public_key=os.environ["PUBLIC_KEY"],
        uvicorn_options={
            "host": "0.0.0.0",
            "port": 1028,
            "log_level": "debug"
        },
        health=True
    )
