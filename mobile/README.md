# MLE Flutter applications

- `customer_app`: customer mobility and future super-app entry point.
- `driver_app`: driver availability, offers, active trips, and earnings.
- `mle_ui`: shared orange-and-blue design tokens and components.
- `mle_api`: shared Dio REST client, secure JWT persistence/refresh, DTOs,
  repositories, and reconnecting versioned WebSocket client.

Flutter is not installed in the current workspace, so native Android/iOS runner
folders have not been generated and compilation is pending. After installing
Flutter:

```text
cd mobile/customer_app
flutter create --platforms=android,ios .
flutter pub get
flutter analyze

cd ../driver_app
flutter create --platforms=android,ios .
flutter pub get
flutter analyze
```

The apps use Riverpod provider containers and the shared network package.
Build-time endpoints are supplied with:

```text
--dart-define=MLE_API_URL=https://api.example.com
--dart-define=MLE_WS_URL=wss://api.example.com
```

Feature screen wiring, geolocation plugins, localization, and offline command
queues remain the next mobile implementation slice.
