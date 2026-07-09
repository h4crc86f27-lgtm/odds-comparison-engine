# CODEMAP

## Core Engine

gamma/arb_monitor.py
Main orchestration loop.

gamma/mysql_interface.py
Legacy credentials/config-style file. Not an active database interface module.
Database access is currently done directly with pymysql in arb_monitor.py and provider modules.

gamma/history_processor.py
Historical processing.

## Provider Modules

gamma/arber_modules/betfair.py
Betfair Exchange integration.

gamma/arber_modules/unibet.py
Unibet integration.

gamma/arber_modules/bet3000.py
Bet3000 integration.

## Legacy Providers

The remaining provider modules are retained for historical reasons and are currently inactive.

## Configuration

gamma/config.ini

gamma/arber_modules/config.ini

## Certificates

certs/

gamma/certs/

