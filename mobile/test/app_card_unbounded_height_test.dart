// Regressiya: ro'yxatlar bo'm-bo'sh ko'rinib qolgan bug uchun.
//
// `AppCard` 2px chap qirrani `Row(crossAxisAlignment: stretch)` bilan
// chizardi. `ListView` bolasiga balandlikni CHEKSIZ beradi, `stretch` esa
// shu cheksizlikni bolaga tight qilib uzatardi:
//   "BoxConstraints forces an infinite height"
// Debug'da assert otardi, release'da esa assert yo'q — karta cheksiz
// balandlikda "joylashib", umuman bo'yalmasdi. Natija: telefonlar,
// aksessuarlar, qarzlar, filiallar ro'yxati bo'm-bo'sh.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/features/accessories/data/models/accessory_model.dart';
import 'package:mobile/features/accessories/presentation/widgets/accessory_card.dart';
import 'package:mobile/features/capital/data/models/capital_model.dart';
import 'package:mobile/features/phones/data/models/phone_model.dart';
import 'package:mobile/features/phones/presentation/widgets/phone_card.dart';
import 'package:mobile/shared/widgets/app_card.dart';
import 'package:mobile/shared/widgets/app_primary_button.dart';
import 'package:mobile/shared/widgets/velmora_app_bar.dart';

// api.mobirex.uz dan olingan haqiqiy javoblar.
const _phoneJson = '''
{"id":909,"name":"Honor Magic 6","category":{"id":6,"name":"Honor","description":null},
"category_id":6,"branch":{"id":4,"name":"Demo Market","address":"Demo ko'chasi, 1","is_active":true},
"branch_id":4,"imei":"350011000000000","storage":"256","color":"Black","from_by":"Demo supplier",
"cost_price":"650.00","sell_price":null,"is_sold":false,"for_month_close":false,
"added_by":{"id":10,"username":"demo_phone"},"added_by_id":10,"sold_by":null,"sold_by_id":null,
"profit":"-650.00","is_profitable":false,"added_at":"2026-05-25T11:41:52.832050+05:00",
"updated_at":"2026-05-25T11:41:52.832060+05:00","sold_at":null}''';

const _accJson = '''
{"id":12,"name":"Bluetooth Earphones","category":{"id":19,"name":"Avto kalla","description":null},
"category_id":19,"branch":{"id":4,"name":"Demo Market","address":"Demo ko'chasi, 1","is_active":true},
"branch_id":4,"unit_cost":"15.00","stock":19,"image":null,"image_url":null,
"added_by":{"id":11,"username":"demo_accessory"},"added_by_id":11,"is_active":true,
"added_at":"2026-05-25T11:41:52.949353+05:00","updated_at":"2026-05-25T11:41:52.955738+05:00"}''';

/// Backend joriy oy uchun yozuv bo'lmasa shu qatorni qaytaradi.
const _capitalPlaceholderJson = '''
{"id":null,"branch":{"id":4,"name":"Demo Market","address":"Demo ko'chasi, 1","is_active":true},
"branch_id":4,"month":"2026-07-01","month_number":7,"year":2026,"invested_amount":"0.00",
"current_balance":"0.00","is_placeholder":true,"added_at":null,"updated_at":null}''';

/// Kartani AYNAN ro'yxatdagidek — cheksiz balandlikli ota ichida — chizadi.
Future<void> _pumpInList(WidgetTester tester, Widget card) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: ListView(children: [card]),
      ),
    ),
  );
}

