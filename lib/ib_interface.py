__author__ = 'jph'

#TODO: create class that servers as async IB interface for required tasks

import time
import datetime as dt

from ib.opt import ibConnection
from ib.ext import Contract


class IBInterface(object):
    def __init__(self):
        self.con = ibConnection(host='localhost', port=7499, clientId=1)
        #self.con.enableLogging()
        self.con.register(self.account_handler, 'UpdateAccountValue')
        self.con.register(self.portfolio_handler, 'UpdatePortfolio')
        self.con.register(self.tick_handler, 'TickSize', 'TickPrice')
        self.con.register(self.string_handler, 'TickString')
        self.con.register(self.error_handler, 'Error')

        self.prices = {}
        self.request_id = 1
        self.accounts = {}

    def connect(self):
        self.con.connect()
        self.con.reqAccountUpdates(True, '')

    def disconnect(self):
        self.con.disconnect()

    def reqmktdata(self, symbol, type="STK", exch="SMART", generic="", snapshot=True, **kwargs):
        """
        Requests marketdata and returns a request ID
        symbol: symbol as string
        type: "STK" for Stocks, FUT for Futures
        exch: "SMART" for Stocks, "CME"/"GLOBEX" for futures
        generic: n/a
        snapshot: requests snapshot or continuous data stream
        """

        contract = Contract.Contract()
        contract.m_symbol = symbol
        contract.m_secType = type
        contract.m_exchange = exch
        contract.m_currency = "USD"
        self.prices[self.request_id] = {}
        self.con.reqMktData(self.request_id, contract, generic, snapshot)
        self.request_id += 1
        return self.request_id - 1

    def tick_handler(self, msg):
        if msg.field == 1:
            self.prices[msg.tickerId]['bidprice'] = msg.price
        elif msg.field == 2:
            self.prices[msg.tickerId]['askprice'] = msg.price
        elif msg.field == 4:
            self.prices[msg.tickerId]['last'] = msg.price
        elif msg.field == 6:
            self.prices[msg.tickerId]['high'] = msg.price
        elif msg.field == 7:
            self.prices[msg.tickerId]['low'] = msg.price
        elif msg.field == 14:
            self.prices[msg.tickerId]['open'] = msg.price
        elif msg.field == 0:
            self.prices[msg.tickerId]['bidsize'] = msg.size
        elif msg.field == 3:
            self.prices[msg.tickerId]['asksize'] = msg.size
        elif msg.field == 5:
            self.prices[msg.tickerId]['lastsize'] = msg.size
        elif msg.field == 8:
            self.prices[msg.tickerId]['volume'] = msg.size

    def string_handler(self, msg):
        if msg.tickType == 45:
            self.prices[msg.tickerId]['timestamp'] = dt.datetime.fromtimestamp(int(msg.value))

    def error_handler(self, msg):
        print msg

    def execution_handler(self, msg):
        pass

    def account_handler(self, msg):
        if msg.accountName not in self.accounts:
            self.accounts[msg.accountName] = {'portfolio': {}}
        if msg.key == 'CashBalance':
            self.accounts[msg.accountName]['cash'] = msg.value
        elif msg.key == "MaintMarginReq":
            self.accounts[msg.accountName]['margin'] = msg.value
        elif msg.key == "NetLiquidation":
            self.accounts[msg.accountName]['netliq'] = msg.value
        elif msg.key == "EquityWithLoanValue":
            self.accounts[msg.accountName]['equity'] = msg.value
        elif msg.key == "PreviousDayEquityWithLoanValue":
            self.accounts[msg.accountName]['prevequity'] = msg.value

    def portfolio_handler(self, msg):
        symbol = msg.contract.m_symbol
        if msg.accountName not in self.accounts:
            self.accounts[msg.accountName] = {'portfolio': {}}
        if symbol not in self.accounts[msg.accountName]['portfolio']:
            self.accounts[msg.accountName]['portfolio'][symbol] = {}
        self.accounts[msg.accountName]['portfolio'][symbol]['position'] = msg.position
        self.accounts[msg.accountName]['portfolio'][symbol]['price'] = msg.marketPrice
        self.accounts[msg.accountName]['portfolio'][symbol]['value'] = msg.marketValue
        self.accounts[msg.accountName]['portfolio'][symbol]['cost'] = msg.averageCost
        self.accounts[msg.accountName]['portfolio'][symbol]['unrealpnl'] = msg.unrealizedPNL
        self.accounts[msg.accountName]['portfolio'][symbol]['realpnl'] = msg.realizedPNL


if __name__ == '__main__':
    #TODO only for testing

    ib = IBInterface()
    ib.connect()
    time.sleep(3)
    a = time.time()
    id = ib.reqmktdata('SPY', snapshot=True)
    while not ib.prices[id]:
        pass
    b = time.time()
    time.sleep(1)
    print ib.prices[id]
    print b - a
    time.sleep(1)
    from util import synch

    @synch(ib.prices, required=('last', 'open', 'high', 'low'))
    def synch_mkt_data(*args, **kwargs):
        return ib.reqmktdata(*args, **kwargs)

    a = time.time()
    print synch_mkt_data('SPY', snapshot=True)
    b = time.time()
    print b - a

    @synch(ib.prices)
    def synch_mkt_data(*args, **kwargs):
        return ib.reqmktdata(*args, **kwargs)

    a = time.time()
    print synch_mkt_data('SPY', snapshot=True)
    b = time.time()
    print b - a

    print ib.accounts

    #pdb.set_trace()