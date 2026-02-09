The plan is ready. Here's a quick summary of what it covers:
                                                                                                                            The only real change is how pips translate to price. The current bot does entry + pips directly (works for WelTrade       synthetics). For Exness, each asset needs a pip_size multiplier so the formula becomes entry + pips × pip_size.

  Key changes across 7 files:

- .env — Exness MT5 credentials
- config_manager.py — 26 new symbols with pip_size definitions, grouped by class (Forex/Metals/Indices/Oil/Crypto)
- pair_strategy_engine.py — Every pip calculation multiplied by pip_size (TP, SL, grid distance, single fire trigger,
  protection distance)
- trading_engine.py — Exness connection + fill mode (IOC instead of FOK)
- strategy_orchestrator.py — Pass pip_size to engines
- Frontend — New symbol list grouped by asset class

  Strategy logic stays 100% identical — same atomic fires, same grid, same single fire recovery, same nuclear reset.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?
                                                                                                                           Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Implementation Plan: Clone Bot for Exness

 Context

 The current bot (bot-final) trades synthetic indices on WelTrade via MT5. We're cloning it to bot-final-exness to trade  
 real market instruments on Exness (Pro/Raw Spread/Zero account, no symbol suffixes). The trading strategy and rules
 remain identical — the only changes are broker connection, supported assets, and how "pips" translate to price movement  
 per asset class.

 ---
 Core Problem: Pip-to-Price Conversion

 The current bot treats pips as direct price addition (e.g., entry + 600 = TP), which works for WelTrade synthetic
 indices. On Exness, "1 pip" means different price movements per asset:
 ┌──────────────────┬─────────┬─────────┬────────────────────┐
 │   Asset Class    │ Example │ 1 Pip = │ 50 Pips on 1.08000 │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Forex (standard) │ EURUSD  │ 0.0001  │ +0.0050 → 1.08500  │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Forex (JPY)      │ USDJPY  │ 0.01    │ +0.50 → 150.00     │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Gold             │ XAUUSD  │ 0.1     │ +5.0 → 2925.0      │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Silver           │ XAGUSD  │ 0.01    │ +0.50 → 32.50      │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Indices          │ NAS100  │ 1.0     │ +50.0 → 21550.0    │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Oil              │ USOIL   │ 0.01    │ +0.50 → 72.50      │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Crypto (BTC)     │ BTCUSD  │ 1.0     │ +50.0 → 97550.0    │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Crypto (ETH)     │ ETHUSD  │ 0.1     │ +5.0 → 2705.0      │
 ├──────────────────┼─────────┼─────────┼────────────────────┤
 │ Crypto (SOL)     │ SOLUSD  │ 0.01    │ +0.50 → 200.50     │
 └──────────────────┴─────────┴─────────┴────────────────────┘
 Solution: Add a pip_size field per symbol in config. All pip-based calculations become pips × pip_size instead of just
 pips.

 ---
 Step-by-Step Implementation

 Step 1: Clone Repository

- Copy bot-final → C:\Users\antho\Documents\codes-websites\bot-final-exness
- Initialize fresh git repo

 Step 2: Update .env — Broker Connection

 File: .env

