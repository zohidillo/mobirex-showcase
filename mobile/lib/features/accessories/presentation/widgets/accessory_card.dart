import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../../phones/presentation/widgets/phone_card.dart'
    show PhoneCardTitleRow;
import '../../data/models/accessory_model.dart';
import '../../data/models/accessory_sale_model.dart';

/// Ombordagi aksessuar kartasi —
/// `redesign4/accessories/unsold-accessories.html` `.card`.
///
/// Telefon kartasining egizagi; farqi — meta qatorida miqdor:
/// "Kategoriya · Ombor: 24 dona".
class UnsoldAccessoryCard extends StatelessWidget {
  final AccessoryModel accessory;
  final VoidCallback onSell;
  final VoidCallback onDelete;

  const UnsoldAccessoryCard({
    super.key,
    required this.accessory,
    required this.onSell,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final meta = <String>[
      if (accessory.category != null) accessory.category!.name,
      'Ombor: ${accessory.stock} dona',
    ].join(' · ');

    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _AccessoryThumb(imageUrl: accessory.image),
          const SizedBox(width: AppSpacing.s3),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                PhoneCardTitleRow(
                  title: accessory.name,
                  trailing: accessory.branch?.name,
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: AppHeroValue(value: formatMoney(accessory.unitCost)),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 7),
                  child: Text(
                    meta,
                    style: AppText.meta,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: AppSpacing.s3),
                  child: Row(
                    children: [
                      const Spacer(),
                      AppSecondaryButton(
                        label: 'O\'chirish',
                        onPressed: onDelete,
                      ),
                      const SizedBox(width: 6),
                      AppPrimaryButton(
                        label: 'Sotish',
                        onPressed: accessory.stock > 0 ? onSell : null,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Sotilgan aksessuar kartasi —
/// `redesign4/accessories/sold-accessories.html` `.card.pos`.
class SoldAccessoryCard extends StatelessWidget {
  final AccessorySaleModel sale;
  final bool canReturn;
  final VoidCallback? onReturn;

  const SoldAccessoryCard({
    super.key,
    required this.sale,
    required this.canReturn,
    this.onReturn,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      edge: AppCardEdge.positive,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _AccessoryThumb(imageUrl: sale.accessory?.image),
          const SizedBox(width: AppSpacing.s3),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                PhoneCardTitleRow(
                  title: sale.accessory?.name ?? 'Aksessuar',
                  trailing: sale.branch?.name,
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: AppHeroValue(
                    value: formatMoney(sale.totalPrice),
                    suffix: 'foyda ${formatMoney(sale.profit)}',
                    color: AppColors.pos,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: 7),
                  child: Text(
                    'Miqdor: ${sale.quantity} · ${formatDateShort(sale.soldAt)}',
                    style: AppText.meta,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.only(top: AppSpacing.s3),
                  child: Row(
                    children: [
                      const Spacer(),
                      if (canReturn)
                        AppSecondaryButton(
                          label: 'Qaytarish',
                          onPressed: onReturn,
                          isDanger: true,
                        )
                      else
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 14),
                          child: Text(
                            'O\'tgan oy'.toUpperCase(),
                            style: AppText.meta.copyWith(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Aksessuar rasmi — 52px kvadrat, `--r-input` (10px) burchak.
///
/// Sotuvchi 50 ta aksessuarni ko'zdan kechirganda rasm matndan tezroq
/// tanitadi, shuning uchun u kartaning boshida turadi.
///
/// Rasm yo'q, bo'sh, yoki yuklanmasa — bir xil tekis placeholder
/// (`--card-pressed` fon + `--ink-3` ikon). Hech qanday holatda
/// istisno otmaydi va layout siljimaydi.
class _AccessoryThumb extends StatelessWidget {
  const _AccessoryThumb({this.imageUrl});

  final String? imageUrl;

  static const double _size = 52;

  Widget _placeholder() => Container(
    width: _size,
    height: _size,
    alignment: Alignment.center,
    decoration: const BoxDecoration(
      color: AppColors.cardPressed,
      borderRadius: AppRadius.inputRadius,
    ),
    child: const Icon(
      Icons.image_outlined,
      size: 22,
      color: AppColors.ink3,
    ),
  );

  @override
  Widget build(BuildContext context) {
    final url = imageUrl;
    if (url == null || url.isEmpty) return _placeholder();

    return ClipRRect(
      borderRadius: AppRadius.inputRadius,
      child: Image.network(
        url,
        width: _size,
        height: _size,
        fit: BoxFit.cover,
        // 1000px manbani ro'yxatda to'liq o'lchamda dekodlamaslik uchun.
        cacheWidth: (_size * MediaQuery.devicePixelRatioOf(context)).round(),
        errorBuilder: (_, _, _) => _placeholder(),
      ),
    );
  }
}
