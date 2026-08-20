class SaleAccessoryRef {
  final int id;
  final String name;
  final String? image;

  const SaleAccessoryRef({required this.id, required this.name, this.image});

  factory SaleAccessoryRef.fromJson(Map<String, dynamic> json) =>
      SaleAccessoryRef(
        id: json['id'] as int,
        name: json['name'] as String,
        image: json['image'] as String?,
      );
}

class SaleBranch {
  final int id;
  final String name;

  const SaleBranch({required this.id, required this.name});

  factory SaleBranch.fromJson(Map<String, dynamic> json) =>
      SaleBranch(id: json['id'] as int, name: json['name'] as String);
}

class AccessorySaleModel {
  final int id;
  final SaleAccessoryRef? accessory;
  final SaleBranch? branch;
  final int quantity;
  final String unitCost;
  final String totalCost;
  final String totalPrice;
  final String profit;
  final String? soldAt;

  const AccessorySaleModel({
    required this.id,
    this.accessory,
    this.branch,
    required this.quantity,
    required this.unitCost,
    required this.totalCost,
    required this.totalPrice,
    required this.profit,
    this.soldAt,
  });

  factory AccessorySaleModel.fromJson(Map<String, dynamic> json) =>
      AccessorySaleModel(
        id: json['id'] as int,
        accessory: json['accessory'] != null
            ? SaleAccessoryRef.fromJson(
                json['accessory'] as Map<String, dynamic>,
              )
            : null,
        branch: json['branch'] != null
            ? SaleBranch.fromJson(json['branch'] as Map<String, dynamic>)
            : null,
        quantity: json['quantity'] as int? ?? 0,
        unitCost: json['unit_cost'] as String? ?? '0.00',
        totalCost: json['total_cost'] as String? ?? '0.00',
        totalPrice: json['total_price'] as String? ?? '0.00',
        profit: json['profit'] as String? ?? '0.00',
        soldAt: json['sold_at'] as String?,
      );
}
