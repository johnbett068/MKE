import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mke_ui/mke_ui.dart';

import 'driver_flow.dart';

void main() => runApp(const ProviderScope(child: DriverApp()));

class DriverApp extends StatelessWidget {
  const DriverApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'MKE Driver',
        theme: mkeTheme(),
        home: const DriverFlowScreen(),
      );
}

class DriverFlowScreen extends ConsumerWidget {
  const DriverFlowScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(driverFlowProvider);
    final controller = ref.read(driverFlowProvider.notifier);
    final body = switch (state.step) {
      DriverStep.phone => _Phone(controller),
      DriverStep.otp => _Otp(controller, state.phone),
      DriverStep.verification => _Verification(state, controller),
      DriverStep.duty => _Duty(state, controller),
      DriverStep.activeTrip => _ActiveTrip(state, controller),
      DriverStep.wallet => _Wallet(state, controller),
    };
    return Scaffold(
      body: SafeArea(
        child: Stack(
          children: [
            body,
            if (state.offer != null) _OfferOverlay(state, controller),
            if (state.busy)
              const ColoredBox(
                color: Color(0x330B1F3A),
                child: Center(child: CircularProgressIndicator()),
              ),
            if (state.error != null)
              Positioned(
                left: 16,
                right: 16,
                bottom: 16,
                child: Material(
                  color: MkeColors.danger,
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
  const _Phone(this.controller);
  final DriverFlowController controller;
  @override
  State<_Phone> createState() => _PhoneState();
}

class _PhoneState extends State<_Phone> {
  final phone = TextEditingController(text: '+254');
  @override
  Widget build(BuildContext context) => _Shell(
        title: 'Drive. Earn. Move MKE.',
        subtitle: 'Sign in with the phone number on your driver account.',
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
      );
}

class _Otp extends StatefulWidget {
  const _Otp(this.controller, this.phone);
  final DriverFlowController controller;
  final String phone;
  @override
  State<_Otp> createState() => _OtpState();
}

class _OtpState extends State<_Otp> {
  final code = TextEditingController();
  @override
  Widget build(BuildContext context) => _Shell(
        title: 'Verify your number',
        subtitle: 'We sent a 6-digit code to ${widget.phone}.',
        children: [
          TextField(
            controller: code,
            keyboardType: TextInputType.number,
            maxLength: 6,
            decoration: const InputDecoration(labelText: 'Verification code'),
          ),
          FilledButton(
            onPressed: () => widget.controller.confirmOtp(code.text.trim()),
            child: const Text('Continue'),
          ),
        ],
      );
}

class _Shell extends StatelessWidget {
  const _Shell({
    required this.title,
    required this.subtitle,
    required this.children,
  });
  final String title;
  final String subtitle;
  final List<Widget> children;
  @override
  Widget build(BuildContext context) => Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0B1F3A), Color(0xFF155EEF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const MkeBrandMark(size: 54),
                    const SizedBox(height: 22),
                    Text(title,
                        style: Theme.of(context).textTheme.headlineMedium),
                    const SizedBox(height: 8),
                    Text(subtitle),
                    const SizedBox(height: 26),
                    ...children,
                  ],
                ),
              ),
            ),
          ),
        ),
      );
}

class _Verification extends StatelessWidget {
  const _Verification(this.state, this.controller);
  final DriverFlowState state;
  final DriverFlowController controller;
  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const MkeBrandMark(),
          const SizedBox(height: 20),
          Text(
            'Driver verification',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 8),
          Text(
            'Application status: ${state.applicationStatus.replaceAll('_', ' ')}',
          ),
          const SizedBox(height: 20),
          ...[
            ('national_id', 'National ID', Icons.badge),
            ('driving_license', 'Driving licence', Icons.credit_card),
            ('vehicle_logbook', 'Vehicle logbook', Icons.directions_car),
            ('insurance', 'Insurance certificate', Icons.verified_user),
          ].map((item) {
            final uploaded = state.documents.any(
              (doc) => doc['document_type'] == item.$1,
            );
            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              child: ListTile(
                leading: Icon(
                  item.$3,
                  color: uploaded ? MkeColors.success : MkeColors.orange,
                ),
                title: Text(item.$2),
                subtitle:
                    Text(uploaded ? 'Uploaded — under review' : 'Required'),
                trailing: uploaded
                    ? const Icon(Icons.check_circle, color: MkeColors.success)
                    : IconButton(
                        icon: const Icon(Icons.camera_alt),
                        onPressed: () => controller.uploadDocument(item.$1),
                      ),
              ),
            );
          }),
          const SizedBox(height: 14),
          FilledButton(
            onPressed: controller.refreshApplication,
            child: const Text('Refresh approval status'),
          ),
        ],
      );
}

