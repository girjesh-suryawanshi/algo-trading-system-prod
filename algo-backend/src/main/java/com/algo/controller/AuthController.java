package com.algo.controller;

import com.algo.model.*;
import com.algo.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<AuthResponse> register(@RequestBody SignupRequest request) {
        String token = authService.register(request.getEmail(), request.getPassword(), request.getName());
        return ResponseEntity.ok(AuthResponse.builder()
                .token(token)
                .email(request.getEmail())
                .name(request.getName())
                .build());
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody LoginRequest request) {
        String token = authService.login(request.getEmail(), request.getPassword());
        User user = authService.findByEmail(request.getEmail()).orElseThrow();
        return ResponseEntity.ok(AuthResponse.builder()
                .token(token)
                .email(user.getEmail())
                .name(user.getName())
                .build());
    }
}
