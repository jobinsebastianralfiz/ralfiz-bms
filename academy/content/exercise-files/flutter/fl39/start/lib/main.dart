import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:http/http.dart' as http;

// STARTER - lesson 7.1: News Reader. It compiles and shows an empty list.
void main() => runApp(NewsApp(api: PostsApi(http.Client())));

class Post {
  const Post({required this.id, required this.userId, required this.title, required this.body});
  final int id;
  final int userId;
  final String title;
  final String body;

  // TODO(1): parse the map with a switch expression and a map pattern
  // {'id': int id, 'userId': int userId, 'title': String title, 'body': String body}.
  // Throw a FormatException when the shape is wrong.
  factory Post.fromJson(Map<String, dynamic> json) {
    throw UnimplementedError('TODO(1)');
  }

  // TODO(2): return the four fields as a map with the same JSON keys.
  Map<String, dynamic> toJson() => {};
}

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
    // TODO(3): GET $_base/posts with a 10 second timeout.
    // Throw ApiException when statusCode is not 200.
    // jsonDecode the body, check it is a List and map each item to Post.
    // TODO(4): turn TimeoutException, http.ClientException and
    // FormatException into ApiException with a friendly message.
    await Future<void>.delayed(const Duration(milliseconds: 300));
    return [];
  }
}

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
    // TODO(5): catch ApiException and emit PostsFailure(e.message).
    emit(PostsLoaded(await _api.fetchPosts()));
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
        theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepOrange)),
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
          // TODO(6): show an icon, the message and a Retry button that calls load().
          PostsFailure(:final message) => Center(child: Text(message)),
          PostsLoaded(:final posts) => ListView.separated(
              itemCount: posts.length,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final post = posts[index];
                // TODO(7): add a CircleAvatar with the id, a 2-line body
                // subtitle, and onTap that pushes a PostPage(post: post).
                return ListTile(title: Text(post.title));
              },
            ),
        },
      ),
    );
  }
}

// TODO(8): create PostPage: AppBar 'Post <id>', then title (titleLarge),
// 'By user <userId>' (labelMedium) and body (bodyLarge) in a padded ListView.
