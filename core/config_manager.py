import json
import os
from typing import Dict, Any, List, Optional

# All available trading symbols (Exness)
AVAILABLE_SYMBOLS = [
    # Forex Majors
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    # Forex Minors
    "EURGBP", "EURJPY", "GBPJPY", "AUDNZD", "EURAUD", "GBPAUD", "EURCHF", "AUDCAD", "NZDJPY",
    # Metals
    "XAUUSD", "XAGUSD",
    # Indices
    "NAS100", "US30", "US500",
    # Oil
    "USOIL", "UKOIL",
    # Crypto
    "BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "BNBUSD"
]

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
    "XRPUSD": 0.001,
    "BNBUSD": 0.1
}

def get_default_symbol_config(symbol: str = "EURUSD") -> Dict[str, Any]:
    """
    Default configuration for a single symbol/asset (Pair Strategy)
    Defaults derived from Exness asset class characteristics.
    """
    # Get default pip size or fallback to 0.0001
    pip_size = PIP_SIZES.get(symbol, 0.0001)

    # Asset Class Defaults
    # Gold (XAUUSD)
    if symbol == "XAUUSD":
        grid = 50.0; sf_tp = 40.0; sf_sl = 20.0; prot = 200.0
    elif symbol == "XAGUSD":
        grid = 50.0; sf_tp = 100.0; sf_sl = 150.0; prot = 200.0
    elif symbol.startswith("BTC"):
        grid = 100.0; sf_tp = 200.0; sf_sl = 300.0; prot = 500.0
    elif symbol in ["ETHUSD", "SOLUSD", "BNBUSD"]:
        grid = 100.0; sf_tp = 200.0; sf_sl = 300.0; prot = 500.0
    elif symbol in ["NAS100", "US30"]:
        grid = 30.0; sf_tp = 50.0; sf_sl = 80.0; prot = 100.0
    elif symbol == "US500":
        grid = 8.0; sf_tp = 15.0; sf_sl = 20.0; prot = 30.0
    elif "OIL" in symbol:
        grid = 40.0; sf_tp = 80.0; sf_sl = 100.0; prot = 150.0
    else:
        grid = 20.0; sf_tp = 50.0; sf_sl = 60.0; prot = 100.0

    return {
        "enabled": False,
        "pip_size": pip_size,        # Conversion factor for pips
        "grid_distance": grid,       # Pips between atomic fires
        "bx_lot": 0.01,              # Initial Buy lot (Pair X)
        "sy_lot": 0.01,              # Initial Sell lot (Pair Y)
        "sx_lot": 0.01,              # Completing Sell lot (Pair X)
        "by_lot": 0.01,              # Completing Buy lot (Pair Y)
        "single_fire_lot": 0.01,         # Single fire lot size
        "single_fire_tp_pips": sf_tp,    # Single fire TP
        "single_fire_sl_pips": sf_sl,    # Single fire SL
        "protection_distance": prot,     # Pips before nuclear reset on reversal
    }


