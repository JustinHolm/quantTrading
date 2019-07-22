import ccxt
import sys
import ccxt
import random
import time
import datetime
import json
import os
import numpy as np
import pandas as pd
from enum import Enum

buy_from_neutral = 0.0050
sell_from_long = 0.0002

buy_from_short = -0.0002
sell_from_neutral = -0.0050

timeframe = '1m'
pairs = ['BTC/USDT']
size = 0.01

live_trading = True
bot_name = 'mac'

excel_file = '/var/www/html/'+ bot_name +'_mkt_data.xlsx'
excel_file = bot_name +'_data.xlsx'

position_file = '/var/www/html/'+ bot_name +'_position.json'
position_file = bot_name +'_position.json'

filename = '/var/www/html/'+ bot_name +'_signals.csv'
filename = bot_name +'_signals.csv'

class TradeAction(Enum):
    BUY_FROM_NEUTRAL = 1
    SELL_FROM_NEUTRAL = 2
    SELL_FROM_LONG = 3
    BUY_FROM_SHORT = 4
    REMAIN_NEUTRAL = 5
    
def action(signal):
    if (signal > buy_from_neutral):
        return "long"
    elif (signal < sell_from_neutral):
        return "short"
    else:
        return "none"

def get_time(time_str):
    return time.strftime("%d %b %Y %H:%M:%S",time.localtime(time_str/1000))
    
def buy_at(trade,price):
    try:
        if (trade == "long"):
            return price
    except:
        return ""

def sell_at(trade,price):
    try:
        if (trade == "short"):
            return price
    except:
        return ""

def rsi(values):
    up = values[values>0].mean()
    down = -1*values[values<0].mean()
    return 100 * up / (up + down)

def loadExchanges():
    exchanges = []

    binance = ccxt.binance()
    binance.apiKey = 'key here'
    binance.secret = 'secret here'
    exchanges.append(binance)

    return exchanges

exchanges = loadExchanges()

with open(position_file) as json_file:  
    pos = json.load(json_file)
position = pos['position']

