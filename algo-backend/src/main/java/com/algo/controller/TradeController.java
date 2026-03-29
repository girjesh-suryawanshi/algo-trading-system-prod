package com.algo.controller;

import com.algo.model.Trade;
import com.algo.model.User;
import com.algo.repository.TradeRepository;
import com.algo.repository.UserRepository;
import com.algo.service.DhanExecutionService;
import com.algo.service.RiskService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class TradeController {

    private final TradeRepository repo;
    private final UserRepository userRepo;
    private final RiskService riskService;
    private final DhanExecutionService executionService;

    private User getCurrentUser() {
        String email = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return userRepo.findByEmail(email).orElseThrow(() -> new RuntimeException("User not found"));
    }

    @PostMapping("/trade")
    public ResponseEntity<String> execute(@RequestBody Trade trade) {
        User user = getCurrentUser();
        trade.setUser(user);

        if (!riskService.isSafeToTrade(trade)) {
            trade.setStatus("REJECTED");
            trade.setCreatedAt(LocalDateTime.now());
            repo.save(trade);
            return ResponseEntity.badRequest().body("Risk limits hit or Kill switch active");
        }

        if (executionService.placeOrder(trade)) {
            trade.setStatus("OPEN");
            trade.setCreatedAt(LocalDateTime.now());
            repo.save(trade);
            return ResponseEntity.ok("Trade Executed Successfully");
        } else {
            return ResponseEntity.internalServerError().body("Dhan API Order Failed");
        }
    }

    @GetMapping("/trades")
    public List<Trade> getAll() {
        User user = getCurrentUser();
        return repo.findByUser(user);
    }
    
    @PostMapping("/kill")
    public String killSwitch(@RequestParam boolean active) {
        // Kill switch remains global for now, or could be per-user in future
        if (active) riskService.activateKillSwitch();
        else riskService.deactivateKillSwitch();
        return "Kill switch status: " + active;
    }
}
