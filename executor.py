import locale

import sys
import warnings

import stock.coinmarketcap.gainers_losers as gl
import stock.coinmarketcap.stats as ms
import stock.coinmarketcap.cap as mc
import time
import _thread
import pandas as pd
import db.connector as connector
from stock.coinmarketcap.exchanges import Exchanges

warnings.filterwarnings("ignore")
# locale.setlocale( locale.LC_ALL, '' )
# locale.currency( 188518982.18, grouping=True )

# SOURCES
# 1 bitfinex
# 2,poloniex
# 3,coinmarketcap

# -------------------------------------------------------
#  MARKET CAP
# -------------------------------------------------------
import stock.coinmarketcap.markets as market
from utility.config_parser import get_config


# market_cap = mc.Cap()
# data_cap = market_cap.get_data()
# print(data_cap.head())
# # -------------------------------------------------------
#
# # -------------------------------------------------------
# #  STATS
# # -------------------------------------------------------
# market_stats = ms.Stats()
# data_stats = market_stats.get_data()
# print(data_stats)
# # -------------------------------------------------------
#
# # -------------------------------------------------------
# #  GAINERS LOSERS DATA
# # -------------------------------------------------------
# gainers_losers = gl.Gainers_Losers()
# data_gl = gainers_losers.get_data()
# print(data_gl.head())



# --------------------------------------------------------------------
# SYNC CURRENCIES SITE - OUR DB
# --------------------------------------------------------------------
def sync_currecies():
    # --------------------------------------------------------------------
    # READ STOCK CACHED PARAMS
    # --------------------------------------------------------------------
    socket_generic_arguments_dict = get_config(config_type='stock', section='generic-arguments')

    # --------------------------------------------------------------------
    # CREATE CONNECTION
    # --------------------------------------------------------------------
    con = connector.create()
    cursor = con.cursor()

    # --------------------------------------------------------------------
    # COLLECT OUR COINS IN DB
    # --------------------------------------------------------------------
    data_cap_from_db = pd.read_sql('Select * from currency', con=con)
    data_cap_from_db.set_index(['id'], inplace=True)

    # --------------------------------------------------------------------
    # COLLECT ALL COINS AND THEIR GENERAL STATISTICS
    # --------------------------------------------------------------------
    market_cap = mc.Cap()
    data_cap = market_cap.get_data()

    # --------------------------------------------------------------------
    # FILTER OUT INVALUABLE COINS FROM THE LIST SO THAT WE CAN FOCUS ON VALUABLE ONES.
    # --------------------------------------------------------------------
    # read from stock config files
    limit_coin_24h_usd_volume = int(socket_generic_arguments_dict['limit_coin_24h_usd_volume'])
    data_cap = data_cap[data_cap['24h_volume_usd'] >= limit_coin_24h_usd_volume]
    data_cap.set_index(['id'], inplace=True)

    # --------------------------------------------------------------------
    # COMPARE TWO SET FOR DIFFERENCES
    # --------------------------------------------------------------------
    currency_index_from_db = pd.Index(data_cap_from_db.index)
    currency_index_from_site = pd.Index(data_cap.index)
    new_index_from_site = currency_index_from_site.difference(currency_index_from_db)

    # --------------------------------------------------------------------
    # FILTER THESE IDs FROM CAP SITE DATAFRAEM
    # --------------------------------------------------------------------
    data_cap = data_cap.reindex(new_index_from_site, fill_value='missing')
    len_data_cap = len(data_cap)

    # --------------------------------------------------------------------
    # NEW DATA CAPS ARE BEING WRITTEN INTO CURRENCY TABLES
    # --------------------------------------------------------------------
    if len_data_cap > 0:
        print(len_data_cap, 'new currencies are going to be written in currency table')
        for _index, _row in data_cap.iterrows():
            values = "'" + _row['symbol'] + "','" + str(_row['Insertion_Time']) + "','" + _index + "','" + _row[
                'name'] + "'"
            cursor.execute("INSERT INTO currency(symbol, inserted_time, id, name) VALUES (" + values + ")")
        print('New currencies are inserted to table')
    else:
        print('Nothing new to be inserted')

    # --------------------------------------------------------------------
    # CONNECTION DISCONNECTED
    # --------------------------------------------------------------------
    connector.disconnect(con)


