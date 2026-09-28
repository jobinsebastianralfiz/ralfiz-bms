# Lab 5.4: Meetup Hub navigation

Give the meetup app a proper shell: bottom navigation, tabs and a drawer.

## Setup
1. flutter create meetup_hub
2. Replace lib/main.dart with start/lib/main.dart. No packages are needed.

## Tasks
- TODO(1) Wrap the Scaffold in DefaultTabController(length: 3). Show a TabBar
  (Upcoming, Past, Saved) in AppBar.bottom only while the Events destination is selected.
- TODO(2) Make EventsPage return a TabBarView with three EventList children.
  Give each list a PageStorageKey so its scroll position survives tab changes.
- TODO(3) Add a NavigationBar with Events, Tickets and Profile. Use outlined icons
  and filled selectedIcons.
- TODO(4) Replace the list lookup in body with an IndexedStack.
- TODO(5) Add the drawer: a UserAccountsDrawerHeader, Events and My tickets items that
  close the drawer and switch destination, a Divider, and an About item that opens
  showAboutDialog.

## Acceptance criteria
- The Events destination shows three tabs; swiping or tapping switches between them.
- Saved shows only "Flutter Meetup Kochi".
- The TabBar disappears on Tickets and Profile, and the title changes to My tickets / Profile.
- Turn on Event reminders in Profile, go to Tickets, come back: the switch is still on.
- Choose the Saved tab, go to Profile and back: Saved is still selected.
- The hamburger icon opens the drawer; tapping My tickets closes it and shows the tickets.
- About opens a dialog that shows Meetup Hub and 1.0.0.

## Try this
Change IndexedStack back to the list lookup and repeat the reminders test. Explain what you see.
