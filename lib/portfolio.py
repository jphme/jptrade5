__author__ = 'jph'

from math import floor
import threading

from lib.events import OrderEvent, ErrorEvent, SignalEvent


class Portfolio(object):
    """
    Interface between Strategy signals and Orders - keeps track of positions and generates orders
    """

    def __init__(self, queue, max_leverage=1):
        self.queue = queue
        self.capital = 0
        self.positions = {'SPY': {'price': 0, 'position': 0}}
        self.updated = 0
        self.netliq = 0
        self.max_leverage = max_leverage
        self.get_gesordersize('SPY')

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
        time_valid = event.time_valid
        if side == "BUY" or side == "SELL":
            targetsize = leverage * self.gesordersize
            ordersize = int(floor(targetsize))
            if side == "BUY" and self.positions[event.symbol]['position'] + ordersize > self.max_position:
                self.queue.put(ErrorEvent('Max leverage exceeded'))
            elif side == "SELL" and self.positions[event.symbol]['position'] - ordersize < -1 * self.max_position:
                self.queue.put(ErrorEvent('Max leverage exceeded'))
            else:
                type = "MKT" if limit is None else "LMT"
                order = OrderEvent(symbol, side, type, ordersize, limit=limit, trigger=trigger, signalid=signalid,
                                   time_valid=time_valid)
                self.queue.put(order)
                if event.duration is not None:
                    self.close_signal(event)
                    #TODO genau regeln fuer reihenfolge zu schliessender Positionen erarbeiten
        elif side == "CLOSE":
            if abs(self.positions[symbol]['position']) > 0:
                side = "SELL" if self.positions[symbol]['position'] > 0 else "BUY"
                ordersize = abs(self.positions[symbol]['position'])
                type = "MKT" if limit is None else "LMT"
                order = OrderEvent(symbol, side, type, ordersize, limit=limit, trigger=trigger, signalid=signalid,
                                   time_valid=time_valid)
                self.queue.put(order)
            else:
                self.queue.put(ErrorEvent('No positions open'))
        else:
            self.queue.put(ErrorEvent('Signal not Buy or Sell'))

    def get_gesordersize(self, symbol="SPY"):
        try:
            self.gesordersize = int(self.netliq / self.positions[symbol]['price'] * 0.95)
            self.max_position = int(self.max_leverage * self.gesordersize)
        except ZeroDivisionError:
            self.gesordersize = 0
            self.max_position = 0

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
            self.positions[symbol]['position'] += quantity
            self.positions[symbol]['price'] = price
        else:
            self.positions[symbol] = {'position': quantity, 'price': price}

        self.capital -= price * quantity + commission
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['position'] for x in self.positions))

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

    def __init__(self, queue, capital=1000000.0, startportfolio=None):
        super(SimPortfolio, self).__init__(queue=queue)
        self.capital = capital
        if startportfolio is not None:
            self.positions = startportfolio
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['position'] for x in self.positions))
        self.signals = {}

    def update_portfolio(self, datahandler):
        spy_price = round(datahandler.get_latest_data()['close'][0], 2)
        self.positions['SPY']['price'] = spy_price
        self.netliq = self.capital + sum(
            (self.positions[x]['price'] * self.positions[x]['position'] for x in self.positions))


class IBPortfolio(Portfolio):
    """
    IB Portfolio
    takes kwgargs:
    IBcon - IBComfort Instance, must be connected
    """

    def __init__(self, queue, ibcon):
        super(IBPortfolio, self).__init__(queue=queue)
        self.ibcon = ibcon
        self.update_portfolio()
        self.get_gesordersize('SPY')

    def update_portfolio(self, accountname='DU159389'):
        #TODO implement FA accounts and sum over all accounts
        self.positions = self.ibcon.accounts[accountname]['portfolio']
        self.netliq = self.ibcon.accounts[accountname]['netliq']
        self.capital = self.ibcon.accounts[accountname]['cash']
        if 'SPY' not in self.positions:
            self.positions['SPY'] = {'price': 0.0, 'position': 0}
        self.positions['SPY']['price'] = self.ibcon.getspy()['last']