- Change MT5 login, password, server to Exness credentials
- Update MT5 terminal path to Exness MT5 installation
- User will provide credentials at implementation time

 Step 3: Update Config Manager — Asset Definitions & Pip System

 File: core/config_manager.py

 3a. Replace KNOWN_SYMBOLS list with new Exness assets organized by class:

 FOREX_MAJORS:  EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD
 FOREX_MINORS:  EURGBP, EURJPY, GBPJPY, AUDNZD, EURAUD, GBPAUD, EURCHF, AUDCAD, NZDJPY,
 METALS:        XAUUSD, XAGUSD
 INDICES:       NAS100, US30, US500
 OIL:           USOIL, UKOIL
 CRYPTO:        BTCUSD, ETHUSD, SOLUSD, XRPUSD, BNBUSD

 3b. Add PIP_SIZES lookup dict mapping each symbol to its pip_size value:
 PIP_SIZES = {
     # Forex standard (5-digit) — 1 pip = 0.0001
     "EURUSD": 0.0001, "GBPUSD": 0.0001, "AUDUSD": 0.0001,
     "NZDUSD": 0.0001, "USDCHF": 0.0001, "USDCAD": 0.0001,
     "EURGBP": 0.0001, "EURAUD": 0.0001, "GBPAUD": 0.0001,
     "EURCHF": 0.0001, "AUDNZD": 0.0001, "AUDCAD": 0.0001,
     # Forex JPY (3-digit) — 1 pip = 0.01
     "USDJPY": 0.01, "EURJPY": 0.01, "GBPJPY": 0.01, "NZDJPY": 0.01,
     # Metals
     "XAUUSD": 0.1,    # Gold — 1 pip = $0.10
     "XAGUSD": 0.01,   # Silver — 1 pip = $0.01
     # Indices — 1 pip = 1 point
     "NAS100": 1.0, "US30": 1.0, "US500": 1.0,
     # Oil — 1 pip = $0.01
     "USOIL": 0.01, "UKOIL": 0.01,
     # Crypto
     "BTCUSD": 1.0,    # 1 pip = $1
     "ETHUSD": 0.1,    # 1 pip = $0.10
     "SOLUSD": 0.01,   # 1 pip = $0.01
 }

 3c. Add pip_size to each symbol's config block (stored in JSON, editable via UI):
 {
   "EURUSD": {
     "enabled": false,
     "pip_size": 0.0001,
     "grid_distance": 20,
     "tp_pips": 50,
     "sl_pips": 60,
     "bx_lot": 0.01,
     "sy_lot": 0.01,
     "sx_lot": 0.02,
     "by_lot": 0.02,
     "single_fire_lot": 0.03,
     "single_fire_tp_pips": 15,
     "single_fire_sl_pips": 15,
     "protection_distance": 15
   }
 }

 3d. Provide sensible defaults per asset class (different default pip values for forex vs gold vs indices etc.) — user
 tunes from the UI.

 3e. Add helper method get_pip_size(symbol) -> float that returns the pip_size from config (with fallback to PIP_SIZES
 lookup).

 Step 4: Update Strategy Engine — Pip Conversion in All Calculations

 File: core/engine/pair_strategy_engine.py

 This is the most critical change. Every place that currently does direct pip addition needs to multiply by pip_size.
 Specifically:

 4a. Store pip_size as an instance variable on the engine (passed from config).

 4b. Modify TP/SL calculation in _open_order():

# BEFORE (WelTrade - direct addition)

 tp = entry + tp_pips
 sl = entry - sl_pips

# AFTER (Exness - pip conversion)

 tp = entry + tp_pips *self.pip_size
 sl = entry - sl_pips* self.pip_size

 4c. Modify grid distance check in _check_grid_trigger():

# BEFORE

 if price >= start_price + grid_distance:

# AFTER

 if price >= start_price + grid_distance * self.pip_size:

 4d. Modify single fire trigger (3 × grid_distance math):

# BEFORE

 trigger = second_fire_price + 3 * grid_distance

# AFTER

 trigger = second_fire_price + 3 *grid_distance* self.pip_size

 4e. Modify protection distance check:

# Same pattern: protection_distance * self.pip_size

 4f. Modify single fire TP/SL:

# Same pattern: single_fire_tp_pips * self.pip_size

 4g. Modify spread safety / trade_stops_level check:

# Ensure minimum distance uses pip_size for comparison

 Step 5: Update Trading Engine — Connection & Fill Mode

 File: core/trading_engine.py

- Update MT5 initialization to use Exness credentials from .env
- May need to adjust type_filling — Exness Pro typically supports ORDER_FILLING_IOC (Immediate-or-Cancel) instead of
 ORDER_FILLING_FOK
- Adjust deviation (slippage) appropriately for real market conditions (currently 200 — may need tuning per asset)

 Step 6: Update Order Placement

 File: core/engine/pair_strategy_engine.py (in _open_order)

- Verify fill mode compatibility with Exness (IOC vs FOK)
- Add dynamic fill mode detection: symbol_info.filling_mode to pick the right mode
- Ensure magic number is different from WelTrade bot (e.g., 234567) to avoid conflicts if both run simultaneously

 Step 7: Update Strategy Orchestrator

 File: core/strategy_orchestrator.py

- Pass pip_size when creating PairStrategyEngine instances
- Ensure update_strategies() reads pip_size from config for each symbol

 Step 8: Update Frontend UI

 File: static/index.html (and any JS files)

- Update symbol dropdowns/lists to show new Exness assets
- Group assets by class (Forex Majors, Forex Minors, Metals, Indices, Oil, Crypto)
- Add pip_size display (read-only or editable) in the config panel
- Update any hardcoded references to WelTrade symbol names

 Step 9: Update API Server

 File: api/server.py

