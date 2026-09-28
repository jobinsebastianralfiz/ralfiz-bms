# Lesson 10.2 lab: choosing storage and caching API responses

TaskFlow's todo screen loads https://dummyjson.com/todos?limit=20. Today it
waits for the network on every start and shows an error offline. You will:

- keep the dark mode switch in shared_preferences (already done for you),
- cache the API response in a Hive CE box with your own TypeAdapter,
- show the cached copy instantly, then refresh from the network
  (cache-then-network), with a 5 minute freshness window (TTL),
- fall back to the saved copy when the network fails.

## Setup

    flutter create taskflow_cache
    cd taskflow_cache
    flutter pub add dio hive_ce hive_ce_flutter shared_preferences

Why hive_ce and not hive? The original hive package is no longer
maintained. Hive CE (community edition) is the maintained continuation
with the same style of API.

Copy the files:

- flutter/fl56/lib/main.dart -> lib/main.dart (finished UI)
- flutter/fl56/start/lib/data/todo_cache.dart -> lib/data/todo_cache.dart

Run on an Android or iOS emulator (desktop and web work too).

## Your tasks (TODOs in todo_cache.dart)

1-2. CachedResponseAdapter: write the body then the time; read them back
     in the same order.
3.   Register the adapter before opening the box.
4-5. CacheStore.read and CacheStore.write.
6.   watchTodos: yield the cached copy first; skip the network when the
     copy is fresh (younger than ttl) and force is false.
7.   Save the network response in the cache.
8.   On DioException: show the cached copy with the warning
     "Offline: showing saved data", or rethrow when there is no copy.

## How to test offline

Start the app once online. Then turn on airplane mode on the emulator
(or disconnect your computer) and tap Refresh. Within 5 minutes of the
last download a restart does not even try the network: the copy is fresh.

## Acceptance criteria

- First start online: a spinner, then 20 todos and the banner
  "Fresh from the network".
- Restart within 5 minutes: the list appears at once with
  "From cache, saved ..." and no network call is made.
- Tapping Refresh shows the cached copy, then "Fresh from the network".
- Offline, tap Refresh (or restart after more than 5 minutes): the saved
  list stays on screen and the banner turns red with
  "Offline: showing saved data".
- After Clear cache, an offline restart shows
  "Could not load todos. Check your connection." and a Retry button.
- The dark mode choice survives a restart.