import 'dart:io';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:package_info_plus/package_info_plus.dart';

class DeviceContextCollector {
  static String? _version;
  static String? _buildNumber;
  static String? _platform;
  static String? _osVersion;
  static String? _deviceModel;

  static Future<void> initialize() async {
    final packageInfo = await PackageInfo.fromPlatform();
    _version = packageInfo.version;
    _buildNumber = packageInfo.buildNumber;

    final plugin = DeviceInfoPlugin();
    if (Platform.isAndroid) {
      _platform = 'android';
      final info = await plugin.androidInfo;
      _deviceModel = info.model;
      _osVersion = 'Android ${info.version.release}';
    } else if (Platform.isIOS) {
      _platform = 'ios';
      final info = await plugin.iosInfo;
      _deviceModel = info.utsname.machine;
      _osVersion = 'iOS ${info.systemVersion}';
    } else {
      _platform = Platform.operatingSystem;
      _osVersion = '';
      _deviceModel = '';
    }
  }

  static Map<String, dynamic> snapshot() => {
        'app_version': '${_version ?? "?"}+${_buildNumber ?? "?"}',
        'platform': _platform ?? 'unknown',
        'os_version': _osVersion ?? '',
        'device_model': _deviceModel ?? '',
      };
}