- No major changes expected — the API is symbol-agnostic
- Ensure config validation accepts new symbol names
- Verify the active_symbols list pulls from the new config correctly

 Step 10: Clean Up & Test

- Remove WelTrade-specific references from comments/logs
- Update any hardcoded symbol references
- Test connection to Exness MT5
- Verify pip calculations for each asset class with manual spot checks

 ---
 Asset List with Pip Sizes (Final)
 ┌─────┬────────┬─────────────┬──────────┬───────────────────┬───────────────────┬──────────────┐
 │  #  │ Symbol │    Class    │ Pip Size │ Default TP (pips) │ Default SL (pips) │ Default Grid │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 1   │ EURUSD │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 2   │ GBPUSD │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 3   │ USDJPY │ Forex Major │ 0.01     │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 4   │ USDCHF │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 5   │ USDCAD │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 6   │ AUDUSD │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 7   │ NZDUSD │ Forex Major │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 8   │ EURGBP │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 9   │ EURJPY │ Forex Minor │ 0.01     │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 10  │ GBPJPY │ Forex Minor │ 0.01     │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 11  │ AUDNZD │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 12  │ EURAUD │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 13  │ GBPAUD │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 14  │ EURCHF │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 15  │ AUDCAD │ Forex Minor │ 0.0001   │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 16  │ NZDJPY │ Forex Minor │ 0.01     │ 50                │ 60                │ 20           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 17  │ XAUUSD │ Metal       │ 0.1      │ 100               │ 150               │ 50           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 18  │ XAGUSD │ Metal       │ 0.01     │ 100               │ 150               │ 50           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 19  │ NAS100 │ Index       │ 1.0      │ 50                │ 80                │ 30           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 20  │ US30   │ Index       │ 1.0      │ 50                │ 80                │ 30           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 21  │ US500  │ Index       │ 1.0      │ 15                │ 20                │ 8            │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 22  │ USOIL  │ Oil         │ 0.01     │ 80                │ 100               │ 40           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 23  │ UKOIL  │ Oil         │ 0.01     │ 80                │ 100               │ 40           │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 24  │ BTCUSD │ Crypto      │ 1.0      │ 200               │ 300               │ 100          │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 25  │ ETHUSD │ Crypto      │ 0.1      │ 200               │ 300               │ 100          │
 ├─────┼────────┼─────────────┼──────────┼───────────────────┼───────────────────┼──────────────┤
 │ 26  │ SOLUSD │ Crypto      │ 0.01     │ 200               │ 300               │ 100          │
 └─────┴────────┴─────────────┴──────────┴───────────────────┴───────────────────┴──────────────┘
 Note: Default TP/SL/Grid values are starting points — user tunes these via the UI.

 ---

Files Modified (Summary)
 ┌─────────────────────────────────────┬─────────────┬───────────────────────────────────────────────────┐
 │                File                 │ Change Type │                       Scope                       │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ .env                                │ Rewrite     │ Exness MT5 credentials + path                     │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ core/config_manager.py              │ Major       │ New symbols, pip_sizes, defaults, helper method   │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ core/engine/pair_strategy_engine.py │ Major       │ All pip calculations × pip_size                   │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ core/trading_engine.py              │ Minor       │ Connection config, fill mode                      │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ core/strategy_orchestrator.py       │ Minor       │ Pass pip_size to engines                          │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ api/server.py                       │ Minor       │ Validation updates if needed                      │
 ├─────────────────────────────────────┼─────────────┼───────────────────────────────────────────────────┤
 │ static/index.html + JS              │ Moderate    │ New symbol list, asset grouping, pip_size display │
 └─────────────────────────────────────┴─────────────┴───────────────────────────────────────────────────┘
 ---

 Verification

 1. Connection test: Start bot, verify MT5 connects to Exness and can pull ticks for each symbol
 2. Pip math spot check: For each asset class, manually verify that pips × pip_size gives correct price distances
 3. Order test: Place a small test trade on EURUSD, verify TP/SL prices are calculated correctly
 4. Grid test: Start a cycle on a demo account, verify grid distance triggers at the right price level
 5. Multi-asset test: Enable 2-3 symbols from different classes simultaneously, verify independent operation
 6. UI test: Verify all 26 symbols appear grouped correctly in the frontend
