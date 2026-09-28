import 'dart:isolate';

import 'package:flutter/material.dart';

void main() => runApp(const FeedApp());

class Post {
  const Post(this.id, this.author, this.caption, this.likes);
  final int id;
  final String author;
  final String caption;
  final int likes;

  String get imageUrl => 'https://picsum.photos/seed/post$id/1200/800';
}

final seedPosts = List.generate(
  1000,
  (i) => Post(i, 'User ' + (i % 37).toString(), 'Photo number ' + i.toString(), (i * 7919) % 500),
);

/// Stand-in for heavy work such as decoding a large JSON file.
int countPrimes(int below) {
  var count = 0;
  for (var n = 2; n < below; n++) {
    var prime = true;
    for (var d = 2; d * d <= n; d++) {
      if (n % d == 0) {
        prime = false;
        break;
      }
    }
    if (prime) count++;
  }
  return count;
}

/// Top-level entry point for Isolate.run, so no State object is captured.
int primesBelow3M() => countPrimes(3000000);

class FeedApp extends StatelessWidget {
  const FeedApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Photo Feed',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Color(0xFFE65100))),
      home: FeedPage(),
    );
  }
}

class FeedPage extends StatefulWidget {
  const FeedPage({super.key});

  @override
  State<FeedPage> createState() => _FeedPageState();
}

class _FeedPageState extends State<FeedPage> {
  final _posts = [...seedPosts];
  bool _byLikes = false;
  bool _busy = false;
  String? _stats;

  void _toggleSort() => setState(() => _byLikes = !_byLikes);

  void _delete(Post p) => setState(() => _posts.remove(p));

  Future<void> _computeStats() async {
    setState(() => _busy = true);
    await Future<void>.delayed(const Duration(milliseconds: 50));
    // TODO(5): this blocks the UI thread. Use await Isolate.run(primesBelow3M).
    final count = primesBelow3M();
    if (!mounted) return;
    setState(() {
      _busy = false;
      _stats = '$count primes below 3,000,000';
    });
    debugPrint('Isolate available: ' + Isolate.current.debugName.toString());
  }

  @override
  Widget build(BuildContext context) {
    // TODO(1): sorting 1,000 posts on every build is wasted work.
    final posts = [..._posts]..sort((a, b) => _byLikes ? b.likes.compareTo(a.likes) : a.id.compareTo(b.id));
    return Scaffold(
      appBar: AppBar(
        title: Text('Photo Feed'), // TODO(6): const
        actions: [
          IconButton(icon: Icon(Icons.sort), tooltip: 'Sort', onPressed: _toggleSort),
          IconButton(icon: Icon(Icons.analytics), tooltip: 'Stats', onPressed: _busy ? null : _computeStats),
        ],
      ),
      body: Column(
        children: [
          if (_busy) LinearProgressIndicator(),
          if (_busy) Padding(padding: EdgeInsets.all(8), child: CircularProgressIndicator()),
          if (_stats != null) Padding(padding: EdgeInsets.all(8), child: Text(_stats!)),
          Expanded(
            // TODO(2): this builds all 1,000 cards up front. Use ListView.builder.
            child: ListView(
              children: [
                for (final p in posts)
                  // TODO(3): add key: ValueKey(p.id)
                  PostCard(post: p, onDelete: () => _delete(p)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class PostCard extends StatefulWidget {
  const PostCard({super.key, required this.post, required this.onDelete});
  final Post post;
  final VoidCallback onDelete;

  @override
  State<PostCard> createState() => _PostCardState();
}

class _PostCardState extends State<PostCard> {
  bool _liked = false;

  @override
  Widget build(BuildContext context) {
    final post = widget.post;
    return Card(
      margin: EdgeInsets.fromLTRB(12, 6, 12, 6),
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          // TODO(4): decode at display size with cacheWidth.
          Image.network(
            post.imageUrl,
            height: 180,
            width: double.infinity,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => SizedBox(height: 180, child: Center(child: Icon(Icons.broken_image))),
          ),
          ListTile(
            leading: IconButton(
              icon: Icon(_liked ? Icons.favorite : Icons.favorite_border),
              color: _liked ? Colors.red : null,
              onPressed: () => setState(() => _liked = !_liked),
            ),
            title: Text(post.author),
            subtitle: Text(post.caption + ' · ' + post.likes.toString() + ' likes'),
            trailing: IconButton(icon: Icon(Icons.delete_outline), onPressed: widget.onDelete),
          ),
        ],
      ),
    );
  }
}
