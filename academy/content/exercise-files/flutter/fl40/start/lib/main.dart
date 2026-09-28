import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// STARTER - lesson 7.2. This works, but it has a classic bug:
// the request starts inside build(), so every rebuild downloads again.
// Tap the counter button in the app bar and watch the spinner come back.
void main() => runApp(const NewsApp());

class Post {
  const Post(this.id, this.title);
  final int id;
  final String title;

  factory Post.fromJson(Map<String, dynamic> json) => switch (json) {
        {'id': int id, 'title': String title} => Post(id, title),
        _ => throw FormatException('Unexpected post JSON: $json'),
      };
}

Future<List<Post>> fetchPosts() async {
  debugPrint('fetchPosts called');
  final response = await http
      .get(Uri.parse('https://jsonplaceholder.typicode.com/posts'))
      .timeout(const Duration(seconds: 10));
  if (response.statusCode != 200) {
    final code = response.statusCode;
    throw Exception('HTTP $code');
  }
  final data = jsonDecode(response.body) as List<dynamic>;
  return [for (final item in data) Post.fromJson(item as Map<String, dynamic>)];
}

class NewsApp extends StatelessWidget {
  const NewsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'News Reader',
      theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange)),
      home: const FeedPage(),
    );
  }
}

class FeedPage extends StatefulWidget {
  const FeedPage({super.key});

  @override
  State<FeedPage> createState() => _FeedPageState();
}

class _FeedPageState extends State<FeedPage> {
  int _taps = 0; // only here to cause rebuilds

  // TODO(1): add late Future<List<Post>> _postsFuture and create it once
  // in initState.

  // TODO(4): add a Stream<int> ticker (Stream.periodic, 1 second) created
  // in initState, and show 'Updated N s ago' above the list with a
  // StreamBuilder. Treat ConnectionState.waiting as 0.

  // TODO(3): add Future<void> _refresh() that creates a new future,
  // stores it with setState, then awaits it (catch errors: the
  // FutureBuilder shows them).

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('News Reader'),
        actions: [
          TextButton(
            onPressed: () => setState(() => _taps++),
            child: Text('Rebuild $_taps'),
          ),
        ],
      ),
      // TODO(3): wrap the FutureBuilder in a RefreshIndicator(onRefresh: _refresh)
      // and give every child scrollable physics, including the error view.
      body: FutureBuilder<List<Post>>(
        future: fetchPosts(), // BUG - TODO(1): use _postsFuture instead
        builder: (context, snapshot) {
          // TODO(2): handle snapshot.hasError first, then !hasData
          // (spinner), then the list. Check connectionState only if you
          // really need it.
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final posts = snapshot.data ?? [];
          return ListView.builder(
            itemCount: posts.length,
            itemBuilder: (context, index) => ListTile(
              leading: CircleAvatar(child: Text(posts[index].id.toString())),
              title: Text(posts[index].title,
                  maxLines: 1, overflow: TextOverflow.ellipsis),
            ),
          );
        },
      ),
    );
  }
}
