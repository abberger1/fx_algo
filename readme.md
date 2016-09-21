# FX Stochastic Event-Based Trading Algorithm

all packages used (except talib) are included in the Anaconda distribution of Python 3.5:
  - https://docs.continuum.io/anaconda/
  - 
see below for how to install ta-lib for the technical analysis component of this module

install:
    git clone https://github.com/abberger1/fx_stoch_event_algo
    pip install .
  
dependencies:
  pandas
    - pip
  numpy
    - pip
  statsmodels
    - pip 
  ta-lib:
    - if you do not have this package already, you will need to build the underlying c from source:
    - http://prdownloads.sourceforge.net/ta-lib/
    - (untar and cd, ./configure, then make && sudo make install)
    - then you can pip install TA-Lib or git clone https://github.com/mrjbq7/ta-lib to install
