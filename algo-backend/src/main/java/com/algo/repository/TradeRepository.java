package com.algo.repository;

import com.algo.model.Trade;
import com.algo.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.LocalDateTime;
import java.util.List;

public interface TradeRepository extends JpaRepository<Trade, Long> {
    List<Trade> findByUser(User user);
    List<Trade> findByUserAndCreatedAtAfter(User user, LocalDateTime timestamp);
    List<Trade> findByUserAndStatus(User user, String status);
}
