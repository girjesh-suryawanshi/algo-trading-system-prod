# DhanHQ API v2.0 - Developer Summary

This document serves as a simplified, step-by-step summary of the [DhanHQ v2 API Documentation](https://dhanhq.co/docs/v2/) tailored for Python and Backend developers integrating algorithmic trading systems.

## 1. Overview & Setup

The DhanHQ API is a RESTful robust financial API that allows developers to access market data, execute trades, and manage portfolios programmatically.

### Two Ways to Connect:
1. **REST APIs:** Direct HTTP requests expecting JSON payloads.
2. **Python SDK (Recommended):** The easiest way to integrate Dhan into Python microservices.
   ```bash
   pip install dhanhq
   ```

### Authentication
Every request requires two key credentials:
*   `client_id`: Found in your Dhan Developer Dashboard.
*   `access_token`: A JWT Token generated from your console.

**In Python SDK:**
```python
from dhanhq import dhanhq
dhan = dhanhq("your_client_id", "your_access_token")
```

**In REST API:**
Passed in the Headers:
`access-token: YOUR_JWT_TOKEN`

---

## 2. Core Concepts: Segments & Instruments

Dhan uses a unique `securityId` for all its products rather than just trading symbols. You must specify the `exchangeSegment`:
*   `NSE_EQ`: National Stock Exchange (Equity Shares)
*   `NSE_FNO`: Future & Options
*   `BSE_EQ`: Bombay Stock Exchange
*   `MCX_COMM`: Commodities

*Note: You use `dhanhq` instrument list dumps (Usually a CSV file provided daily by Dhan) to map human-readable symbols (like "RELIANCE") to their exact `securityId`.*

---

## 3. Data APIs (Market Information)

Before placing a trade, your algorithm needs data. The Dhan API provides a few key endpoints:

### A. Market Quotes
Gets the static snapshot of a stock/option for the day (LTP, Open, High, Low, Close, Volume).
```python
dhan.get_market_quote(
    exchange_segment=dhan.NSE_EQ, 
    instrument_type="EQUITY", 
    symbol="RELIANCE", 
    security_id="2885"
)
```

### B. Historical Data
Fetches OHLCV (Open, High, Low, Close, Volume) data bars (e.g., 1 minute, 5 minute, 1 Day candles).

### C. Live Market Feed (WebSockets)
For high-frequency or exact second-by-second updates, you must connect to their **Live Market WebSocket** rather than hitting REST APIs continuously to avoid rate-listing.

### D. Option Chain
Retrieves all available Strikes (Calls and Puts) underlying a specific index (like NIFTY or BANKNIFTY) along with their Greeks and LTPs.

---

## 4. Trading APIs (Execution)

Once the data tells your algorithm to buy or sell, you use the Orders API.

### Placing an Order
The standard payload requires explicit parameters:
*   `transactionType`: `BUY` or `SELL`
*   `orderType`: `MARKET` (execute immediately), `LIMIT` (at specific price), `STOP_LOSS`
*   `productType`: `INTRADAY` (MIS - Auto squared off), `MARGIN` (NRML - Carry forward)

**Example Python Payload:**
```python
dhan.place_order(
    security_id='1333',   # e.g., HDFC Bank
    exchange_segment=dhan.NSE_EQ,
    transaction_type=dhan.BUY,
    quantity=10,
    order_type=dhan.MARKET,
    product_type=dhan.INTRADAY,
    price=0
)
```

### Modifying / Cancelling Orders
*   **Modify:** You can alter the price or quantity of a `PENDING` order using its `orderId`. Note: Dhan explicitly limits order modifications to a **maximum of 25 times per order**.
*   **Cancel:** Cancels an unexecuted limit/trigger order completely.

---

## 5. Account & Post-Trade Events

*   **Portfolio API:** Fetches Holdings and active Positions (M2M PnL, Traded Qty).
*   **Funds & Margins:** Use `dhan.get_fund_limits()` to verify you have enough cash available before dispatching a fat-finger trade.
*   **Postbacks (Webhooks):** Dhan allows you to set up a Webhook URL on their portal. When an order executes, Dhan will send a real-time `POST` request back to your Java Spring Boot backend (`/api/postback`) so your application knows instantly if a Target or StopLoss was hit without repeatedly polling the broker.

---
### Summary of Limits & Errors
*   **Rate Limits:** Polling market data REST endpoints too fast can result in HTTP `429 Too Many Requests`.
*   **Errors:** Standard format: `{ "errorType": ..., "errorCode": ..., "errorMessage": ... }`

---
*Ready for integration into our Python Strategy Engine!*
