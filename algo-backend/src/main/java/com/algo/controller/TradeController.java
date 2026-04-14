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
        trade.setManualTrade(true);
        trade.setTradeMode(user.getPaperTradingMode() ? "PAPER" : "LIVE");
        trade.setExchangeSegment(user.getExchangeSegment());
        trade.setSecurityId(user.getInstrumentId() != null ? user.getInstrumentId().toString() : null);

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

        boolean isPending = signal.containsKey("isPending") && (boolean) signal.get("isPending");
        String status = isPending ? "WAITING" : "OPEN";

        String symbol = signal.get("symbol").toString();
        String strikeStr = signal.get("strike").toString();
        int strike = (int) Double.parseDouble(strikeStr);
        String optType = signal.get("optionType").toString();

        // Fix Duplicate: Check for ANY active trade (WAITING or OPEN) for this instrument
        Optional<Trade> existing = repo.findByUserAndSymbolAndStatusIn(user, symbol, java.util.List.of("WAITING", "OPEN"));

        Trade trade;
        if (existing.isPresent()) {
            trade = existing.get();
        } else {
            trade = new Trade();
            trade.setUser(user);
            trade.setSymbol(symbol);
            trade.setStrike(strike);
            trade.setOptionType(optType);
            trade.setStrategyName(signal.get("strategyName").toString());
            trade.setTradeMode(user.getPaperTradingMode() ? "PAPER" : "LIVE");
            trade.setSecurityId(signal.containsKey("securityId") ? signal.get("securityId").toString() : null);
            trade.setExchangeSegment(signal.containsKey("segment") ? signal.get("segment").toString() : user.getExchangeSegment());
            trade.setCreatedAt(LocalDateTime.now());
        }

        // Always update prices and OI
        trade.setEntryPrice(Double.parseDouble(signal.get("entryPrice").toString()));
        trade.setStopLoss(Double.parseDouble(signal.get("stopLoss").toString()));
        trade.setTarget1(Double.parseDouble(signal.get("target1").toString()));
        trade.setQty(Integer.parseInt(signal.get("qty").toString()));
        if (signal.containsKey("oi")) {
            trade.setOi(Long.valueOf(signal.get("oi").toString()));
        }
        boolean wasWaiting = existing.map(e -> "WAITING".equals(e.getStatus())).orElse(true);
        trade.setStatus(status);
        trade.setManualTrade(false);

        if ("OPEN".equals(status) && wasWaiting) {
            if ("PAPER".equals(trade.getTradeMode())) {
                double cost = trade.getEntryPrice() * trade.getQty();
                user.setVirtualBalance(user.getVirtualBalance() - cost);
                userRepo.save(user);
            }
        }

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
        String symbol = signal.get("symbol").toString();
        
        // Find existing WAITING trade for this user, symbol and option type
        List<Trade> pending = repo.findByUserAndStatus(userRepo.findById(userId).get(), "WAITING");
        Optional<Trade> target = pending.stream()
                .filter(t -> t.getOptionType().equals(optType) && t.getSymbol().equals(symbol))
                .findFirst();

        if (target.isPresent()) {
            Trade t = target.get();
            t.setStatus("CANCELLED");
            if (executionService.cancelOrder(t)) {
                repo.save(t);
                return ResponseEntity.ok("Pending Order " + optType + " Cancelled");
            } else {
                return ResponseEntity.internalServerError().body("Broker Cancellation Failed");
            }
        }
        return ResponseEntity.ok("No pending order found to cancel");
    }

    @PostMapping("/engine/exit")
    public ResponseEntity<String> executeExit(@RequestBody Map<String, Object> signal, @RequestHeader("X-Engine-Token") String token) {
        if (!"lumina-secret-2026".equals(token)) return ResponseEntity.status(401).body("Unauthorized");

        Long userId = Long.valueOf(signal.get("userId").toString());
        String optType = signal.get("optionType").toString();
        String symbol = signal.get("symbol").toString();
        String status = signal.get("status").toString(); // "TARGET_HIT" or "SL_HIT"
        double exitPrice = Double.parseDouble(signal.get("exitPrice").toString());

        User user = userRepo.findById(userId).get();
        List<Trade> openTrades = repo.findByUserAndStatus(user, "OPEN");
        Optional<Trade> target = openTrades.stream()
                .filter(t -> t.getOptionType().equals(optType) && t.getSymbol().equals(symbol))
                .findFirst();

        if (target.isPresent()) {
            Trade t = target.get();
            t.setStatus(status);
            t.setExitPrice(exitPrice);
            t.setClosedAt(LocalDateTime.now());
            double pnl = (exitPrice - t.getEntryPrice()) * t.getQty();
            t.setPnl(pnl);

            if ("PAPER".equals(t.getTradeMode())) {
                double returnAmount = exitPrice * t.getQty();
                user.setVirtualBalance(user.getVirtualBalance() + returnAmount);
                userRepo.save(user);
            }

            if (executionService.placeOrder(t)) {
                repo.save(t);
                return ResponseEntity.ok("Trade Exited: " + status + " PnL: " + pnl);
            } else {
                return ResponseEntity.internalServerError().body("Broker Exit Failed");
            }
        }
        return ResponseEntity.ok("No open order found to exit");
    }
    @PostMapping("/engine/update")
    public ResponseEntity<String> updateTrade(@RequestBody Map<String, Object> update, @RequestHeader("X-Engine-Token") String token) {
        if (!"lumina-secret-2026".equals(token)) return ResponseEntity.status(401).body("Unauthorized");

        Long userId = Long.valueOf(update.get("userId").toString());
        String optType = update.get("optionType").toString();
        String symbol = update.get("symbol").toString();
        double newSL = Double.parseDouble(update.get("stopLoss").toString());

        User user = userRepo.findById(userId).get();
        List<Trade> openTrades = repo.findByUserAndStatus(user, "OPEN");
        Optional<Trade> target = openTrades.stream()
                .filter(t -> t.getOptionType().equals(optType) && t.getSymbol().equals(symbol))
                .findFirst();

        if (target.isPresent()) {
            Trade t = target.get();
            t.setStopLoss(newSL);
            repo.save(t);
            return ResponseEntity.ok("Trade SL Updated: " + newSL);
        }
        return ResponseEntity.ok("No open trade found to update");
    }
}
