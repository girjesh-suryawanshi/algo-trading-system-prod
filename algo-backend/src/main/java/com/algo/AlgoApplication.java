package com.algo;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class AlgoApplication {
    public static void main(String[] args) {
        SpringApplication.run(AlgoApplication.class, args);
    }
}
