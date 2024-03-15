# Bybit Trading Automation

This project automates trading on Bybit, allowing for spot orders. It utilizes the Bybit API to manage and execute trades based on user-defined configurations. The automation script is capable of handling order operations such as buying and selling a specified token or the entirety of one's portfolio.

## Features

- **Mainnet and Testnet Support**: Easily switch between using Bybit's mainnet and testnet environments.
- **Flexible Order Operations**: Support for buying and selling specific tokens or all tokens in the portfolio.
- **Dynamic Order Quantities**: Ability to dynamically determine order quantities based on wallet balance for sells, and predefined USD amounts for buys.
- **Environment Variable Configuration**: Secure storage of API keys, secrets, and other configurations using environment variables.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.6 or later
- [pybit](https://github.com/bybit-exchange/pybit) - A Python library for the Bybit API
- An account on Bybit (either mainnet or testnet)
- API keys generated from Bybit

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/your-username/your-project-name.git
cd your-project-name
```

## Configuration
Rename .env.example to .env.
Edit .env to include your Bybit API keys, secret, and other configurations such as coin list for trading.

## Usage
To execute an operation, use the following command syntax:
```bash
python bybit.py [operation] [token_symbol/EVERYTHING]
```
operation: Either buy or sell.
token_symbol: The symbol of the token to trade, or EVERYTHING to operate on the entire portfolio.

## Examples
To buy $100 worth of BTC:
```bash
python bybit.py buy BTC
```
