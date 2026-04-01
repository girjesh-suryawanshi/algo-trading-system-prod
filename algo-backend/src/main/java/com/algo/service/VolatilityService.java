package com.algo.service;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.util.concurrent.atomic.AtomicReference;

@Service
@Slf4j
@RequiredArgsConstructor
public class VolatilityService {

    private final AtomicReference<Double> currentIndiaVix = new AtomicReference<>(15.0);

    @Getter
    private Double indiaVix = 15.0;

    /**
     * Poll India VIX every 1 minute during market hours.
     * In a real implementation, this would call the Dhan API for Security ID: 21.
     */
    @Scheduled(fixedRate = 60000)
    public void fetchLatestVix() {
        try {
            // Mocking VIX fluctuation between 12 and 18 for demo purposes
            double mockVix = 12.0 + (Math.random() * 6.0);
            indiaVix = mockVix;
            currentIndiaVix.set(mockVix);
            log.info("Updated India VIX: {}", String.format("%.2f", mockVix));
        } catch (Exception e) {
            log.error("Failed to fetch India VIX", e);
        }
    }
    
    public double getCurrentVix() {
        return indiaVix;
    }
}
