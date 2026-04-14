package com.algo.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class DhanOrderRequest {
    private String dhanClientId;
    private String correlationId;
    private String transactionType; // BUY or SELL
    private String exchangeSegment; // NSE_EQ, NSE_FNO, etc.
    private String productType;     // MARGIN, INTRADAY, CNC, etc.
    private String orderType;       // MARKET, LIMIT, SL, SLM
    private String validity;        // DAY, IOC
    private String securityId;
    private String quantity;
    private String price;
    private String triggerPrice;
    private boolean afterMarketOrder;
}
