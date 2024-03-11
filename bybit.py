"""
Order History   : https://www.bybit.com/user/assets/order/fed/spot-orders/active
Spot Balance    : https://www.bybit.com/user/assets/home/spot
"""

from pybit.unified_trading import HTTP
import pybit
import sys
import math
import time
import requests
import json
import hmac
import hashlib
from dotenv import load_dotenv
import os

load_dotenv()

# Mainnet
mainnet_config = {
    "api_key": os.getenv("MAINNET_API_KEY"),
    "api_secret": os.getenv("MAINNET_API_SECRET"),
    "coin_list": json.loads(os.getenv("MAINNET_COIN_LIST", "{}"))
}

# Testnet
testnet_config = {
    "api_key": os.getenv("TESTNET_API_KEY"),
    "api_secret": os.getenv("TESTNET_API_SECRET"),
    "coin_list": json.loads(os.getenv("TESTNET_COIN_LIST", "{}"))
}

use_testnet = os.getenv("USE_TESTNET") == "True"

# Select config
config = testnet_config if use_testnet else mainnet_config

session = HTTP(testnet=use_testnet, api_key=config["api_key"], api_secret=config["api_secret"])


def generate_signature(message, secret):
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def get_wallet_balance(coin):
    if not use_testnet:
        timestamp = str(int(time.time() * 1000))
        url = f"https://api.bybit.com/v5/account/wallet-balance?accountType=SPOT&coin={coin}"
        message = timestamp + config["api_key"] + "5000" + f"accountType=SPOT&coin={coin}"
        signature = generate_signature(message, config["api_secret"])
        headers = {
            "X-BAPI-SIGN": signature,
            "X-BAPI-API-KEY": config["api_key"],
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": "5000"
        }
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None
    else:
        return session.get_wallet_balance(accountType="UNIFIED", coin=coin)


def process_order(operation, token_symbol, qty=None, retry_decimals=8):
    symbol = f"{token_symbol}USDT"
    attempt = 0
    max_attempts = 16  # Maximum attempts to reduce decimal places

    while attempt < max_attempts:
        try:
            if operation == "Sell":
                if qty is None:
                    qty = 0
                    balance_info = get_wallet_balance(coin=token_symbol)
                    if len(balance_info['result']['list'][0]['coin']) > 0:
                        wallet_balance_str = balance_info['result']['list'][0]['coin'][0]['walletBalance']
                        if wallet_balance_str:
                            balance_float = float(wallet_balance_str)
                            decimal_places = min(len(wallet_balance_str.split('.')[-1]), retry_decimals)
                            qty_format = "{:." + str(decimal_places) + "f}"
                            qty = float(qty_format.format(balance_float))
                            print(f"Selling {qty} of {token_symbol}...")
                    else:
                        print(f"{token_symbol}: Wallet empty, skipping.")
                        return

            elif operation == "Buy":
                if qty is None:
                    qty = config['coin_list'].get(token_symbol, 0)
                print(f"Buying {qty} USD worth of {token_symbol}...")

            if qty > 0:
                order_response = session.place_order(
                    category="spot",
                    symbol=symbol,
                    side=operation,
                    orderType="Market",
                    qty=str(qty),  # Ensure qty is converted to string for API request
                )

                if order_response['retCode'] == 0:
                    print("Order placed successfully.\nFetching execution price...")
                    orderId = order_response['result']['orderId']

                    executions_response = session.get_executions(
                        category="spot",
                        limit=1000
                    )

                    execution_found = False
                    execution_fetch_attempts = 0
                    max_execution_fetch_attempts = 10
                    sleep_seconds = 1  # Time to wait between checks

                    while not execution_found and execution_fetch_attempts < max_execution_fetch_attempts:
                        executions_response = session.get_executions(category="spot", limit=1000)
                        for execution in executions_response['result']['list']:
                            if execution['orderId'] == orderId:
                                operation_word = "sold" if operation == "Sell" else "bought"
                                exec_qty = float(execution['execQty'])
                                exec_price = float(execution['execPrice'])
                                
                                print(f"Amount {operation_word}: {exec_qty}", token_symbol) 
                                print(f"Price per coin: {exec_price} USD")

                                try:
                                    exec_value = float(execution['execValue'])
                                    print(f"Exact Operation Total: {exec_value} USD")
                                except Exception:
                                    exec_value = exec_qty * exec_price
                                    print(f"Estimated Operation Total: {exec_value} USD")                                

                                execution_found = True

                        time.sleep(sleep_seconds)
                        execution_fetch_attempts += 1

                    if not execution_found:
                        print("Execution details not found, order might still be in progress and/or not filled. Please check manually.")

                    # This ensures the function exits after a successful order placement.
                    return  
                else:
                    print("Failed to place order:", order_response['retMsg'])
                    # Exit the loop if order placement failed and cannot be retried.
                    break  

            else:
                print(f"{token_symbol}: Quantity to trade is 0 AND/OR insufficient balance.")
                break  # Exit the loop if qty is 0 or negative

        except pybit.exceptions.InvalidRequestError as e:
            error_message = e.args[0]
            if "170137" in error_message:  # Assuming error message contains the error code
                print("Error occurred: Order quantity has too many decimals. Retrying with fewer decimals...")
                qty = math.floor(qty * (10 ** (retry_decimals - 1))) / (10 ** (retry_decimals - 1))
                retry_decimals -= 1  # Decrease decimal precision for retry
                attempt += 1
                if retry_decimals < 0:
                    print("Error: Could not place order with adjusted decimals.")
                    break
            else:
                print("Error occurred while trying to process order:", error_message)
                break
        except Exception as e:
            print(e)
            break

    

def main():
    if len(sys.argv) > 2:
        operation, token_arg = sys.argv[1].capitalize(), sys.argv[2].upper()
        if token_arg == "EVERYTHING":
            confirm = input(f"Are you sure you want to {operation.lower()} everything?\nType '{operation.upper()} EVERYTHING' to confirm: ")
            print("*****************************")
            if confirm != f"{operation.upper()} EVERYTHING":
                print("Operation canceled.")
                return
            if operation == "Sell":
                # Fetch balances for all coins and sell each
                for coin in config['coin_list'].keys():
                    process_order(operation, coin)
                    print("*****************************")
            elif operation == "Buy":
                # Buy each coin based on predefined USD amounts
                for coin, amount in config['coin_list'].items():
                    process_order(operation, coin, qty=amount)
                    print("*****************************")
        else:
            # Process a single coin operation
            process_order(operation, token_arg)
    else:
        print("Usage: python bybit.py [buy/sell] [CoinSymbol/EVERYTHING]")

if __name__ == "__main__":
    main()

