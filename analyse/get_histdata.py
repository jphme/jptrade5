__author__ = 'jph'

import time
import pickle
import datetime as dt

import lib.ib_interface


lastdate = dt.datetime(2014, 8, 21, 0, 0)
firstdate = dt.datetime(2014, 8, 20, 0, 0)

ib = lib.ib_interface.IBComfort(port=7499, clientId=12)  #TWS 7499/7496 , Gateway 4001
ib.connect()
time.sleep(5)

trades = ib.comf_reqhistdata(lastdate, firstdate, 'SPY', interval="2 D", resol="1 min", show="TRADES")
bid = ib.comf_reqhistdata(lastdate, firstdate, 'SPY', interval="2 D", resol="1 min", show="BID")
ask = ib.comf_reqhistdata(lastdate, firstdate, 'SPY', interval="2 D", resol="1 min", show="ASK")

bed_high = trades.high > ask.high
trades.high[bed_high] = ask.high
bed_low = trades.low < bid.low
trades.low[bed_low] = bid.low
bed_open_high = trades.open > ask.high
trades.open[bed_open_high] = ask.high
bed_open_low = trades.open < bid.low
trades.open[bed_open_low] = bid.low
bed_close_high = trades.close > ask.high
trades.close[bed_close_high] = ask.high
bed_close_low = trades.close < bid.low
trades.close[bed_close_low] = bid.low
trades.low[trades.low > trades.open] = trades.open
trades.high[trades.high < trades.open] = trades.open

spynew = trades

assert spynew[spynew.close > spynew.high].empty
assert spynew[spynew.open > spynew.high].empty
assert spynew[spynew.close < spynew.low].empty
assert spynew[spynew.open < spynew.low].empty

print spynew.describe()

pickle.dump(spynew, open('minutedata_20_210814.p', 'wb'))
print