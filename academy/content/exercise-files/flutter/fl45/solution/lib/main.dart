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
    try {
      final file = await _picker.pickImage(source: source, maxWidth: 1024, imageQuality: 85);
      if (file == null) return; // cancelled
      final bytes = await file.readAsBytes();
      if (!mounted) return;
      setState(() => _photo = bytes);
    } on PlatformException {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not open ' + source.name + '. Check permissions.')),
      );
    }
  }

  Future<void> _chooseSource() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera),
              title: const Text('Take a photo'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Choose from gallery'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source != null) await _pick(source);
  }

  @override
  Widget build(BuildContext context) {
    final photo = _photo;
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            GestureDetector(
              onTap: _chooseSource,
              child: CircleAvatar(
                radius: 64,
                backgroundImage: photo == null ? null : MemoryImage(photo),
                child: photo == null ? const Icon(Icons.person, size: 64) : null,
              ),
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
    String status;
    try {
      final level = await _channel.invokeMethod<int>('getBatteryLevel');
      status = 'Battery: $level%';
    } on PlatformException catch (e) {
      status = 'Failed: ' + (e.message ?? e.code);
    } on MissingPluginException {
      status = 'Not available here';
    }
    if (!mounted) return;
    setState(() => _status = status);
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
