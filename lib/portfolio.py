__author__ = 'jph'

from math import floor

from lib.events import OrderEvent


class Portfolio(object):
    """
    Interface between Strategy signals and Orders - keeps track of positions and generates orders
    """

    def __init__(self, queue):
        self.queue = queue
        self.capital = 0
        self.positions = {}
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

    def get_signal(self, event):
        """
        generates orders based on a signal event
        """
        side = event.side
        leverage = event.leverage
        symbol = event.symbol
        limit = event.limit
        targetsize = leverage * self.netliq / self.positions[symbol]['price']
        currentsize = self.positions[symbol]['shares']
        ordersize = targetsize - currentsize if side == "BUY" else targetsize + currentsize
        ordersize = floor(ordersize)
        type = "MKT" if limit is None else "LMT"
        order = OrderEvent(symbol, side, type, ordersize, limit=limit)
        self.queue.put(order)

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