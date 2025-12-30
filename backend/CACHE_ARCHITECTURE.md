# Cache Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FileConverter API                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP Request
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Router Layer                            │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │  Image   │  Video   │  Audio   │ Document │    ...       │  │
│  │  Router  │  Router  │  Router  │  Router  │  (10 total)  │  │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┴──────┬───────┘  │
│       │          │          │          │            │           │
└───────┼──────────┼──────────┼──────────┼────────────┼───────────┘
        │          │          │          │            │
        │ convert_with_cache()                        │
        ▼          ▼          ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Base Converter Layer                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           convert_with_cache() Method                      │ │
│  │                                                             │ │
│  │  1. Generate cache key                                     │ │
│  │     └─> file_hash + output_format + options_hash           │ │
│  │                                                             │ │
│  │  2. Check cache ───────┐                                   │ │
│  │                        ▼                                    │ │
│  │              ┌──────────────────┐                          │ │
│  │              │  Cache Service   │                          │ │
│  │              │  get_cached()    │                          │ │
│  │              └────────┬─────────┘                          │ │
│  │                       │                                     │ │
│  │            ┌──────────┴──────────┐                         │ │
│  │            ▼                     ▼                          │ │
│  │        Cache Hit             Cache Miss                    │ │
│  │     (Return cached)       (Continue to 3)                  │ │
│  │                                                             │ │
│  │  3. Perform conversion                                     │ │
│  │     └─> Call actual convert() method                       │ │
│  │                                                             │ │
│  │  4. Store in cache                                         │ │
│  │     └─> Cache service stores result                        │ │
│  │                                                             │ │
│  │  5. Return converted file                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────┬─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Cache Service Layer                        │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              CacheService Class                            │ │
│  │                                                             │ │
│  │  Methods:                                                  │ │
│  │  • generate_cache_key()     Generate unique identifier    │ │
│  │  • get_cached_result()      Check & retrieve cached file  │ │
│  │  • store_result()           Save conversion result        │ │
│  │  • cleanup_expired()        Remove old entries            │ │
│  │  • cleanup_by_size()        Enforce size limits           │ │
│  │  • get_cache_info()         Statistics & monitoring       │ │
│  │                                                             │ │
│  │  Statistics:                                               │ │
│  │  • hits: Counter            Cache hit count               │ │
│  │  • misses: Counter          Cache miss count              │ │
│  │  • total_requests: Counter  Total cache lookups           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────┬─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      File System Layer                           │
│                                                                   │
│  cache/                                                          │
│  ├── {cache_key_1}/                                             │
│  │   ├── metadata.json          ← Cache metadata               │
│  │   └── converted_file.ext     ← Converted file               │
│  ├── {cache_key_2}/                                             │
│  │   ├── metadata.json                                          │
│  │   └── converted_file.ext                                     │
│  └── ...                                                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow Diagram

```
User Request
     │
     ▼
┌─────────────────────┐
│   Upload File       │
│   + Options         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Router: converter.convert_with_cache() │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Generate Cache Key                 │
│  hash(file) + format + hash(options)│
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Check Cache                        │
│  cache_service.get_cached_result()  │
└──────────┬──────────────────────────┘
           │
           ├──────────────┬─────────────────┐
           ▼              ▼                 ▼
      ┌────────┐    ┌─────────┐      ┌──────────┐
      │  HIT   │    │  MISS   │      │ EXPIRED  │
      │  ✓     │    │  ✗      │      │  ✗       │
      └───┬────┘    └────┬────┘      └─────┬────┘
          │              │                  │
          │              ▼                  │
          │         ┌──────────────────┐   │
          │         │  Perform         │   │
          │         │  Conversion      │◄──┘
          │         │  (CPU intensive) │
          │         └────────┬─────────┘
          │                  │
          │                  ▼
          │         ┌──────────────────┐
          │         │  Store in Cache  │
          │         │  + Metadata      │
          │         └────────┬─────────┘
          │                  │
          └──────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │ Return File      │
           │ to User          │
           └─────────┬────────┘
                     │
                     ▼
              ┌───────────┐
              │ Response  │
              └───────────┘
```

## Cache Key Generation

```
Input File: image.png (contains "data")
Output Format: jpg
Options: {quality: 95, width: 800}

                    ┌─────────────────┐
                    │  Read File      │
                    │  image.png      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  MD5 Hash       │
                    │  "data"         │
                    └────────┬────────┘
                             │
                 file_hash = "c8e2975020a1708a93422e96b717bad1"

Options: {quality: 95, width: 800}
         │
         ▼
┌─────────────────────┐
│  JSON stringify     │
│  (sorted keys)      │
└──────────┬──────────┘
           │
    JSON = '{"quality":95,"width":800}'
           │
           ▼
┌─────────────────────┐
│  MD5 Hash           │
│  (first 8 chars)    │
└──────────┬──────────┘
           │
options_hash = "96451082"

                    ┌─────────────────────┐
                    │  Combine            │
                    │  file_hash +        │
                    │  format +           │
                    │  options_hash       │
                    └──────────┬──────────┘
                               │
                               ▼
    cache_key = "c8e2975020a1708a93422e96b717bad1_jpg_96451082"
```

## Cache Cleanup Flow

