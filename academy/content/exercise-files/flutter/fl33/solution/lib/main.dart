import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
    home: const HomePage(),
  ));
}

class Meetup {
  const Meetup(this.title, this.date, {this.saved = false});
  final String title;
  final String date;
  final bool saved;
}

const upcoming = [
  Meetup('Flutter Meetup Kochi', 'Sat 10 Oct', saved: true),
  Meetup('Dart 3 Deep Dive', 'Thu 22 Oct'),
  Meetup('State Management Night', 'Sat 7 Nov'),
];
const past = [
  Meetup('Intro to Widgets', 'Sat 12 Sep'),
  Meetup('Firebase Basics', 'Sat 29 Aug'),
];

class HomePage extends StatefulWidget {
  const HomePage({super.key});
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  static const _titles = ['Meetup Hub', 'My tickets', 'Profile'];
  int _index = 0;

  void _select(int i) => setState(() => _index = i);

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(_titles[_index]),
          bottom: _index == 0
              ? const TabBar(tabs: [Tab(text: 'Upcoming'), Tab(text: 'Past'), Tab(text: 'Saved')])
              : null,
        ),
        drawer: AppDrawer(onSelect: _select),
        // IndexedStack keeps every page alive, so each keeps its state.
        body: IndexedStack(
          index: _index,
          children: const [EventsPage(), TicketsPage(), ProfilePage()],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: _select,
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.event_outlined), selectedIcon: Icon(Icons.event), label: 'Events'),
            NavigationDestination(
                icon: Icon(Icons.confirmation_number_outlined),
                selectedIcon: Icon(Icons.confirmation_number),
                label: 'Tickets'),
            NavigationDestination(
                icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Profile'),
          ],
        ),
      ),
    );
  }
}

class AppDrawer extends StatelessWidget {
  const AppDrawer({super.key, required this.onSelect});
  final ValueChanged<int> onSelect;
  @override
  Widget build(BuildContext context) {
    void go(int i) {
      Navigator.pop(context); // close the drawer first
      onSelect(i);
    }

    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          const UserAccountsDrawerHeader(
            accountName: Text('Asha Nair'),
            accountEmail: Text('asha@example.com'),
            currentAccountPicture: CircleAvatar(child: Text('AN')),
          ),
          ListTile(leading: const Icon(Icons.event), title: const Text('Events'), onTap: () => go(0)),
          ListTile(
              leading: const Icon(Icons.confirmation_number),
              title: const Text('My tickets'),
              onTap: () => go(1)),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.info_outline),
            title: const Text('About'),
            onTap: () {
              Navigator.pop(context);
              showAboutDialog(
                  context: context, applicationName: 'Meetup Hub', applicationVersion: '1.0.0');
            },
          ),
        ],
      ),
    );
  }
}

class EventsPage extends StatelessWidget {
  const EventsPage({super.key});
  @override
  Widget build(BuildContext context) {
    final saved = upcoming.where((m) => m.saved).toList();
    return TabBarView(children: [
      EventList(key: const PageStorageKey('upcoming'), items: upcoming),
      EventList(key: const PageStorageKey('past'), items: past),
      EventList(key: const PageStorageKey('saved'), items: saved),
    ]);
  }
}

class EventList extends StatelessWidget {
  const EventList({super.key, required this.items});
  final List<Meetup> items;
  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return const Center(child: Text('Nothing here yet'));
    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, i) => ListTile(
        leading: const CircleAvatar(child: Icon(Icons.event)),
        title: Text(items[i].title),
        subtitle: Text(items[i].date),
        trailing: Icon(items[i].saved ? Icons.bookmark : Icons.bookmark_border),
      ),
    );
  }
}

class TicketsPage extends StatelessWidget {
  const TicketsPage({super.key});
  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(8), children: const [
      Card(child: ListTile(leading: Icon(Icons.qr_code), title: Text('Flutter Meetup Kochi'), subtitle: Text('Student · Sat 10 Oct'))),
      Card(child: ListTile(leading: Icon(Icons.qr_code), title: Text('Dart 3 Deep Dive'), subtitle: Text('Standard · Thu 22 Oct'))),
    ]);
  }
}

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});
  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  bool _reminders = false; // survives tab switches thanks to IndexedStack

  @override
  Widget build(BuildContext context) {
    return ListView(children: [
      const ListTile(
          leading: CircleAvatar(child: Text('AN')), title: Text('Asha Nair'), subtitle: Text('asha@example.com')),
      SwitchListTile(
        title: const Text('Event reminders'),
        value: _reminders,
        onChanged: (v) => setState(() => _reminders = v),
      ),
    ]);
  }
}
