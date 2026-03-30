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

@Slf4j
@RestController
@RequestMapping("/api/user")
@RequiredArgsConstructor
public class ProfileController {

    private final UserRepository userRepo;
    private final EncryptionService encryptionService;

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
                .build());
    }

    @PutMapping("/profile")
    public ResponseEntity<String> updateProfile(@RequestBody UserProfileDTO dto) {
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

            userRepo.save(user);
            return ResponseEntity.ok("Profile updated successfully");
        } catch (Exception e) {
            log.error("Failed to update profile", e);
            return ResponseEntity.internalServerError().body("Failed to update profile: " + e.getMessage());
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
