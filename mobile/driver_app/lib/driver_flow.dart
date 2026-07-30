import 'dart:async';
import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mle_api/mle_api.dart';

import 'app_providers.dart';

enum DriverStep { phone, otp, verification, duty, activeTrip, wallet }

class DriverFlowState {
  const DriverFlowState({
    this.step = DriverStep.phone,
    this.busy = false,
    this.phone = '',
    this.online = false,
    this.heartbeatHealthy = false,
    this.applicationStatus = 'not_submitted',
    this.documents = const [],
    this.offer,
    this.trip,
    this.offerSeconds = 0,
    this.wallet,
    this.error,
  });
  final DriverStep step;
  final bool busy;
  final String phone;
  final bool online;
  final bool heartbeatHealthy;
  final String applicationStatus;
  final List<Map<String, dynamic>> documents;
  final TripOfferDto? offer;
  final TripDto? trip;
  final int offerSeconds;
  final WalletDto? wallet;
  final String? error;

  DriverFlowState copyWith({
    DriverStep? step,
    bool? busy,
    String? phone,
    bool? online,
    bool? heartbeatHealthy,
    String? applicationStatus,
    List<Map<String, dynamic>>? documents,
    TripOfferDto? offer,
    TripDto? trip,
    int? offerSeconds,
    WalletDto? wallet,
    String? error,
    bool clearOffer = false,
    bool clearError = false,
  }) =>
      DriverFlowState(
        step: step ?? this.step,
        busy: busy ?? this.busy,
        phone: phone ?? this.phone,
        online: online ?? this.online,
        heartbeatHealthy: heartbeatHealthy ?? this.heartbeatHealthy,
        applicationStatus: applicationStatus ?? this.applicationStatus,
        documents: documents ?? this.documents,
        offer: clearOffer ? null : (offer ?? this.offer),
        trip: trip ?? this.trip,
        offerSeconds: offerSeconds ?? this.offerSeconds,
        wallet: wallet ?? this.wallet,
        error: clearError ? null : (error ?? this.error),
      );
}

class DriverFlowController extends StateNotifier<DriverFlowState> {
  DriverFlowController(this.ref) : super(const DriverFlowState()) {
    _events = ref.read(driverRealtimeProvider).events.listen(_onEvent);
  }
  final Ref ref;
  StreamSubscription<RealtimeEnvelope>? _events;
  Timer? _heartbeat;
  Timer? _offerTimer;
  DateTime? _tripStartedAt;
  Position? _lastTripPosition;
  double _tripDistanceKm = 0;

  Future<void> requestOtp(String phone) => _run(() async {
        await ref.read(authRepositoryProvider).requestPhoneCode(phone);
        state = state.copyWith(phone: phone, step: DriverStep.otp);
      });

  Future<void> confirmOtp(String code) => _run(() async {
        await ref
            .read(authRepositoryProvider)
            .confirmPhoneCode(state.phone, code);
        await refreshApplication();
      });

  Future<void> refreshApplication() => _run(() async {
        try {
          final app = await ref.read(driverRepositoryProvider).application();
          final docs = await ref.read(driverRepositoryProvider).documents();
          final status = app['status']?.toString() ?? 'not_submitted';
          state = state.copyWith(
            applicationStatus: status,
            documents: docs,
            step: status == 'approved'
                ? DriverStep.duty
                : DriverStep.verification,
          );
        } catch (_) {
          state = state.copyWith(
            applicationStatus: 'not_submitted',
            step: DriverStep.verification,
          );
        }
      });

  Future<void> uploadDocument(String type) => _run(() async {
        final file = await ImagePicker().pickImage(
          source: ImageSource.camera,
          imageQuality: 82,
        );
        if (file == null) return;
        await ref
            .read(driverRepositoryProvider)
            .uploadDocument(documentType: type, filePath: file.path);
        state = state.copyWith(
          documents: await ref.read(driverRepositoryProvider).documents(),
        );
      });

  Future<void> toggleDuty(bool online) => _run(() async {
        if (!online) {
          _heartbeat?.cancel();
          await ref.read(driverRepositoryProvider).goOffline();
          state = state.copyWith(online: false, heartbeatHealthy: false);
          return;
        }
        final point = await _position();
        await ref
            .read(driverRepositoryProvider)
            .goOnline(point.latitude, point.longitude);
        await ref.read(driverRealtimeProvider).connect('/ws/v1/drivers/me/');
        state = state.copyWith(online: true, heartbeatHealthy: true);
        _heartbeat = Timer.periodic(
          const Duration(seconds: 20),
          (_) => _sendHeartbeat(),
        );
      });

  Future<void> _sendHeartbeat() async {
    try {
      final point = await _position();
      await ref
          .read(driverRepositoryProvider)
          .heartbeat(point.latitude, point.longitude);
      state = state.copyWith(heartbeatHealthy: true);
      if (state.trip != null) {
        if (_lastTripPosition != null) {
          _tripDistanceKm += _distanceKm(_lastTripPosition!, point);
        }
        _lastTripPosition = point;
        ref.read(driverRealtimeProvider).send('driver_location_updated', {
          'trip_id': state.trip!.id,
          'latitude': point.latitude,
          'longitude': point.longitude,
        });
      }
    } catch (_) {
      state = state.copyWith(heartbeatHealthy: false);
    }
  }