# --------------------------------------------------------------------
# SYNC CURRENCIES SITE - OUR DB
# --------------------------------------------------------------------
def get_currencies():
    # --------------------------------------------------------------------
    # CREATE CONNECTION
    # --------------------------------------------------------------------
    con = connector.create()
    cursor = con.cursor()

    # --------------------------------------------------------------------
    # COLLECT OUR COINS IN DB
    # --------------------------------------------------------------------
    data_cap_from_db = pd.read_sql('Select * from currency', con=con)
    data_cap_from_db.set_index(['id'], inplace=True)

    # --------------------------------------------------------------------
    # COLLECT ALL COINS AND THEIR GENERAL STATISTICS
    # --------------------------------------------------------------------
    market_cap = mc.Cap()
    data_cap = market_cap.get_data()
    data_cap.set_index(['id'], inplace=True)

    # --------------------------------------------------------------------
    # COMPARE TWO SET FOR DIFFERENCES
    # --------------------------------------------------------------------
    currency_index_from_db = pd.Index(data_cap_from_db.index)

    # --------------------------------------------------------------------
    # FILTER THESE IDs FROM CAP SITE DATAFRAEM
    # --------------------------------------------------------------------
    data_cap = data_cap.reindex(currency_index_from_db, fill_value='missing')
    len_data_cap = len(data_cap)
    data_cap.fillna(0, inplace=True)

    # --------------------------------------------------------------------
    # CONNECTION DISCONNECTED
    # --------------------------------------------------------------------
    connector.disconnect(con)

    print('Pure cap data is captured')

    return data_cap, len_data_cap


# --------------------------------------------------------------------
# INSERT CURRENCY OVERALL SNAPSHOT TO OUR DB
# --------------------------------------------------------------------
def insert_currencies_overall_snapshot(data_cap, len_data_cap):
    # --------------------------------------------------------------------
    # CREATE CONNECTION
    # --------------------------------------------------------------------
    con = connector.create()
    cursor = con.cursor()

    if len_data_cap > 0:
        print(len_data_cap, 'currency snapshots are going to be written in currency_overall_snapshot table')
        for _index, _row in data_cap.iterrows():
            values = "'" + str(_row['Insertion_Time']) + "','" \
                     + _index + "'," \
                     + str(_row['rank']) + "," \
                     + str(_row['price_usd']) + "," \
                     + str(_row['price_btc']) + "," \
                     + str(_row['24h_volume_usd']) + "," \
                     + str(_row['market_cap_usd']) + "," \
                     + str(_row['available_supply']) + "," \
                     + str(_row['total_supply']) + "," \
                     + str(_row['percent_change_1h']) + "," \
                     + str(_row['percent_change_24h']) + "," \
                     + str(_row['percent_change_7d'])
            cursor.execute(
                "INSERT INTO currency_overall_snapshot(inserted_time,currency_id, rank, price_usd, price_btc, 24h_volume_usd, market_cap_usd, available_supply,total_supply,percent_change_1h,percent_change_24h,percent_change_7d) VALUES (" + values + ")")
        print('Currency snapshot are inserted to table')
    else:
        print('Nothing to be inserted')

    # --------------------------------------------------------------------
    # CONNECTION DISCONNECTED
    # --------------------------------------------------------------------
    connector.disconnect(con)

# --------------------------------------------------------------------
# INSERT CURRENCY OVERALL SNAPSHOT TO OUR DB
# --------------------------------------------------------------------
def insert_market_stats():
    # --------------------------------------------------------------------
    # CREATE CONNECTION
    # --------------------------------------------------------------------
    con = connector.create()
    cursor = con.cursor()

    # --------------------------------------------------------------------
    # NEW MARKET STATS ARE BEING WRITTEN INTO TABLE
    # --------------------------------------------------------------------
    market_stats = ms.Stats()
    data_stats = market_stats.get_data()
    print('Market stats are going to be written in market_stats table')
    for _index, _row in data_stats.iterrows():
        values = "'" + str(_row['insertion_time']) + "'," \
                 + str(_row['active_assets']) + "," \
                 + str(_row['active_currencies']) + "," \
                 + str(_row['active_markets']) + "," \
                 + str(_row['bitcoin_percentage_of_market_cap']) + "," \
                 + str(_row['total_24h_volume_usd']) + "," \
                 + str(_row['total_market_cap_usd'])
        cursor.execute(
            "INSERT INTO market_stats (inserted_time,active_assets, active_currencies, active_markets, bitcoin_percent_of_market, total_24h_volume_usd,total_market_cap_usd) VALUES (" + values + ")")
    print('Currency snapshot are inserted to table')


    # --------------------------------------------------------------------
    # CONNECTION DISCONNECTED
    # --------------------------------------------------------------------
    connector.disconnect(con)


