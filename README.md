fiat-value
==========

Calculate the current fiat (EUR/USD/...) value of your Kraken account.

Usage
-----

* Have Python 3 installed
* Create a virtualenv, etc.
* Install deps from `requirements.txt` (`pip install -r requirements.txt`)
* Copy `fiat-value.cfg.sample` to `fiat-value.cfg`; add your Kraken key and secret.
* Run `python fiat_value.py`. See `--help` for additional parameters.
  For instance, if you have 3 BTC and 5 BCH outside Kraken, you can invoke
  `python fiat_value.py -b XBT=3 BCH=5`.