class ConfigManager:
    """
    Multi-Asset Configuration Manager
    
    Structure:
    {
        "global": {
            "max_runtime_minutes": 0
        },
        "symbols": {
            "EURUSD": { ...symbol config... },
            "GBPUSD": { ...symbol config... },
            ...
        }
    }
    """
    
    def __init__(self, user_id: str = "default", config_file: str = "config.json"):
        self.user_id = user_id
        
        # If a specific user is logged in, use their unique config file
        if user_id and user_id != "default":
            self.config_file = f"config_{user_id}.json"
        else:
            self.config_file = config_file
            
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    
                # Check if it's the new multi-asset format
                # New format has "symbols" as a DICT, old format has it as a LIST
                symbols_data = loaded.get("symbols")
                is_new_format = isinstance(symbols_data, dict) and "global" in loaded
                
                if is_new_format:
                    self.config = loaded
                else:
                    # Migrate from old format (symbols is a list or missing)
                    print(f"[CONFIG] Migrating config to multi-asset format...")
                    self.config = self._migrate_old_config(loaded)
                    self.save_config()
                    
            except Exception as e:
                print(f"[CONFIG] Error loading config {self.config_file}: {e}")
                self.config = self._get_defaults()
        else:
            print(f"[CONFIG] Creating new config file: {self.config_file}")
            self.config = self._get_defaults()
            self.save_config()

    def _migrate_old_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate from old single-asset config to new multi-asset format"""
        new_config = self._get_defaults()
        
        # Migrate global settings
        if "max_runtime_minutes" in old_config:
            new_config["global"]["max_runtime_minutes"] = old_config["max_runtime_minutes"]
        
        # Migrate old symbols to new format
        # Note: Exness symbols are different, so strict migration might not map 1:1
        # We will try to map if names match, otherwise just keep defaults
        
        old_symbols = old_config.get("symbols", [])
        if isinstance(old_symbols, list):
             for symbol in old_symbols:
                if symbol in new_config["symbols"]:
                    sym_cfg = new_config["symbols"][symbol]
                    sym_cfg["enabled"] = True
                    # Attempt to copy lot sizes if keys match
                    # But structure changed slightly, so relying on defaults is safer for now
                    
        return new_config

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f" Error saving config: {e}")

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update config with new values.
        Handles both flat updates and nested symbol updates.
        """
        # Handle global settings
        if "global" in new_config:
            self.config["global"].update(new_config["global"])
        
        # Handle symbol-specific settings
        if "symbols" in new_config:
            for symbol, sym_cfg in new_config["symbols"].items():
                if symbol in self.config["symbols"]:
                    self.config["symbols"][symbol].update(sym_cfg)
                    
                    # Validate grid_distance: must be > 0
                    grid_dist = self.config["symbols"][symbol].get("grid_distance", 50.0)
                    self.config["symbols"][symbol]["grid_distance"] = max(1.0, float(grid_dist))
                    
                    # Validate pip_size: must be > 0
                    ps = self.config["symbols"][symbol].get("pip_size", 0.0001)
                    self.config["symbols"][symbol]["pip_size"] = max(0.00000001, float(ps))
                    
                    # Validate lot sizes: all must be > 0, default to 0.01
                    for lot_field in ["bx_lot", "sy_lot", "sx_lot", "by_lot", "single_fire_lot"]:
                        lot_val = self.config["symbols"][symbol].get(lot_field, 0.01)
                        self.config["symbols"][symbol][lot_field] = max(0.01, float(lot_val))

                    # Validate single fire TP/SL pips: must be > 0
                    for sf_field in ["single_fire_tp_pips", "single_fire_sl_pips"]:
                        sf_val = self.config["symbols"][symbol].get(sf_field, 150.0)
                        self.config["symbols"][symbol][sf_field] = max(1.0, float(sf_val))

                    # Validate protection_distance: must be > 0
                    prot_dist = self.config["symbols"][symbol].get("protection_distance", 100.0)
                    self.config["symbols"][symbol]["protection_distance"] = max(1.0, float(prot_dist))
        
        self.save_config()
        return self.config

    def get_config(self) -> Dict[str, Any]:
        return self.config
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global settings"""
        return self.config.get("global", {})
    
    def get_symbol_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get config for a specific symbol"""
        return self.config.get("symbols", {}).get(symbol)
    
    def get_pip_size(self, symbol: str) -> float:
        """Get pip size for a symbol from config or defaults"""
        sym_cfg = self.get_symbol_config(symbol)
        if sym_cfg and "pip_size" in sym_cfg:
            return float(sym_cfg["pip_size"])
        return PIP_SIZES.get(symbol, 0.0001)
    
    def get_enabled_symbols(self) -> List[str]:
        """Get list of symbols that are enabled"""
        enabled = []
        for symbol, cfg in self.config.get("symbols", {}).items():
            if cfg.get("enabled", False):
                enabled.append(symbol)
        return enabled
    
    def enable_symbol(self, symbol: str, enabled: bool = True):
        """Enable or disable a symbol"""
        if symbol in self.config.get("symbols", {}):
            self.config["symbols"][symbol]["enabled"] = enabled
            self.save_config()
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Generate default multi-asset config structure"""
        return {
            "global": {
                "max_runtime_minutes": 0
            },
            "symbols": {
                symbol: get_default_symbol_config(symbol)
                for symbol in AVAILABLE_SYMBOLS
            }
        }