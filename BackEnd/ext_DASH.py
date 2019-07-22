import ccxt
import sys
import ccxt
import random
import time
import sys
import datetime
import json
import os
import numpy as np
import pandas as pd
from enum import Enum

buy_from_neutral = 0.0025
sell_from_long = -0.001

buy_from_short = +0.001
sell_from_neutral = -0.0025

timeframe = '1m'
base = 'BTC/USDT'
pairs = ['DASH/USDT']
size = 1

live_trading = True
bot_name = 'ext_DASH'


if sys.platform == 'win32':
    excel_file = bot_name +'_data.xlsx'
    position_file = bot_name +'_position.json'
    filename = bot_name +'_signals.csv'
else:
    excel_file = '/var/www/html/'+ bot_name +'_mkt_data.xlsx'
    position_file = '/var/www/html/'+ bot_name +'_position.json'
    filename = '/var/www/html/'+ bot_name +'_signals.csv'

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
    binance.apiKey = 'API key'
    binance.secret = 'API secret'
    exchanges.append(binance)

    return exchanges

exchanges = loadExchanges()

with open(position_file) as json_file:  
    pos = json.load(json_file)
position = pos['position']

for e in exchanges:
    for pair in pairs:
        #holdings = e.fetchBalance()['free']
        #print("BTC: ",holdings['BTC'])
        #print("USDT: ", holdings['USDT'])
        
        ind_trades = e.fetch_trades(base)
        df_ind_trades = pd.DataFrame.from_records(ind_trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        df_ind_trades['trade_time'] = df_ind_trades.apply(lambda x: get_time(x['timestamp']), axis=1)

        #Get Data
        #print('get data')
        x = datetime.datetime.now()
        datestr = str(x.strftime('%Y/%m/%d %H:%M:%S'))
        orderbook = e.fetch_order_book (pair)
        df_bid_orders = pd.DataFrame(orderbook['bids'],columns = ['price','units'])
        df_ask_orders = pd.DataFrame(orderbook['asks'],columns = ['price','units'])
        bid_sum = df_bid_orders[df_bid_orders['price'] > float(orderbook['bids'][0][0])*0.999]['units'].sum()
        ask_sum = df_ask_orders[df_ask_orders['price'] < float(orderbook['asks'][0][0])*1.001]['units'].sum()
        
        ask = float(orderbook['asks'][0][0])
        bid = float(orderbook['bids'][0][0])

        #df_bid_orders['EWMA_90'] = df_bid_orders['units'].ewm(com=0.9).mean()  
        #df_ask_orders['EWMA_90'] = df_ask_orders['units'].ewm(com=0.9).mean() 

        ohlcv_1d = e.fetch_ohlcv (pair, '1d')
        
        ind_ohlcv = e.fetch_ohlcv ('BTC/USDT', timeframe)
        ohlcv = e.fetch_ohlcv (pair, timeframe)
        
        trades = e.fetch_trades(pair)

        #my_trades = e.fetch_my_trades(pair)

        #df_my_trades = pd.DataFrame.from_records(my_trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        #df_my_trades['trade_time'] = df_my_trades.apply(lambda x: get_time(x['timestamp']), axis=1)

        df_ind_ohlcv = pd.DataFrame.from_records(ind_ohlcv, columns = ['timestamp' , 'open', 'high','low','close','volume'])
        df_ind_ohlcv['trade_time'] = df_ind_ohlcv.apply(lambda x: get_time(x['timestamp']), axis=1)

        df_trades = pd.DataFrame.from_records(trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        df_trades['trade_time'] = df_trades.apply(lambda x: get_time(x['timestamp']), axis=1)

        total_volume = df_trades['amount'].sum()
        trades_buy = df_trades[df_trades['side'] == "buy"]['amount'].sum()
        trades_sell = df_trades[df_trades['side'] == "sell"]['amount'].sum()
        
        #print(df_ind_ohlcv.tail(10))
        #last_row['close'].values[0]
        #print(df_ind_trades.tail(1))
        #print(df_ind_trades['timestamp'].tail(1).values[0])
        
        df_ind_trades.tail(1)

        last_trade = df_trades['timestamp'].tail(1).values[0]
        #print(last_trade)
        #print(df_trades['timestamp'].tail(1).values[0])
        
        df_ind_ohlcv_hist = df_ind_ohlcv[(df_ind_ohlcv['timestamp'] < df_trades['timestamp'].tail(1).values[0])] 
        df_ind_trades_hist = df_ind_trades[(df_ind_trades['timestamp'] < df_trades['timestamp'].tail(1).values[0])] 

        print('BTC time and sales (most recent):')
        print(df_ind_trades[['timestamp','trade_time','price','amount','symbol']].tail(5))

        print('BTC minute bars:')
        print(df_ind_ohlcv_hist[['timestamp','trade_time','close']].tail(5))
        print('BTC time and sales:')
        print(df_ind_trades_hist[['timestamp','trade_time','price','amount','symbol']].tail(5))
        
        print('DASH time and sales:')
        print(df_trades[['timestamp','trade_time','price','amount','symbol']].tail(5))

        
        if len(df_ind_trades_hist) >0 :
            print('enough time and sales')
            print("BTC from ",df_ind_trades_hist['price'].tail(1).values[0], " to ",df_ind_trades['price'].tail(1).values[0],df_ind_trades['price'].tail(1).values[0]/df_ind_trades_hist['price'].tail(1).values[0]-1)
            pred_move = df_ind_trades['price'].tail(1).values[0]/df_ind_trades_hist['price'].tail(1).values[0]-1
        else:
            print('need minutes bars')
            print("BTC from ",df_ind_ohlcv_hist['close'].tail(1).values[0], " to ",df_ind_trades['price'].tail(1).values[0],df_ind_trades['price'].tail(1).values[0]/df_ind_ohlcv_hist['close'].tail(1).values[0]-1)
            #pred_move = df_ind_ohlcv_hist['close'].tail(1).values[0]/df_ind_trades_hist['price'].tail(1).values[0]-1
            pred_move = df_ind_trades['price'].tail(1).values[0]/df_ind_ohlcv_hist['close'].tail(1).values[0]-1
        
        last_price = df_trades['price'].tail(1).values[0]

        print('bid:',bid, 'ask:',ask,'last:',last_price, 'fv: ',last_price * (1 +pred_move))
        
        fv = last_price * (1 +pred_move)

        if (ask < fv):
            signal_ext = fv/ask -1            
        elif (bid > fv):
            signal_ext = fv/bid-1
        else:
            signal_ext = 0

        print('signal','{x:.4%}'.format(x=signal_ext))   

        cols = ['datetime','open','high','low','close','volume']
        
        df_ohlcv = pd.DataFrame(ohlcv,columns = cols)
        df_ohlcv_1d = pd.DataFrame(ohlcv_1d,columns = cols)
        df_ohlcv_1d['EWMA_90'] = df_ohlcv_1d['close'].ewm(com=0.9).mean()  
        df_ohlcv_1d['EWMA_60'] = df_ohlcv_1d['close'].ewm(com=0.6).mean()  
        df_ohlcv_1d['trade_time'] = df_ohlcv_1d.apply(lambda x: get_time(x['datetime']), axis=1)

        df_ohlcv['close_pct_move'] = df_ohlcv['close'].pct_change()
        df_ohlcv['RSI_10m'] = df_ohlcv['close_pct_move'].rolling(center=False,window=10).apply(rsi,raw=False)
        df_ohlcv['RSI_60m'] = df_ohlcv['close_pct_move'].rolling(center=False,window=60).apply(rsi,raw=False)
        df_ohlcv['EWMA_90'] = df_ohlcv['close'].ewm(com=0.9).mean()  
        df_ohlcv['EWMA_60'] = df_ohlcv['close'].ewm(com=0.6).mean()

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
                
        last_row = df_ohlcv[['close','RSI_10m','RSI_60m','EWMA','trade','buy_at','sell_at','signal','signal_EWMA','signal_RSI','high','low']].tail(1)

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

        signal = signal_ext
        
        execution = "Trading off..."
        lastb_buy_px = float(pos['lastb_buy_px'])
        lastb_sell_px = float(pos['lastb_sell_px'])
        buy_price = ''
        sell_price = ''

        pnl = 0
        cost = 0
        amount = 0
        pos_ls = 0
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

        #print("signal EWMA:",signal_EWMA)
        #print("signal RSI:",signal_RSI)
        #print("signal trade imbalance:",signal_trade_imb)
        #print("signal OB:",signal_OB)
        #print("signal OB 1 pct:",signal_OB_1_pct)
        #print("signal (final):",signal)
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
            'long_name' : 'Extrapolating Sniper',
            #'prev_EWMA' : signal_EWMA,
            #'prev_RSI' : signal_RSI,
            #'prev_OB' : signal_OB,
            #'prev_IB' : signal_trade_imb,
            'prev_final' : signal
            }

        #Save down files

        file_exists = os.path.isfile(filename)
        file1 = open(filename,"a")

        if not file_exists:
            file1.writelines('timedate,bid_1,ask_1,RSI,EWMA,trade,buy_at,sell_at,Signal,bid_sum,ask_sum,Last Trade,EWMA Signal,RSI Signal,Total Volume,bid_5,ask_5,OB Signal,Trade Bal Signal,Trade_PnL,Trade_Cost,Amount,Running PnL,pos_ls'+ "\n")
            pos['running_pnl'] = 100
            running_pnl = 100

        file1.writelines(datestr  + ',' + str(orderbook['bids'][0][0]) + ',' + str(orderbook['asks'][0][0]) + ',' 
            + str(round(RSI,0)) + ',' +  str(round(EWMA,2)) + ','
            + str(execution) +  ',' + str(buy_price) + ',' + str(sell_price) + ',' + '{x:.4%}'.format(x=signal) 
            + ',' + str(round(bid_sum,2)) + ',' + str(round(ask_sum,2))  + ',' + str(trade)
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
        df_ind_trades.to_excel(writer,'BTC_trades')
        df_ind_ohlcv.to_excel(writer,'BTC_OHLC')
        df_trades.to_excel(writer,'trades')
        df_ohlcv.to_excel(writer,'ohlcv')
        df_ohlcv_1d.to_excel(writer,'ohlcv_1d')
        df_ask_orders.to_excel(writer,'ask')
        df_bid_orders.to_excel(writer,'bid')
        #df_my_trades.to_excel(writer,'my_trades')
        df_ind_trades.to_excel(writer,'BTC')
        writer.save()