class AccessoryCategory {
  final int id;
  final String name;

  const AccessoryCategory({required this.id, required this.name});

  factory AccessoryCategory.fromJson(Map<String, dynamic> json) =>
      AccessoryCategory(id: json['id'] as int, name: json['name'] as String);

  @override
  bool operator ==(Object other) =>
      other is AccessoryCategory && other.id == id;

  @override
  int get hashCode => id.hashCode;
}

class AccessoryBranch {
  final int id;
  final String name;

  const AccessoryBranch({required this.id, required this.name});

  factory AccessoryBranch.fromJson(Map<String, dynamic> json) =>
      AccessoryBranch(id: json['id'] as int, name: json['name'] as String);
}

class AccessoryModel {
  final int id;
  final String name;
  final AccessoryCategory? category;
  final AccessoryBranch? branch;
  final String unitCost;
  final int stock;
  final String? image;

  const AccessoryModel({
    required this.id,
    required this.name,
    this.category,
    this.branch,
    required this.unitCost,
    required this.stock,
    this.image,
  });

  factory AccessoryModel.fromJson(Map<String, dynamic> json) => AccessoryModel(
    id: json['id'] as int,
    name: json['name'] as String,
    category: json['category'] != null
        ? AccessoryCategory.fromJson(json['category'] as Map<String, dynamic>)
        : null,
    branch: json['branch'] != null
        ? AccessoryBranch.fromJson(json['branch'] as Map<String, dynamic>)
        : null,
    unitCost: json['unit_cost'] as String? ?? '0.00',
    stock: json['stock'] as int? ?? 0,
    image: json['image'] as String?,
  );
}
