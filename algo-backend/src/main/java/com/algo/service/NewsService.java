package com.algo.service;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
public class NewsService {

    private final RestTemplate restTemplate = new RestTemplate();
    private final String PYTHON_ENGINE_URL = "http://python:8000/fetch-news"; // Docker internal URL
    
    private List<NewsEvent> todaysEvents = new ArrayList<>();

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class NewsEvent {
        private String title;
        private String time; // HH:mm
        private String impact;
        private String currency;
    }

    /**
     * Fetch economic news daily at 8:00 AM and every 4 hours.
     */
    @Scheduled(cron = "0 0 8,12,16 * * *")
    @Scheduled(fixedRate = 14400000) // Also every 4 hours
    public void fetchNews() {
        try {
            log.info("Fetching today's economic news from engine...");
            Map<String, Object> response = restTemplate.getForObject(PYTHON_ENGINE_URL, Map.class);
            if (response != null && response.containsKey("events")) {
                List<Map<String, String>> eventsList = (List<Map<String, String>>) response.get("events");
                todaysEvents.clear();
                for (Map<String, String> e : eventsList) {
                    todaysEvents.add(new NewsEvent(e.get("title"), e.get("time"), e.get("impact"), e.get("currency")));
                }
                log.info("Loaded {} economic news events.", todaysEvents.size());
            }
        } catch (Exception e) {
            log.error("Failed to fetch news from engine. Falling back to empty list.", e);
        }
    }

    public boolean isNewsPending(int bufferMinutes) {
        if (todaysEvents.isEmpty()) return false;
        
        LocalTime now = LocalTime.now();
        for (NewsEvent event : todaysEvents) {
            if (!"HIGH".equalsIgnoreCase(event.getImpact())) continue;
            
            try {
                LocalTime eventTime = LocalTime.parse(event.getTime());
                LocalTime bufferStart = eventTime.minusMinutes(bufferMinutes);
                LocalTime bufferEnd = eventTime.plusMinutes(bufferMinutes);
                
                if (now.isAfter(bufferStart) && now.isBefore(bufferEnd)) {
                    log.warn("Economic News Kill Switch Triggered! Event: {} at {}", event.getTitle(), event.getTime());
                    return true;
                }
            } catch (Exception ex) {
                log.error("Error parsing news event time: {}", event.getTime());
            }
        }
        return false;
    }
    
    public List<NewsEvent> getTodaysEvents() {
        return todaysEvents;
    }
}
