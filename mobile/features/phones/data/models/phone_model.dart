class PhoneCategory {
  final int id;
  final String name;

  const PhoneCategory({required this.id, required this.name});

  factory PhoneCategory.fromJson(Map<String, dynamic> json) =>
      PhoneCategory(id: json['id'] as int, name: json['name'] as String);

  @override
  bool operator ==(Object other) => other is PhoneCategory && other.id == id;

  @override
  int get hashCode => id.hashCode;
}

class PhoneBranch {
  final int id;
  final String name;

  const PhoneBranch({required this.id, required this.name});

  factory PhoneBranch.fromJson(Map<String, dynamic> json) =>
      PhoneBranch(id: json['id'] as int, name: json['name'] as String);
}

class PhoneModel {
  final int id;
  final String name;
  final String imei;
  final String storage;
  final String color;
  final String costPrice;
  final String? sellPrice;
  final bool isSold;
  final String? soldAt;
  final PhoneCategory? category;
  final PhoneBranch? branch;

  const PhoneModel({
    required this.id,
    required this.name,
    required this.imei,
    required this.storage,
    required this.color,
    required this.costPrice,
    this.sellPrice,
    required this.isSold,
    this.soldAt,
    this.category,
    this.branch,
  });

  factory PhoneModel.fromJson(Map<String, dynamic> json) => PhoneModel(
    id: json['id'] as int,
    name: json['name'] as String,
    imei: json['imei'] as String? ?? '',
    storage: json['storage'] as String? ?? '',
    color: json['color'] as String? ?? '',
    costPrice: json['cost_price'] as String? ?? '0.00',
    sellPrice: json['sell_price'] as String?,
    isSold: json['is_sold'] as bool? ?? false,
    soldAt: json['sold_at'] as String?,
    category: json['category'] != null
        ? PhoneCategory.fromJson(json['category'] as Map<String, dynamic>)
        : null,
    branch: json['branch'] != null
        ? PhoneBranch.fromJson(json['branch'] as Map<String, dynamic>)
        : null,
  );
}