  Future<Position> _position() async {
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw StateError('Location permission is required while on duty.');
    }
    return Geolocator.getCurrentPosition();
  }

  void acceptOffer() {
    final offer = state.offer;
    if (offer == null || state.offerSeconds <= 0) return;
    ref.read(driverRealtimeProvider).send(
        'offer_accept',
        {
          'offer_id': offer.id,
        },
        requestId: 'accept-${offer.id}');
  }

  void rejectOffer() {
    final offer = state.offer;
    if (offer == null) return;
    ref.read(driverRealtimeProvider).send(
        'offer_reject',
        {
          'offer_id': offer.id,
        },
        requestId: 'reject-${offer.id}');
    _offerTimer?.cancel();
    state = state.copyWith(clearOffer: true, offerSeconds: 0);
  }

  void arrived() {
    final trip = state.trip;
    if (trip == null) return;
    ref.read(driverRealtimeProvider).send(
        'driver_arrived',
        {
          'trip_id': trip.id,
        },
        requestId: 'arrive-${trip.id}');
  }

  void startTrip(String pin) {
    final trip = state.trip;
    if (trip == null) return;
    ref.read(driverRealtimeProvider).send(
        'trip_start',
        {
          'trip_id': trip.id,
          'pin': pin,
        },
        requestId: 'start-${trip.id}');
  }

  void completeTrip() {
    final trip = state.trip;
    if (trip == null) return;
    final elapsed = DateTime.now().difference(
      _tripStartedAt ?? DateTime.now().subtract(const Duration(minutes: 1)),
    );
    ref.read(driverRealtimeProvider).send(
        'trip_complete',
        {
          'trip_id': trip.id,
          'distance_km': _tripDistanceKm.clamp(0.1, 9999),
          'duration_minutes': (elapsed.inSeconds / 60).clamp(0.1, 999),
        },
        requestId: 'complete-${trip.id}');
  }

  double _distanceKm(Position from, Position to) {
    const earthRadiusKm = 6371.0;
    final lat1 = from.latitude * math.pi / 180;
    final lat2 = to.latitude * math.pi / 180;
    final dLat = (to.latitude - from.latitude) * math.pi / 180;
    final dLon = (to.longitude - from.longitude) * math.pi / 180;
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(lat1) *
            math.cos(lat2) *
            math.sin(dLon / 2) *
            math.sin(dLon / 2);
    return earthRadiusKm * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
  }

  Future<void> openWallet() => _run(() async {
        final wallets = await ref.read(walletRepositoryProvider).wallets();
        state = state.copyWith(
          wallet: wallets.isEmpty ? null : wallets.first,
          step: DriverStep.wallet,
        );
      });

  Future<void> topUp(double amount) => _run(() async {
        final wallet = state.wallet;
        if (wallet == null) return;
        await ref.read(paymentRepositoryProvider).initiateStk(
              walletId: wallet.id,
              purpose: wallet.debtBalance > 0 ? 'cash_debt' : 'wallet_topup',
              amount: amount,
              phoneNumber: state.phone,
              idempotencyKey:
                  'driver-${wallet.id}-${DateTime.now().millisecondsSinceEpoch}',
            );
      });

  void closeWallet() => state = state.copyWith(step: DriverStep.duty);

  void _onEvent(RealtimeEnvelope event) {
    if (event.type == 'offer_received') {
      final origin = Map<String, dynamic>.from(event.data['origin'] as Map);
      final destination = Map<String, dynamic>.from(
        event.data['destination'] as Map,
      );
      final offer = TripOfferDto(
        id: (event.data['offer_id'] as num).toInt(),
        trip: TripDto(
          id: (event.data['trip_id'] as num).toInt(),
          status: 'requested',
          originId: (origin['id'] as num).toInt(),
          destinationId: (destination['id'] as num).toInt(),
          quotedFare: double.parse(event.data['quoted_fare'].toString()),
        ),
        distanceToPickupKm: double.parse(
          event.data['distance_to_pickup_km'].toString(),
        ),
        expiresAt: DateTime.parse(event.data['expires_at'] as String),
      );
      final seconds =
          offer.expiresAt.difference(DateTime.now()).inSeconds.clamp(0, 30);
      state = state.copyWith(offer: offer, offerSeconds: seconds);
      _offerTimer?.cancel();
      _offerTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
        final left = state.offerSeconds - 1;
        if (left <= 0) {
          timer.cancel();
          state = state.copyWith(clearOffer: true, offerSeconds: 0);
        } else {
          state = state.copyWith(offerSeconds: left);
        }
      });
      return;
    }
    if (event.type == 'command_succeeded') {
      final command = event.data['command']?.toString();
      final tripId = (event.data['trip_id'] as num?)?.toInt();
      if (tripId != null) {
        final previous = state.trip ?? state.offer?.trip;
        if (previous == null) return;
        final status = event.data['status']?.toString() ?? previous.status;
        final trip = TripDto(
          id: tripId,
          status: status,
          originId: previous.originId,
          destinationId: previous.destinationId,
          driverId: previous.driverId,
          quotedFare: previous.quotedFare,
        );
        if (command == 'offer_accept') {
          _tripDistanceKm = 0;
          _lastTripPosition = null;
          _offerTimer?.cancel();
          state = state.copyWith(
            trip: trip,
            step: DriverStep.activeTrip,
            clearOffer: true,
          );
        } else {
          if (command == 'trip_start') _tripStartedAt = DateTime.now();
          state = state.copyWith(
            trip: trip,
            step: command == 'trip_complete'
                ? DriverStep.duty
                : DriverStep.activeTrip,
          );
        }
      }
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(busy: true, clearError: true);
    try {
      await action();
    } catch (error) {
      state = state.copyWith(
        error: error.toString().replaceFirst('Bad state: ', ''),
      );
    } finally {
      state = state.copyWith(busy: false);
    }
  }

  @override
  void dispose() {
    _heartbeat?.cancel();
    _offerTimer?.cancel();
    _events?.cancel();
    super.dispose();
  }
}

final driverFlowProvider =
    StateNotifierProvider<DriverFlowController, DriverFlowState>(
  (ref) => DriverFlowController(ref),
);
