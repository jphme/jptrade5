__author__ = 'jph'

from math import floor
import threading

from lib.events import OrderEvent, ErrorEvent, SignalEvent


class Portfolio(object):
    """
    Interface between Strategy signals and Orders - keeps track of positions and generates orders
    """

    def __init__(self, queue):
        self.queue = queue
        self.capital = 0
        self.positions = {'SPY': {'price': 0, 'shares': 0}}
        self.updated = 0

    def get_signal(self, event):
        """
        generates orders based on a signal event
        """
        raise NotImplementedError

    def get_fill(self, event):
        """
        updates portfolio based on fill events
        """
        raise NotImplementedError

    def close_signal(self, event):
        side = "BUY" if event.side == "SELL" else "SELL"
        leverage = event.leverage
        symbol = event.symbol
        trigger = event.trigger
        timetillclose = event.duration
        parent = event.id
        close_event = SignalEvent(side, leverage, limit=None, trigger=trigger, symbol=symbol, duration=None,
                                  parent=parent)

        def place_close_event(event):
            self.queue.put(event)

        t = threading.Timer(timetillclose * 60, place_close_event, args=[close_event])
        t.start()
        return t


class SimPortfolio(Portfolio):
    """
    Simulated Portfolio
    takes kwgargs:
    capital - starting capital, float
    startportfolio - dict, starting positions
    """

    def __init__(self, queue, capital=100000.0, startportfolio=None):
        super(SimPortfolio, self).__init__(queue=queue)
        self.capital = capital
        if startportfolio is not None:
            self.positions = startportfolio
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['shares'] for x in self.positions))
        self.signals = {}

    def get_signal(self, event):
        """
        generates orders based on a signal event
        """
        side = event.side
        leverage = event.leverage
        symbol = event.symbol
        limit = event.limit
        trigger = event.trigger
        signalid = event.id
        if side == "BUY" or side == "SELL":
            targetsize = leverage * self.netliq / self.positions[symbol]['price']
            ordersize = floor(targetsize)
            type = "MKT" if limit is None else "LMT"
            order = OrderEvent(symbol, side, type, ordersize, limit=limit, trigger=trigger, signalid=signalid)
            self.queue.put(order)
            if event.duration is not None:
                self.close_signal(event)
        else:
            self.queue.put(ErrorEvent('Signal not Buy or Sell'))

    def update_portfolio(self, datahandler):
        spy_price = round(datahandler.get_latest_data()['close'][0], 2)
        self.positions['SPY']['price'] = spy_price
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['shares'] for x in self.positions))

    def get_fill(self, event):
        """
        updates portfolio based on fill events
        """
        side = event.side
        symbol = event.symbol
        quantity = event.quantity if side == "BUY" else -1 * event.quantity
        price = event.price
        commission = event.total_cost

        if symbol in self.positions:
            self.positions[symbol]['shares'] += quantity
            self.positions[symbol]['price'] = price
        else:
            self.positions[symbol] = {'shares': quantity, 'price': price}

        self.capital -= price * quantity + commission
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['shares'] for x in self.positions))