# Lesson 7.5 lab: Chat app real-time messages

You continue the Chat app from lesson 7.4. Signed-in users can now send
messages to a shared room called "general" and see everyone's messages live.

## Setup

1. Use the Chat app project from lesson 7.4. It already has firebase_core,
   firebase_auth and lib/firebase_options.dart (made by flutterfire configure).
   Starting fresh? Run: flutter create chat_app, then flutterfire configure,
   then flutter pub add firebase_core firebase_auth.
2. Add Firestore:  flutter pub add cloud_firestore
3. Firebase console > Firestore Database > Create database (production mode).
4. Rules tab: paste the rules from the "Security rules" section below and Publish.
5. Authentication > Sign-in method: enable Anonymous (the starter has a
   "Continue as guest" button). You may use your 7.4 email sign-in instead.
6. Copy start/lib/main.dart over lib/main.dart and lib/message_bubble.dart
   into lib/ (the finished chat bubble widget; the solution uses it too).

## Data model

    rooms/{roomId}
      name: string
      lastMessage: string
      updatedAt: timestamp (server)
    rooms/{roomId}/messages/{messageId}
      text: string (1 to 500 characters)
      senderId: string (must equal the signed-in uid)
      senderName: string
      createdAt: timestamp (must be the server time)

## Security rules (paste into Firestore > Rules)

    rules_version = '2';

    service cloud.firestore {
      match /databases/{database}/documents {

        function signedIn() {
          return request.auth != null;
        }

        // Room documents: any signed-in user may read and update them.
        // (A real app would check membership, e.g. request.auth.uid in resource.data.members.)
        match /rooms/{roomId} {
          allow read, write: if signedIn();

          match /messages/{messageId} {
            allow read: if signedIn();

            allow create: if signedIn()
              && request.resource.data.keys().hasOnly(['text', 'senderId', 'senderName', 'createdAt'])
              && request.resource.data.senderId == request.auth.uid
              && request.resource.data.text is string
              && request.resource.data.text.size() > 0
              && request.resource.data.text.size() <= 500
              && request.resource.data.createdAt == request.time;

            // Messages are immutable in this lab.
            allow update, delete: if false;
          }
        }
      }
    }

## Your tasks (TODOs in lib/main.dart)

- TODO(1) Message.fromFirestore: read the fields; createdAt may be null.
- TODO(2) Message.toFirestore: return the map; createdAt uses
  FieldValue.serverTimestamp().
- TODO(3) In initState, build the messages stream ONCE: withConverter,
  orderBy createdAt descending, limit 50, snapshots().
- TODO(4) StreamBuilder: error text, spinner, "No messages yet. Say hi!",
  otherwise a reversed ListView.builder of MessageBubble widgets.
- TODO(5) _send: one batch that sets a new message and merges lastMessage and
  updatedAt into the room. Clear the field before awaiting commit().
- TODO(6) Catch FirebaseException; for permission-denied show the SnackBar
  "Not sent: messages must be 1 to 500 characters."

## Acceptance criteria

- A new room shows "No messages yet. Say hi!".
- A sent message appears at once with "Sending..." under it, and the label
  disappears when the server confirms.
- A message sent from a second device appears without any refresh.
- A 501-character message is rejected and the SnackBar appears.
- In the console, rooms/general has lastMessage equal to the last text sent.

Compare with solution/lib/main.dart when you are done.
