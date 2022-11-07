ocean = create_ocean_instance()
alice_wallet = create_alice_wallet(ocean) #you're Alice

from helper import *
from prophet import Prophet

###### ML MODEL ##########
#get predicted ETH values
import pandas as pd
data = pd.DataFrame({"ds": dts, "y": allcex_vals})

train_data = data.iloc[944:,:]
test_data = data.iloc[-12:,:]

model = Prophet()
model.fit(train_data)


###### CALCULATE NMSE ##########
# get the time range we want to test for
start_dt = datetime.datetime.now() - datetime.timedelta(hours=24) #must be >= 12h ago
start_dt = round_to_nearest_hour(start_dt) # so that times line up
target_uts = target_12h_unixtimes(start_dt)
print_datetime_info("target times", target_uts)

# get the actual ETH values at that time
import ccxt
cex_x = ccxt.binance().fetch_ohlcv('ETH/USDT', '1h')

# cex_x is a list of 500 items, one for every hour, on the hour.
#
# Each item has a list of 6 entries:
# (0) timestamp (1) open price (2) high price (3) low price (4) close price (5) volume
# Example item: [1662998400000, 1706.38, 1717.87, 1693, 1713.56, 2186632.9224]
# Timestamp is unix time, but in ms. To get unix time (in s), divide by 1000

cex_uts = [xi[0]/1000 for xi in cex_x] #get unix timestamps in seconds
cex_vals = [xi[4] for xi in cex_x] #get close prices
print_datetime_info("cex times", cex_uts)

cex_vals = filter_to_target_uts(target_uts, cex_uts, cex_vals)

# now, we have predicted and actual values. Let's find error, and plot!
nmse = calc_nmse(cex_vals, pred_vals)
print(f"NMSE = {nmse}")
plot_prices(cex_vals, pred_vals)

####### SAVE PREDICTIONS #######
file_name = "/tmp/pred_vals.csv"
save_list(pred_vals, file_name)

####### UPLOAD CSV TO ARWEAVE #######
from pybundlr import pybundlr
file_name = "/tmp/pred_vals.csv"
url = pybundlr.fund_and_upload(file_name, "matic", alice_wallet.private_key)
#e.g. url = "https://arweave.net/qctEbPb3CjvU8LmV3G_mynX74eCxo1domFQIlOBH1xU"
print(f"Your csv url: {url}")

####### PUBLISH OCEAN ASSET #######
name = "ETH predictions " + str(time.time()) #time for unique name
(data_nft, datatoken, asset) = ocean.assets.create_url_asset(name, url, alice_wallet, wait_for_aqua=False)
data_nft.set_metadata_state(metadata_state=5, from_wallet=alice_wallet)
print(f"New asset created, with did={asset.did}, and datatoken.address={datatoken.address}")

###### SHARE PREDICTIONS TO JUDGES ########
to_address="0xA54ABd42b11B7C97538CAD7C6A2820419ddF703E" #official judges address
datatoken.mint(to_address, ocean.to_wei(10), alice_wallet)
