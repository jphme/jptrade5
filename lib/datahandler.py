__author__ = 'jph'

import pickle
from math import floor

import pytz
import pandas as pd

from events import MarketDataEvent, StartStopEvent, ErrorEvent


class DataHandler(object):
    """
    Basic Data  Handler structure to provide an interface for accessing live or simulated market data
    """
    def __init__(self, queue):
        self.queue = queue

    def get_latest_data(self, symbol, n=1):
        """
        get latest marketdata for symbol and create MarketEvent if new data available
        """
        raise NotImplementedError


    def read_data(self, workfile='workfile_tmp.p'):
        """
        Initializes database from workfile
        Standard pickle
        """
        self.data = pickle.load(open(workfile, 'rb'))


class BacktestDataHandler(DataHandler):
    """
    Basic Data  Handler structure to provide an interface for accessing live or simulated market data
    """

    def __init__(self, queue, workfile='workfile_tmp.p', split=0.1):
        super(BacktestDataHandler, self).__init__(queue)
        self.read_data(workfile)
        splitno = int(floor(len(self.data) * (1 - split)))
        self.btest = self.data[splitno:]
        self.data = self.data[:splitno]

    def get_latest_data(self, symbol='SPY', n=1):
        """
        get latest marketdata for symbol and create MarketEvent if new data available
        """
        return self.data.ix[-n - 1:-1]

    def get_execution_data(self, symbol='SPY'):
        """
        get latest bar - only for backtest execution simulation
        """
        return self.data.ix[-1]

    def data_event(self):
        try:
            new_bar = self.btest.ix[0]
            self.btest = self.btest.ix[1:]
            self.data = self.data.append(new_bar)
            self.queue.put(MarketDataEvent())
        except IndexError:
            self.queue.put(StartStopEvent())

    def read_data(self, workfile='workfile_tmp.p'):
        """
        Initializes database from workfile
        Standard pickle
        """
        self.data = pickle.load(open(workfile, 'rb'))


class IBDataHandler(DataHandler):
    """
    Basic Data  Handler structure to provide an interface for accessing live or simulated market data
    """

    def __init__(self, queue, workfile='workfile_tmp.p', ibcon=None):
        super(IBDataHandler, self).__init__(queue)
        self.read_data(workfile)
        self.ibcon = ibcon

    def get_latest_data(self, symbol='SPY', n=1):
        return self.data.ix[-n:]

    def data_event(self):
        newdata = self.ibcon.new_bars()
        try:
            if newdata.index[-1] > self.data.index[-1]:
                self.data = self.data.combine_first(newdata)
                self.queue.put(MarketDataEvent())
        except IndexError:
            if len(self.data) == 0:
                self.data = newdata
                self.queue.put(MarketDataEvent())
            else:
                self.queue.put(ErrorEvent(msg='Index out of Bounds, data refresh failed...'))

    def read_data(self, workfile=None):
        """
        Initializes database from workfile
        Standard pickle
        """
        est = pytz.timezone('US/Eastern')
        cet = pytz.timezone('Europe/Berlin')
        if workfile is not None:
            self.data = pickle.load(open(workfile, 'rb'))
            self.data = self.data.tz_localize(est)
        else:
            self.data = pd.DataFrame()

    def refresh_data(self):
        newdata = self.ibcon.new_bars(freq='1m', current_index=self.data.index)
        self.data = self.data.combine_first(newdata)