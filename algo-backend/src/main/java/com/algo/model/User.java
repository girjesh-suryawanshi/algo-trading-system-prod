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

    @Enumerated(EnumType.STRING)
    @Builder.Default
    private AuthProvider provider = AuthProvider.LOCAL;

    private String role;
}
