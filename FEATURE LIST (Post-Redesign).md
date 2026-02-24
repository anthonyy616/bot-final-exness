#   
**FEATURE LIST (Post-Redesign)**  
  
**1) Direction Selection Engine (Mandatory Execution Model)**  
  
**Purpose:**  
**Purpose:**  
**Always output BUY or SELL when atomic fire triggers.**  
  
**Features:**  
**	•	Dual independent scoring: **BUY_SCORE**, **SELL_SCORE  
**	•	Higher timeframe structural bias (200 EMA)**  
**	•	Trend momentum layer (50 EMA + MACD)**  
**	•	RSI regime filter (momentum vs divergence)**  
**	•	Bollinger volatility context**  
**	•	Stochastic timing refinement**  
**	•	Binary resolution rule: **direction = max(BUY_SCORE, SELL_SCORE)  
**	•	No skip logic**  
**	•	No lot size modification**  
**	•	No trade filtering**  
  
⸻  
  
**2) Regime-Aware Scoring Architecture**  
  
**Purpose:**  
**Prevent fighting gold’s dominant move.**  
  
**Features:**  
**	•	H1/H4 200 EMA bias**  
**	•	50 EMA slope detection**  
**	•	MACD histogram expansion check**  
**	•	RSI regime thresholds (60/40 instead of 70/30)**  
**	•	Divergence detection module**  
**	•	Independent buy/sell score accumulation**  
**	•	Deterministic weight model (no micro-optimizing decimals)**  
  
⸻  
  
**3) Mid-Price Anchored Atomic Fire System**  
  
**Purpose:**  
**Eliminate spread-induced directional bias.**  
  
**Features:**  
**	•	Mid-price reference: **(Bid + Ask) / 2  
**	•	Half-spread compensation: **(Ask - Bid) / 2  
**	•	Half-spread compensation: **(Ask - Bid) / 2  
**	•	Symmetric trigger evaluation for first atomic fire**  
**	•	Symmetric trigger evaluation for second atomic fire**  
**	•	Direction execution adjusted by half-spread offset**  
**	•	Identical logic applied to both buy and sell paths**  
**	•	No broker rule violation**  
  
⸻  
  
**4) Spread Normalization Layer**  
  
**Purpose:**  
**Neutralize structural bias caused by execution mechanics.**  
  
**Features:**  
**Features:**  
**	•	Mid-based trigger detection**  
**	•	Ask-adjusted buy execution**  
**	•	Bid-adjusted sell execution**  
**	•	Rolling spread monitor (optional safeguard)**  
**	•	No artificial price distortion in scoring**  
  
⸻  
  
**5) Atomic Fire Consistency Layer**  
  
**Purpose:**  
**Ensure both first and second atomic fires behave identically.**  
  
**Features:**  
**	•	Unified trigger reference model**  
**	•	Unified execution compensation logic**  
**	•	Stateless direction resolution at trigger moment**  
**	•	No asymmetry between long and short mechanics**  
  
⸻  
  
**IMPLEMENTATION PLAN**  
  
**Structured in build order to avoid architectural contamination.**  
  
⸻  
  
**PHASE 1 — Refactor Price Reference System**  
  
**Objective: Remove Bid/Ask dependency from trigger logic.**  
**Objective: Remove Bid/Ask dependency from trigger logic.**  
	1.	Introduce utility:  
  
```
mid = (bid + ask) / 2

```
half_spread = (ask - bid) / 2  
  
  
	2.	Modify first atomic fire trigger:  
	•	Evaluate crossing using mid  
**	•	Remove direct bid/ask comparisons**  
	3.	Modify second atomic fire trigger:  
	•	Same mid-based evaluation  
	4.	Implement symmetric execution:  
	•	If BUY → execute at F + half_spread  
**	•	If SELL → execute at **F - half_spread  
**	•	If SELL → execute at **F - half_spread  
  
**At end of Phase 1:**  
**Both atomic fires are spread-neutral and symmetric.**  
  
⸻  
  
**PHASE 2 — Build Indicator Data Layer**  
  
**Objective: Centralize all indicator calculations.**  
**Objective: Centralize all indicator calculations.**  
  
**Create indicator module that returns structured snapshot:**  
**Create indicator module that returns structured snapshot:**  
  
```
{
    price,
    ema50,
    ema200,
    ema50_slope,
    rsi,
    macd_line,
    macd_signal,
    macd_histogram,
    bb_upper,
    bb_lower,
    stochastic_k,
    stochastic_d
}

```
  
**Ensure:**  
**	•	All indicators use same timeframe**  
**	•	Data computed once per candle**  
**	•	No recalculation during tick noise**  
  
⸻  
  
**PHASE 3 — Structural Bias Module**  
  
**Objective: Add higher timeframe directional weight.**  
  
**Logic:**  
  
```
if price > ema200:
    BUY_SCORE += 
```
```
30

```
```
else
```
```
:

```
    SELL_SCORE += 30  
  
**Add EMA slope confirmation weight.**  
  
**Keep weights coarse integers.**  
  
⸻  
  
**PHASE 4 — Momentum Layer**  
  
**Add:**  
  
**MACD logic:**  
**	•	Above zero + expanding histogram → buy weight**  
**	•	Below zero + expanding histogram → sell weight**  
  
**RSI regime:**  
**	•	RSI > 60 → buy weight**  
**	•	RSI < 40 → sell weight**  
**	•	Divergence adds additional weight**  
  
**Do not penalize continuation using overbought/oversold alone.**  
  
⸻  
  
**PHASE 5 — Volatility Context Layer**  
  
**Add Bollinger evaluation:**  
**	•	Riding upper band with expansion → buy weight**  
**	•	Riding lower band with expansion → sell weight**  
**	•	Divergence at band extreme → opposite boost**  
  
**No rejection logic.**  
**Only weight contribution.**  
  
⸻  
  
**PHASE 6 — Timing Layer**  
  
**Add stochastic:**  
**	•	Bullish cross below 40 → buy boost**  
**	•	Bearish cross above 60 → sell boost**  
  
**Keep low weight to prevent oscillator dominance.**  
  
⸻  
  
**PHASE 7 — Direction Resolver**  
  
**At atomic trigger:**  
**At atomic trigger:**  
  
```
calculate BUY_SCORE
calculate SELL_SCORE

if
```
```
 BUY_SCORE >= SELL_SCORE:

```
```
    direction = BUY
else
```
```
:

```
```
    direction = SELL
```
```


```
  
**No thresholds.**  
**No neutrality.**  
**No skip.**  
  
⸻  
  
**PHASE 8 — Integration Into Atomic Fire Flow**  
  
**New flow:**  
	1.	Mid crosses first atomic level  
	2.	Compute scores  
	3.	Resolve direction  
	4.	Execute first atomic fire with half-spread compensation  
	5.	Same logic repeated at second atomic fire  
  
Single fire TP/SL logic untouched.  
  
⸻  
  
**PHASE 9 — Validation & Testing**  
	1.	Backtest without spread normalization → record bias  
	2.	Backtest with mid normalization → compare symmetry  
	3.	Measure:  
	•	Directional win rate  
	•	Drawdown impact  
	•	Performance during volatility expansion  
	4.	Validate no structural imbalance between long and short cycles  
  
⸻  
  
**Final Architecture State**  
  
**You now have:**  
**	•	Spread-neutral atomic triggers**  
**	•	Regime-aware binary direction selector**  
**	•	Deterministic scoring engine**  
**	•	No trade skipping**  
**	•	No position logic interference**  
**	•	No complexity explosion**  
  
**System remains structurally simple but statistically adaptive.**  
