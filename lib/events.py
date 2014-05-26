__author__ = 'Jan Philipp Harries'

"""
events.py provides the following Events which are used for communication inside the main loop

MarketDataEvent
SignalEvent
OrderEvent
FillEvent
"""

import datetime as dt


class Event(object):
    """
    Provides interfaces for all events
    """

    def __init__(self):
        self.timestamp = dt.datetime.today()
        self.logged = False


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

    def __init__(self, side, leverage):
        """
        Parameters:
        side - long or short
        leverage - leverage for respective side
        """
        super(SignalEvent, self).__init__()
        self.type = 'SIGNAL'
        self.side = side
        self.leverage = leverage


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
        self.direction = side
        self.other_args = kwargs


class FillEvent(Event):
    """
    Returns Filled Orders for Logging/Portfolio
    """

    def __init__(self, timestamp, symbol, exchange, quantity,
                 side, total_cost, orderid):
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


if __name__ == "__main__":
    test = OrderEvent("spy", "buy", 100, "buy", blablabla=215235)
    print test.timestamp
    print test.type
    print test.other_args