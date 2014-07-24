__author__ = 'jph'


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