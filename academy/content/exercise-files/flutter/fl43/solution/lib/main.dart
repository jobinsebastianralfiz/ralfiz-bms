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
          if (snap.data != null) return const ChatPage(roomId: 'general');
          return Scaffold(
            body: Center(
              child: FilledButton(
                onPressed: () => FirebaseAuth.instance.signInAnonymously(),
                child: const Text('Continue as guest'),
              ),
            ),
          );
        },
      ),
    );
  }
}

class Message {
  const Message({required this.text, required this.senderId, required this.senderName, this.createdAt});
  final String text;
  final String senderId;
  final String senderName;
  final DateTime? createdAt; // null until the server fills in the timestamp

  factory Message.fromFirestore(DocumentSnapshot<Map<String, dynamic>> doc, SnapshotOptions? options) {
    final data = doc.data() ?? const <String, dynamic>{};
    return Message(
      text: data['text'] as String? ?? '',
      senderId: data['senderId'] as String? ?? '',
      senderName: data['senderName'] as String? ?? 'Guest',
      createdAt: (data['createdAt'] as Timestamp?)?.toDate(),
    );
  }

  Map<String, Object?> toFirestore() => {
        'text': text,
        'senderId': senderId,
        'senderName': senderName,
        'createdAt': FieldValue.serverTimestamp(),
      };
}

class ChatPage extends StatefulWidget {
  const ChatPage({super.key, required this.roomId});
  final String roomId;

  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final _controller = TextEditingController();
  final _db = FirebaseFirestore.instance;
  late final _room = _db.collection('rooms').doc(widget.roomId);
  late final _messagesRef = _room.collection('messages').withConverter<Message>(
        fromFirestore: Message.fromFirestore,
        toFirestore: (m, _) => m.toFirestore(),
      );
  late final Stream<QuerySnapshot<Message>> _messages;

  @override
  void initState() {
    super.initState();
    _messages = _messagesRef.orderBy('createdAt', descending: true).limit(50).snapshots();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    final user = FirebaseAuth.instance.currentUser!;
    final batch = _db.batch()
      ..set(_messagesRef.doc(), Message(text: text, senderId: user.uid, senderName: user.displayName ?? 'Guest'))
      ..set(_room, {'lastMessage': text, 'updatedAt': FieldValue.serverTimestamp()}, SetOptions(merge: true));
    _controller.clear(); // the listener shows the message from the local cache at once
    try {
      await batch.commit();
    } on FirebaseException catch (e) {
      if (!mounted) return;
      final msg = e.code == 'permission-denied' ? 'Not sent: messages must be 1 to 500 characters.' : 'Not sent: ' + e.code;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = FirebaseAuth.instance.currentUser!.uid;
    return Scaffold(
      appBar: AppBar(
        title: const Text('General'),
        actions: [IconButton(icon: const Icon(Icons.logout), onPressed: () => FirebaseAuth.instance.signOut())],
      ),
      body: Column(children: [
        Expanded(
          child: StreamBuilder<QuerySnapshot<Message>>(
            stream: _messages,
            builder: (context, snap) {
              if (snap.hasError) return Center(child: Text('Error: ' + snap.error.toString()));
              if (!snap.hasData) return const Center(child: CircularProgressIndicator());
              final docs = snap.data!.docs;
              if (docs.isEmpty) return const Center(child: Text('No messages yet. Say hi!'));
              return ListView.builder(
                reverse: true, // newest (index 0) at the bottom
                padding: const EdgeInsets.all(12),
                itemCount: docs.length,
                itemBuilder: (context, i) {
                  final m = docs[i].data();
                  return MessageBubble(message: m, mine: m.senderId == me, pending: docs[i].metadata.hasPendingWrites);
                },
              );
            },
          ),
        ),
        SafeArea(
          top: false,
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: const InputDecoration(hintText: 'Message', border: OutlineInputBorder()),
                  onSubmitted: (_) => _send(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(icon: const Icon(Icons.send), onPressed: _send),
            ]),
          ),
        ),
      ]),
    );
  }
}
