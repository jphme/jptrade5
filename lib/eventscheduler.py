__author__ = 'jph'
import time
import threading


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

    def schedule_events(self, event, actiontime):
        #TODO remove if not necessary
        self.scheduled_events.append((actiontime, event))
        self.scheduled_events.sort(key=lambda x: x[0])
        if self.scheduling_thread is not None:
            self.scheduling_thread.kill()
        self.scheduling_thread = self.start_scheduling()

    def start_scheduling(self):
        #TODO remove if not necessary
        def query_events(events):
            while time.time() < events[0][0]:
                time.sleep(0.01)
            self.queue.put(events[0][1])
            events = events[1:]
            query_events(events)

        t = threading.Thread(target=query_events, name="scheduled_events_queue", args=(self.scheduled_events,))
        t.daemon = True
        t.start()
        return t


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

