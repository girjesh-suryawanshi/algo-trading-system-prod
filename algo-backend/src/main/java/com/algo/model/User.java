package com.algo.model;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = true)
    private String password;

    private String name;

    @Column(columnDefinition = "TEXT")
    private String dhanAccessToken;
    private String dhanClientId;
    
    private String telegramBotToken;
    private String telegramChatId;
    
    @Builder.Default
    private Double targetPriceLimit = 12.0;

    // Trading Preferences
    private String tradingInstrument;
    private String preferredExpiry;
    private Integer instrumentId;
    private String exchangeSegment;

    @Enumerated(EnumType.STRING)
    @Builder.Default
    private AuthProvider provider = AuthProvider.LOCAL;

    @Builder.Default
    private Double maxDailyLoss = 5000.0;
    
    @Builder.Default
    private Integer maxTradesPerDay = 10;
    
    @Builder.Default
    private Double trailingStopLossStep = 1.0;

    @Builder.Default
    private Double vixThreshold = 25.0;

    @Builder.Default
    private Boolean newsKillSwitchActive = true;

    @Builder.Default
    private Integer newsBufferMinutes = 30;

    private String role;
}
