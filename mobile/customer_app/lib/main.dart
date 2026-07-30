import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:mle_ui/mle_ui.dart';

import 'customer_flow.dart';

void main() => runApp(const ProviderScope(child: CustomerApp()));

class CustomerApp extends StatelessWidget {
  const CustomerApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'MKE',
        theme: mleTheme(),
        home: const CustomerFlowScreen(),
      );
}

class CustomerFlowScreen extends ConsumerWidget {
  const CustomerFlowScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(customerFlowProvider);
    final controller = ref.read(customerFlowProvider.notifier);
    final body = switch (state.step) {
      CustomerStep.phone => _Phone(controller: controller),
      CustomerStep.otp => _Otp(controller: controller, phone: state.phone),
      CustomerStep.home => _MapHome(state: state, controller: controller),
      CustomerStep.quote => _Quote(state: state, controller: controller),
      CustomerStep.dispatching => _Dispatch(
          state: state,
          controller: controller,
        ),
      CustomerStep.tracking => _Tracking(state: state, controller: controller),
      CustomerStep.complete => _Complete(state: state, controller: controller),
    };
    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            body,
            if (state.busy)
              const ColoredBox(
                color: Color(0x330B1F3A),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (state.error != null)
              Positioned(
                left: 16,
                right: 16,
                bottom: 18,
                child: Material(
                  color: MleColors.danger,
                  borderRadius: BorderRadius.circular(14),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      state.error!,
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Phone extends StatefulWidget {
  const _Phone({required this.controller});
  final CustomerFlowController controller;
  @override
  State<_Phone> createState() => _PhoneState();
}

class _PhoneState extends State<_Phone> {
  final phone = TextEditingController(text: '+254');
  @override
  Widget build(BuildContext context) => _AuthShell(
        title: 'Your city, one tap away.',
        subtitle: 'Enter your mobile number to securely continue.',
        child: Column(
          children: [
            TextField(
              controller: phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone number'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => widget.controller.requestOtp(phone.text.trim()),
              child: const Text('Send verification code'),
            ),
          ],
        ),
      );
}

class _Otp extends StatefulWidget {
  const _Otp({required this.controller, required this.phone});
  final CustomerFlowController controller;
  final String phone;
  @override
  State<_Otp> createState() => _OtpState();
}

class _OtpState extends State<_Otp> {
  final code = TextEditingController();
  @override
  Widget build(BuildContext context) => _AuthShell(
        title: 'Verify it’s you',
        subtitle: 'Enter the 6-digit code sent to ${widget.phone}.',
        child: Column(
          children: [
            TextField(
              controller: code,
              maxLength: 6,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Verification code'),
            ),
            FilledButton(
              onPressed: () => widget.controller.confirmOtp(code.text.trim()),
              child: const Text('Verify and continue'),
            ),
          ],
        ),
      );
}

class _AuthShell extends StatelessWidget {
  const _AuthShell({
    required this.title,
    required this.subtitle,
    required this.child,
  });
  final String title;
  final String subtitle;
  final Widget child;
  @override
  Widget build(BuildContext context) => Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFFFFF7ED), Color(0xFFEFF4FF)],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const MleBrandMark(size: 54),
                      const SizedBox(height: 24),
                      Text(
                        title,
                        style: Theme.of(context).textTheme.headlineMedium,
                      ),
                      const SizedBox(height: 8),
                      Text(subtitle),
                      const SizedBox(height: 28),
                      child,
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      );
}

class _MapHome extends StatefulWidget {
  const _MapHome({required this.state, required this.controller});
  final CustomerFlowState state;
  final CustomerFlowController controller;
  @override
  State<_MapHome> createState() => _MapHomeState();
}

class _MapHomeState extends State<_MapHome> {
  bool choosingDropoff = false;
  static const fallback = LatLng(-0.7813, 35.3416);
  @override
  Widget build(BuildContext context) {
    final pickup = widget.state.pickup;
    final dropoff = widget.state.dropoff;
    final markers = <Marker>{
      if (pickup != null)
        Marker(
          markerId: const MarkerId('pickup'),
          position: LatLng(pickup.latitude, pickup.longitude),
          infoWindow: const InfoWindow(title: 'Pickup'),
        ),
      if (dropoff != null)
        Marker(
          markerId: const MarkerId('dropoff'),
          position: LatLng(dropoff.latitude, dropoff.longitude),
          infoWindow: const InfoWindow(title: 'Destination'),
        ),
    };
    return Stack(
      children: [
        GoogleMap(
          initialCameraPosition: CameraPosition(
            target: pickup == null
                ? fallback
                : LatLng(pickup.latitude, pickup.longitude),
            zoom: 14,
          ),
          myLocationEnabled: true,
          myLocationButtonEnabled: true,
          markers: markers,
          onTap: (point) => choosingDropoff
              ? widget.controller.setDropoff(point.latitude, point.longitude)
              : widget.controller.setPickup(point.latitude, point.longitude),
        ),
        Positioned(
          top: 16,
          left: 16,
          right: 16,
          child: Row(
            children: [
              const MleBrandMark(),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Where are you going?',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
            ],
          ),
        ),
        Positioned(
          left: 16,
          right: 16,
          bottom: 16,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _PlaceRow(
                    icon: Icons.my_location,
                    color: MleColors.orange,
                    label: pickup?.label ?? 'Tap map to choose pickup',
                    selected: !choosingDropoff,
                    onTap: () => setState(() => choosingDropoff = false),
                  ),
                  const Divider(),
                  _PlaceRow(
                    icon: Icons.location_on,
                    color: MleColors.blue,
                    label: dropoff?.label ?? 'Tap map to choose destination',
                    selected: choosingDropoff,
                    onTap: () => setState(() => choosingDropoff = true),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: () async {
                      final current =
                          await widget.controller.useCurrentLocation();
                      if (current != null) {
                        await widget.controller.setPickup(
                          current.latitude,
                          current.longitude,
                        );
                      }
                    },
                    icon: const Icon(Icons.gps_fixed),
                    label: const Text('Use my current location'),
                  ),
                  const SizedBox(height: 8),
                  FilledButton(
                    onPressed: pickup != null && dropoff != null
                        ? widget.controller.quote
                        : null,
                    child: const Text('See fare options'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _PlaceRow extends StatelessWidget {
  const _PlaceRow({
    required this.icon,
    required this.color,
    required this.label,
    required this.selected,
    required this.onTap,
  });
  final IconData icon;
  final Color color;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => ListTile(
        onTap: onTap,
        selected: selected,
        selectedTileColor: MleColors.orangeSoft,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        leading: Icon(icon, color: color),
        title: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
        trailing: selected ? const Icon(Icons.edit_location_alt) : null,
      );
}

class _Quote extends StatelessWidget {
  const _Quote({required this.state, required this.controller});
  final CustomerFlowState state;
  final CustomerFlowController controller;
  @override
  Widget build(BuildContext context) {
    final quote = state.quote!;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 12),
        Text(
          'Choose your ride',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text(
          '${quote.distanceKm.toStringAsFixed(1)} km • '
          '${quote.durationMinutes.ceil()} min estimated',
        ),
        const SizedBox(height: 24),
        Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(18),
            leading: const CircleAvatar(
              backgroundColor: MleColors.orangeSoft,
              child: Icon(Icons.local_taxi, color: MleColors.orange),
            ),
            title: const Text(
              'MKE Ride',
              style: TextStyle(fontWeight: FontWeight.w800),
            ),
            subtitle: const Text('Comfortable, dependable city ride'),
            trailing: Text(
              'KES ${quote.fare.toStringAsFixed(0)}',
              style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 18),
            ),
          ),
        ),
        const SizedBox(height: 16),
        SegmentedButton<String>(
          segments: const [
            ButtonSegment(
              value: 'cash',
              label: Text('Cash'),
              icon: Icon(Icons.payments),
            ),
            ButtonSegment(
              value: 'mpesa',
              label: Text('M-Pesa'),
              icon: Icon(Icons.phone_android),
            ),
          ],
          selected: {state.paymentMethod},
          onSelectionChanged: (value) => controller.choosePayment(value.first),
        ),
        const SizedBox(height: 16),
        Card(
          color: const Color(0xFFEFF4FF),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.lock_clock, color: MleColors.blue),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'Price locked until '
                    '${TimeOfDay.fromDateTime(quote.expiresAt).format(context)}',
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 28),
        FilledButton(
          onPressed: controller.book,
          child: const Text('Confirm ride'),
        ),
      ],
    );
  }
}

class _Dispatch extends StatelessWidget {
  const _Dispatch({required this.state, required this.controller});
  final CustomerFlowState state;
  final CustomerFlowController controller;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const SizedBox(
                width: 96,
                height: 96,
                child: CircularProgressIndicator(strokeWidth: 8),
              ),
              const SizedBox(height: 30),
              Text(
                'Finding your driver',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              const Text(
                  'We’re sending your request to nearby verified drivers.'),
              const SizedBox(height: 28),
              if (state.trip?.startPin != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      children: [
                        const Text('YOUR RIDE-START PIN'),
                        const SizedBox(height: 8),
                        Text(
                          state.trip!.startPin!,
                          style: const TextStyle(
                            fontSize: 38,
                            fontWeight: FontWeight.w900,
                            letterSpacing: 8,
                          ),
                        ),
                        const Text(
                            'Only share this after meeting your driver.'),
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 24),
              TextButton(
                onPressed: controller.cancel,
                child: const Text('Cancel request'),
              ),
            ],
          ),
        ),
      );
}

