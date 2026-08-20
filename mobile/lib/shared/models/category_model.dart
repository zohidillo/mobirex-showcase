class CategoryItem {
  final int id;
  final String name;

  const CategoryItem({required this.id, required this.name});

  factory CategoryItem.fromJson(Map<String, dynamic> json) =>
      CategoryItem(id: json['id'] as int, name: json['name'] as String);

  @override
  bool operator ==(Object other) => other is CategoryItem && other.id == id;

  @override
  int get hashCode => id.hashCode;
}
