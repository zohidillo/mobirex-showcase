import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/utils/date_formatter.dart';
import '../../../../shared/utils/money_formatter.dart';
import '../../../../shared/widgets/app_card.dart';
import '../../../../shared/widgets/app_primary_button.dart';
import '../../../../shared/widgets/app_secondary_button.dart';
import '../../data/models/phone_model.dart';

/// Sotilmagan telefon kartasi — `redesign3/unsold-phones.html` `.card`.
///
/// Anatomiya: model + filial · hero narx · meta qator · harakatlar.
/// Konstruktor va callbacklar o'zgarmadi.
class UnsoldPhoneCard extends StatelessWidget {
  final PhoneModel phone;
  final VoidCallback onSell;
  final VoidCallback onDelete;

  const UnsoldPhoneCard({
    super.key,
    required this.phone,
    required this.onSell,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PhoneCardTitleRow(
            title: phone.name,
            trailing: phone.branch?.name,
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(formatMoney(phone.costPrice), style: AppText.display),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              phoneMetaLine(phone, trailing: phone.color),
              style: AppText.meta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          PhoneCardImeiLine(imei: phone.imei),
          Padding(
            padding: const EdgeInsets.only(top: AppSpacing.s3),
            child: Row(
              children: [
                const Spacer(),
                AppSecondaryButton(label: 'O\'chirish', onPressed: onDelete),
                const SizedBox(width: 6),
                AppPrimaryButton(label: 'Sotish', onPressed: onSell),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Sotilgan telefon kartasi — `redesign4/phones/sold-phones.html` `.card.pos`.
///
/// Chap qirra va narx `--pos` rangda; harakat — ghost-danger "Qaytarish"
/// yoki "O'tgan oy" yozuvi.
class SoldPhoneCard extends StatelessWidget {
  final PhoneModel phone;
  final bool canReturn;
  final VoidCallback? onReturn;

  const SoldPhoneCard({
    super.key,
    required this.phone,
    required this.canReturn,
    this.onReturn,
  });

  @override
  Widget build(BuildContext context) {
    return AppCard(
      edge: AppCardEdge.positive,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          PhoneCardTitleRow(
            title: phone.name,
            trailing: phone.branch?.name,
          ),
          Padding(
            padding: const EdgeInsets.only(top: 6),
            child: Text(
              phone.sellPrice != null ? formatMoney(phone.sellPrice) : '-',
              style: AppText.display.copyWith(color: AppColors.pos),
            ),
          ),
          Padding(
            padding: const EdgeInsets.only(top: 7),
            child: Text(
              phoneMetaLine(phone, trailing: formatDateShort(phone.soldAt)),
              style: AppText.meta,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          PhoneCardImeiLine(imei: phone.imei),
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
    );
  }
}

/// `.c1` — model (16/650) chapda, filial (`.brn` 10/700 UPPERCASE) o'ngda.
class PhoneCardTitleRow extends StatelessWidget {
  const PhoneCardTitleRow({super.key, required this.title, this.trailing});

  final String title;
  final String? trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.baseline,
      textBaseline: TextBaseline.alphabetic,
      children: [
        Expanded(
          child: Text(
            title,
            style: AppText.bodyLg,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        if (trailing != null && trailing!.isNotEmpty) ...[
          const SizedBox(width: 10),
          Text(
            trailing!.toUpperCase(),
            style: AppText.meta.copyWith(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.0,
            ),
          ),
        ],
      ],
    );
  }
}

/// `.meta` birinchi qatori — "256 GB · Black · Honor".
///
/// IMEI bu yerda YO'Q: u [PhoneCardImeiLine] da alohida qatorda to'liq
/// ko'rsatiladi.
String phoneMetaLine(PhoneModel phone, {String? trailing}) {
  final parts = <String>[];
  if (phone.storage.isNotEmpty) parts.add('${phone.storage} GB');
  if (trailing != null && trailing.isNotEmpty) parts.add(trailing);
  if (phone.category != null) parts.add(phone.category!.name);
  return parts.join(' · ');
}

/// `.meta` ikkinchi qatori — TO'LIQ IMEI.
///
/// Avval `3567…4567` ko'rinishida qisqartirilardi va to'liq raqam ilovaning
/// hech qayerida ochilmasdi. Kafolat, militsiya tekshiruvi va mijozni
/// tasdiqlash uchun butun raqam kerak; do'kon xodimlari odatda OXIRGI
/// raqamlarni aytadi, shuning uchun dum hech qachon yashirilmasligi shart.
///
/// Xotira + rang + sana + kategoriya bilan bitta qatorda 15 raqamli IMEI
/// 390px ekranga sig'masdi, shuning uchun shrift kichraytirilmadi
/// (`AppText.meta` shkalasi qulflangan) — IMEI o'z qatoriga chiqarildi.
class PhoneCardImeiLine extends StatelessWidget {
  const PhoneCardImeiLine({super.key, required this.imei});

  final String imei;

  @override
  Widget build(BuildContext context) {
    if (imei.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 3),
      child: Text(
        'IMEI $imei',
        style: AppText.meta,
        // Xavfsizlik to'ri: kutilmagan uzun qiymat layoutni buzmasin.
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
    );
  }
}
