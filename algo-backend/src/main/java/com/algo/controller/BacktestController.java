package com.algo.controller;

import com.algo.model.User;
import com.algo.repository.UserRepository;
import com.algo.service.EncryptionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.*;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/backtest")
@RequiredArgsConstructor
public class BacktestController {

    private final UserRepository userRepo;
    private final EncryptionService encryptionService;
    private final RestTemplate restTemplate;
    private final String PYTHON_ENGINE_URL = "http://python:8000/backtest";

    @org.springframework.beans.factory.annotation.Autowired
    public BacktestController(UserRepository userRepo, EncryptionService encryptionService) {
        this.userRepo = userRepo;
        this.encryptionService = encryptionService;
        
        org.springframework.http.client.SimpleClientHttpRequestFactory factory = new org.springframework.http.client.SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(120000); // 120 seconds
        this.restTemplate = new RestTemplate(factory);
    }

    private User getCurrentUser() {
        String email = (String) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return userRepo.findByEmail(email).orElseThrow(() -> new RuntimeException("User not found"));
    }

    @PostMapping("/run")
    public ResponseEntity<Object> runBacktest(@RequestBody Map<String, String> request) {
        User user = getCurrentUser();
        
        String accessToken = encryptionService.decrypt(user.getDhanAccessToken());
        String clientId = encryptionService.decrypt(user.getDhanClientId());

        if (accessToken == null || clientId == null) {
            return ResponseEntity.badRequest().body(Map.of("error", "Dhan API keys not configured in Profile."));
        }

        // Prepare the payload for Python engine
        Map<String, String> pythonPayload = new HashMap<>(request);
        pythonPayload.put("accessToken", accessToken);
        pythonPayload.put("clientId", clientId);

        try {
            ResponseEntity<Object> response = restTemplate.postForEntity(PYTHON_ENGINE_URL, pythonPayload, Object.class);
            return ResponseEntity.ok(response.getBody());
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of("error", "Python Engine communication failed: " + e.getMessage()));
        }
    }
}
