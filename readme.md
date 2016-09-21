# FX Stochastic Event-Based Trading Algorithm

all packages used (except talib) are included in the Anaconda distribution of Python 3.5:
  - https://docs.continuum.io/anaconda/
  - 
see below for how to install ta-lib for the technical analysis component of this module

to install:

    git clone https://github.com/abberger1/fx_stoch_event_algo
    pip install .
  
dependencies:
  - pandas
    - pip
  - numpy
    - pip
  - statsmodels
    - pip 
  - ta-lib:
    - if you do not have this package already, you will need to build the underlying c from source:
    - http://prdownloads.sourceforge.net/ta-lib/
    - (untar and cd, ./configure, then make && sudo make install)
    - then you can pip install TA-Lib or git clone https://github.com/mrjbq7/ta-lib to install

examples:
  
    >> import matplotlib.pyplot as plt
    >> from oanda_api_fx.util import GetCandles
    >> candles = GetCandles(1250, 'EUR_USD', 'S5').request()
    >> candles['closeMid'].plot()
    >> plt.show()
    
    >> from oanda_api_fx.util import StreamPrices
    >> stream = StreamPrices('EUR_USD')
    >> stream.prices()
    
    >> from oanda_api_fx.util import Signals, OrderHandler
    >> tick = Signals(1250, 'EUR_USD', 900, 450).tick
    >> OrderHandler('EUR_USD', tick, 'BUY', 1000000).send_order()
    
    >> from oanda_api_fx.util import Positions
    >> position = Positions().checkPosition('EUR_USD')

