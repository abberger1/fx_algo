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
  
    >> from oanda_api_fx.util import GetCandles
    >> candles = GetCandles(1250, 'EUR_USD', 'S5').request()
    >> candles.head()
                     volume   symbol     timestamp  closeMid    lowMid  \
time                                                                     
2016-09-21 13:53:25       1  EUR_USD  1.474484e+09  1.114395  1.114395   
2016-09-21 13:53:30       1  EUR_USD  1.474484e+09  1.114400  1.114400   
2016-09-21 13:53:35       3  EUR_USD  1.474484e+09  1.114420  1.114365   
2016-09-21 13:54:10       2  EUR_USD  1.474484e+09  1.114390  1.114385   
2016-09-21 13:54:15       1  EUR_USD  1.474484e+09  1.114405  1.114405   

                      highMid   openMid  
time                                     
2016-09-21 13:53:25  1.114395  1.114395  
2016-09-21 13:53:30  1.114400  1.114400  
2016-09-21 13:53:35  1.114420  1.114365  
2016-09-21 13:54:10  1.114390  1.114385  
2016-09-21 13:54:15  1.114405  1.114405
