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

    @Transient
    private Long userId;

    private String symbol;
    private Integer strike;
    private String optionType;
    private String securityId;
    private String exchangeSegment;

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
    private Long oi;
    private Boolean manualTrade = false;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id")
    private User user;

    private String tradeMode; // PAPER or LIVE
    private String dhanOrderId;
    private LocalDateTime createdAt;
    private LocalDateTime closedAt;
}
