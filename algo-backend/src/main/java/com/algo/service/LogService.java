package com.algo.service;

import com.algo.model.SystemLog;
import com.algo.repository.SystemLogRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.time.LocalDateTime;

@Service
@RequiredArgsConstructor
public class LogService {
    private final SystemLogRepository repository;

    public void log(String message, String type) {
        SystemLog log = new SystemLog();
        log.setMessage(message);
        log.setType(type);
        log.setTimestamp(LocalDateTime.now());
        repository.save(log);
    }
}
