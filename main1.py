import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import matplotlib.pyplot as plt
from fbprophet import Prophet

TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
DEX_API_KEY = 'YOUR_DEX_SCREENER_API_KEY'

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Cryptocurrency Price Prediction bot. Please enter the smart contract address of the cryptocurrency you want to predict the price for.")

def predict(update, context):
    try:
        # Get the smart contract address from the user
        address = update.message.text
        url = f"https://api.dexscreener.com/v1/arbitrum/address/{address}"
        
        # Get information about the specified cryptocurrency from Dex Screener API
        headers = {'Authorization': f"Bearer {DEX_API_KEY}"}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Get current price, trading volume, liquidity, and market cap of the specified cryptocurrency
        price = data['data']['quote']['USD']['price']
        volume = data['data']['quote']['USD']['volume_24h']
        liquidity = data['data']['quote']['USD']['liquidity_score']
        market_cap = data['data']['quote']['USD']['market_cap']
        
        # Send the cryptocurrency details to the user
        message = f"Current price: {price} USD\nTrading volume (24h): {volume} USD\nLiquidity score: {liquidity}\nMarket cap: {market_cap} USD"
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        
        # Use Prophet to generate a 30-minute price prediction chart
        history = data['data']['history']
        prices = []
        times = []
        for h in history:
            prices.append(h['quote']['USD']['price'])
            times.append(h['time'])
        df = {'ds': times, 'y': prices}
        m = Prophet()
        m.fit(df)
        future = m.make_future_dataframe(periods=30, freq='min')
        forecast = m.predict(future)
        
        # Save the chart as a photo and send it to the user
        fig = m.plot(forecast)
        fig.savefig('chart.png')
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('chart.png', 'rb'))
        
        # Get the DEX where the specified cryptocurrency is listed and generate a link to the buy now button
        dex = data['data']['dex']
        buy_now_link = f"https://{dex}/trade/{address}"
        
        # Send the link to the buy now button to the user
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"You can buy {address} on {dex} at {buy_now_link}")
    except Exception as e:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")
        return

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher
start_handler = CommandHandler('start', start)
predict_handler = MessageHandler(Filters.text & (~Filters.command), predict)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(predict_handler)
updater.start_polling()
updater.idle()
