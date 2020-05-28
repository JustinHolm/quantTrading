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
import matplotlib.pyplot as plt
import statsmodels.formula.api as sm

def rsi(values):
    up = values[values>0].mean()
    down = -1*values[values<0].mean()
    return 100 * up / (up + down)

def loadExchanges():
    exchanges = []

    with open(key_file) as json_file:  
        keys = json.load(json_file)

    binance = ccxt.binance()
    binance.apiKey = keys['exchanges']['binance']['key']
    binance.secret = keys['exchanges']['binance']['secret']
    exchanges.append(binance)

    return exchanges

def get_time(time_str):
    return time.strftime("%d %b %Y %H:%M:%S",time.localtime(time_str/1000))

bot_name = 'arb_search'

if sys.platform == 'win32':
    key_file = 'API_key.json'
    excel_file = bot_name +'_data.xlsx'
    position_file = bot_name +'_position.json'
    filename = bot_name +'_signals.csv'
else:
    key_file = '/root/bots/API_key.json'
    excel_file = '/var/www/html/'+ bot_name +'_mkt_data.xlsx'
    position_file = '/var/www/html/'+ bot_name +'_position.json'
    filename = '/var/www/html/'+ bot_name +'_signals.csv'

pairs = ['BTC/USDT']
pairs = ['ADA/USDT','AION/USDT','ALGO/USDT','ANKR/USDT','ARPA/USDT','ATOM/USDT','BAND/USDT','BAT/USDT',
         'BCH/USDT','BEAM/USDT','BEAR/USDT','BNB/USDT','BNT/USDT','BSV/USDT','BTC/USDT',
         'BTCUP/USDT','BTS/USDT','BTT/USDT','BULL/USDT','BUSD/USDT','CELR/USDT','CHR/USDT',
         'CHZ/USDT','COCOS/USDT','COS/USDT','COTI/USDT','CTSI/USDT','CTXC/USDT','CVC/USDT',
         'DASH/USDT','DATA/USDT','DENT/USDT','DOCK/USDT','DOGE/USDT','DREP/USDT','DUSK/USDT',
         'ENJ/USDT','EOS/USDT','ERD/USDT','ETC/USDT','ETH/USDT','EUR/USDT','FET/USDT',
         'FTM/USDT','FTT/USDT','FUN/USDT','GTO/USDT','HBAR/USDT','HC/USDT','HIVE/USDT',
         'HOT/USDT','ICX/USDT','IOST/USDT','IOTA/USDT','IOTX/USDT','KAVA/USDT','KEY/USDT',
         'LINK/USDT','LSK/USDT','LTC/USDT','LTO/USDT','MATIC/USDT','MBL/USDT','MCO/USDT',
         'MFT/USDT','MITH/USDT','MTL/USDT','NANO/USDT','NEO/USDT','NKN/USDT','NPXS/USDT',
         'NULS/USDT','OGN/USDT','OMG/USDT','ONE/USDT','ONG/USDT','ONT/USDT','PAX/USDT','PERL/USDT',
         'QTUM/USDT','REN/USDT','RLC/USDT','RVN/USDT','STORM/USDT','STPT/USDT','STRAT/USDT','STX/USDT',
         'TCT/USDT','TFUEL/USDT','THETA/USDT','TOMO/USDT','TROY/USDT','TRX/USDT','TUSD/USDT',
         'USDC/USDT','USDS/USDT','USDSB/USDT','VEN/USDT','VET/USDT','VITE/USDT','WAN/USDT',
         'WAVES/USDT','WIN/USDT','WRX/USDT','WTC/USDT','XLM/USDT','XMR/USDT','XRP/USDT',
         'XTZ/USDT','XZC/USDT','ZEC/USDT','ZIL/USDT','ZRX/USDT'
]
pairs = ['BTS/USDT','DASH/USDT','DATA/USDT','DENT/USDT','DOCK/USDT','STORM/USDT','DREP/USDT','FTT/USDT',
         'TROY/USDT','FTM/USDT','THETA/USDT','MCO/USDT','BEAM/USDT','OMG/USDT','QTUM/USDT','IOST/USDT',
         'RVN/USDT','OGN/USDT','ALGO/USDT','WRX/USDT','ICX/USDT','XMR/USDT','AION/USDT','ONT/USDT','ZEC/USDT',
         'HC/USDT','XZC/USDT','VET/USDT','ADA/USDT','MATIC/USDT','ATOM/USDT']

