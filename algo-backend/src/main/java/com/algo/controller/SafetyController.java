package com.algo.controller;

import com.algo.service.NewsService;
import com.algo.service.VolatilityService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/safety")
@RequiredArgsConstructor
public class SafetyController {

    private final VolatilityService vixService;
    private final NewsService newsService;

    @GetMapping("/status")
    public ResponseEntity<Object> getSafetyStatus() {
        return ResponseEntity.ok(Map.of(
            "indiaVix", vixService.getCurrentVix(),
            "newsEvents", newsService.getTodaysEvents(),
            "isNewsPending", newsService.isNewsPending(30) // Default 30 min check
        ));
    }
}
