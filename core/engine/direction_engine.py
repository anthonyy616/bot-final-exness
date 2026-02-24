"""
Direction Scoring Engine

Self-contained module that evaluates multiple technical indicators
to determine single fire direction. Called once per single fire trigger event.

Indicators and timeframes:
    H1:  200 EMA (structural bias), 50 EMA + slope (trend momentum)
    M5:  MACD (12,26,9), RSI (14), Bollinger Bands (20, 2)
    M1:  Stochastic (14, 3)

Resolution: direction = 'buy' if BUY_SCORE >= SELL_SCORE else 'sell'
No minimum threshold. No skip. No None return. Always resolves.
"""

import MetaTrader5 as mt5


class DirectionEngine:
    """
    Computes a directional score from technical indicators at the moment
    a single fire trigger fires. Returns 'buy' or 'sell' — always.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol

    # ──────────────────────────────────────────────
    # DATA FETCHING
    # ──────────────────────────────────────────────

    def _fetch_candles(self, timeframe, count: int):
        """
        Fetch OHLCV candle data from MT5.
        Returns list of tuples or None on failure.
        Each element has: time, open, high, low, close, tick_volume, spread, real_volume
        """
        rates = mt5.copy_rates_from_pos(self.symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            return None
        return rates

    # ──────────────────────────────────────────────
    # INDICATOR CALCULATIONS (pure Python)
    # ──────────────────────────────────────────────

    def _ema(self, closes: list, period: int) -> float:
        """Calculate EMA and return the last value."""
        if len(closes) < period:
            return closes[-1] if closes else 0.0

        multiplier = 2.0 / (period + 1)
        # Seed with SMA of first `period` values
        ema_val = sum(closes[:period]) / period

        for price in closes[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val

        return ema_val

    def _ema_series(self, closes: list, period: int) -> list:
        """Calculate EMA and return the full series (for slope and MACD)."""
        if len(closes) < period:
            return closes[:]

        multiplier = 2.0 / (period + 1)
        # Seed with SMA of first `period` values
        ema_val = sum(closes[:period]) / period
        result = [ema_val]

        for price in closes[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
            result.append(ema_val)

        return result

    def _macd(self, closes: list):
        """
        MACD (12, 26, 9). Returns (macd_line, signal, histogram) for the last candle.
        """
        if len(closes) < 26:
            return 0.0, 0.0, 0.0

        ema12 = self._ema_series(closes, 12)
        ema26 = self._ema_series(closes, 26)

        # Align lengths — ema26 is shorter
        offset = len(ema12) - len(ema26)
        macd_line_series = []
        for i in range(len(ema26)):
            macd_line_series.append(ema12[i + offset] - ema26[i])

        if len(macd_line_series) < 9:
            macd_val = macd_line_series[-1] if macd_line_series else 0.0
            return macd_val, 0.0, macd_val

        # Signal = 9-period EMA of MACD line
        signal_series = self._ema_series(macd_line_series, 9)

        macd_val = macd_line_series[-1]
        signal_val = signal_series[-1]
        histogram = macd_val - signal_val

        return macd_val, signal_val, histogram

    def _rsi(self, closes: list, period: int = 14) -> float:
        """RSI for the last candle."""
        if len(closes) < period + 1:
            return 50.0  # Neutral fallback

        # Calculate price changes
        changes = []
        for i in range(1, len(closes)):
            changes.append(closes[i] - closes[i - 1])

        # Initial average gain/loss over first `period` changes
        gains = []
        losses = []
        for c in changes[:period]:
            if c > 0:
                gains.append(c)
            else:
                losses.append(abs(c))

        avg_gain = sum(gains) / period if gains else 0.0
        avg_loss = sum(losses) / period if losses else 0.0

        # Smoothed (Wilder's) for remaining changes
        for c in changes[period:]:
            gain = c if c > 0 else 0.0
            loss = abs(c) if c < 0 else 0.0
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _rsi_series(self, closes: list, period: int = 14) -> list:
        """RSI series for divergence detection."""
        if len(closes) < period + 1:
            return [50.0]

        changes = []
        for i in range(1, len(closes)):
            changes.append(closes[i] - closes[i - 1])

        gains = []
        losses = []
        for c in changes[:period]:
            if c > 0:
                gains.append(c)
            else:
                losses.append(abs(c))

        avg_gain = sum(gains) / period if gains else 0.0
        avg_loss = sum(losses) / period if losses else 0.0

        rsi_values = []
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

        for c in changes[period:]:
            gain = c if c > 0 else 0.0
            loss = abs(c) if c < 0 else 0.0
            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100.0 - (100.0 / (1.0 + rs)))

        return rsi_values

    def _bollinger(self, closes: list, period: int = 20, num_std: float = 2.0):
        """
        Bollinger Bands. Returns (upper, lower, mid, bandwidth) for the last candle.
        bandwidth = (upper - lower) / mid — used to detect expansion.
        """
        if len(closes) < period:
            mid = closes[-1] if closes else 0.0
            return mid, mid, mid, 0.0

        window = closes[-period:]
        mid = sum(window) / period
        variance = sum((x - mid) ** 2 for x in window) / period
        std = variance ** 0.5

        upper = mid + num_std * std
        lower = mid - num_std * std
        bandwidth = (upper - lower) / mid if mid != 0 else 0.0

        return upper, lower, mid, bandwidth

    def _stochastic(self, highs: list, lows: list, closes: list,
                    k_period: int = 14, d_period: int = 3):
        """
        Stochastic %K and %D for the last few candles.
        Returns (k_current, d_current, k_prev, d_prev) for crossover detection.
        """
        if len(closes) < k_period + d_period:
            return 50.0, 50.0, 50.0, 50.0

        # Calculate raw %K series
        k_values = []
        for i in range(k_period - 1, len(closes)):
            window_highs = highs[i - k_period + 1: i + 1]
            window_lows = lows[i - k_period + 1: i + 1]
            highest = max(window_highs)
            lowest = min(window_lows)
            if highest == lowest:
                k_values.append(50.0)
            else:
                k_values.append(100.0 * (closes[i] - lowest) / (highest - lowest))

        if len(k_values) < d_period:
            k_val = k_values[-1] if k_values else 50.0
            return k_val, k_val, k_val, k_val

        # %D = SMA of %K
        d_values = []
        for i in range(d_period - 1, len(k_values)):
            d_val = sum(k_values[i - d_period + 1: i + 1]) / d_period
            d_values.append(d_val)

        k_current = k_values[-1]
        d_current = d_values[-1]
        k_prev = k_values[-2] if len(k_values) >= 2 else k_current
        d_prev = d_values[-2] if len(d_values) >= 2 else d_current

        return k_current, d_current, k_prev, d_prev

    def _divergence(self, closes: list, rsi_values: list):
        """
        Simple two-point divergence on the last 5 candles.
        Bullish: price makes lower low but RSI makes higher low.
        Bearish: price makes higher high but RSI makes lower high.
        Returns 'bullish', 'bearish', or None.
        """
        if len(closes) < 5 or len(rsi_values) < 5:
            return None

        # Use last 5 values — compare the endpoints as "two swings"
        recent_closes = closes[-5:]
        recent_rsi = rsi_values[-5:]

        # Find the two lowest price points and their RSI
        price_low_1 = min(recent_closes[:3])  # First swing region
        price_low_2 = min(recent_closes[2:])  # Second swing region
        idx_low_1 = recent_closes[:3].index(price_low_1)
        idx_low_2 = recent_closes[2:].index(price_low_2) + 2

        # Find the two highest price points and their RSI
        price_high_1 = max(recent_closes[:3])
        price_high_2 = max(recent_closes[2:])
        idx_high_1 = recent_closes[:3].index(price_high_1)
        idx_high_2 = recent_closes[2:].index(price_high_2) + 2

        # Bullish divergence: price lower low + RSI higher low
        if price_low_2 < price_low_1 and recent_rsi[idx_low_2] > recent_rsi[idx_low_1]:
            return 'bullish'

        # Bearish divergence: price higher high + RSI lower high
        if price_high_2 > price_high_1 and recent_rsi[idx_high_2] < recent_rsi[idx_high_1]:
            return 'bearish'

        return None

    # ──────────────────────────────────────────────
    # MAIN SCORING RESOLUTION
    # ──────────────────────────────────────────────

    def resolve(self, ask: float, bid: float) -> str:
        """
        Evaluate all indicators and return 'buy' or 'sell'.
        Called once per single fire trigger event.
        Never returns None. Ties resolve to 'buy'.
        """
        buy_score = 0
        sell_score = 0
        mid = (ask + bid) / 2

        # ── Fetch candle data ──
        h1_candles = self._fetch_candles(mt5.TIMEFRAME_H1, 200)
        m5_candles = self._fetch_candles(mt5.TIMEFRAME_M5, 100)
        m1_candles = self._fetch_candles(mt5.TIMEFRAME_M1, 50)

        # Extract close arrays (index 4 = close in MT5 rate tuples)
        h1_closes = [c[4] for c in h1_candles] if h1_candles is not None else []
        m5_closes = [c[4] for c in m5_candles] if m5_candles is not None else []
        m1_closes = [c[4] for c in m1_candles] if m1_candles is not None else []
        m1_highs = [c[2] for c in m1_candles] if m1_candles is not None else []
        m1_lows = [c[3] for c in m1_candles] if m1_candles is not None else []
        m5_highs = [c[2] for c in m5_candles] if m5_candles is not None else []
        m5_lows = [c[3] for c in m5_candles] if m5_candles is not None else []

        # ── 1. 200 EMA structural bias (H1) — weight: 30 ──
        if len(h1_closes) >= 200:
            ema200 = self._ema(h1_closes, 200)
            if mid > ema200:
                buy_score += 30
            elif mid < ema200:
                sell_score += 30

        # ── 2. 50 EMA slope (H1) — weight: 20 ──
        if len(h1_closes) >= 50:
            ema50_series = self._ema_series(h1_closes, 50)
            if len(ema50_series) >= 2:
                slope = ema50_series[-1] - ema50_series[-2]
                if slope > 0:
                    buy_score += 20
                elif slope < 0:
                    sell_score += 20

        # ── 3. MACD histogram (M5) — weight: 20 ──
        if len(m5_closes) >= 26:
            macd_line, signal, histogram = self._macd(m5_closes)

            # Check if histogram is expanding (current > previous magnitude)
            # Recalculate with one fewer candle to get previous histogram
            _, _, prev_histogram = self._macd(m5_closes[:-1])

            if histogram > 0 and abs(histogram) > abs(prev_histogram):
                buy_score += 20
            elif histogram < 0 and abs(histogram) > abs(prev_histogram):
                sell_score += 20

        # ── 4. RSI regime (M5) — weight: 15 ──
        if len(m5_closes) >= 15:
            rsi_val = self._rsi(m5_closes)
            if rsi_val > 60:
                buy_score += 15
            elif rsi_val < 40:
                sell_score += 15

        # ── 5. RSI divergence (M5) — weight: 10 ──
        if len(m5_closes) >= 19:  # Need enough for RSI series + 5 candle lookback
            rsi_series = self._rsi_series(m5_closes)
            if len(rsi_series) >= 5:
                div = self._divergence(m5_closes[-5:], rsi_series[-5:])
                if div == 'bullish':
                    buy_score += 10
                elif div == 'bearish':
                    sell_score += 10

        # ── 6. Bollinger Bands (M5) — weight: 10 ──
        if len(m5_closes) >= 20:
            upper, lower, bb_mid, bandwidth = self._bollinger(m5_closes)

            # Also get previous bandwidth for expansion detection
            _, _, _, prev_bandwidth = self._bollinger(m5_closes[:-1])
            expanding = bandwidth > prev_bandwidth

            if expanding:
                # Price riding upper band with expansion -> bullish
                if mid >= upper:
                    buy_score += 10
                # Price riding lower band with expansion -> bearish
                elif mid <= lower:
                    sell_score += 10

        # ── 7. Stochastic crossover (M1) — weight: 5 ──
        if len(m1_closes) >= 17:  # k_period(14) + d_period(3)
            k_curr, d_curr, k_prev, d_prev = self._stochastic(
                m1_highs, m1_lows, m1_closes
            )

            # Bullish cross: %K crosses above %D below 40
            if k_prev <= d_prev and k_curr > d_curr and k_curr < 40:
                buy_score += 5
            # Bearish cross: %K crosses below %D above 60
            elif k_prev >= d_prev and k_curr < d_curr and k_curr > 60:
                sell_score += 5

        # ── Resolution ──
        direction = 'buy' if buy_score >= sell_score else 'sell'

        print(f'[DIR] BUY_SCORE={buy_score} SELL_SCORE={sell_score} → {direction.upper()}')

        return direction
