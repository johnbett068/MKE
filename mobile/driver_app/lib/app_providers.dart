import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mke_api/mke_api.dart';

const apiBaseUrl = String.fromEnvironment(
  'MKE_API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);
const websocketBaseUrl = String.fromEnvironment(
  'MKE_WS_URL',
  defaultValue: 'ws://10.0.2.2:8000',
);

final tokenStoreProvider = Provider<TokenStore>((ref) => TokenStore());
final apiClientProvider = Provider<ApiClient>(
  (ref) =>
      ApiClient(baseUrl: apiBaseUrl, tokenStore: ref.watch(tokenStoreProvider)),
);
final driverRepositoryProvider = Provider<DriverRepository>(
  (ref) => DriverRepository(ref.watch(apiClientProvider)),
);
final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(ref.watch(apiClientProvider)),
);
final walletRepositoryProvider = Provider<WalletRepository>(
  (ref) => WalletRepository(ref.watch(apiClientProvider)),
);
final paymentRepositoryProvider = Provider<PaymentRepository>(
  (ref) => PaymentRepository(ref.watch(apiClientProvider)),
);
final driverRealtimeProvider = Provider<RealtimeClient>((ref) {
  final client = RealtimeClient(
    websocketBaseUrl: websocketBaseUrl,
    tokens: ref.watch(tokenStoreProvider),
    refreshTokens: ref.watch(apiClientProvider).refreshTokens,
  );
  ref.onDispose(client.close);
  return client;
});
final authSessionProvider = FutureProvider<AuthTokens?>(
  (ref) => ref.watch(tokenStoreProvider).read(),
);
