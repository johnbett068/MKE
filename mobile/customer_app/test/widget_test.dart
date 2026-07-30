import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mle_customer/main.dart';

void main() {
  testWidgets('renders the customer phone authentication screen',
      (tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: CustomerApp()),
    );

    expect(find.text('Your city, one tap away.'), findsOneWidget);
    expect(find.text('Send verification code'), findsOneWidget);
  });
}
