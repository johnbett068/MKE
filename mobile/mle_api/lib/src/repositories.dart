import 'package:dio/dio.dart';

import 'api_client.dart';
import 'auth_session.dart';
import 'dtos.dart';

class AuthRepository {
  const AuthRepository(this.api);
  final ApiClient api;

  Future<void> requestPhoneCode(String phoneNumber) async {
    await api.http.post<void>(
      '/api/v1/accounts/phone-login/request/',
      data: {'identifier': phoneNumber},
    );
  }

  Future<AuthTokens> confirmPhoneCode(String phoneNumber, String code) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/accounts/phone-login/confirm/',
      data: {'phone_number': phoneNumber, 'code': code},
    );
    final tokens = AuthTokens(
      access: response.data!['access'] as String,
      refresh: response.data!['refresh'] as String,
    );
    await api.tokens.write(tokens);
    return tokens;
  }
}

class CustomerRepository {
  const CustomerRepository(this.api);
  final ApiClient api;

  Future<FareQuoteDto> createQuote(Map<String, dynamic> request) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/trips/quotes/',
      data: request,
    );
    return FareQuoteDto.fromJson(response.data!);
  }

  Future<LocationDto> resolveLocation(double latitude, double longitude) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/locations/resolve/',
      data: {'latitude': latitude, 'longitude': longitude},
    );
    return LocationDto.fromJson(response.data!);
  }

  Future<TripDto> requestTrip({
    required int quoteId,
    required String paymentMethod,
  }) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/trips/',
      data: {'quote_id': quoteId, 'payment_method': paymentMethod},
    );
    return TripDto.fromJson(response.data!);
  }

  Future<TripDto> trip(int id) async {
    final response = await api.http.get<Map<String, dynamic>>(
      '/api/v1/trips/$id/',
    );
    return TripDto.fromJson(response.data!);
  }

  Future<TripDto> cancelTrip(int id, {String reason = ''}) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/trips/$id/cancel/',
      data: {'reason': reason},
    );
    return TripDto.fromJson(response.data!);
  }
}

class DriverRepository {
  const DriverRepository(this.api);
  final ApiClient api;

  Future<DriverProfileDto> goOnline(double latitude, double longitude) =>
      _presence('online', latitude, longitude);

  Future<DriverProfileDto> heartbeat(double latitude, double longitude) =>
      _presence('heartbeat', latitude, longitude);

  Future<DriverProfileDto> _presence(
    String command,
    double latitude,
    double longitude,
  ) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/drivers/presence/$command/',
      data: {'latitude': latitude, 'longitude': longitude},
    );
    return DriverProfileDto.fromJson(response.data!);
  }

  Future<List<TripOfferDto>> offers() async {
    final response = await api.http.get<List<dynamic>>('/api/v1/trips/offers/');
    return response.data!
        .map(
          (item) =>
              TripOfferDto.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(growable: false);
  }

  Future<TripDto> acceptOffer(int offerId) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/trips/offers/$offerId/accept/',
    );
    return TripDto.fromJson(response.data!);
  }

  Future<DriverProfileDto> goOffline() async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/drivers/presence/offline/',
    );
    return DriverProfileDto.fromJson(response.data!);
  }

  Future<Map<String, dynamic>> application() async {
    final response = await api.http.get<Map<String, dynamic>>(
      '/api/v1/drivers/applications/me/',
    );
    return response.data!;
  }

  Future<List<Map<String, dynamic>>> documents() async {
    final response = await api.http.get<List<dynamic>>(
      '/api/v1/drivers/documents/',
    );
    return response.data!
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList(growable: false);
  }

  Future<Map<String, dynamic>> uploadDocument({
    required String documentType,
    required String filePath,
    String documentNumber = '',
  }) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/drivers/documents/',
      data: FormData.fromMap({
        'document_type': documentType,
        'document_number': documentNumber,
        'file': await MultipartFile.fromFile(filePath),
      }),
    );
    return response.data!;
  }
}

class PaymentRepository {
  const PaymentRepository(this.api);
  final ApiClient api;

  Future<Map<String, dynamic>> initiateStk({
    required int walletId,
    required String purpose,
    required double amount,
    required String phoneNumber,
    required String idempotencyKey,
  }) async {
    final response = await api.http.post<Map<String, dynamic>>(
      '/api/v1/payments/mpesa/stk/',
      data: {
        'wallet_id': walletId,
        'purpose': purpose,
        'amount': amount,
        'phone_number': phoneNumber,
      },
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    return response.data!;
  }
}

class WalletRepository {
  const WalletRepository(this.api);
  final ApiClient api;

  Future<List<WalletDto>> wallets() async {
    final response = await api.http.get<List<dynamic>>(
      '/api/v1/wallets/my-wallets/',
    );
    return response.data!
        .map(
          (item) => WalletDto.fromJson(Map<String, dynamic>.from(item as Map)),
        )
        .toList(growable: false);
  }
}
