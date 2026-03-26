package com.algo.controller;

import com.algo.model.Trade;
import com.algo.repository.TradeRepository;
import com.algo.service.DhanExecutionService;
import com.algo.service.RiskService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class TradeController {

    private final TradeRepository repo;
    private final RiskService riskService;
    private final DhanExecutionService executionService;

    @PostMapping("/trade")
    public ResponseEntity<String> execute(@RequestBody Trade trade) {
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
        return repo.findAll();
    }
    
    @PostMapping("/kill")
    public String killSwitch(@RequestParam boolean active) {
        if (active) riskService.activateKillSwitch();
        else riskService.deactivateKillSwitch();
        return "Kill switch status: " + active;
    }
}
