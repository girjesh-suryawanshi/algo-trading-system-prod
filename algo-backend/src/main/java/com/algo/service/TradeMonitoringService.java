package com.algo.service;

import com.algo.model.Trade;
import com.algo.repository.TradeRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TradeMonitoringService {

    private final TradeRepository tradeRepository;
    private final DhanExecutionService executionService;

    @Scheduled(fixedRate = 5000) // Every 5 seconds
    public void monitorTrades() {
        List<Trade> openTrades = tradeRepository.findAll().stream()
                .filter(t -> "OPEN".equals(t.getStatus()))
                .toList();

        for (Trade trade : openTrades) {
            // In real app, fetch live LTP for the specific securityId from Dhan API
            double currentLtp = executionService.getLiveLtp(trade.getStrike().toString());

            if (currentLtp <= trade.getStopLoss()) {
                exitTrade(trade, currentLtp, "SL_HIT");
            } else if (currentLtp >= trade.getTarget3()) {
                exitTrade(trade, currentLtp, "TARGET_HIT");
            } else if (currentLtp >= trade.getTarget2() || currentLtp >= trade.getTarget1()) {
                // Partial booking or trailing SL could be implemented here
                System.out.println("Profit target 1/2 reached for " + trade.getSymbol());
            }
        }
    }

    private void exitTrade(Trade trade, double exitPrice, String status) {
        trade.setExitPrice(exitPrice);
        trade.setStatus(status);
        trade.setClosedAt(LocalDateTime.now());
        trade.setPnl((exitPrice - trade.getEntryPrice()) * trade.getQty());
        tradeRepository.save(trade);
        System.out.println("Exited trade: " + trade.getId() + " Status: " + status + " PnL: " + trade.getPnl());
    }
}
