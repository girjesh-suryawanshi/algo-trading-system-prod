package com.algo.controller;

import com.algo.model.User;
import com.algo.model.UserProfileDTO;
import com.algo.repository.UserRepository;
import com.algo.service.EncryptionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class ProfileController {

    private final UserRepository userRepo;
    private final EncryptionService encryptionService;
    private final RestTemplate restTemplate = new RestTemplate();
    private final String pythonUrl = "http://python:8000";

    private User getCurrentUser() {
        String email = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return userRepo.findByEmail(email).orElseThrow(() -> new RuntimeException("User not found"));
    }

    @GetMapping("/profile")
    public ResponseEntity<UserProfileDTO> getProfile() {
        User user = getCurrentUser();
        return ResponseEntity.ok(UserProfileDTO.builder()
                .email(user.getEmail())
                .name(user.getName())
                .dhanAccessToken(mask(user.getDhanAccessToken()))
                .dhanClientId(mask(user.getDhanClientId()))
                .telegramBotToken(mask(user.getTelegramBotToken()))
                .telegramChatId(mask(user.getTelegramChatId()))
                .targetPriceLimit(user.getTargetPriceLimit())
                .tradingInstrument(user.getTradingInstrument())
                .preferredExpiry(user.getPreferredExpiry())
                .instrumentId(user.getInstrumentId())
                .exchangeSegment(user.getExchangeSegment())
                .build());
    }

    @PutMapping("/profile")
    public ResponseEntity<Object> updateProfile(@RequestBody UserProfileDTO dto) {
        log.info("Updating profile for user: {}", dto.getEmail());
        User user = getCurrentUser();
        
        if (dto.getName() != null && !dto.getName().isEmpty()) {
            user.setName(dto.getName());
        }
        
        if (dto.getTargetPriceLimit() != null) {
            user.setTargetPriceLimit(dto.getTargetPriceLimit());
        }
        
        try {
            // Only update if not masked (user entered new value)
            if (dto.getDhanAccessToken() != null && !dto.getDhanAccessToken().contains("••••")) {
                user.setDhanAccessToken(encryptionService.encrypt(dto.getDhanAccessToken()));
            }
            if (dto.getDhanClientId() != null && !dto.getDhanClientId().contains("••••")) {
                user.setDhanClientId(encryptionService.encrypt(dto.getDhanClientId()));
            }
            if (dto.getTelegramBotToken() != null && !dto.getTelegramBotToken().contains("••••")) {
                user.setTelegramBotToken(encryptionService.encrypt(dto.getTelegramBotToken()));
            }
            if (dto.getTelegramChatId() != null && !dto.getTelegramChatId().contains("••••")) {
                user.setTelegramChatId(encryptionService.encrypt(dto.getTelegramChatId()));
            }

            user.setTradingInstrument(dto.getTradingInstrument());
            user.setPreferredExpiry(dto.getPreferredExpiry());
            user.setInstrumentId(dto.getInstrumentId());
            user.setExchangeSegment(dto.getExchangeSegment());

            userRepo.save(user);
            return ResponseEntity.ok(Map.of("message", "Profile updated successfully"));
        } catch (Exception e) {
            log.error("Failed to update profile", e);
            return ResponseEntity.internalServerError().body(Map.of("message", "Failed to update profile: " + e.getMessage()));
        }
    }

    @GetMapping("/instruments")
    public ResponseEntity<Object> getInstruments() {
        try {
            Object response = restTemplate.getForObject(pythonUrl + "/instruments", Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("data", Map.of("NIFTY", 13, "BANKNIFTY", 25, "FINNIFTY", 27, "SENSEX", 1))); 
        }
    }

    @PostMapping("/fetch-expiries")
    public ResponseEntity<Object> fetchExpiries(@RequestBody Map<String, Object> req) {
        User user = getCurrentUser();
        try {
            Map<String, Object> payload = Map.of(
                "accessToken", encryptionService.decrypt(user.getDhanAccessToken()),
                "clientId", encryptionService.decrypt(user.getDhanClientId()),
                "securityId", req.get("securityId"),
                "segment", req.get("segment")
            );
            Object response = restTemplate.postForObject(pythonUrl + "/fetch-expiries", payload, Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error fetching expiries from python", e);
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @PostMapping("/engine/toggle")
    public ResponseEntity<Object> toggleEngine(@RequestBody Map<String, Object> params) {
        User user = getCurrentUser();
        boolean active = (boolean) params.getOrDefault("active", false);
        String endpoint = active ? "/engine/start" : "/engine/stop";
        
        Map<String, Object> payload = Map.of(
            "userId", user.getId(),
            "accessToken", encryptionService.decrypt(user.getDhanAccessToken()),
            "clientId", encryptionService.decrypt(user.getDhanClientId()),
            "targetPriceLimit", user.getTargetPriceLimit(),
            "symbol", params.getOrDefault("symbol", "NIFTY"),
            "securityId", String.valueOf(params.getOrDefault("securityId", "13")),
            "segment", params.getOrDefault("segment", "IDX_I"),
            "expiry", params.getOrDefault("expiry", "")
        );

        try {
            Object response = restTemplate.postForObject(pythonUrl + endpoint, payload, Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error toggling engine", e);
            return ResponseEntity.internalServerError().body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/engine/status")
    public ResponseEntity<Object> getEngineStatus() {
        User user = getCurrentUser();
        try {
            Object response = restTemplate.getForObject(pythonUrl + "/engine/status/" + user.getId(), Object.class);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("auto_running", false));
        }
    }

    private String mask(String value) {
        if (value == null || value.isEmpty()) return "";
        try {
            String decrypted = encryptionService.decrypt(value);
            if (decrypted == null || decrypted.isEmpty()) return "";
            if (decrypted.length() <= 4) return "••••";
            return "••••" + decrypted.substring(decrypted.length() - 4);
        } catch (Exception e) {
            log.warn("Failed to decrypt field during masking: {}", e.getMessage());
            return ""; // Return empty instead of crashing the whole profile load
        }
    }
}
