package com.algo.service;

import com.algo.model.DhanOrderRequest;
import com.algo.model.Trade;
import com.algo.model.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class DhanExecutionService {

    private final EncryptionService encryptionService;
    private final RestTemplate restTemplate = new RestTemplate();
    private final String DHAN_BASE_URL = "https://api.dhan.co/v2";

    public boolean placeOrder(Trade trade) {
        User user = trade.getUser();
        if ("PAPER".equals(trade.getTradeMode())) {
            String type = "WAITING".equals(trade.getStatus()) ? "LIMIT" : "MARKET";
            log.info("PAPER MODE [{}]: Simulation of {} for {} | Price: {}", 
                type, trade.getStatus(), user.getEmail(), trade.getEntryPrice());
            return true;
        }

        try {
            String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
            String clientId = encryptionService.decrypt(user.getDhanClientId());

            if (accessToken == null || clientId == null || accessToken.isEmpty()) {
                log.error("Live Execution Failed: Missing Dhan Credentials for {}", user.getEmail());
                return false;
            }

            // Determine if this is an ENTRY (BUY) or EXIT (SELL)
            String transactionType = "BUY";
            if (trade.getStatus().contains("HIT") || trade.getStatus().equals("CLOSED")) {
                transactionType = "SELL";
            }

            DhanOrderRequest request = DhanOrderRequest.builder()
                .dhanClientId(clientId)
                .correlationId(UUID.randomUUID().toString())
                .transactionType(transactionType)
                .exchangeSegment(trade.getExchangeSegment() != null ? trade.getExchangeSegment() : "NSE_FNO")
                .productType("MARGIN") // User approved MARGIN
                .orderType("WAITING".equals(trade.getStatus()) ? "LIMIT" : "MARKET")
                .validity("DAY") // User approved DAY
                .securityId(trade.getSecurityId())
                .quantity(String.valueOf(trade.getQty()))
                .price(transactionType.equals("BUY") ? String.valueOf(trade.getEntryPrice()) : String.valueOf(trade.getExitPrice()))
                .afterMarketOrder(false)
                .build();

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            headers.set("access-token", accessToken);

            HttpEntity<DhanOrderRequest> entity = new HttpEntity<>(request, headers);
            
            log.info("LIVE EXECUTION: Sending {} Order to Dhan for securityId: {}", transactionType, trade.getSecurityId());
            Map<String, Object> response = restTemplate.postForObject(DHAN_BASE_URL + "/orders", entity, Map.class);
            
            if (response != null && response.containsKey("orderId")) {
                trade.setDhanOrderId(response.get("orderId").toString());
                log.info("LIVE SUCCESS: Dhan Order ID: {}", trade.getDhanOrderId());
                return true;
            } else {
                log.error("LIVE FAILED: Dhan API error: {}", response);
                return false;
            }

        } catch (Exception e) {
            log.error("FATAL ERROR: Failed to place live order on Dhan", e);
            return false;
        }
    }

    public boolean cancelOrder(Trade trade) {
        User user = trade.getUser();
        if ("PAPER".equals(trade.getTradeMode())) {
            log.info("PAPER MODE: Cancelling Pending Order for {}", user.getEmail());
            return true;
        }
        
        if (trade.getDhanOrderId() == null) {
            log.warn("LIVE CANCEL: No Dhan Order ID found for trade {}", trade.getId());
            return true;
        }

        try {
            String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
            HttpHeaders headers = new HttpHeaders();
            headers.set("access-token", accessToken);
            HttpEntity<Void> entity = new HttpEntity<>(headers);

            log.info("LIVE CANCEL: Requesting cancellation for Dhan Order: {}", trade.getDhanOrderId());
            restTemplate.delete(DHAN_BASE_URL + "/orders/" + trade.getDhanOrderId(), entity);
            return true;
        } catch (Exception e) {
            log.error("LIVE CANCEL FAILED: Dhan cancellation error", e);
            return false;
        }
    }
    
    public double getLiveLtp(String securityId) {
        // This would typically involve Dhan market feed API
        return 0.0; 
    }
}
