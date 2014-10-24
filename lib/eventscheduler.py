__author__ = 'jph'
import time
import threading
import datetime as dt
import copy

import pytz

from lib.events import SignalEvent, ErrorEvent, StartStopEvent


class EventScheduler(object):
    """
    Takes an event queue and datahandler,strategy,portfolio, trader and execution
    objects and processes all events on the queue
    """

    def __init__(self, queue, datahandler, strategy, portfolio, trader, verbose=True, inputqueue=None):
        self.queue = queue
        if inputqueue is None:
            self.inputqueue = self.queue
        else:
            self.inputqueue = inputqueue
        self.datahandler = datahandler
        self.strategy = strategy
        self.portfolio = portfolio
        self.trader = trader
        self.verbose = verbose
        self.counter = 0
        self.scheduled_events = {}
        self.filled = []
        #self.scheduled_events=[(2407416654, ErrorEvent("Error, End of scheduled Events reached"))]
        #self.scheduling_thread=None

    def schedule_events(self, event):
        if event.cancelall == True:
            self.scheduled_events = {}
        elif event.cancelid is not None:
            self.scheduled_events.pop(event.cancelid, None)
        elif (event.offset is not None) and (event.childevent is not None):
            self.scheduled_events[event.id] = {'counter': self.counter + event.offset, 'childevent': event.childevent,
                                               'parent': event.parent}
        else:
            self.inputqueue.put(ErrorEvent(msg='Error - wrong scheduling arguments'))

    def check_scheduled_events(self):
        scheduled_events_snapshot = copy.deepcopy(self.scheduled_events)
        for id, scheduled_event in scheduled_events_snapshot.iteritems():
            if scheduled_event['counter'] <= self.counter:
                if (scheduled_event['parent'] is None) or (scheduled_event['parent'] in self.filled):
                    scheduled_event['childevent'].timestamp = dt.datetime.today()
                    self.inputqueue.put(scheduled_event['childevent'])
                self.scheduled_events.pop(id, None)

    def process_events(self):
        while True:
            event = self.queue.get()
            if self.verbose:
                print event
            if event.type == "MARKET":
                self.counter += 1
                self.check_scheduled_events()
                self.additional_market_actions()
                self.strategy.calculate_signals()
            elif event.type == "SIGNAL":
                self.portfolio.get_signal(event)
            elif event.type == "ORDER":
                self.trader.execute_order(event)
            elif event.type == "FILL":
                self.filled.append(event.signalid)
                self.portfolio.get_fill(event)
            elif event.type == "SCHEDULE":
                self.schedule_events(event)

    def additional_market_actions(self):
        pass


class BacktestScheduler(EventScheduler):
    def __init__(self, queue, datahandler, strategy, portfolio, trader, verbose=True, inputqueue=None):
        super(BacktestScheduler, self).__init__(queue, datahandler, strategy, portfolio, trader, verbose=verbose,
                                                inputqueue=inputqueue)
        self.old_signal = None

    def additional_market_actions(self):
        self.trader.update_prices(self.datahandler)
        self.portfolio.update_portfolio(self.datahandler)


class IBScheduler(EventScheduler):
    def __init__(self, queue, datahandler, strategy, portfolio, trader, verbose=True, inputqueue=None):
        super(IBScheduler, self).__init__(queue, datahandler, strategy, portfolio, trader, verbose=verbose,
                                          inputqueue=inputqueue)
        self.old_signal = None

    def mainloop(self):
        est = pytz.timezone('US/Eastern')
        cet = pytz.timezone('Europe/Berlin')
        print "Waiting..."

        def heartbeat():
            updated = False
            try: #TODO debug raus
                while True:
                    jetzt = cet.localize(dt.datetime.today()).astimezone(est)
                    week = jetzt.weekday() not in (5, 6)
                    market_open = (jetzt.hour >= 10) | ((jetzt.hour == 9) & (jetzt.minute >= 31))
                    market_close = jetzt.hour <= 15
                    takt = jetzt.second == 0
                    if week & market_open & market_close:
                        if (jetzt.hour == 15) & (jetzt.minute >= 59):
                            print jetzt
                            self.queue.put(SignalEvent("CLOSE", 1))
                            updated = False
                            self.scheduled_events = {}
                            self.filled = []
                            time.sleep(61)
                        elif (jetzt.hour == 9) & (jetzt.minute == 31) & (updated == False):
                            print jetzt
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
            except:
                import sys

                msg = ", ".join([str(x) for x in sys.exc_info()])
                print msg
                self.queue.put(ErrorEvent(msg=msg))
                self.queue.put(StartStopEvent())
                raise


        t = threading.Thread(target=heartbeat, name="mainloop_thread")
        t.daemon = True
        t.start()
        #heartbeat()