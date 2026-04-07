package com.algo.model;

import jakarta.persistence.*;
import lombok.Data;

import java.time.LocalDateTime;

@Entity
@Table(name = "trades")
@Data
public class Trade {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String symbol;
    private Integer strike;
    private String optionType;

    private Double entryPrice;
    private Double stopLoss;
    private Double target1;
    private Double target2;
    private Double target3;
    
    private Double exitPrice;
    private String status; // OPEN, CLOSED, SL_HIT, TARGET_HIT, REJECTED
    private Double pnl;
    
    private String strategyName;
    private Double trailingSL;
    private Double tslPercentage;
    private Integer qty;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    private LocalDateTime createdAt;
    private LocalDateTime closedAt;
}
