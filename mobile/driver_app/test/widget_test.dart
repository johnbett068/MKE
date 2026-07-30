import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mle_driver/main.dart';

void main() {
  testWidgets('renders the driver phone authentication screen', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: DriverApp()),
    );

    expect(find.text('Drive. Earn. Move MKE.'), findsOneWidget);
    expect(find.text('Send verification code'), findsOneWidget);
  });
}
