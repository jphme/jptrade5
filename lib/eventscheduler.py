__author__ = 'jph'
import time
import threading
import datetime as dt
import pytz
from lib.events import SignalEvent


class EventScheduler(object):
    """
    Takes an event queue and datahandler,strategy,portfolio, trader and execution
    objects and processes all events on the queue
    """

    def __init__(self, queue, datahandler, strategy, portfolio, trader):
        self.queue = queue
        self.datahandler = datahandler
        self.strategy = strategy
        self.portfolio = portfolio
        self.trader = trader
        #self.scheduled_events=[(2407416654, ErrorEvent("Error, End of scheduled Events reached"))]
        #self.scheduling_thread=None

    def process_events(self):
        raise NotImplementedError


class BacktestScheduler(EventScheduler):
    def __init__(self, queue, datahandler, strategy, portfolio, trader, verbose=True):
        super(BacktestScheduler, self).__init__(queue, datahandler, strategy, portfolio, trader)
        self.old_signal = None
        self.verbose = verbose

    def process_events(self):
        while True:
            event = self.queue.get()
            if self.verbose:
                print event
            if event.type == "MARKET":
                self.trader.update_prices(self.datahandler)
                self.portfolio.update_portfolio(self.datahandler)
                self.strategy.calculate_signals()
            elif event.type == "SIGNAL":
                self.portfolio.get_signal(event)
            elif event.type == "ORDER":
                self.trader.execute_order(event)
            elif event.type == "FILL":
                self.portfolio.get_fill(event)


class IBScheduler(EventScheduler):
    def __init__(self, queue, datahandler, strategy, portfolio, trader, verbose=True):
        super(IBScheduler, self).__init__(queue, datahandler, strategy, portfolio, trader)
        self.old_signal = None
        self.verbose = verbose

    def process_events(self):
        while True:
            event = self.queue.get()
            if self.verbose:
                print event
            if event.type == "MARKET":
                self.strategy.calculate_signals()
            elif event.type == "SIGNAL":
                self.portfolio.get_signal(event)
            elif event.type == "ORDER":
                self.trader.execute_order(event)
            elif event.type == "FILL":
                self.portfolio.get_fill(event)

    def mainloop(self):
        est = pytz.timezone('US/Eastern')
        cet = pytz.timezone('Europe/Berlin')
        print "Waiting..."

        def heartbeat():
            while True:
                jetzt = cet.localize(dt.datetime.today()).astimezone(est)
                week = jetzt.weekday() not in (5, 6)
                market_open = (jetzt.hour >= 10) | ((jetzt.hour == 9) & (jetzt.minute >= 31))
                market_close = jetzt.hour <= 15
                takt = jetzt.second == 0
                updated = False
                if week & market_open & market_close:
                    if (jetzt.hour == 15) & (jetzt.minute >= 59):
                        self.queue.put(SignalEvent("CLOSE", 1))
                        updated = False
                        time.sleep(61)
                    elif (jetzt.hour == 9) & (jetzt.minute == 31) & (updated == False):
                        #self.datahandler.refresh_data()
                        updated = True
                        self.portfolio.update_portfolio()
                        time.sleep(5)
                    elif takt:
                        self.datahandler.data_event()
                        time.sleep(1)
                    else:
                        pass
                else:
                    pass
                time.sleep(0.1)

        t = threading.Thread(target=heartbeat, name="mainloop_thread")
        t.daemon = True
        t.start()
        #heartbeat()