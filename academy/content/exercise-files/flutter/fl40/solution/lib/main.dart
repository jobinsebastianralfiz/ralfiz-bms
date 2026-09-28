import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

// SOLUTION - lesson 7.2: News Reader with FutureBuilder, StreamBuilder
// and pull-to-refresh.
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

  // Created once in initState, NOT in build.
  late Future<List<Post>> _postsFuture;
  late Stream<int> _secondsSinceRefresh;

  @override
  void initState() {
    super.initState();
    _postsFuture = fetchPosts();
    _secondsSinceRefresh = _ticker();
  }

  Stream<int> _ticker() =>
      Stream.periodic(const Duration(seconds: 1), (i) => i + 1);

  Future<void> _refresh() async {
    final future = fetchPosts();
    setState(() {
      _postsFuture = future;
      _secondsSinceRefresh = _ticker();
    });
    try {
      await future; // keeps the refresh spinner until the data arrives
    } on Exception {
      // The FutureBuilder shows the error; nothing else to do here.
    }
  }

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
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(8),
            child: StreamBuilder<int>(
              stream: _secondsSinceRefresh,
              builder: (context, snapshot) {
                // After a new stream is set, the old value is kept while
                // waiting, so treat "waiting" as 0.
                final seconds =
                    snapshot.connectionState == ConnectionState.waiting
                        ? 0
                        : snapshot.data ?? 0;
                return Text('Updated $seconds s ago',
                    style: Theme.of(context).textTheme.labelMedium);
              },
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refresh,
              child: FutureBuilder<List<Post>>(
                future: _postsFuture,
                builder: (context, snapshot) {
                  if (snapshot.hasError) {
                    return const _Message(
                        'Could not load posts. Pull down to try again.');
                  }
                  if (!snapshot.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final posts = snapshot.data!;
                  return ListView.builder(
                    physics: const AlwaysScrollableScrollPhysics(),
                    itemCount: posts.length,
                    itemBuilder: (context, index) => ListTile(
                      leading: CircleAvatar(
                          child: Text(posts[index].id.toString())),
                      title: Text(posts[index].title,
                          maxLines: 1, overflow: TextOverflow.ellipsis),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// A scrollable message, so pull-to-refresh still works on error.
class _Message extends StatelessWidget {
  const _Message(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(32),
      children: [
        const Icon(Icons.cloud_off, size: 48),
        const SizedBox(height: 12),
        Text(text, textAlign: TextAlign.center),
      ],
    );
  }
}
