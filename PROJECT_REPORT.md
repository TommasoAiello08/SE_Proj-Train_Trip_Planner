# Italian Train Trip Planner - Project Report

## Project Overview

We developed an intelligent multi-day train travel planner for Italy. It is implemented in Python and designed as a web application with a Flask backend server and an interactive HTML/JavaScript frontend. The system is intended for travelers who want to optimize their Italian rail journeys by visiting multiple cities with real train schedules, curated attractions, and weather-aware recommendations.

## Architecture Components

The project consists of three main components:

**1. Backend Planning Engine**: After receiving user input from the UI (start city, end city, trip duration, and interests like history, art, nature), we compute the optimal route through a multi-stage algorithm:

   - **Stage 1 - Candidate Selection**: From 106 Italian cities, we score each using a route-based function that considers attraction count, interest matching, and geographic alignment. Cities along the direct path (e.g., Bologna between Milano-Roma) receive bonuses, while detours are penalized. This filters down to ~25-35 candidate cities.
   
   - **Stage 2 - Train Matrix Construction**: For each candidate city pair and each day, we query Trenitalia's API for real train schedules. To reduce API load from O(cities²) to manageable levels, we use a greedy neighbor selection that keeps only the 8 most relevant connections per city (based on distance + attraction score), always force-including the final destination to guarantee reachability.
   
   - **Stage 3 - Dynamic Programming Optimization**: We solve `dp[day][city] = max_score` with two transition types: STAY (remain in city if < 2 consecutive days, +30 bonus) or MOVE (travel to new city, +50 exploration bonus - 5×travel_time penalty). The DP respects constraints: travel_time + 2h minimum stay ≤ 13h daily window, max 12h train travel per day. User preferences influence city scores: attractions matching selected interests (history/art/nature) receive 10× weight multipliers.
   
   - **Stage 4 - POI Selection**: For each city in the optimal route, we run a greedy knapsack to select 2-3 attractions per day. POI scoring combines interest matching (×10), rating (×2), and popularity, constrained by a running clock (8:00-21:00, 3h per POI). This connects user preferences directly to daily activities - a "history" interest prioritizes castles and monuments over beaches.

**2. Data Integration Layer**: We aggregate data from multiple sources: Trenitalia's real-time API for train schedules, and OpenStreetMap for 2000+ curated points of interest across 106 Italian provinces (weather integration prepared but not yet implemented). The system includes caching mechanisms (7-day TTL for OSM, per-date for trains) to avoid redundant API calls and improve response times from potential minutes to ~20-30 seconds.

**3. Interactive Frontend**: A web interface allows users to visually select cities on an Italy map, configure trip parameters, and view the generated itinerary with daily schedules, train connections, attractions, costs, and weather information.

## Interesting Problems Encountered

**API Rate Limiting and Timeouts**: The Trenitalia API proved unreliable with frequent connection failures and no documented rate limits. For a 5-day trip with 35 candidate cities and 8 connections per city, we need ~1400 API calls. We implemented aggressive caching, fallback geometric estimations when API calls fail, and timeout handling (5 seconds per request) to prevent the system from hanging indefinitely.

**DP State Space Explosion**: The initial DP formulation had a state space of `days × cities × consecutive_stay_count`, which grew prohibitively large. We reduced complexity by: (1) pre-filtering candidate cities using a route-based scoring function that penalizes detours from the optimal path, (2) limiting connections per city from all candidates to just the 8 most relevant neighbors, and (3) enforcing a maximum 2-day stay constraint to encourage route diversity.

**Destination Reachability Bug**: A critical bug emerged where the DP algorithm could never reach the destination city, even for short trips like Milano→Bologna (200km). The root cause was in the neighbor selection function: while it selected the top-12 closest/highest-scoring cities for each origin, the destination wasn't guaranteed to be included. This caused the algorithm to always fail and trigger a fallback to simple linear routes. We fixed this by ensuring `force_include` cities (especially the destination) are always added first before filling remaining slots with top-scoring neighbors.

**POI Curation Quality**: OpenStreetMap data is noisy and inconsistent. Initially, we retrieved all POIs in a city's bounding box, resulting in thousands of low-quality entries (random benches, bus stops, etc.). We implemented a filtering pipeline that: selects only from 28 meaningful categories (museums, monuments, beaches, etc.), balances rating distribution (mix of top-rated 9-10 and hidden gems 7-8), enforces category diversity to avoid 20 churches, and caches results per city to maintain consistency across requests.

## Ideas and Solutions

**Time-Aware Train Search**: Rather than searching all trains naively, we implemented context-aware scheduling: Day 1 searches from 9:00 AM (early departure), while subsequent days search from 1:00 PM (assuming arrival the previous evening and morning activities). This realistic scheduling improved both computation time and itinerary quality.

**Hybrid Scoring Function**: The DP transition combines multiple factors: raw city attraction score (from OSM data and user interests), exploration bonus (+50 points for visiting new cities), stay bonus (+30 points for consecutive days in the same city to reduce travel fatigue), and travel penalty (-5 points per hour of train travel). This creates naturally balanced itineraries without hard-coding specific behaviors.

**Running Clock Constraint**: Each day has 13 available hours (8:00-21:00). The algorithm enforces `travel_time + minimum_stay_hours ≤ daily_hours`, preventing unrealistic itineraries where travelers spend 10 hours on trains with no time to visit attractions.

## Current Status and Limitations

The system successfully generates diverse, realistic itineraries for trips ranging from 2 to 7+ days across Italy. Testing shows it correctly handles cases like Trieste→Siracusa (5 unique cities), Milano→Palermo (7 unique cities), and short Roma→Napoli (2 cities). 

However, practical limitations remain: the Trenitalia API's unreliability sometimes forces fallback to geometric estimations, the system doesn't handle real-time train delays or cancellations, and computation time for long trips (7+ days, distant cities) can exceed 30 seconds due to API latency. Additionally, the current cost estimation is simplified and doesn't account for advance booking discounts or regional passes.
