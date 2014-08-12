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
import uuid


class Event(object):
    """
    Provides interfaces for all events
    """

    def __init__(self):
        self.timestamp = dt.datetime.today()
        self.logged = False
        self.type = None
        self.id = uuid.uuid4().int % 10000000000

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'id': self.id, 'event': self.type})


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


class ErrorEvent(Event):
    """
    Signals incoming new market data
    """

    def __init__(self, msg="Error"):
        super(ErrorEvent, self).__init__()
        self.type = 'ERROR'
        self.msg = msg

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'id': self.id, 'event': self.type, 'msg': self.msg})


class SignalEvent(Event):
    """
    Sends Signal from Strategy to Portfolio object
    """

    def __init__(self, side, leverage, limit=None, trigger=None, symbol="SPY", duration=None, parent=None):
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
        self.trigger = trigger
        self.duration = duration
        self.parent = parent

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'id': self.id, 'event': "SIGNAL", 'symbol': self.symbol,
                           'side': self.side, 'leverage': self.leverage, 'limit': self.limit,
                           'trigger': self.trigger, 'duration': self.duration, 'parent': self.parent})


class OrderEvent(Event):
    """
    Sends Order from Portfolio object to Execution System
    """

    def __init__(self, symbol, side, order_type, quantity, limit=None, trigger=None, signalid=None, **kwargs):
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
        self.limit = limit
        self.trigger = trigger
        self.signalid = signalid
        self.other_args = kwargs

    def __str__(self):
        #TODO include other kwargs
        return json.dumps({'timestamp': str(self.timestamp), 'id': self.id, 'event': "ORDER", 'symbol': self.symbol,
                           'order_type': self.order_type, 'quantity': self.quantity, 'side': self.side,
                           'limit': self.limit, 'trigger': self.trigger, 'signalid': self.signalid})


class FillEvent(Event):
    """
    Returns Filled Orders for Logging/Portfolio
    """

    def __init__(self, timestamp, symbol, exchange, quantity,
                 side, total_cost, orderid, price, ordereventid=None):
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
        self.ordereventid = ordereventid

    def __str__(self):
        return json.dumps({'timestamp': str(self.timestamp), 'id': self.id, 'event': "FILL", 'symbol': self.symbol,
                           'order_timestamp': str(self.order_timestamp), 'quantity': self.quantity,
                           'side': self.side, 'total_cost': self.total_cost, 'exchange': self.exchange,
                           'orderid': self.orderid, 'price': self.price, 'ordereventid': self.ordereventid})


if __name__ == "__main__":
    test = OrderEvent("spy", "buy", 100, "buy", blablabla=215235)
    print test.timestamp
    print test.type
    print test.other_args