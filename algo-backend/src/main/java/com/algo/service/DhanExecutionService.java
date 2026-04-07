package com.algo.service;

import com.algo.model.Trade;
import com.algo.model.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class DhanExecutionService {

    private final EncryptionService encryptionService;

    public boolean placeOrder(Trade trade) {
        User user = trade.getUser();
        if (user.getPaperTradingMode()) {
            String type = "WAITING".equals(trade.getStatus()) ? "LIMIT" : "MARKET";
            System.out.println("PAPER MODE [" + type + "]: Skipping API for " + user.getEmail() + " | Price: " + trade.getEntryPrice());
            return true;
        }

        String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
        String clientId = encryptionService.decrypt(user.getDhanClientId());

        if (accessToken == null || clientId == null) {
            return false;
        }

        // Real Dhan API call would go here
        String type = "WAITING".equals(trade.getStatus()) ? "LIMIT" : "MARKET";
        System.out.println("LIVE MODE [" + type + "]: Placing order for " + user.getEmail());
        return true;
    }

    public boolean cancelOrder(Trade trade) {
        User user = trade.getUser();
        if (user.getPaperTradingMode()) {
            System.out.println("PAPER MODE: Cancelling Pending Order for " + user.getEmail());
            return true;
        }
        
        // Real Dhan API Cancel call
        System.out.println("LIVE MODE: Dhan API Cancel for " + user.getEmail());
        return true;
    }
    
    public double getLiveLtp(String securityId) {
        return 15.0; // Mock LTP
    }
}
