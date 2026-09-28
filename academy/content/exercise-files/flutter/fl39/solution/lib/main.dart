import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:http/http.dart' as http;

// SOLUTION - lesson 7.1: News Reader (JSONPlaceholder posts).
void main() => runApp(NewsApp(api: PostsApi(http.Client())));

// ---------- Model ----------
class Post {
  const Post({required this.id, required this.userId, required this.title, required this.body});
  final int id;
  final int userId;
  final String title;
  final String body;
  factory Post.fromJson(Map<String, dynamic> json) => switch (json) {
        {'id': int id, 'userId': int userId, 'title': String title, 'body': String body} =>
          Post(id: id, userId: userId, title: title, body: body),
        _ => throw FormatException('Unexpected post JSON: $json'),
      };
  Map<String, dynamic> toJson() =>
      {'id': id, 'userId': userId, 'title': title, 'body': body};
}

// ---------- Data ----------
class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => 'ApiException: $message';
}

class PostsApi {
  PostsApi(this._client);
  final http.Client _client;
  static const _base = 'https://jsonplaceholder.typicode.com';
  Future<List<Post>> fetchPosts() async {
    try {
      final response = await _client
          .get(Uri.parse('$_base/posts'))
          .timeout(const Duration(seconds: 10));
      if (response.statusCode != 200) {
        final code = response.statusCode;
        throw ApiException('The server answered with status $code.');
      }
      final data = jsonDecode(response.body);
      if (data is! List) throw const FormatException('Expected a JSON list');
      return [for (final item in data) Post.fromJson(item as Map<String, dynamic>)];
    } on TimeoutException {
      throw const ApiException('The server took too long to answer.');
    } on http.ClientException {
      throw const ApiException('No connection. Check your internet.');
    } on FormatException {
      throw const ApiException('The server sent data we could not read.');
    }
  }
}

// ---------- Presentation ----------
sealed class PostsState {
  const PostsState();
}

final class PostsLoading extends PostsState {
  const PostsLoading();
}

final class PostsLoaded extends PostsState {
  const PostsLoaded(this.posts);
  final List<Post> posts;
}

final class PostsFailure extends PostsState {
  const PostsFailure(this.message);
  final String message;
}

class PostsCubit extends Cubit<PostsState> {
  PostsCubit(this._api) : super(const PostsLoading());
  final PostsApi _api;
  Future<void> load() async {
    emit(const PostsLoading());
    try {
      emit(PostsLoaded(await _api.fetchPosts()));
    } on ApiException catch (e) {
      emit(PostsFailure(e.message));
    }
  }
}

class NewsApp extends StatelessWidget {
  const NewsApp({super.key, required this.api});
  final PostsApi api;
  @override
  Widget build(BuildContext context) {
    return RepositoryProvider.value(
      value: api,
      child: MaterialApp(
        title: 'News Reader',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange)),
        home: BlocProvider(
          create: (context) => PostsCubit(context.read<PostsApi>())..load(),
          child: const PostsPage(),
        ),
      ),
    );
  }
}

class PostsPage extends StatelessWidget {
  const PostsPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('News Reader')),
      body: BlocBuilder<PostsCubit, PostsState>(
        builder: (context, state) => switch (state) {
          PostsLoading() => const Center(child: CircularProgressIndicator()),
          PostsFailure(:final message) => Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off, size: 48),
                  const SizedBox(height: 12),
                  Text(message, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: () => context.read<PostsCubit>().load(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                  ),
                ],
              ),
            ),
          PostsLoaded(:final posts) => ListView.separated(
              itemCount: posts.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final post = posts[index];
                return ListTile(
                  leading: CircleAvatar(child: Text(post.id.toString())),
                  title: Text(post.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: Text(post.body, maxLines: 2, overflow: TextOverflow.ellipsis),
                  onTap: () => Navigator.push(context,
                      MaterialPageRoute(builder: (_) => PostPage(post: post))),
                );
              },
            ),
        },
      ),
    );
  }
}

class PostPage extends StatelessWidget {
  const PostPage({super.key, required this.post});
  final Post post;
  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final id = post.id;
    final author = post.userId;
    return Scaffold(
      appBar: AppBar(title: Text('Post $id')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(post.title, style: text.titleLarge),
          const SizedBox(height: 8),
          Text('By user $author', style: text.labelMedium),
          const SizedBox(height: 16),
          Text(post.body, style: text.bodyLarge),
        ],
      ),
    );
  }
}
