# Lesson 4.1 lab: Travel Explorer home

Build the Travel Explorer home screen with Material 3 components.

## Components to use
- SearchAnchor.bar: search destinations by name (contains, case-insensitive).
- FilterChip: one per type (Beach, Mountains, City, Heritage, Backwaters). Several can be on.
- SegmentedButton<Budget>: Budget, Mid, Luxury. One or none can be selected.
- DestinationCard: Card with a coloured header icon, a ListTile and a favourite IconButton.
- NavigationBar: Explore and Saved; Badge.count on the Saved icon.

## Files
- start/lib/main.dart: data and a plain list. Complete TODO(1) to TODO(5).
- solution/lib/main.dart: the finished screen.

## Acceptance criteria
- Typing "ba" in the search view suggests Dubai and Banff.
- Selecting Mountains shows Munnar and Banff; adding Luxury leaves only Banff.
- Tapping Luxury again clears the budget filter.
- Saving Goa and Jaipur makes the Saved badge show 2; the Saved tab lists both.
- With no match, the text "No destinations match" appears.
