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
    // TODO(1): wrap the Scaffold in DefaultTabController(length: 3) and, when
    //          _index == 0, set AppBar.bottom to a TabBar: Upcoming, Past, Saved.
    return Scaffold(
      appBar: AppBar(title: Text(_titles[_index])),
      // TODO(5): add drawer: AppDrawer(onSelect: _select) and finish AppDrawer below.
      // TODO(4): replace this list lookup with an IndexedStack so pages keep state.
      body: const [EventsPage(), TicketsPage(), ProfilePage()][_index],
      // TODO(3): add a NavigationBar with Events, Tickets and Profile
      //          that calls _select.
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

    // TODO(5): return a Drawer with a UserAccountsDrawerHeader (Asha Nair),
    //          ListTiles for Events (go(0)) and My tickets (go(1)), a Divider and
    //          an About tile that closes the drawer and calls showAboutDialog.
    return Drawer(child: ListTile(title: const Text('Events'), onTap: () => go(0)));
  }
}

class EventsPage extends StatelessWidget {
  const EventsPage({super.key});
  @override
  Widget build(BuildContext context) {
    // TODO(2): return a TabBarView with three EventList children (upcoming,
    //          past, and upcoming filtered to saved), each with a PageStorageKey.
    return const EventList(items: upcoming);
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
