__author__ = 'Jan Philipp Harries'

"""
events.py provides the following Events which are used for communication inside the main loop

MarketDataEvent
SignalEvent
OrderEvent
FillEvent
"""

import datetime as dt
import json


class Event(object):
    """
    Provides interfaces for all events
    """

    def __init__(self):
        self.timestamp = dt.datetime.today()
        self.logged = False
        self.type = None

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'event': self.type}) + "\n"


class StartStopEvent(Event):
    """
    Starts/Stops asynchronous queue querying
    """

    def __init__(self):
        super(StartStopEvent, self).__init__()
        self.type = 'STOP'


class MarketDataEvent(Event):
    """
    Signals incoming new market data
    """

    def __init__(self):
        super(MarketDataEvent, self).__init__()
        self.type = 'MARKET'


class SignalEvent(Event):
    """
    Sends Signal from Strategy to Portfolio object
    """

    def __init__(self, side, leverage, limit=None, symbol="SPY"):
        """
        Parameters:
        side - long or short
        leverage - leverage for respective side
        """
        super(SignalEvent, self).__init__()
        self.type = 'SIGNAL'
        self.side = side
        self.leverage = leverage
        self.symbol = symbol
        self.limit = limit

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'event': "SIGNAL", 'symbol': self.symbol,
                           'side': self.side, 'leverage': self.leverage, 'limit': self.limit}) + "\n"


class OrderEvent(Event):
    """
    Sends Order from Portfolio object to Execution System
    """

    def __init__(self, symbol, side, order_type, quantity, **kwargs):
        """
        Parameters:
        symbol
        side - "BUY" or "SELL"
        order_type
        quantity
        other order options as kwargs
        """
        super(OrderEvent, self).__init__()
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.side = side
        self.other_args = kwargs

    def __str__(self):
        #TODO include other kwargs
        return json.dumps({'timestamp': str(self.timestamp), 'event': "ORDER", 'symbol': self.symbol,
                           'order_type': self.order_type, 'quantity': self.quantity, 'side': self.side}) + "\n"


class FillEvent(Event):
    """
    Returns Filled Orders for Logging/Portfolio
    """

    def __init__(self, timestamp, symbol, exchange, quantity,
                 side, total_cost, orderid, price):
        """
        Parameters:
        timestamp - order_timestamp (timestamp is event timestamp)
        symbol
        exchange
        quantity
        side
        total_cost
        orderid
        """
        super(FillEvent, self).__init__()
        self.type = 'FILL'
        self.order_timestamp = timestamp
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.side = side
        self.total_cost = total_cost
        self.orderid = orderid
        self.price = price

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'event': "FILL", 'symbol': self.symbol,
                           'order_timestamp': str(self.order_timestamp), 'quantity': self.quantity,
                           'side': self.side, 'total_cost': self.total_cost, 'exchange': self.exchange,
                           'orderid': self.orderid, 'price': self.price}) + "\n"


if __name__ == "__main__":
    test = OrderEvent("spy", "buy", 100, "buy", blablabla=215235)
    print test.timestamp
    print test.type
    print test.other_args