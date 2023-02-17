import requests
import json
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from fbprophet import Prophet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

def start(update, context):
    update.message.reply_text('Hi! I am a cryptocurrency price prediction bot. Send me the Smart Contract address of the cryptocurrency you want a price prediction for.')

def predict(update, context):
    url = f"https://api.dxscreener.com/api/v1/coins?chain=arbitrum-one&search={context.args[0]}"
    response = requests.get(url)
    data = json.loads(response.text)
    if not data["coins"]:
        update.message.reply_text('Sorry, the coin you requested could not be found.')
        return

    coin_data = data["coins"][0]

    # Get price data from API
    url = f"https://api.dxscreener.com/api/v1/token?chain=arbitrum-one&address={context.args[0]}"
    response = requests.get(url)
    data = json.loads(response.text)
    price_data = data["prices"]

    # Create dataframe with price data
    df = pd.DataFrame(price_data, columns=["ds", "y"])
    df["ds"] = pd.to_datetime(df["ds"], unit="ms")
    df["y"] = df["y"].astype(float)

    # Train model
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=30, freq='MIN')
    forecast = model.predict(future)
    forecast = forecast[["ds", "yhat"]]
    forecast = forecast.tail(30)

    # Generate plot
    fig, ax = plt.subplots()
    ax.plot(df["ds"], df["y"], label="Actual Price")
    ax.plot(forecast["ds"], forecast["yhat"], label="Predicted Price")
    ax.set_xlabel("Time")
    ax.set_ylabel("Price")
    ax.set_title(f"{coin_data['name']} Price Prediction for Next 30 Minutes")
    ax.legend()
    
    # Save plot to bytes buffer
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    plot_image = Image.open(buffer)

    # Prepare message text
    message_text = f"<b>{coin_data['name']} Price Prediction:</b>\n"
    message_text += f"Network: {coin_data['network'].upper()}\n"
    message_text += f"Price: {df.tail(1)['y'].values[0]:,.8f}\n"
    message_text += f"Volume: ${coin_data['volume']:,.1f}\n"
    message_text += f"Liquidity: ${coin_data['liquidity']:,.1f} ({coin_data['liquidity_eth']:.2f} WETH)\n"
    message_text += f"Marketcap: ${coin_data['marketcap']:,.2f}\n"
    message_text += f"Predicted Price: {forecast.tail(1)['yhat'].values[0]:,.8f}\n"

    # Send message
    context.bot.send_photo(update.message.chat_id, photo=plot_image)
    context.bot.send_message(update.message.chat_id, text=message_text, parse_mode=ParseMode.HTML)

def main():
    updater = Updater('YOUR_TELEGRAM_BOT_TOKEN', use_context=True)
    dp = updater
