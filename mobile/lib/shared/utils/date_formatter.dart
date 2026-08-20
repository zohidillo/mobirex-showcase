import 'package:intl/intl.dart';

String formatDate(String? isoDate) {
  if (isoDate == null) return '';
  try {
    final dt = DateTime.parse(isoDate).toLocal();
    return DateFormat('dd MMM yyyy, HH:mm').format(dt);
  } catch (_) {
    return isoDate;
  }
}

String formatDateShort(String? isoDate) {
  if (isoDate == null) return '';
  try {
    final dt = DateTime.parse(isoDate).toLocal();
    return DateFormat('dd MMM yyyy').format(dt);
  } catch (_) {
    return isoDate;
  }
}

bool isCurrentMonth(String? isoDate) {
  if (isoDate == null) return false;
  try {
    final dt = DateTime.parse(isoDate).toLocal();
    final now = DateTime.now();
    return dt.year == now.year && dt.month == now.month;
  } catch (_) {
    return false;
  }
}

List<Map<String, int>> lastMonths({int count = 12}) {
  final now = DateTime.now();
  return List.generate(count, (i) {
    final dt = DateTime(now.year, now.month - i, 1);
    return {'year': dt.year, 'month': dt.month};
  });
}

String monthName(int month) {
  return DateFormat('MMMM').format(DateTime(2000, month));
}
