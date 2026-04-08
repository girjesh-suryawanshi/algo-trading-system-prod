package com.algo.service;

import com.algo.model.Trade;
import com.algo.model.User;
import com.algo.repository.TradeRepository;
import com.algo.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class RiskService {

    private final TradeRepository tradeRepository;
    private final UserRepository userRepo;
    private final VolatilityService vixService;
    private final NewsService newsService;
    
    private boolean killSwitch = false;
    private static final double DEFAULT_MAX_DAILY_LOSS = 5000.0;
    private static final int DEFAULT_MAX_TRADES_PER_DAY = 10;
    private static final double DEFAULT_VIX_THRESHOLD = 25.0;
    private static final int DEFAULT_NEWS_BUFFER = 30;

    public boolean isSafeToTrade(Trade trade) {
        if (Boolean.TRUE.equals(trade.getManualTrade())) return true; // Bypass for manual trades
        if (killSwitch) return false;

        // Try to get user settings from the trade's user or the first user in DB
        User user = (trade.getUser() != null) ? trade.getUser() : userRepo.findAll().stream().findFirst().orElse(null);

        double maxLoss = (user != null) ? user.getMaxDailyLoss() : DEFAULT_MAX_DAILY_LOSS;
        int maxTrades = (user != null) ? user.getMaxTradesPerDay() : DEFAULT_MAX_TRADES_PER_DAY;
        double vixLimit = (user != null) ? user.getVixThreshold() : DEFAULT_VIX_THRESHOLD;
        int newsBuffer = (user != null) ? user.getNewsBufferMinutes() : DEFAULT_NEWS_BUFFER;
        boolean newsKillSwitchEnabled = (user != null) && user.getNewsKillSwitchActive();

        // 1. Time Filter (9:20 AM - 3:20 PM)
        LocalTime now = LocalTime.now();
        if (now.isBefore(LocalTime.of(9, 20)) || now.isAfter(LocalTime.of(15, 20))) {
            return false;
        }

        // 2. India VIX Filter (Bypassed in Paper Mode)
        if (user != null && !user.getPaperTradingMode() && vixService.getCurrentVix() > vixLimit) {
            return false;
        }

        // 3. Economic News Kill Switch (Bypassed in Paper Mode)
        if (user != null && !user.getPaperTradingMode() && newsKillSwitchEnabled && newsService.isNewsPending(newsBuffer)) {
            return false;
        }

        // 4. Max Trades Check
        LocalDateTime startOfDay = LocalDateTime.now().with(LocalTime.MIN);
        List<Trade> todayTrades = tradeRepository.findByUserAndCreatedAtAfter(user, startOfDay);
        
        if (todayTrades.size() >= maxTrades) {
            return false;
        }

        // 5. Daily Loss Check
        double currentPnl = todayTrades.stream()
                .filter(t -> t.getPnl() != null)
                .mapToDouble(Trade::getPnl)
                .sum();
        
        if (currentPnl <= -Math.abs(maxLoss)) {
            return false;
        }

        // 6. Validate One Trade Per Strike
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