class _Tracking extends StatelessWidget {
  const _Tracking({required this.state, required this.controller});
  final CustomerFlowState state;
  final CustomerFlowController controller;
  @override
  Widget build(BuildContext context) {
    final pickup = state.pickup!;
    final driver = state.driverLatitude == null
        ? null
        : LatLng(state.driverLatitude!, state.driverLongitude!);
    return Stack(
      children: [
        GoogleMap(
          initialCameraPosition: CameraPosition(
            target: LatLng(pickup.latitude, pickup.longitude),
            zoom: 15,
          ),
          markers: {
            Marker(
              markerId: const MarkerId('pickup'),
              position: LatLng(pickup.latitude, pickup.longitude),
            ),
            if (driver != null)
              Marker(
                markerId: const MarkerId('driver'),
                position: driver,
                icon: BitmapDescriptor.defaultMarkerWithHue(
                  BitmapDescriptor.hueOrange,
                ),
              ),
          },
        ),
        Positioned(
          left: 16,
          right: 16,
          bottom: 16,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    state.trip?.status == 'in_progress'
                        ? 'You’re on your way'
                        : 'Your driver is coming',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Live trip status: ${state.trip?.status.replaceAll('_', ' ')}',
                  ),
                  if (state.trip?.startPin != null) ...[
                    const SizedBox(height: 12),
                    Text(
                      'Start PIN  ${state.trip!.startPin}',
                      style: const TextStyle(
                        color: MleColors.orange,
                        fontWeight: FontWeight.w900,
                        fontSize: 20,
                      ),
                    ),
                  ],
                  const SizedBox(height: 12),
                  TextButton(
                    onPressed: controller.cancel,
                    child: const Text('Cancel trip'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _Complete extends StatelessWidget {
  const _Complete({required this.state, required this.controller});
  final CustomerFlowState state;
  final CustomerFlowController controller;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const CircleAvatar(
                radius: 42,
                backgroundColor: Color(0xFFE7F8EF),
                child: Icon(Icons.check, size: 48, color: MleColors.success),
              ),
              const SizedBox(height: 22),
              Text(
                'You’ve arrived',
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Fare: KES ${state.trip?.quotedFare?.toStringAsFixed(0) ?? '—'}',
              ),
              const SizedBox(height: 28),
              FilledButton(
                onPressed: controller.reset,
                child: const Text('Book another ride'),
              ),
            ],
          ),
        ),
      );
}