# Define a function for the thread
def print_time(threadName, delay):
    count = 0
    while count < 5:
        time.sleep(delay)
        count += 1
        print("%s: %s" % (threadName, time.ctime(time.time())))


def get_time():
    if sys.platform == 'win32':
        default_timer = time.clock()
    else:
        default_timer = time.time()
    return default_timer

def convert_timer_to_readable(time):
    hours, rem = divmod(time, 3600)
    minutes, seconds = divmod(rem, 60)
    return  "{:0>2}:{:0>2}:{:05.2f}".format(int(hours),int(minutes),seconds)

if __name__ == '__main__':
    socket_generic_arguments_dict = get_config(config_type='stock', section='generic-arguments')
    currency_update_interval = eval(socket_generic_arguments_dict['currency_update_interval'])
    print('Application is started on', time.time())
    iteration = 0


    # ----------------------------------------
    # CODE TEST
    # ----------------------------------------
    _exchange = Exchanges()
    aa = _exchange.get_data()
    print(aa.head())
    # while True:
    #     iteration_start = get_time()
    #     print('*' * 50)
    #     print('*' * 25)
    #     print('Iteration', str(iteration), 'is started on',convert_timer_to_readable(iteration_start) )
    #     print('*' * 25)
    #     print('*' * 50)
    #
    #     # -------------------------------------------------------------------------------------------
    #     # INSERT MARKET STATS
    #     # -------------------------------------------------------------------------------------------
    #     insert_marketstats_start = get_time()
    #     print('-' * 50)
    #     print('Iteration', str(iteration), 'insert market stats is started on',
    #           convert_timer_to_readable(insert_marketstats_start))
    #     insert_market_stats()
    #     insert_marketstats_end = get_time()
    #     print('Iteration', str(iteration), 'insert market stats is ended on',
    #           convert_timer_to_readable(insert_marketstats_end), 'process took',
    #           str(insert_marketstats_end - insert_marketstats_start), 'seconds.')
    #
    #     #-------------------------------------------------------------------------------------------
    #     # SYNC CURRENCIES
    #     # -------------------------------------------------------------------------------------------
    #     sync_currecies_start = get_time()
    #     print('-'*50)
    #     print('Iteration', str(iteration), 'sync currencies is started on', convert_timer_to_readable(sync_currecies_start))
    #     sync_currecies()
    #     sync_currecies_end = get_time()
    #     print('Iteration', str(iteration), 'sync currencies is ended on', convert_timer_to_readable(sync_currecies_end), 'process took',str(sync_currecies_end - sync_currecies_start), 'seconds.')
    #
    #     # -------------------------------------------------------------------------------------------
    #     # GET CURRENCIES
    #     # -------------------------------------------------------------------------------------------
    #     get_currecies_start = get_time()
    #     print('-' * 50)
    #     print('Iteration', str(iteration), 'get currencies is started on', convert_timer_to_readable(get_currecies_start))
    #     data_cap, len_data_cap = get_currencies()
    #     get_currecies_end = get_time()
    #     print('Iteration', str(iteration), 'get currencies is ended on', convert_timer_to_readable(get_currecies_end), 'process took',
    #           str(get_currecies_end - get_currecies_start), 'seconds.')
    #
    #     # -------------------------------------------------------------------------------------------
    #     # INSERT CURRENCIES
    #     # -------------------------------------------------------------------------------------------
    #     insert_currecies_start = get_time()
    #     print('-' * 50)
    #     print('Iteration', str(iteration), 'insert currencies is started on', convert_timer_to_readable(insert_currecies_start))
    #     insert_currencies_overall_snapshot(data_cap, len_data_cap)
    #     insert_currecies_end = get_time()
    #     print('Iteration', str(iteration), 'insert currencies is ended on', convert_timer_to_readable(insert_currecies_end), 'process took',
    #           str(insert_currecies_end - insert_currecies_start), 'seconds.')
    #
    #     # -------------------------------------------------------------------------------------------
    #     # CURRENCY MARKET
    #     # -------------------------------------------------------------------------------------------
    #
    #     # -------------------------------------------------------------------------------------------
    #     # CURRENCY PRICE
    #     # -------------------------------------------------------------------------------------------
    #
    #     iteration_end = get_time()
    #     print('Iteration', str(iteration), 'is ended on', convert_timer_to_readable(iteration_end))
    #     print('Iteration', str(iteration), 'took', str(iteration_end - iteration_start))
    #     time.sleep(currency_update_interval)
    #     iteration += 1
    #
