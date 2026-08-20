import 'package:intl/intl.dart';

final _fmt = NumberFormat('#,##0.##', 'en_US');

String formatMoney(dynamic value) {
  if (value == null) return r'$0';
  double? amount;
  if (value is String) {
    amount = double.tryParse(value);
  } else if (value is num) {
    amount = value.toDouble();
  }
  if (amount == null) return '\$${value.toString()}';
  if (amount < 0) {
    return '-\$${_fmt.format(amount.abs())}';
  }
  return '\$${_fmt.format(amount)}';
}
