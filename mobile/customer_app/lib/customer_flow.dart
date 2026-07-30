import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:mle_api/mle_api.dart';

import 'app_providers.dart';

enum CustomerStep { phone, otp, home, quote, dispatching, tracking, complete }

class CustomerFlowState {
  const CustomerFlowState({
    this.step = CustomerStep.phone,
    this.busy = false,
    this.phone = '',
    this.pickup,
    this.dropoff,
    this.quote,
    this.trip,
    this.driverLatitude,
    this.driverLongitude,
    this.paymentMethod = 'cash',
    this.error,
  });

  final CustomerStep step;
  final bool busy;
  final String phone;
  final LocationDto? pickup;
  final LocationDto? dropoff;
  final FareQuoteDto? quote;
  final TripDto? trip;
  final double? driverLatitude;
  final double? driverLongitude;
  final String paymentMethod;
  final String? error;

  CustomerFlowState copyWith({
    CustomerStep? step,
    bool? busy,
    String? phone,
    LocationDto? pickup,
    LocationDto? dropoff,
    FareQuoteDto? quote,
    TripDto? trip,
    double? driverLatitude,
    double? driverLongitude,
    String? paymentMethod,
    String? error,
    bool clearError = false,
  }) =>
      CustomerFlowState(
        step: step ?? this.step,
        busy: busy ?? this.busy,
        phone: phone ?? this.phone,
        pickup: pickup ?? this.pickup,
        dropoff: dropoff ?? this.dropoff,
        quote: quote ?? this.quote,
        trip: trip ?? this.trip,
        driverLatitude: driverLatitude ?? this.driverLatitude,
        driverLongitude: driverLongitude ?? this.driverLongitude,
        paymentMethod: paymentMethod ?? this.paymentMethod,
        error: clearError ? null : (error ?? this.error),
      );
}

class CustomerFlowController extends StateNotifier<CustomerFlowState> {
  CustomerFlowController(this.ref) : super(const CustomerFlowState()) {
    _events = ref.read(realtimeProvider).events.listen(_onEvent);
  }

  final Ref ref;
  StreamSubscription<RealtimeEnvelope>? _events;

  Future<void> requestOtp(String phone) => _run(() async {
        await ref.read(authRepositoryProvider).requestPhoneCode(phone);
        state = state.copyWith(phone: phone, step: CustomerStep.otp);
      });

  Future<void> confirmOtp(String code) => _run(() async {
        await ref
            .read(authRepositoryProvider)
            .confirmPhoneCode(state.phone, code);
        state = state.copyWith(step: CustomerStep.home);
      });

  Future<LocationDto?> useCurrentLocation() async {
    return _runValue(() async {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) {
        throw StateError('Location permission is required to request a ride.');
      }
      final point = await Geolocator.getCurrentPosition();
      return ref
          .read(customerRepositoryProvider)
          .resolveLocation(point.latitude, point.longitude);
    });
  }

  Future<void> setPickup(double latitude, double longitude) => _run(() async {
        final location = await ref
            .read(customerRepositoryProvider)
            .resolveLocation(latitude, longitude);
        state = state.copyWith(pickup: location);
      });

  Future<void> setDropoff(double latitude, double longitude) => _run(() async {
        final location = await ref
            .read(customerRepositoryProvider)
            .resolveLocation(latitude, longitude);
        state = state.copyWith(dropoff: location);
      });

  Future<void> quote() => _run(() async {
        final pickup = state.pickup;
        final dropoff = state.dropoff;
        if (pickup == null || dropoff == null) {
          throw StateError('Choose both pickup and destination.');
        }
        final quote = await ref.read(customerRepositoryProvider).createQuote({
          'origin': pickup.id,
          'destination': dropoff.id,
          'service_type': 'ride',
          'pickup_latitude': pickup.latitude,
          'pickup_longitude': pickup.longitude,
          'dropoff_latitude': dropoff.latitude,
          'dropoff_longitude': dropoff.longitude,
        });
        state = state.copyWith(quote: quote, step: CustomerStep.quote);
      });

  void choosePayment(String value) =>
      state = state.copyWith(paymentMethod: value, clearError: true);

  Future<void> book() => _run(() async {
        final quote = state.quote;
        if (quote == null || quote.expiresAt.isBefore(DateTime.now())) {
          throw StateError('Your fare lock expired. Request a new quote.');
        }
        final trip = await ref
            .read(customerRepositoryProvider)
            .requestTrip(quoteId: quote.id, paymentMethod: state.paymentMethod);
        state = state.copyWith(trip: trip, step: CustomerStep.dispatching);
        await ref.read(realtimeProvider).connect('/ws/v1/trips/${trip.id}/');
      });

  Future<void> cancel() => _run(() async {
        final trip = state.trip;
        if (trip == null) return;
        await ref
            .read(customerRepositoryProvider)
            .cancelTrip(trip.id, reason: 'Cancelled from customer app');
        state = const CustomerFlowState(step: CustomerStep.home);
      });

  void reset() =>
      state = CustomerFlowState(step: CustomerStep.home, phone: state.phone);

  void _onEvent(RealtimeEnvelope event) {
    final trip = state.trip;
    if (trip == null || event.aggregateId != trip.id.toString()) return;
    if (event.type == 'driver_location_updated') {
      state = state.copyWith(
        driverLatitude: (event.data['latitude'] as num?)?.toDouble(),
        driverLongitude: (event.data['longitude'] as num?)?.toDouble(),
      );
      return;
    }
    final status = event.data['status']?.toString() ??
        {
          'driver_accepted': 'accepted',
          'driver_arrived': 'accepted',
          'trip_started': 'in_progress',
          'trip_completed': 'completed',
          'trip_cancelled': 'cancelled',
        }[event.type];
    if (status == null) return;
    final updated = TripDto(
      id: trip.id,
      status: status,
      originId: trip.originId,
      destinationId: trip.destinationId,
      driverId: (event.data['driver_id'] as num?)?.toInt() ?? trip.driverId,
      quotedFare: trip.quotedFare,
      startPin: trip.startPin,
    );
    state = state.copyWith(
      trip: updated,
      step: status == 'completed'
          ? CustomerStep.complete
          : status == 'accepted' || status == 'in_progress'
              ? CustomerStep.tracking
              : state.step,
    );
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(busy: true, clearError: true);
    try {
      await action();
    } catch (error) {
      state = state.copyWith(error: _message(error));
    } finally {
      state = state.copyWith(busy: false);
    }
  }

  Future<T?> _runValue<T>(Future<T> Function() action) async {
    state = state.copyWith(busy: true, clearError: true);
    try {
      return await action();
    } catch (error) {
      state = state.copyWith(error: _message(error));
      return null;
    } finally {
      state = state.copyWith(busy: false);
    }
  }

  String _message(Object error) => error
      .toString()
      .replaceFirst('Bad state: ', '')
      .replaceFirst('Exception: ', '');

  @override
  void dispose() {
    _events?.cancel();
    super.dispose();
  }
}

final customerFlowProvider =
    StateNotifierProvider<CustomerFlowController, CustomerFlowState>(
  (ref) => CustomerFlowController(ref),
);
