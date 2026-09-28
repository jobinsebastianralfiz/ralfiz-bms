import 'package:flutter/material.dart';

void main() => runApp(const OnboardingApp());

class OnboardingApp extends StatelessWidget {
  const OnboardingApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Onboarding',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6A1B9A))),
      home: const OnboardingPage(),
    );
  }
}

class Slide {
  const Slide(this.icon, this.title, this.body);
  final IconData icon;
  final String title;
  final String body;
}

const slides = [
  Slide(Icons.explore, 'Discover', 'Find study groups near you.'),
  Slide(Icons.event_available, 'Plan', 'Book sessions in two taps.'),
  Slide(Icons.celebration, 'Grow', 'Track streaks and level up.'),
];

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final _pager = PageController();
  int _page = 0;

  bool get _isLast => _page == slides.length - 1;

  void _next() {
    if (_isLast) {
      // TODO(5): pushReplacement a PageRouteBuilder that fades to HomePage (600 ms).
      Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const HomePage()));
    } else {
      // TODO(2): animate with nextPage (350 ms, Curves.easeOutCubic).
      _pager.jumpToPage(_page + 1);
    }
  }

  @override
  void dispose() {
    _pager.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: _isLast ? null : () => _pager.jumpToPage(slides.length - 1),
                child: const Text('Skip'),
              ),
            ),
            Expanded(
              child: PageView.builder(
                controller: _pager,
                itemCount: slides.length,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (context, i) => SlideView(slide: slides[i]),
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (var i = 0; i < slides.length; i++)
                  // TODO(1): make this an AnimatedContainer; active dot 24 wide.
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: i == _page ? scheme.primary : scheme.outlineVariant,
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _next,
                  // TODO(3): AnimatedSwitcher + Text with key: ValueKey(_isLast).
                  child: Text(_isLast ? 'Get started' : 'Next'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class SlideView extends StatefulWidget {
  const SlideView({super.key, required this.slide});
  final Slide slide;

  @override
  State<SlideView> createState() => _SlideViewState();
}

// TODO(4): add SingleTickerProviderStateMixin, an AnimationController (700 ms)
// started in initState and disposed in dispose, then ScaleTransition on the icon
// and SlideTransition + FadeTransition on the texts.
class _SlideViewState extends State<SlideView> {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final icon = Container(
      width: 120,
      height: 120,
      decoration: BoxDecoration(color: theme.colorScheme.primaryContainer, shape: BoxShape.circle),
      child: Icon(widget.slide.icon, size: 56, color: theme.colorScheme.onPrimaryContainer),
    );
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          icon, // TODO(5): wrap in Hero(tag: 'logo') on the last slide only.
          const SizedBox(height: 32),
          Text(widget.slide.title, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Text(widget.slide.body, textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        // TODO(5): wrap this icon in Hero(tag: 'logo').
        leading: const Icon(Icons.celebration),
        title: const Text('Home'),
      ),
      body: const Center(child: Text('You are all set!')),
    );
  }
}
