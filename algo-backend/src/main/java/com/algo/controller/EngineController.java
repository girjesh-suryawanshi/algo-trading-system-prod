package com.algo.controller;

import com.algo.model.User;
import com.algo.repository.UserRepository;
import com.algo.service.EncryptionService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/engine")
@RequiredArgsConstructor
public class EngineController {

    private final UserRepository userRepo;
    private final EncryptionService encryptionService;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${app.maxConcurrentEngines:10}")
    private int maxConcurrentEngines;

    private final String PYTHON_ENGINE_URL = "http://python:8000/engine";

    private User getCurrentUser() {
        String email = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return userRepo.findByEmail(email).orElseThrow(() -> new RuntimeException("User not found"));
    }

    @PostMapping("/toggle")
    public ResponseEntity<Object> toggleEngine(@RequestParam boolean active) {
        User user = getCurrentUser();
        
        String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
        String clientId = encryptionService.decrypt(user.getDhanClientId());

        if (accessToken == null || clientId == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Dhan API keys not configured in Profile."));
        }

        Map<String, Object> payload = new HashMap<>();
        payload.put("userId", user.getId());
        payload.put("accessToken", accessToken);
        payload.put("clientId", clientId);
        payload.put("targetPriceLimit", user.getTargetPriceLimit());

        String endpoint = active ? "/start" : "/stop";
        try {
            ResponseEntity<Object> response = restTemplate.postForEntity(PYTHON_ENGINE_URL + endpoint, payload, Object.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "Engine communication failed: " + e.getMessage()));
        }
    }

    @GetMapping("/status")
    public ResponseEntity<Object> getStatus() {
        User user = getCurrentUser();
        try {
            ResponseEntity<Object> response = restTemplate.getForEntity(PYTHON_ENGINE_URL + "/status/" + user.getId(), Object.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.ok(Map.of("auto_running", false, "strategy_state", new HashMap<>()));
        }
    }
}
