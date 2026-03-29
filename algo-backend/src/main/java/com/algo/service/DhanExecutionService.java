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
        String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
        String clientId = encryptionService.decrypt(user.getDhanClientId());

        if (accessToken == null || clientId == null) {
            System.err.println("User " + user.getEmail() + " has not configured Dhan API keys.");
            return false;
        }

        // Real Dhan API call would go here using decrypted accessToken/clientId
        System.out.println("Placing order for User: " + user.getEmail() + " | Strike: " + trade.getStrike() + " Type: " + trade.getOptionType());
        return true;
    }
    
    public double getLiveLtp(String securityId) {
        return 15.0; // Mock LTP
    }
}
