import 'package:flutter/material.dart';

void main() => runApp(const OnboardingApp());

class OnboardingApp extends StatelessWidget {
  const OnboardingApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Onboarding',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6A1B9A))),
        home: const OnboardingPage(),
      );
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
      Navigator.of(context).pushReplacement(PageRouteBuilder(
        transitionDuration: const Duration(milliseconds: 600),
        pageBuilder: (_, __, ___) => const HomePage(),
        transitionsBuilder: (_, animation, __, child) => FadeTransition(opacity: animation, child: child),
      ));
    } else {
      _pager.nextPage(duration: const Duration(milliseconds: 350), curve: Curves.easeOutCubic);
    }
  }

  void _skip() =>
      _pager.animateToPage(slides.length - 1, duration: const Duration(milliseconds: 500), curve: Curves.easeInOutCubic);

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
        child: Column(children: [
            Align(alignment: Alignment.centerRight, child: TextButton(onPressed: _isLast ? null : _skip, child: const Text('Skip'))),
            Expanded(
              child: PageView.builder(
                controller: _pager,
                itemCount: slides.length,
                onPageChanged: (i) => setState(() => _page = i),
                itemBuilder: (context, i) => SlideView(slide: slides[i], heroTag: i == slides.length - 1 ? 'logo' : null),
              ),
            ),
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              for (var i = 0; i < slides.length; i++)
                AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  curve: Curves.easeOut,
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _page ? 24 : 8, // the active dot grows
                  height: 8,
                  decoration: BoxDecoration(
                    color: i == _page ? scheme.primary : scheme.outlineVariant,
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
            ]),
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _next,
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    child: Text(_isLast ? 'Get started' : 'Next', key: ValueKey(_isLast)),
                  ),
                ),
              ),
            ),
          ]),
      ),
    );
  }
}

class SlideView extends StatefulWidget {
  const SlideView({super.key, required this.slide, this.heroTag});
  final Slide slide;
  final String? heroTag;

  @override
  State<SlideView> createState() => _SlideViewState();
}

class _SlideViewState extends State<SlideView> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 700));
  late final Animation<double> _scale = CurvedAnimation(parent: _c, curve: Curves.elasticOut);
  late final Animation<double> _fade = CurvedAnimation(parent: _c, curve: Curves.easeOut);
  late final Animation<Offset> _slide = Tween(begin: const Offset(0, 0.4), end: Offset.zero).animate(_fade);

  @override
  void initState() {
    super.initState();
    _c.forward();
  }

  @override
  void dispose() {
    _c.dispose(); // always dispose controllers
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    Widget icon = CircleAvatar(radius: 60, child: Icon(widget.slide.icon, size: 56));
    final tag = widget.heroTag;
    if (tag != null) icon = Hero(tag: tag, child: icon);
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        ScaleTransition(scale: _scale, child: icon),
        const SizedBox(height: 32),
        FadeTransition(
          opacity: _fade,
          child: SlideTransition(
            position: _slide,
            child: Column(children: [
              Text(widget.slide.title, style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Text(widget.slide.body, textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
            ]),
          ),
        ),
      ]),
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          leading: const Padding(
            padding: EdgeInsets.all(8),
            child: Hero(tag: 'logo', child: CircleAvatar(child: Icon(Icons.celebration, size: 22))),
          ),
          title: const Text('Home'),
        ),
        body: const Center(child: Text('You are all set!')),
      );
}