class _Duty extends StatelessWidget {
  const _Duty(this.state, this.controller);
  final DriverFlowState state;
  final DriverFlowController controller;
  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Row(
            children: [
              const MkeBrandMark(),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Driver control',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ),
              IconButton(
                onPressed: controller.openWallet,
                icon: const Icon(Icons.account_balance_wallet),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Container(
            padding: const EdgeInsets.all(22),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: state.online
                    ? [MkeColors.orange, const Color(0xFFFF6B35)]
                    : [MkeColors.navy, const Color(0xFF344054)],
              ),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            state.online ? 'You’re online' : 'You’re offline',
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w900,
                              fontSize: 24,
                            ),
                          ),
                          const SizedBox(height: 5),
                          Text(
                            state.online
                                ? 'Ready for nearby requests'
                                : 'Go online when you’re ready',
                            style: const TextStyle(color: Colors.white70),
                          ),
                        ],
                      ),
                    ),
                    Switch(
                      value: state.online,
                      activeTrackColor: Colors.white,
                      activeThumbColor: MkeColors.orange,
                      onChanged: controller.toggleDuty,
                    ),
                  ],
                ),
                if (state.online) ...[
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Icon(
                        state.heartbeatHealthy
                            ? Icons.gps_fixed
                            : Icons.gps_off,
                        color: Colors.white,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        state.heartbeatHealthy
                            ? 'GPS heartbeat healthy'
                            : 'Reconnecting GPS heartbeat',
                        style: const TextStyle(color: Colors.white),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 28),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  const Icon(Icons.radar, color: MkeColors.blue, size: 54),
                  const SizedBox(height: 14),
                  Text(
                    state.online
                        ? 'Scanning nearby requests'
                        : 'Requests paused',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Only offers assigned to you will appear here.',
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
        ],
      );
}

class _OfferOverlay extends StatelessWidget {
  const _OfferOverlay(this.state, this.controller);
  final DriverFlowState state;
  final DriverFlowController controller;
  @override
  Widget build(BuildContext context) {
    final offer = state.offer!;
    return ColoredBox(
      color: const Color(0xCC0B1F3A),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  SizedBox(
                    width: 92,
                    height: 92,
                    child: CustomPaint(
                      painter: _CountdownPainter(state.offerSeconds / 30),
                      child: Center(
                        child: Text(
                          '${state.offerSeconds}',
                          style: const TextStyle(
                            fontSize: 32,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 18),
                  Text(
                    'New ride request',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    '${offer.distanceToPickupKm.toStringAsFixed(1)} km to pickup',
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'KES ${offer.trip.quotedFare?.toStringAsFixed(0) ?? '—'}',
                    style: const TextStyle(
                      color: MkeColors.orange,
                      fontSize: 28,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 22),
                  FilledButton(
                    onPressed: controller.acceptOffer,
                    child: const Text('Accept ride'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: controller.rejectOffer,
                    child: const Text('Decline'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _CountdownPainter extends CustomPainter {
  const _CountdownPainter(this.progress);
  final double progress;
  @override
  void paint(Canvas canvas, Size size) {
    final rect = Offset.zero & size;
    canvas.drawArc(
      rect.deflate(5),
      -math.pi / 2,
      math.pi * 2 * progress,
      false,
      Paint()
        ..color = progress < .25 ? MkeColors.danger : MkeColors.orange
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round
        ..strokeWidth = 8,
    );
  }

  @override
  bool shouldRepaint(_CountdownPainter oldDelegate) =>
      oldDelegate.progress != progress;
}

class _ActiveTrip extends StatefulWidget {
  const _ActiveTrip(this.state, this.controller);
  final DriverFlowState state;
  final DriverFlowController controller;
  @override
  State<_ActiveTrip> createState() => _ActiveTripState();
}

class _ActiveTripState extends State<_ActiveTrip> {
  final pin = TextEditingController();
  @override
  Widget build(BuildContext context) {
    final status = widget.state.trip?.status ?? 'accepted';
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text('Active trip', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        Text('Status: ${status.replaceAll('_', ' ')}'),
        const SizedBox(height: 24),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                const Icon(Icons.navigation, size: 50, color: MkeColors.blue),
                const SizedBox(height: 12),
                Text(
                  status == 'in_progress'
                      ? 'Driving to destination'
                      : 'Head to pickup',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        if (status == 'accepted') ...[
          FilledButton(
            onPressed: widget.controller.arrived,
            child: const Text('I have arrived'),
          ),
          const SizedBox(height: 14),
          TextField(
            controller: pin,
            maxLength: 4,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Customer 4-digit PIN',
            ),
          ),
          FilledButton(
            onPressed: () => widget.controller.startTrip(pin.text.trim()),
            child: const Text('Verify PIN and start trip'),
          ),
        ] else if (status == 'in_progress')
          FilledButton(
            onPressed: widget.controller.completeTrip,
            child: const Text('Complete trip'),
          ),
      ],
    );
  }
}

class _Wallet extends StatefulWidget {
  const _Wallet(this.state, this.controller);
  final DriverFlowState state;
  final DriverFlowController controller;
  @override
  State<_Wallet> createState() => _WalletState();
}

class _WalletState extends State<_Wallet> {
  final amount = TextEditingController(text: '500');
  @override
  Widget build(BuildContext context) {
    final wallet = widget.state.wallet;
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Row(
          children: [
            IconButton(
              onPressed: widget.controller.closeWallet,
              icon: const Icon(Icons.arrow_back),
            ),
            Text(
              'Wallet & commission',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ],
        ),
        const SizedBox(height: 24),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('AVAILABLE BALANCE'),
                const SizedBox(height: 6),
                Text(
                  'KES ${wallet?.availableBalance.toStringAsFixed(2) ?? '0.00'}',
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const Divider(height: 30),
                Text(
                  'Commission debt: KES '
                  '${wallet?.debtBalance.toStringAsFixed(2) ?? '0.00'}',
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        TextField(
          controller: amount,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Top-up amount (KES)'),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: () {
            final value = double.tryParse(amount.text);
            if (value != null && value > 0) widget.controller.topUp(value);
          },
          icon: const Icon(Icons.phone_android),
          label: const Text('Top up with M-Pesa'),
        ),
      ],
    );
  }
}
