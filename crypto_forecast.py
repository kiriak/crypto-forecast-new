import requests
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import datetime

def fetch_crypto_data(coin='bitcoin'):
    url = f'https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=365'
    response = requests.get(url)
    data = response.json()['prices']
    df = pd.DataFrame(data, columns=['timestamp', 'price'])
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df[['date', 'price']]

def create_lstm():
    model = Sequential()
    model.add(LSTM(64, input_shape=(60, 1), return_sequences=True))
    model.add(LSTM(32))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    return model

def prepare_data(prices):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(prices.reshape(-1, 1))
    X, y = [], []
    for i in range(60, len(scaled)):
        X.append(scaled[i-60:i, 0])
        y.append(scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))
    return X, y, scaler

def forecast(model, data, scaler, days=180):
    inputs = scaler.transform(data[-60:].reshape(-1,1))
    predictions = []
    for _ in range(days):
        X = inputs[-60:].reshape(1, 60, 1)
        pred = model.predict(X)
        predictions.append(pred[0,0])
        inputs = np.append(inputs, pred, axis=0)
    return scaler.inverse_transform(np.array(predictions).reshape(-1,1))

def plot_forecast(dates, prices, forecasted, coin):
    plt.figure(figsize=(10,5))
    plt.plot(dates, prices, label='Historical')
    last = dates.iloc[-1]
    future = [last + datetime.timedelta(days=i) for i in range(1, len(forecasted)+1)]
    plt.plot(future, forecasted, label='Forecast', linestyle='--')
    plt.title(f'{coin.capitalize()} Forecast (6 Months)')
    plt.xlabel('Date')
    plt.ylabel('USD')
    plt.legend()
    plt.grid()
    plt.savefig(f'{coin}_forecast.png')
    plt.close()

def main():
    coins = ['bitcoin', 'ethereum', 'solana']
    for coin in coins:
        print(f"Fetching data and forecasting for {coin.capitalize()}")
        df = fetch_crypto_data(coin)
        prices = df['price'].values
        dates = df['date']
        X, y, scaler = prepare_data(prices)
        model = create_lstm()
        model.fit(X, y, epochs=5, batch_size=32, verbose=0)
        prediction = forecast(model, prices, scaler)
        plot_forecast(dates, prices, prediction, coin)
        print(f"{coin} forecast saved!")

if __name__ == '__main__':
    main()

