import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';

import 'firebase_options.dart';
import 'message_bubble.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(const ChatApp());
}

class ChatApp extends StatelessWidget {
  const ChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Chat',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF00796B))),
      home: StreamBuilder<User?>(
        stream: FirebaseAuth.instance.authStateChanges(),
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Scaffold(body: Center(child: CircularProgressIndicator()));
          }
          return snap.data == null ? const SignInPage() : const ChatPage(roomId: 'general');
        },
      ),
    );
  }
}

class SignInPage extends StatelessWidget {
  const SignInPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: FilledButton(
          onPressed: () => FirebaseAuth.instance.signInAnonymously(),
          child: const Text('Continue as guest'),
        ),
      ),
    );
  }
}

class Message {
  const Message({required this.text, required this.senderId, required this.senderName, this.createdAt});
  final String text;
  final String senderId;
  final String senderName;
  final DateTime? createdAt;

  factory Message.fromFirestore(DocumentSnapshot<Map<String, dynamic>> doc, SnapshotOptions? options) {
    // TODO(1): read text, senderId, senderName and createdAt (a Timestamp, may be null).
    return const Message(text: '', senderId: '', senderName: '');
  }

  Map<String, Object?> toFirestore() {
    // TODO(2): return the fields; createdAt must be FieldValue.serverTimestamp().
    return {};
  }
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key, required this.roomId});
  final String roomId;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _controller = TextEditingController();
  late final Stream<QuerySnapshot<Message>> _messages;

  @override
  void initState() {
    super.initState();
    // TODO(3): rooms/{roomId}/messages with withConverter, ordered by createdAt
    // descending, limited to 50, as snapshots().
    _messages = const Stream<QuerySnapshot<Message>>.empty();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    // TODO(5): one batch: set a new message + merge lastMessage/updatedAt into the room.
    // TODO(6): catch FirebaseException and show a SnackBar for permission-denied.
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final me = FirebaseAuth.instance.currentUser!.uid;
    return Scaffold(
      appBar: AppBar(
        title: const Text('General'),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: () => FirebaseAuth.instance.signOut()),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: StreamBuilder<QuerySnapshot<Message>>(
              stream: _messages,
              builder: (context, snap) {
                // TODO(4): error, loading, empty and list states.
                // Use MessageBubble(message: ..., mine: ... == me, pending: ...).
                return Center(child: Text('Signed in as ' + me));
              },
            ),
          ),
          SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      decoration: const InputDecoration(hintText: 'Message', border: OutlineInputBorder()),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(icon: const Icon(Icons.send), onPressed: _send),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
