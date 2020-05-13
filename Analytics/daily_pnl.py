import pandas as pd
import requests
from pandas.compat import StringIO
import datetime

def get_analysis_file(symbol='AAPL.US', api_token="5cdbaa3d950687.20170057", session=None):
    if session is None:
        session = requests.Session()
        url = 'https://eodhistoricaldata.com/api/eod/%s' % symbol
        params = {'api_token': api_token}
        r = session.get(url, params=params)
        if r.status_code == requests.codes.ok:
            df = pd.read_csv(StringIO(r.text), skipfooter=1, parse_dates=[0], index_col=0)
        return df
    else:
        print(r.status_code)
        raise Exception(r.status_code, r.reason, url)

def date_generator(days):
    date_list = []
    base = datetime.date.today()
    end = base + datetime.timedelta(days=-1)
    start  = base + datetime.timedelta(days=-days)
    delta = datetime.timedelta(days=1)
    base = start
    while(end>base):
        base = base+delta
        date_list.append(base.strftime("%d-%m-%Y"))
    return date_list

date_list = date_generator(50)
algo_list = ['ext_IOTA','ext_ADA','sol','dep','mac','osc','ext_DASH','rsi']
results = {}

for a in algo_list:
    first_run = True
    for d in date_list:
        session = requests.Session()
        url = 'http://qctb.tech/archive/'+ a + '_signals'+ str(d) +'.csv'
        #print('get' + url)
        r= session.get(url)
        if first_run:
            df = pd.read_csv(StringIO(r.text), skipfooter=1, parse_dates=[0], index_col=0)
            first_run = False
        else:
            df = df.append(pd.read_csv(StringIO(r.text), skipfooter=1, parse_dates=[0], index_col=0))
    df.reset_index(inplace= True)   
    df['date'] = df['timedate'].dt.date
    df_pnl = df[['date','Trade_PnL']]
    df_pnl['Trade_PnL'] = df_pnl['Trade_PnL'].str.replace('%', '')
    df_pnl['Trade_PnL'] = df_pnl['Trade_PnL'].astype(float)
    df_pnl = df_pnl.groupby("date").sum()
    df_pnl['Trade_PnL_hist'] = df_pnl['Trade_PnL'].cumsum()
    df_pnl[['Trade_PnL','Trade_PnL_hist']].plot(title = a)