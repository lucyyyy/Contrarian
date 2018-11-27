# update of 2.1:
# 1. switch from intersection of small and loser to loser in small
# 2. add stop loss function by stop trading for n weeks if last month return rate is lower than x%
# import modules.
# Dataframe
import pandas as pd
# For getting current datetime.
import datetime as dt
# Wind API data source. 
from WindPy import *
# Algorithm and backtest, default alias of this module is "wa". 
from WindAlgo import *
# Plot and chart. 
from WindCharts import *
# Start Wind. 
w.start(show_welcome = False)

# Contrarian & small capital trading strategy - Classic. 

today = dt.datetime.now().strftime("%Y-%m-%d") # current datetime
# A-share stock list on today. 
securities = w.wset(
	"sectorconstituent", 
	"date="+today+";sectorId=a001010100000000;field=wind_code,sec_name"
).Data[0]

def initialize(context):
	context.capital = 1000000000 # one billion RMB as initial capital
	context.securities = securities # A-share stock list today as security pool
	context.start_date = "20090101" # start backtest on 2009-01-01
	context.end_date = "20171231" # end backtest on 2017-12-31
	context.period = "d" # backtest at day frequency
	context.benchmark = "000300.SH" # HS300 as the backtest benchmark
	# Fields: security name, code, percentage change during rank period, market capital calculated by A-share include restricted shares. 
	context.fields = "sec_name,windcode,pct_chg_per,mkt_cap_ashare2"
	
def handle_data(bar_datetime, context, bar_data):
	pass

def CTR_SCPT(bar_datetime, context, bar_data):
    trade_date = bar_datetime.strftime("%Y-%m-%d") # trade on  "today" in backtest
	start_rank_date = w.tdaysoffset(
		-3, # start rank 3 months ago
		trade_date, 
		"Period=M;Days=Alldays"
	).Data[0][0].strftime("%Y-%m-%d")
	end_rank_date = w.tdaysoffset(
		-1, # end rank 1 day ago
		trade_date, 
		"Period=D;Days=Alldays"
	).Data[0][0].strftime("%Y-%m-%d")
	# Data contains percentage change and market capital. 
	data = w.wss(
		context.securities, 
		context.fields, 
		"startDate="+start_rank_date+";endDate="+end_rank_date+";trade_date="+trade_date+"", 
		usedf = True # generate pandas dataframe directly
	)[1]
	data.dropna(inplace = True) # drop data not available
	data.sort_values("MKT_CAP_ASHARE2", inplace = True) # sort by market capital to select small stocks
	small_stock_list = list(data[ : round(len(data)/10)].index) # select the 10% smallest stocks in the past 3 months
	data.sort_values("PCT_CHG_PER", inplace = True) # sort by percentage change to select loser stocks
	loser_stock_list = list(data[ : round(len(data)/10)].index) # select the 10% worst performing stocks in the past 3 months
	target_list = [x for x in small_stock_list if x in loser_stock_list] # select the intersection of 10% smallest and 10% worst as our target. 
	current_stock_list = wa.query_position().get_field("code") # get the stocks list I currently hold
	buy_list = [x for x in target_list if x not in current_stock_list] # buy stocks I previously don't have but is my target
	wa.change_securities(buy_list) # change context.securities, but why won't it affect next loop?
	sell_list = [x for x in current_stock_list if x not in target_list] # sell stocks i previously have but is not my target
	continue_holding_list = [x for x in target_list if x in current_stock_list] # 
	for code in sell_list:
		volume = wa.query_position()[code]['volume'] # query how much position is in my portfolio
		res = wa.order(code, volume, "sell", price = "close", volume_check = False) # sell stocks
	for code in buy_list:
		res = wa.order_percent(code, 1/len(buy_list), 'buy', price = "close", volume_check = False) # buy stocks equally weighted
	for code in continue_holding_list:
		res = wa.order_target_percent(code, 1/len(continue_holding_list), 'buy', price = "close", volume_check = False) # incremental switching position


wa = BackTest(init_func = initialize, handle_data_func = handle_data)
wa.schedule(CTR_SCPT, "m", 0) # execute strategy on the first trading day each month
res = wa.run(show_progress = True)

def windframe_to_dataframe(windframe):
	df = pd.DataFrame()
	column_list = windframe.fields
	for column in column_list:
		df[column] = wind_frame.get_field(column)
	return df
# Backtest summary. 
result = windframe_to_dataframe(wa.summary("result"))
nav = windframe_to_dataframe(wa.summary("nav"))
trade = windframe_to_dataframe(wa.summary("trade"))
position = windframe_to_dataframe(wa.summary("position"))
monthly_profit = windframe_to_dataframe(wa.summary("monthly_profit"))
position_rate = windframe_to_dataframe(wa.summary("position_rate"))
stat_month = windframe_to_dataframe(wa.summary("stat_month"))
stat_quarter = windframe_to_dataframe(wa.summary("stat_quarter"))
stat_year = windframe_to_dataframe(wa.summary("stat_year"))