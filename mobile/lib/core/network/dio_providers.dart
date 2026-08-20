import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'dio_client.dart';

final dioClientProvider = Provider<DioClient>((ref) => DioClient());
