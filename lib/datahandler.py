__author__ = 'jph'

import pickle


class DataHandler(object):
    """
    Basic Data  Handler structure to provide an interface for accessing live or simulated market data
    """

    def __init__(self, queue):
        self.queue = queue

    def get_latest_data(self, symbol):
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