for e in exchanges:
    for pair in pairs:
        holdings = e.fetchBalance()['free']
        #print("BTC: ",holdings['BTC'])
        #print("USDT: ", holdings['USDT'])
        
        #Get Data
        print('get data')
        x = datetime.datetime.now()
        datestr = str(x.strftime('%Y/%m/%d %H:%M:%S'))
        orderbook = e.fetch_order_book (pair)
        df_bid_orders = pd.DataFrame(orderbook['bids'],columns = ['price','units'])
        df_ask_orders = pd.DataFrame(orderbook['asks'],columns = ['price','units'])
        bid_sum = df_bid_orders[df_bid_orders['price'] > float(orderbook['bids'][0][0])*0.999]['units'].sum()
        ask_sum = df_ask_orders[df_ask_orders['price'] < float(orderbook['asks'][0][0])*1.001]['units'].sum()
        
        ask = float(orderbook['asks'][0][0])
        bid = float(orderbook['bids'][0][0])

        df_bid_orders['EWMA_90'] = df_bid_orders['units'].ewm(com=0.9).mean()  
        df_ask_orders['EWMA_90'] = df_ask_orders['units'].ewm(com=0.9).mean() 

        df_bid_orders['EWMA_99'] = df_bid_orders['units'].ewm(com=0.9999).mean()  
        df_ask_orders['EWMA_99'] = df_ask_orders['units'].ewm(com=0.9999).mean() 

        ohlcv_1d = e.fetch_ohlcv (pair, '1d')
        ohlcv = e.fetch_ohlcv (pair, timeframe)
        trades = e.fetch_trades(pair)

        my_trades = e.fetch_my_trades(pair)

        df_my_trades = pd.DataFrame.from_records(my_trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        df_my_trades['trade_time'] = df_my_trades.apply(lambda x: get_time(x['timestamp']), axis=1)

        df_trades = pd.DataFrame.from_records(trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        df_trades['trade_time'] = df_trades.apply(lambda x: get_time(x['timestamp']), axis=1)

        total_volume = df_trades['amount'].sum()
        trades_buy = df_trades[df_trades['side'] == "buy"]['amount'].sum()
        trades_sell = df_trades[df_trades['side'] == "sell"]['amount'].sum()
        
       #print(df_trades)

        cols = ['datetime','open','high','low','close','volume']
        
        df_ohlcv = pd.DataFrame(ohlcv,columns = cols)
        df_ohlcv_1d = pd.DataFrame(ohlcv_1d,columns = cols)
        df_ohlcv_1d['EWMA_90'] = df_ohlcv_1d['close'].ewm(com=0.9).mean()  
        df_ohlcv_1d['EWMA_60'] = df_ohlcv_1d['close'].ewm(com=0.6).mean()  
        df_ohlcv_1d['trade_time'] = df_ohlcv_1d.apply(lambda x: get_time(x['datetime']), axis=1)

        df_ohlcv['close_pct_move'] = df_ohlcv['close'].pct_change()
        df_ohlcv['RSI_10m'] = df_ohlcv['close_pct_move'].rolling(center=False,window=10).apply(rsi)
        df_ohlcv['RSI_60m'] = df_ohlcv['close_pct_move'].rolling(center=False,window=60).apply(rsi)
        df_ohlcv['EWMA_90'] = df_ohlcv['close'].ewm(com=0.9).mean()  
        df_ohlcv['EWMA_60'] = df_ohlcv['close'].ewm(com=0.6).mean()


        df_ohlcv['WA26'] = df_ohlcv['close'].rolling(26).mean() 
        df_ohlcv['WA14'] = df_ohlcv['close'].rolling(12).mean() 
        df_ohlcv['Diff_12_26'] = df_ohlcv['WA14'] - df_ohlcv['WA26'] 

        df_ohlcv['Diff_WA'] = df_ohlcv['Diff_12_26'].rolling(9, win_type ='triang').mean() 


        df_ohlcv['MACD_Raw_Signal'] =  df_ohlcv['Diff_12_26'] - df_ohlcv['Diff_WA']
        df_ohlcv['MACD_Signal'] = df_ohlcv['MACD_Raw_Signal']/10000

        df_ohlcv['EWMA'] = df_ohlcv['close'].ewm(com=0.8).mean()   
        df_ohlcv['trade_time'] = df_ohlcv.apply(lambda x: get_time(x['datetime']), axis=1)

        #Signal calculations

        df_ohlcv['signal_EWMA'] = (df_ohlcv['close'] / df_ohlcv['EWMA'] -1)
        df_ohlcv['signal_RSI'] = (((df_ohlcv['RSI_60m'] * -0.01) + 0.5)/100)
        df_ohlcv['signal'] = df_ohlcv['signal_EWMA'] + (0.5 * df_ohlcv['signal_RSI'])
        df_ohlcv['trade'] = df_ohlcv.apply(lambda x: action(x['signal']), axis=1)

        df_ohlcv['buy_at'] = df_ohlcv.apply(lambda x: buy_at(x['trade'],ask), axis=1)
        df_ohlcv['sell_at'] = df_ohlcv.apply(lambda x: sell_at(x['trade'],bid), axis=1)

        #print(df_ohlcv[['close','trade','signal_EWMA','signal_RSI','signal']].tail(10))
                
        last_row = df_ohlcv[['MACD_Raw_Signal','Diff_12_26','MACD_Signal','close','RSI_10m','RSI_60m','EWMA','trade','buy_at','sell_at','signal','signal_EWMA','signal_RSI','high','low']].tail(1)

        close = float(last_row['close'].values[0])
        EWMA = float(last_row[['EWMA']].values[0])
        RSI = float(last_row[['RSI_60m']].values[0])
    
        signal_EWMA =  last_row['signal_EWMA'].values[0]
        signal_RSI =  last_row['signal_RSI'].values[0]
        
        signal_OB = ((bid_sum - ask_sum) / (bid_sum + ask_sum)) / 100 
        signal_trade_imb = ((trades_buy - trades_sell) / (trades_buy + trades_sell))/100
        trade  =  last_row['close'].values[0]
        high_px  =  last_row['high'].values[0]
        low_px =  last_row['low'].values[0]
        signal = last_row['MACD_Signal'].values[0]

        Diff_12_26 = float(last_row['Diff_12_26'].values[0])
        MACD_Raw_Signal = float(last_row['MACD_Raw_Signal'].values[0])
        
        #signal = (0.45 * signal_EWMA) + (0.45 * signal_RSI) + (0.05 * signal_OB) + (0.05 * signal_trade_imb)
        
        execution = "Trading off..."
        lastb_buy_px = float(pos['lastb_buy_px'])
        lastb_sell_px = float(pos['lastb_sell_px'])
        buy_price = ''
        sell_price = ''

        pnl = 0
        cost = 0
        amount = 0

        #Trade Logic
        
        print("Starting position: ",pos['position'])
        if live_trading:
            if position == "neutral":
                if signal > buy_from_neutral:
                    order = e.createMarketBuyOrder (pair,size)
                    execution = ("Buy @:" + str(ask))
                    buy_price = order['average']
                    lastb_buy_px = order['average']
                    cost = order['cost']
                    amount = order['amount']
                    #print(order['average'],order)
                    position = "long"
                    pos_ls = 1
                elif signal < sell_from_neutral:
                    order = e.createMarketSellOrder(pair,size)
                    execution = ("Sell @ " + str(bid))
                    sell_price = order['average']
                    lastb_sell_px = order['average']
                    cost = order['cost']
                    amount = order['amount']
                    #print(order['average'],order)
                    position = "short"
                    pos_ls = -1
                else:
                    execution = ("Stay Neutral")
                    position = "neutral"
                    pos_ls = 0
            elif position == "long":
                if signal < sell_from_long:
                    order = e.createMarketSellOrder(pair,size)
                    execution = ("Sell @ " + str(bid))
                    sell_price = order['average']
                    lastb_sell_px = order['average']
                    cost = order['cost']
                    amount = order['amount']
                    #print(order['average'],order)
                    pnl = sell_price/float(pos['lastb_buy_px']) -1
                    position = "neutral"
                    pos_ls = 0
                else:
                    position = "long"
                    pos_ls = 1
                    execution = ("Stay Long")
            elif position == "short":
                if signal > buy_from_short:
                    order = e.createMarketBuyOrder(pair,size)
                    execution = ("Buy @:" + str(ask))
                    buy_price = order['average']
                    lastb_buy_px = order['average']
                    cost = order['cost']
                    amount = order['amount']
                    amount = order['amount']
                    #print(order['average'],order)
                    pnl = -(buy_price/float(pos['lastb_sell_px']) -1)
                    position = "neutral"
                    pos_ls = 0
                else:
                    execution = ("Stay short")
                    position = "short"
                    pos_ls = -1

        # print("signal EWMA:",signal_EWMA)
        # print("signal RSI:",signal_RSI)
        # print("signal trade imbalance:",signal_trade_imb)
        # print("signal OB:",signal_OB)
        #print("signal OB 1 pct:",signal_OB_1_pct)
        print("signal (final):",signal)
        print("Action :" ,execution)
        print("Ending position: ",position)
        print("pnl:",pnl)

        running_pnl = pos['running_pnl'] * (1 + pnl)
        
        pos = {  
            'pair': 'BTC/USDT',
            'position': str(position),
            'pos_ls' : pos_ls,
            'lastb_buy_px' : lastb_buy_px,
            'lastb_sell_px' : lastb_sell_px,
            'running_pnl' : running_pnl,
            'long_name' : 'MACD',
            'prev_EWMA' : signal_EWMA,
            'prev_RSI' : signal_RSI,
            'prev_OB' : signal_OB,
            'prev_IB' : signal_trade_imb,
            'prev_final' : signal
            }

        #Save down files

        file_exists = os.path.isfile(filename)
        file1 = open(filename,"a")

        if not file_exists:
            file1.writelines('timedate,bid_1,ask_1,RSI,EWMA,trade,buy_at,sell_at,Signal,Diff_12_26,MACD_Raw_Signal,Last Trade,EWMA Signal,RSI Signal,Total Volume,bid_5,ask_5,OB Signal,Trade Bal Signal,Trade_PnL,Trade_Cost,Amount,Running PnL,pos_ls'+ "\n")
            pos['running_pnl'] = 100
            running_pnl = 100

        file1.writelines(datestr  + ',' + str(orderbook['bids'][0][0]) + ',' + str(orderbook['asks'][0][0]) + ',' 
            + str(round(RSI,0)) + ',' +  str(round(EWMA,2)) + ','
            + str(execution) +  ',' + str(buy_price) + ',' + str(sell_price) + ',' + '{x:.4%}'.format(x=signal) 
            + ',' + str(round(Diff_12_26,2)) + ',' + str(round(MACD_Raw_Signal,2))  + ',' + str(trade)
            + ',' + '{x:.4%}'.format(x=signal_EWMA) + ',' + '{x:.4%}'.format(x=signal_RSI)
            + ',' + str(round(total_volume,2)) + ',' + str(orderbook['bids'][99][0]) + ',' + str(orderbook['asks'][99][0]) 
            + ',' + '{x:.4%}'.format(x=signal_OB)
            + ',' + '{x:.4%}'.format(x=signal_trade_imb)
            + ',' + '{x:.6%}'.format(x=float(pnl))
            + ',' + str(cost)
            + ',' + str(amount)
            + ',' + str(round(running_pnl,4))
            + ',' + str(pos_ls)
            + "\n" )

        file1.close()

        with open(position_file, 'w') as json_file:  
            json.dump(pos, json_file)

        writer = pd.ExcelWriter(excel_file)
        df_trades.to_excel(writer,'trades')
        df_ohlcv.to_excel(writer,'ohlcv')
        df_ohlcv_1d.to_excel(writer,'ohlcv_1d')
        df_ask_orders.to_excel(writer,'ask')
        df_bid_orders.to_excel(writer,'bid')
        df_my_trades.to_excel(writer,'my_trades')
        
        writer.save()

        # file_mktdata = '/var/www/html/mkt_data/' + pair.replace("/","-") + str(datetime.datetime.now()).replace(":","-").replace(".","-") + '.xlsx'
        
        # writer2 = pd.ExcelWriter(file_mktdata)
        
        # df_trades.to_excel(writer2,'trades')
        # df_ohlcv.to_excel(writer2,'ohlcv')
        # df_ohlcv_1d.to_excel(writer2,'ohlcv_1d')
        # df_ask_orders.to_excel(writer2,'ask')
        # df_bid_orders.to_excel(writer2,'bid')
        # df_my_trades.to_excel(writer2,'my_trades')

        # writer2.save()