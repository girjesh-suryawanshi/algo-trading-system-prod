package com.algo.service;

import com.algo.model.Trade;
import com.algo.repository.TradeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class RiskService {

    private final TradeRepository tradeRepository;
    
    private boolean killSwitch = false;
    private final double MAX_DAILY_LOSS = -5000.0;
    private final int MAX_TRADES_PER_DAY = 5;

    public boolean isSafeToTrade(Trade trade) {
        if (killSwitch) return false;

        // 1. Time Filter (9:20 AM - 12:00 PM)
        LocalTime now = LocalTime.now();
        if (now.isBefore(LocalTime.of(9, 20)) || now.isAfter(LocalTime.of(12, 0))) {
            return false;
        }

        // 2. Max Trades Check
        long count = tradeRepository.count(); // Simplified: should filter by today
        if (count >= MAX_TRADES_PER_DAY) {
            return false;
        }

        // 3. Daily Loss Check
        List<Trade> todayTrades = tradeRepository.findAll();
        double currentPnl = todayTrades.stream()
                .filter(t -> t.getPnl() != null)
                .mapToDouble(Trade::getPnl)
                .sum();
        
        if (currentPnl <= MAX_DAILY_LOSS) {
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