void main() {
  group('AppCard cheksiz balandlikli ota ichida', () {
    testWidgets('UnsoldPhoneCard ListView ichida assert otmaydi', (
      tester,
    ) async {
      final phone = PhoneModel.fromJson(
        jsonDecode(_phoneJson) as Map<String, dynamic>,
      );
      await _pumpInList(
        tester,
        UnsoldPhoneCard(phone: phone, onSell: () {}, onDelete: () {}),
      );

      expect(tester.takeException(), isNull);
      // Karta haqiqatan ham chizildi va balandligi CHEKLI.
      final size = tester.getSize(find.byType(AppCard).first);
      expect(size.height.isFinite, isTrue);
      expect(size.height, greaterThan(0));
      expect(find.text('Honor Magic 6'), findsOneWidget);
    });

    testWidgets('UnsoldAccessoryCard ListView ichida assert otmaydi', (
      tester,
    ) async {
      final acc = AccessoryModel.fromJson(
        jsonDecode(_accJson) as Map<String, dynamic>,
      );
      await _pumpInList(
        tester,
        UnsoldAccessoryCard(accessory: acc, onSell: () {}, onDelete: () {}),
      );

      expect(tester.takeException(), isNull);
      expect(find.text('Bluetooth Earphones'), findsOneWidget);
    });

    testWidgets('AppCardSkeleton ListView ichida assert otmaydi', (
      tester,
    ) async {
      await _pumpInList(tester, const AppCardSkeleton());

      expect(tester.takeException(), isNull);
      final size = tester.getSize(find.byType(AppCardSkeleton));
      expect(size.height.isFinite, isTrue);
      expect(size.height, greaterThan(0));
    });

    testWidgets('bir nechta karta bitta ro\'yxatda chiziladi', (tester) async {
      final phone = PhoneModel.fromJson(
        jsonDecode(_phoneJson) as Map<String, dynamic>,
      );
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ListView.builder(
              itemCount: 8,
              itemBuilder: (_, _) => UnsoldPhoneCard(
                phone: phone,
                onSell: () {},
                onDelete: () {},
              ),
            ),
          ),
        ),
      );

      expect(tester.takeException(), isNull);
      expect(find.byType(AppCard), findsWidgets);
    });
  });

  _imeiTests();
  _tapTargetTests();

  group('CapitalModel placeholder qatori', () {
    test('id: null bilan kelgan qator xatosiz parse bo\'ladi', () {
      final model = CapitalModel.fromJson(
        jsonDecode(_capitalPlaceholderJson) as Map<String, dynamic>,
      );

      expect(model.id, isNull);
      expect(model.branch?.id, 4);
      expect(model.investedAmount, 0.0);
      expect(model.addedAt, isNull);
      expect(model.month?.month, 7);
    });

    test('id siz filial "filial yo\'q" deb qaraladi', () {
      final model = CapitalModel.fromJson({
        'id': null,
        'branch': {'name': 'Nosoz', 'is_active': true},
        'invested_amount': null,
        'current_balance': null,
      });

      expect(model.branch, isNull);
      expect(model.investedAmount, 0.0);
      expect(model.currentBalance, 0.0);
    });
  });
}

/// T1.2 — IMEI to'liq ko'rinadi va 390px ekranda toshib ketmaydi.
void _imeiTests() {
  testWidgets('to\'liq 15 raqamli IMEI 390px da toshmaydi', (tester) async {
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.view.devicePixelRatio = 3.0;
    addTearDown(tester.view.reset);

    // Eng yomon holat: uzun rang + uzun kategoriya + 15 raqamli IMEI.
    final json = jsonDecode(_phoneJson) as Map<String, dynamic>;
    json['imei'] = '356789012345674';
    json['color'] = 'Titanium Space Gray';
    json['storage'] = '1024';
    (json['category'] as Map<String, dynamic>)['name'] = 'Samsung Galaxy S Ultra';
    final phone = PhoneModel.fromJson(json);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            children: [
              UnsoldPhoneCard(phone: phone, onSell: () {}, onDelete: () {}),
            ],
          ),
        ),
      ),
    );

    expect(tester.takeException(), isNull);

    // To'liq raqam ekranda bor — dum kesilmagan.
    final imeiFinder = find.text('IMEI 356789012345674');
    expect(imeiFinder, findsOneWidget);

    // Matn o'z qutisiga sig'gan: ellipsis qo'llanmagan.
    final textWidget = tester.widget<Text>(imeiFinder);
    final painter = TextPainter(
      text: TextSpan(text: textWidget.data, style: textWidget.style),
      maxLines: 1,
      textDirection: TextDirection.ltr,
    )..layout(maxWidth: tester.getSize(imeiFinder).width);
    expect(painter.didExceedMaxLines, isFalse);
    expect(painter.width, lessThanOrEqualTo(tester.getSize(imeiFinder).width));
  });
}

/// T1.4 — tegish maydonlari 44px va header balandligi buzilmagan.
void _tapTargetTests() {
  testWidgets('qidiruv ikonkasi 44×44 va 48px bar ichiga sig\'adi', (
    tester,
  ) async {
    final ctrl = TextEditingController(text: 'test');
    addTearDown(ctrl.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          appBar: VelmoraAppBar(
            subtitle: 'Sotilmagan telefonlar',
            bottom: AppHeaderBottom(
              children: [
                AppSearchBar(
                  controller: ctrl,
                  hintText: 'Qidirish...',
                  onClear: () {},
                  onFilterTap: () {},
                ),
              ],
            ),
          ),
          body: const SizedBox(),
        ),
      ),
    );

    expect(tester.takeException(), isNull);

    // Filtr va tozalash tugmalari 44×44.
    for (final icon in [Icons.tune, Icons.close]) {
      final box = find.ancestor(
        of: find.byIcon(icon),
        matching: find.byType(SizedBox),
      );
      final size = tester.getSize(box.first);
      expect(size.width, 44, reason: '$icon kengligi');
      expect(size.height, 44, reason: '$icon balandligi');
    }
  });

  testWidgets('asosiy tugma block bo\'lmaganda 44px', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Center(
            child: AppPrimaryButton(label: 'Sotish', onPressed: () {}),
          ),
        ),
      ),
    );

    expect(tester.takeException(), isNull);
    expect(
      tester.getSize(find.byType(AppPrimaryButton)).height,
      greaterThanOrEqualTo(44),
    );
  });
}
