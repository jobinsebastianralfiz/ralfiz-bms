import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

void main() => runApp(const ProfileApp());

class ProfileApp extends StatelessWidget {
  const ProfileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Profile Photo',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0277BD))),
      home: const ProfilePage(),
    );
  }
}

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final _picker = ImagePicker();
  Uint8List? _photo;

  Future<void> _pick(ImageSource source) async {
    // TODO(1): pickImage with maxWidth 1024 and imageQuality 85; return on null;
    // read the bytes and setState(() => _photo = bytes).
    // TODO(2): check mounted after each await; catch PlatformException and show
    // SnackBar('Could not open ' + source.name + '. Check permissions.').
    debugPrint('Picker not implemented yet: ' + source.name + ' ' + _picker.toString());
  }

  Future<void> _chooseSource() async {
    // TODO(3): showModalBottomSheet<ImageSource> with two ListTiles that pop
    // ImageSource.camera or ImageSource.gallery; then call _pick.
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            GestureDetector(
              onTap: _chooseSource,
              // TODO(4): show _photo with backgroundImage: MemoryImage(...).
              child: const CircleAvatar(radius: 64, child: Icon(Icons.person, size: 64)),
            ),
            const SizedBox(height: 16),
            Text('Asha Nair', style: Theme.of(context).textTheme.titleLarge),
            const Text('Flutter developer'),
            const SizedBox(height: 24),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                FilledButton.tonalIcon(
                  onPressed: () => _pick(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library),
                  label: const Text('Gallery'),
                ),
                const SizedBox(width: 12),
                OutlinedButton.icon(
                  onPressed: () => _pick(ImageSource.camera),
                  icon: const Icon(Icons.photo_camera),
                  label: const Text('Camera'),
                ),
              ],
            ),
            const SizedBox(height: 32),
            const BatteryTile(),
          ],
        ),
      ),
    );
  }
}

class BatteryTile extends StatefulWidget {
  const BatteryTile({super.key});

  @override
  State<BatteryTile> createState() => _BatteryTileState();
}

class _BatteryTileState extends State<BatteryTile> {
  static const _channel = MethodChannel('academy.ralfiz/battery');
  String _status = 'Unknown';

  Future<void> _read() async {
    // TODO(5): invokeMethod<int>('getBatteryLevel') on _channel.
    // Success: 'Battery: $level%'. PlatformException: 'Failed: ...'.
    // MissingPluginException: 'Not available here'.
    debugPrint('Channel ready: ' + _channel.name);
  }

  @override
  Widget build(BuildContext context) {
    return Card.outlined(
      child: ListTile(
        leading: const Icon(Icons.battery_std),
        title: Text(_status),
        trailing: TextButton(onPressed: _read, child: const Text('Check')),
      ),
    );
  }
}