exchanges = loadExchanges()

writer = pd.ExcelWriter('arb_search.xlsx')

column_list =['pair','min_stale','signal','st_dev','price','fv','bid','ask','r2','beta','trade']
df_output = pd.DataFrame(columns=column_list)

graph = False
output_file = True

for e in exchanges:  
    for pair in pairs:
        BTC_1d_ohlcv = e.fetch_ohlcv ('BTC/USDT', '1d')   
        df_BTC_1d_ohlcv = pd.DataFrame.from_records(BTC_1d_ohlcv, columns = ['timestamp' , 'open', 'high','low','close','volume'])
        df_BTC_1d_ohlcv['trade_time'] = df_BTC_1d_ohlcv.apply(lambda x: get_time(x['timestamp']), axis=1)
        df_BTC_1d_ohlcv.to_excel(writer,'BTC_1d')

        BTC_1m_ohlcv = e.fetch_ohlcv ('BTC/USDT', '1m')   
        df_BTC_1m_ohlcv = pd.DataFrame.from_records(BTC_1m_ohlcv, columns = ['timestamp' , 'open', 'high','low','close','volume'])
        df_BTC_1m_ohlcv['trade_time'] = df_BTC_1m_ohlcv.apply(lambda x: get_time(x['timestamp']), axis=1)
        df_BTC_1m_ohlcv.to_excel(writer,'BTC_1m')
        
        #trade data
        trades = e.fetch_trades(pair)
        df_trades = pd.DataFrame.from_records(trades, columns = ['amount' , 'cost', 'price','side','timestamp','id','symbol']) 
        df_trades['trade_time'] = df_trades.apply(lambda x: get_time(x['timestamp']), axis=1)
        df_trades['trade_time'] = pd.to_datetime(df_trades['trade_time'])
        df_trades['time_gap'] = (df_trades['trade_time']-df_trades['trade_time'].shift()).fillna(0)
        df_trades.to_excel(writer,pair.replace('/USDT','') + '_trades')
        df_trades['trade_time_min'] = df_trades['trade_time'].dt.strftime('%d %b %Y %H:%M:00')
        
        orders = e.fetchOrderBook(pair)
        
        bid = orders['bids'][0][0]
        ask = orders['asks'][0][0]
        
        st_dev = df_trades['price'].to_numpy().std()
        price = df_trades['price'].tail(1).to_numpy()[0]
        
        #last trade time
        last_trade_min = df_trades['trade_time'].dt.strftime('%d %b %Y %H:%M:00').tail(1).to_numpy()[0]
        last_trade = df_trades['trade_time'].tail(1).to_numpy()[0]
        current = np.datetime64(datetime.datetime.now())
        time_delta = (current - last_trade)      
        a = np.timedelta64(time_delta,'ns')       
        min_stale = a.astype('timedelta64[m]').astype(int)
        
        #daily bars
        _1d_ohlcv = e.fetch_ohlcv (pair, '1d')   
        df_1d_ohlcv = pd.DataFrame.from_records(_1d_ohlcv, columns = ['timestamp' , 'open', 'high','low','close','volume'])
        df_1d_ohlcv['trade_time'] = df_1d_ohlcv.apply(lambda x: get_time(x['timestamp']), axis=1)
        df_1d_ohlcv['volume_USD'] = df_1d_ohlcv['close'] * df_1d_ohlcv['volume'] 
        df_1d_ohlcv.to_excel(writer,pair.replace('/USDT','') + '_1d')
         
        #minute bars
        _1m_ohlcv = e.fetch_ohlcv (pair, '1m')   
        df_1m_ohlcv = pd.DataFrame.from_records(_1m_ohlcv, columns = ['timestamp' , 'open', 'high','low','close','volume'])
        df_1m_ohlcv['trade_time'] = df_1m_ohlcv.apply(lambda x: get_time(x['timestamp']), axis=1)
        df_1m_ohlcv['volume_USD'] = df_1m_ohlcv['close'] * df_1m_ohlcv['volume'] 
        df_1m_ohlcv.to_excel(writer,pair.replace('/USDT','') + '_1m')

        #join 1m bars
        ARB_1m_ohlcv = df_BTC_1m_ohlcv.join(df_1m_ohlcv.set_index('timestamp'), on='timestamp', how='left', lsuffix='_BTC', rsuffix='_' +pair)

        df_last_trade = ARB_1m_ohlcv[ARB_1m_ohlcv['trade_time_BTC'] == last_trade_min]
        df_last_btc = ARB_1m_ohlcv.tail(1)
        
        ARB_1d_ohlcv = df_BTC_1d_ohlcv.join(df_1d_ohlcv.set_index('timestamp'), on='timestamp', how='left', lsuffix='_BTC', rsuffix='_' +pair)
        df_tmp = ARB_1d_ohlcv[['trade_time_BTC','close_BTC','close_' + pair]]
        df_tmp = df_tmp[['close_BTC','close_' + pair]].pct_change().dropna()
        df_tmp = df_tmp.rename(columns={"close_BTC": "X", "close_" + pair: "Y"})
        result = sm.ols(formula="Y ~ X", data=df_tmp).fit()
        r2 = result.rsquared
        b = result.params[1]
        btc_move = df_last_btc['close_BTC'].to_numpy()[0] / df_last_trade['close_BTC'].to_numpy()[0] -1
        
        fv = price * (1+btc_move)
        
        if fv < bid:
            trade = 'sell'
            sig = (bid - fv)/bid
        elif fv > ask:
            trade = 'buy'
            sig = (fv - ask)/ask
        else:
            trade = 'neutral'
            sig = 0

        output_dict = {}
        output_dict['pair'] = pair
        output_dict['min_stale'] = min_stale
        output_dict['signal'] = f"{sig:.2%}"
        output_dict['st_dev'] = st_dev
        output_dict['price'] = price
        output_dict['fv'] = fv        
        output_dict['bid'] = bid
        output_dict['ask'] = ask
        output_dict['r2'] = r2
        output_dict['beta'] = b
        output_dict['trade'] = trade
        
        df_output = df_output.append(output_dict, ignore_index=True)

        if graph == True:
            df_graph = ARB_1m_ohlcv[['trade_time_BTC','close_BTC','close_' + pair,'volume_' + pair]].tail(min_stale+60)
            row_indexes = df_graph[df_graph['trade_time_BTC'] >= last_trade_min].index
            BTC_start = df_graph[df_graph['trade_time_BTC'] == last_trade_min].to_numpy()[0][1]
            df_graph['est_fair_value'] = df_graph.loc[row_indexes,]['close_' +pair]* (df_graph['close_BTC'] / BTC_start)
            row_indexes1 = df_graph[df_graph['trade_time_BTC'] > last_trade_min].index
            df_graph.loc[row_indexes1,['close_' +pair]] = np.nan
            df_graph['trade_time_BTC'] >= last_trade_min
            fig, axs = plt.subplots(nrows=2, figsize=(10, 5),sharex=True)
            axs[0].plot(df_graph['trade_time_BTC'],df_graph['close_' +pair],'-g', label=pair)
            axs[0].plot(df_graph['trade_time_BTC'],df_graph['est_fair_value'],'--g', label='Extraploate with BTC')
            axs[0].legend(loc="upper left")
            axs[1].plot(df_graph['trade_time_BTC'],df_graph['volume_' +pair],'-y', label='Volume USD')
            axs[1].legend(loc="upper left")
            plt.show()
        
        if output_file == True:
            file_exists = os.path.isfile(filename)
            file1 = open(filename,"a")
            
            if not file_exists:
                file1.writelines('timedate,pair,min_stale,signal,st_dev,price,fv,bid,ask,r2,beta,trade'+ "\n")

            x = datetime.datetime.now()
            datestr = str(x.strftime('%Y/%m/%d %H:%M:%S'))
            
            tmpstr = ''
            for o in output_dict:
                tmpstr+=str(output_dict[o])
                tmpstr+=','
            tmpstr = tmpstr[:-1:]
            
            file1.writelines(datestr + ',' + tmpstr + "\n" )
            file1.close()

writer.save()