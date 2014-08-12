__author__ = 'jph'

import pickle
from math import floor

from events import MarketDataEvent, StartStopEvent


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
        try:
            newdata = self.ibcon.new_bars()
            self.data = self.data.combine_first(newdata)
            self.queue.put(MarketDataEvent())
        except IndexError:
            self.queue.put(StartStopEvent())

    def read_data(self, workfile='workfile_tmp.p'):
        """
        Initializes database from workfile
        Standard pickle
        """
        self.data = pickle.load(open(workfile, 'rb'))

    def refresh_data(self):
        #TODO implement method for first time start every day or after crash - refresh workfile until now
        raise NotImplementedError