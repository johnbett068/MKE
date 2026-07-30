class FareQuoteDto {
  const FareQuoteDto({
    required this.id,
    required this.distanceKm,
    required this.durationMinutes,
    required this.fare,
    required this.expiresAt,
  });
  final int id;
  final double distanceKm;
  final double durationMinutes;
  final double fare;
  final DateTime expiresAt;

  factory FareQuoteDto.fromJson(Map<String, dynamic> json) => FareQuoteDto(
    id: json['id'] as int,
    distanceKm: double.parse(json['distance_km'].toString()),
    durationMinutes: double.parse(json['duration_minutes'].toString()),
    fare: double.parse(json['fare'].toString()),
    expiresAt: DateTime.parse(json['expires_at'] as String),
  );
}

class LocationDto {
  const LocationDto({
    required this.id,
    required this.country,
    required this.county,
    required this.town,
    required this.zone,
    required this.latitude,
    required this.longitude,
  });
  final int id;
  final String country;
  final String county;
  final String town;
  final String zone;
  final double latitude;
  final double longitude;

  String get label => zone.isEmpty ? '$town, $county' : '$zone, $town';

  factory LocationDto.fromJson(Map<String, dynamic> json) => LocationDto(
    id: json['id'] as int,
    country: json['country'] as String,
    county: json['county'] as String,
    town: json['town'] as String,
    zone: (json['zone'] as String?) ?? '',
    latitude: double.parse(
      (json['selected_latitude'] ?? json['latitude']).toString(),
    ),
    longitude: double.parse(
      (json['selected_longitude'] ?? json['longitude']).toString(),
    ),
  );
}

class TripDto {
  const TripDto({
    required this.id,
    required this.status,
    required this.originId,
    required this.destinationId,
    this.driverId,
    this.quotedFare,
    this.startPin,
  });
  final int id;
  final String status;
  final int originId;
  final int destinationId;
  final int? driverId;
  final double? quotedFare;
  final String? startPin;

  factory TripDto.fromJson(Map<String, dynamic> json) => TripDto(
    id: json['id'] as int,
    status: json['status'] as String,
    originId: json['origin'] as int,
    destinationId: json['destination'] as int,
    driverId: json['driver'] as int?,
    quotedFare: json['quoted_fare'] == null
        ? null
        : double.parse(json['quoted_fare'].toString()),
    startPin: json['start_pin'] as String?,
  );
}

class DriverProfileDto {
  const DriverProfileDto({
    required this.online,
    required this.available,
    this.latitude,
    this.longitude,
    this.lastSeen,
  });
  final bool online;
  final bool available;
  final double? latitude;
  final double? longitude;
  final DateTime? lastSeen;

  factory DriverProfileDto.fromJson(Map<String, dynamic> json) =>
      DriverProfileDto(
        online: json['is_online'] as bool,
        available: json['is_available'] as bool,
        latitude: (json['current_latitude'] as num?)?.toDouble(),
        longitude: (json['current_longitude'] as num?)?.toDouble(),
        lastSeen: json['last_seen'] == null
            ? null
            : DateTime.parse(json['last_seen'] as String),
      );
}

class TripOfferDto {
  const TripOfferDto({
    required this.id,
    required this.trip,
    required this.distanceToPickupKm,
    required this.expiresAt,
  });
  final int id;
  final TripDto trip;
  final double distanceToPickupKm;
  final DateTime expiresAt;

  factory TripOfferDto.fromJson(Map<String, dynamic> json) => TripOfferDto(
    id: json['id'] as int,
    trip: TripDto.fromJson(Map<String, dynamic>.from(json['trip'] as Map)),
    distanceToPickupKm: double.parse(json['distance_to_pickup_km'].toString()),
    expiresAt: DateTime.parse(json['expires_at'] as String),
  );
}

class RealtimeEnvelope {
  const RealtimeEnvelope({
    required this.schemaVersion,
    required this.eventId,
    required this.type,
    required this.occurredAt,
    required this.aggregateType,
    required this.aggregateId,
    required this.data,
  });
  final String schemaVersion;
  final String eventId;
  final String type;
  final DateTime occurredAt;
  final String aggregateType;
  final String aggregateId;
  final Map<String, dynamic> data;

  factory RealtimeEnvelope.fromJson(Map<String, dynamic> json) {
    final aggregate = Map<String, dynamic>.from(json['aggregate'] as Map);
    return RealtimeEnvelope(
      schemaVersion: json['schema_version'] as String,
      eventId: json['event_id'] as String,
      type: json['type'] as String,
      occurredAt: DateTime.parse(json['occurred_at'] as String),
      aggregateType: aggregate['type'] as String,
      aggregateId: aggregate['id'].toString(),
      data: Map<String, dynamic>.from(json['data'] as Map? ?? const {}),
    );
  }
}

class WalletDto {
  const WalletDto({
    required this.id,
    required this.role,
    required this.availableBalance,
    required this.pendingBalance,
    required this.debtBalance,
  });
  final int id;
  final String role;
  final double availableBalance;
  final double pendingBalance;
  final double debtBalance;

  factory WalletDto.fromJson(Map<String, dynamic> json) => WalletDto(
    id: json['id'] as int,
    role: json['role'] as String,
    availableBalance: double.parse(json['available_balance'].toString()),
    pendingBalance: double.parse(json['pending_balance'].toString()),
    debtBalance: double.parse(json['debt_balance'].toString()),
  );
}
