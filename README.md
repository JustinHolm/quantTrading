# QuantTrading

Back End:

This solution is made up of a backend written in Python.  Here the market data is gather and analytics libraries are run to calculate signals.  After a trading signal is calculated the execution logic is run and trades are send to the exchange.  Details of the signal are logged into a CSV file and additional position details are stored in a JSON.  Both of these files are saved on the webserver for presentation to the user.

- Trading Algorithms: Self contained Python Scripts
1. Load Market Data: 
2. Signal Generation: 
3. Trade Exection: Currently only market orders to be neutral, long or short.

Front End:

This is an HTML5/Javascript website which provides position details and trade executions to the user.  Dygraph is used for the graphs.

