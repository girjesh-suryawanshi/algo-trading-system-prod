package com.algo.service;

import com.algo.model.Trade;
import com.algo.model.User;
import com.algo.repository.TradeRepository;
import com.algo.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class RiskService {

    private final TradeRepository tradeRepository;
    private final UserRepository userRepo;
    
    private boolean killSwitch = false;
    private static final double DEFAULT_MAX_DAILY_LOSS = 5000.0;
    private static final int DEFAULT_MAX_TRADES_PER_DAY = 10;

    public boolean isSafeToTrade(Trade trade) {
        if (killSwitch) return false;

        // Try to get user settings from the trade's user or the first user in DB
        User user = null;
        if (trade.getUser() != null) {
            user = trade.getUser();
        } else {
            user = userRepo.findAll().stream().findFirst().orElse(null);
        }

        double maxLoss = (user != null) ? user.getMaxDailyLoss() : DEFAULT_MAX_DAILY_LOSS;
        int maxTrades = (user != null) ? user.getMaxTradesPerDay() : DEFAULT_MAX_TRADES_PER_DAY;

        // 1. Time Filter (9:20 AM - 3:20 PM for Indian Markets)
        LocalTime now = LocalTime.now();
        if (now.isBefore(LocalTime.of(9, 20)) || now.isAfter(LocalTime.of(15, 20))) {
            return false;
        }

        // 2. Max Trades Check
        long count = tradeRepository.count(); 
        if (count >= maxTrades) {
            return false;
        }

        // 3. Daily Loss Check
        List<Trade> todayTrades = tradeRepository.findAll();
        double currentPnl = todayTrades.stream()
                .filter(t -> t.getPnl() != null)
                .mapToDouble(Trade::getPnl)
                .sum();
        
        if (currentPnl <= -Math.abs(maxLoss)) { // Ensure it's treated as a negative floor
            return false;
        }

        // 4. Validate One Trade Per Strike / No Duplicates
        boolean hasDuplicateOrActive = todayTrades.stream()
                .anyMatch(t -> t.getStrike() != null &&
                        t.getStrike().equals(trade.getStrike()) &&
                        t.getOptionType() != null &&
                        t.getOptionType().equals(trade.getOptionType()) &&
                        "OPEN".equals(t.getStatus()));

        if (hasDuplicateOrActive) {
            return false;
        }

        return true;
    }

    public void activateKillSwitch() {
        this.killSwitch = true;
    }
    
    public void deactivateKillSwitch() {
        this.killSwitch = false;
    }
}
