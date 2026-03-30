package com.algo.model;

import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserProfileDTO {
    private String email;
    private String name;
    
    private String dhanAccessToken; // Will be masked when sending GET
    private String dhanClientId;
    private String telegramBotToken;
    private String telegramChatId;
    
    private Double targetPriceLimit;
    
    // Trading Preferences
    private String tradingInstrument;
    private String preferredExpiry;
    private Integer instrumentId;
    private String exchangeSegment;
    
    private Double maxDailyLoss;
    private Integer maxTradesPerDay;
    private Double trailingStopLossStep;
}
