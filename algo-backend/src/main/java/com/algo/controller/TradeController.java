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
import java.util.Map;
import java.util.Optional;

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
        trade.setTradeMode(user.getPaperTradingMode() ? "PAPER" : "LIVE");

        if (!riskService.isSafeToTrade(trade)) {
            trade.setStatus("REJECTED");
            trade.setCreatedAt(LocalDateTime.now());
            repo.save(trade);
            return ResponseEntity.badRequest().body("Risk Blocked: Daily limits or Kill switch active");
        }

        if (executionService.placeOrder(trade)) {
            trade.setStatus("OPEN");
            trade.setCreatedAt(LocalDateTime.now());
            
            // Deduct from Virtual Balance only in PAPER mode
            if ("PAPER".equals(trade.getTradeMode())) {
                double cost = trade.getEntryPrice() * trade.getQty();
                user.setVirtualBalance(user.getVirtualBalance() - cost);
                userRepo.save(user);
            }

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

    // --- Engine Integration Endpoints ---

    @PostMapping("/engine/signal")
    public ResponseEntity<String> receiveSignal(@RequestBody Map<String, Object> signal, @RequestHeader("X-Engine-Token") String token) {
        if (!"lumina-secret-2026".equals(token)) return ResponseEntity.status(401).body("Unauthorized");

        Long userId = Long.valueOf(signal.get("userId").toString());
        User user = userRepo.findById(userId).orElseThrow();

        Trade trade = new Trade();
        trade.setUser(user);
        trade.setSymbol(signal.get("symbol").toString());
        trade.setStrike((int) Double.parseDouble(signal.get("strike").toString()));
        trade.setOptionType(signal.get("optionType").toString());
        trade.setEntryPrice(Double.parseDouble(signal.get("entryPrice").toString()));
        trade.setStopLoss(Double.parseDouble(signal.get("stopLoss").toString()));
        trade.setTarget1(Double.parseDouble(signal.get("target1").toString()));
        trade.setQty(Integer.parseInt(signal.get("qty").toString()));
        trade.setStrategyName(signal.get("strategyName").toString());
        trade.setTradeMode(user.getPaperTradingMode() ? "PAPER" : "LIVE");
        trade.setCreatedAt(LocalDateTime.now());

        boolean isPending = signal.containsKey("isPending") && (boolean) signal.get("isPending");
        trade.setStatus(isPending ? "WAITING" : "OPEN");

        if (executionService.placeOrder(trade)) {
            repo.save(trade);
            return ResponseEntity.ok("Signal Processed: " + trade.getStatus());
        }
        return ResponseEntity.internalServerError().body("Broker Placement Failed");
    }

    @PostMapping("/engine/cancel")
    public ResponseEntity<String> cancelSignal(@RequestBody Map<String, Object> signal, @RequestHeader("X-Engine-Token") String token) {
        if (!"lumina-secret-2026".equals(token)) return ResponseEntity.status(401).body("Unauthorized");

        Long userId = Long.valueOf(signal.get("userId").toString());
        String optType = signal.get("optionType").toString();
        
        // Find existing WAITING trade for this user and option type
        List<Trade> pending = repo.findByUserAndStatus(userRepo.findById(userId).get(), "WAITING");
        Optional<Trade> target = pending.stream().filter(t -> t.getOptionType().equals(optType)).findFirst();

        if (target.isPresent()) {
            Trade t = target.get();
            if (executionService.cancelOrder(t)) {
                t.setStatus("CANCELLED");
                repo.save(t);
                return ResponseEntity.ok("Pending Order Cancelled");
            }
        }
        return ResponseEntity.ok("No pending order to cancel or cancellation failed");
    }
}
