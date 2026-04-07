package com.algo.controller;

import com.algo.model.Trade;
import com.algo.model.User;
import com.algo.repository.TradeRepository;
import com.algo.repository.UserRepository;
import com.algo.service.DhanExecutionService;
import com.algo.service.RiskService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;

@RestController
@RequestMapping("/api/engine")
@RequiredArgsConstructor
public class EngineController {

    private final TradeRepository repo;
    private final UserRepository userRepo;
    private final RiskService riskService;
    private final DhanExecutionService executionService;

    private static final String ENGINE_TOKEN = "lumina-secret-2026";

    @PostMapping("/signal")
    public ResponseEntity<String> receiveSignal(
            @RequestHeader("X-Engine-Token") String token,
            @RequestBody Trade trade) {
        
        if (!ENGINE_TOKEN.equals(token)) {
            return ResponseEntity.status(401).body("Invalid Engine Token");
        }

        Long userId = trade.getUserId();
        if (userId == null) {
            return ResponseEntity.badRequest().body("User ID is missing");
        }

        User user = userRepo.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        
        trade.setUser(user);

        if (!riskService.isSafeToTrade(trade)) {
            trade.setStatus("REJECTED");
            trade.setCreatedAt(LocalDateTime.now());
            repo.save(trade);
            return ResponseEntity.badRequest().body("Risk limits hit");
        }

        if (executionService.placeOrder(trade)) {
            trade.setStatus("OPEN");
            trade.setCreatedAt(LocalDateTime.now());
            
            // Deduct from Virtual Balance
            double cost = trade.getEntryPrice() * trade.getQty();
            user.setVirtualBalance(user.getVirtualBalance() - cost);
            userRepo.save(user);
            
            repo.save(trade);
            return ResponseEntity.ok("Signal Processed Successfully");
        } else {
            return ResponseEntity.internalServerError().body("Execution Failed");
        }
    }
}