```
Background Task (Hourly)
         │
         ▼
┌──────────────────────┐
│  Cleanup Trigger     │
│  (Every 3600s)       │
└─────────┬────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  cache_service.cleanup_all()      │
└─────────┬─────────────────────────┘
          │
          ├─────────────────┬───────────────────┐
          ▼                 ▼                   ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Expired?        │ │  Corrupted?  │ │  Size > Limit?   │
│  (check time)    │ │  (check files)│ │  (check total)   │
└────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
         │                  │                  │
         ▼                  ▼                  ▼
   ┌──────────┐       ┌──────────┐      ┌───────────────┐
   │ Remove   │       │ Remove   │      │ Remove Oldest │
   │ Expired  │       │ Invalid  │      │ Until < Limit │
   └────┬─────┘       └────┬─────┘      └───────┬───────┘
        │                  │                     │
        └──────────────────┴─────────────────────┘
                           │
                           ▼
                ┌────────────────────┐
                │  Log Statistics    │
                │  - Entries removed │
                │  - Space freed     │
                └────────────────────┘
```

## Metadata Structure

```
metadata.json
{
  "cache_key": "c8e297...96451082",          ← Unique identifier
  "original_filename": "input.png",          ← Original file name
  "output_file": "/path/to/cache/.../out.jpg", ← Cached file path
  "output_format": "jpg",                    ← Output format
  "created_at": 1703980800.0,                ← Timestamp (Unix)
  "expires_at": 1703984400.0,                ← Expiration (Unix)
  "file_size": 245678,                       ← Size in bytes
  "conversion_options": {                    ← Options used
    "quality": 95,
    "width": 800
  }
}

Validation on read:
  ✓ JSON parseable?
  ✓ All fields present?
  ✓ Output file exists?
  ✓ Not expired? (expires_at > now)

  If any fail → Remove entry, return cache miss
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Startup                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  main.py: lifespan()   │
              └────────────┬───────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
     ┌──────────────────┐   ┌────────────────────┐
     │  Initialize      │   │  Start Background  │
     │  Cache Service   │   │  Cleanup Task      │
     └────────┬─────────┘   └─────────┬──────────┘
              │                       │
              ▼                       │
     ┌──────────────────┐             │
     │  Initial Cleanup │             │
     │  - Expired       │             │
     │  - Corrupted     │             │
     │  - Size limit    │             │
     └──────────────────┘             │
                                      │
                                      ▼
                           ┌──────────────────┐
                           │  Hourly Loop     │
                           │  - Temp files    │
                           │  - Upload files  │
                           │  - Cache cleanup │
                           └──────────────────┘
```

## API Endpoints

```
Cache Management API
│
├─ GET /api/cache/info
│  └─> Returns:
│      • Cache enabled/disabled
│      • Total size (MB)
│      • Entry count
│      • Hit rate
│      • Statistics (hits, misses, total)
│
├─ POST /api/cache/cleanup
│  └─> Triggers:
│      • Remove expired entries
│      • Enforce size limits
│      • Returns cleanup statistics
│
└─ DELETE /api/cache/clear
   └─> Actions:
       • Removes ALL cache entries
       • Resets statistics
       • Returns success confirmation
```

## Performance Comparison

```
Without Cache:
User Request → Router → Converter → [Conversion Process] → Response
                                    └─> Takes 1-30 seconds

Time: ████████████████████████████████ 30s


With Cache (Hit):
User Request → Router → Cache Check → [Cache Hit!] → Response
                                      └─> Takes 0.05-0.2 seconds

Time: █ 0.2s

Speedup: 150x faster!


With Cache (Miss):
User Request → Router → Cache Check → [Miss] → Convert → Cache Store → Response
                                                └─> Same as without cache + tiny overhead

Time: ████████████████████████████████▌ 30.1s

Overhead: Negligible (~0.1s)
```

## Error Handling Flow

```
Cache Operation
       │
       ├────────────────┬─────────────────┬────────────────┐
       ▼                ▼                 ▼                ▼
  File Error    Metadata Error    Disk Full      Network Error
       │                │                 │                │
       ▼                ▼                 ▼                ▼
   Log Error        Log Error        Log Error        Log Error
       │                │                 │                │
       └────────────────┴─────────────────┴────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Graceful Degradation│
                    │  • Don't fail request│
                    │  • Fall back to      │
                    │    normal conversion │
                    │  • User unaffected   │
                    └──────────────────────┘
```

## Statistics Tracking

```
Cache Service Statistics
┌────────────────────────────────────────┐
│                                        │
│  Total Requests: 234                   │
│  ├─ Hits:   156  (66.7%)  ████████░░  │
│  └─ Misses:  78  (33.3%)  ████░░░░░░  │
│                                        │
│  Cache Size: 234.5 MB / 1000 MB        │
│  ██████░░░░░░░░░░░░░░░░░░              │
│                                        │
│  Entries: 42                           │
│                                        │
│  Expiration: 1 hour                    │
│                                        │
└────────────────────────────────────────┘

Logged at INFO level every cache hit
Tracked in cache_service.stats dictionary
Accessible via /api/cache/info endpoint
```

## Summary

This architecture provides:
- **Fast cache lookups** (< 0.1s overhead)
- **Significant speedups** (10-150x for hits)
- **Automatic management** (cleanup, expiration)
- **Robust error handling** (graceful degradation)
- **Comprehensive monitoring** (statistics, APIs)
- **Scalable design** (configurable limits)
