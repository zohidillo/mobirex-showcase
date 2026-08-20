/// Viloyat — `GET /api/regions/` javobidagi bitta element.
class RegionModel {
  const RegionModel({required this.value, required this.label});

  final String value;
  final String label;

  factory RegionModel.fromJson(Map<String, dynamic> json) => RegionModel(
    value: json['value'] as String? ?? '',
    label: json['label'] as String? ?? '',
  );
}

/// `POST /api/public/contact-request/` tanasi.
class ContactRequest {
  const ContactRequest({required this.phone, required this.region});

  /// `+998901234567` ko'rinishida — maskadagi bo'shliqlar olib tashlanadi.
  final String phone;

  /// Viloyat kaliti (`andijon`), yorlig'i emas.
  final String region;

  Map<String, dynamic> toJson() => {'phone': phone, 'region': region};
}
