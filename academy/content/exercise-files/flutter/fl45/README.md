# Lesson 8.2 lab: Profile Photo app

Pick a profile photo from the gallery or camera with image_picker, and read
the battery level through your own MethodChannel.

## Setup

    flutter create profile_photo
    cd profile_photo
    flutter pub add image_picker

(Or copy pubspec.yaml from this folder and run flutter pub get.)
Replace lib/main.dart with start/lib/main.dart.

### iOS: add usage descriptions

In ios/Runner/Info.plist, inside the top-level <dict>:

    <key>NSPhotoLibraryUsageDescription</key>
    <string>Used to choose your profile photo.</string>
    <key>NSCameraUsageDescription</key>
    <string>Used to take your profile photo.</string>

### Android

image_picker needs no extra setup for this lab. Use an emulator with a
virtual camera, or a real phone.

## Tasks (TODOs in lib/main.dart)

- TODO(1) _pick: call pickImage(source, maxWidth: 1024, imageQuality: 85),
  return on null, read the bytes and store them in _photo.
- TODO(2) Check mounted after each await; catch PlatformException and show
  the SnackBar "Could not open <source>. Check permissions."
- TODO(3) _chooseSource: a modal bottom sheet with "Take a photo" and
  "Choose from gallery" that returns an ImageSource.
- TODO(4) Show _photo in the CircleAvatar with MemoryImage.
- TODO(5) BatteryTile: invoke getBatteryLevel on the channel
  academy.ralfiz/battery; show "Battery: N%", "Failed: ..." or
  "Not available here" (MissingPluginException).

## Optional: native battery handler (Android)

Open android/app/src/main/kotlin/<your package path>/MainActivity.kt and
replace the class with (keep your package line at the top):

    import android.content.Context
    import android.os.BatteryManager
    import io.flutter.embedding.android.FlutterActivity
    import io.flutter.embedding.engine.FlutterEngine
    import io.flutter.plugin.common.MethodChannel

    class MainActivity : FlutterActivity() {
        override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
            super.configureFlutterEngine(flutterEngine)
            MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "academy.ralfiz/battery")
                .setMethodCallHandler { call, result ->
                    if (call.method == "getBatteryLevel") {
                        val manager = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
                        result.success(manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY))
                    } else {
                        result.notImplemented()
                    }
                }
        }
    }

Stop the app and run it again (hot reload does not load native code).

## Acceptance criteria

- Choosing a gallery photo shows it in the round avatar.
- Cancelling the picker leaves the screen unchanged and prints no error.
- Tapping the avatar opens a sheet with two options that both work.
- Picking a second photo replaces the first one.
- Without the Kotlin handler the battery tile reads "Not available here";
  with it, Android shows "Battery: N%".
