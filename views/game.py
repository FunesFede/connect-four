from io import BytesIO
from discord import Interaction
from discord.ui import (
    ActionRow,
    Container,
    DesignerView,
    MediaGallery,
    Section,
    TextDisplay,
)
from PIL import Image
import discord
from helpers.manager import GameManager
import io
from errors.invalidMovement import InvalidMovement


class SelectColumnToSpin(discord.ui.Select):
    def __init__(self, game_manager: GameManager):
        super().__init__(discord.ComponentType.string_select, placeholder="Spin column... (left to right)", options=[
            discord.SelectOption(emoji="<:red_chip:1448166834137206925>" if game_manager.current_turn == game_manager.red_id else "<:yellow_chip:1448166817435746366>", label=f"Column {i+1}", value=str(i)) for i in range(game_manager.columns)])
        self.game_manager = game_manager

    async def callback(self, interaction: Interaction):
        await interaction.edit(content="Selected column correctly!", view=None)
        self.view.stop()  # type: ignore


class SpinItButton(discord.ui.Button):
    def __init__(self, game_manager: GameManager):
        super().__init__(label="Spin it!", emoji="🔄",
                         disabled=not game_manager.spin_it, style=discord.ButtonStyle.primary)
        self.game_manager = game_manager

    async def callback(self, interaction: Interaction):
        if not self.game_manager.can_play(interaction.user.id):  # type: ignore
            return await interaction.respond(content="It is not your turn!", ephemeral=True)

        await interaction.response.defer()

        if self.game_manager.can_spin(interaction.user.id):  # type: ignore
            view = discord.ui.View(timeout=None)
            select = SelectColumnToSpin(self.game_manager)
            view.add_item(select)

            await interaction.respond(view=view, ephemeral=True)

            await view.wait()

            column = int(select.values[0])
            image = self.game_manager.spin_column(
                column, interaction.user.id)  # type: ignore

            game_container = Game(self.game_manager)

            with io.BytesIO() as image_binary:
                image.save(image_binary, "PNG")
                image_binary.seek(0)
                grid = discord.File(fp=image_binary, filename="grid.png")

                await interaction.edit_original_response(view=game_container, files=[grid])

        else:
            await interaction.respond(content="You can't spin a column on this turn!", ephemeral=True)


class PlaceChipSelect(discord.ui.Select):
    def __init__(self, game_manager: GameManager):
        super().__init__(discord.ComponentType.string_select, placeholder="Place chip on column... (left to right)", options=[
            discord.SelectOption(emoji="<:red_chip:1448166834137206925>" if game_manager.current_turn == game_manager.red_id else "<:yellow_chip:1448166817435746366>", label=f"Column {i+1}", value=str(i)) for i in range(game_manager.columns)])
        self.game_manager = game_manager

    async def callback(self, interaction: Interaction):
        if not self.game_manager.can_play(interaction.user.id):  # type: ignore
            return await interaction.respond(content="It is not your turn!", ephemeral=True)

        await interaction.response.defer()

        column = int(self.values[0])

        try:
            image = self.game_manager.make_placement(
                column, interaction.user.id)  # type: ignore

            game_container = Game(self.game_manager)

            with io.BytesIO() as image_binary:
                image.save(image_binary, "PNG")
                image_binary.seek(0)
                grid = discord.File(fp=image_binary, filename="grid.png")
                await interaction.edit(view=game_container, files=[grid])

        except InvalidMovement:
            await interaction.respond(content="You cannot place your chip on this column!", ephemeral=True)


class PlaceChipActionRow(ActionRow):
    def __init__(self, gameManager):
        super().__init__()
        self.add_item(PlaceChipSelect(gameManager))
        # self.add_item(SpinItButton(gameManager))


class Game(DesignerView):
    def __init__(self, game_manager: GameManager):
        super().__init__(timeout=None)
        self.game_manager = game_manager

        container = Container(colour=discord.Colour.blue())
        gallery = MediaGallery()

        gallery.add_item("attachment://grid.png")

        if self.game_manager.turn_count >= self.game_manager.tie_round and self.game_manager.check_tie():
            container.add_text(
                "<:red_chip:1448166834137206925> <:yellow_chip:1448166817435746366> The grid is full! It is a tie!")
            container.add_item(gallery)
        else:
            winner = self.game_manager.validate_connect(
            ) if self.game_manager.turn_count > 6 else None
            if winner:
                container.color = discord.Color.red(
                ) if winner == self.game_manager.red_id else discord.Color.yellow()
                container.add_text(
                    f"{"<:red_chip:1448166834137206925>" if winner == self.game_manager.red_id else "<:yellow_chip:1448166817435746366>"} <@{winner}> wins! They connected four in a row!")
                container.add_item(gallery)

            else:
                container.add_item(Section(TextDisplay(
                    f"{"<:red_chip:1448166834137206925>" if self.game_manager.current_turn == self.game_manager.red_id else "<:yellow_chip:1448166817435746366>"} It is <@{self.game_manager.current_turn}>'s turn!"), accessory=SpinItButton(self.game_manager)))
                container.add_item(gallery)
                container.add_item(PlaceChipActionRow(self.game_manager))

        self.add_item(container)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id not in [self.game_manager.red_id,  # type: ignore
                                       self.game_manager.yellow_id]:
            await interaction.respond(content="This is not your game!", ephemeral=True)
            return False
        return True

    def get_grid(self) -> Image.Image:
        return self.game_manager.get_grid_image()
