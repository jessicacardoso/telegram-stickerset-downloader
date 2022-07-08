from pyrogram import Client
import confuse

# Arquivo localizado em ~/.config/StickerApp/config.yaml
config = confuse.Configuration("StickerApp", __name__)
app = Client("my_account", **config["telegram_key"].get())
app.run()
