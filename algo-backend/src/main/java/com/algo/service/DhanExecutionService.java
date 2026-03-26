package com.algo.service;

import com.algo.model.Trade;
import org.springframework.stereotype.Service;

@Service
public class DhanExecutionService {

    public boolean placeOrder(Trade trade) {
        // In real scenario, make HTTP call to Dhan API
        // For demonstration, we simulate success
        System.out.println("Placing order on Dhan: " + trade.getSymbol() + " " + trade.getStrike());
        return true;
    }
    
    public double getLiveLtp(String securityId) {
        return 15.0; // Mock LTP
    }
}
