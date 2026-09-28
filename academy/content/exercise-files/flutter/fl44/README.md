# Lesson 8.1 lab: Onboarding app

Build a three-slide onboarding flow that uses implicit animations, explicit
animations and a Hero. No packages are needed, so it runs in DartPad too.

## Setup

    flutter create onboarding_app
    cd onboarding_app

Replace lib/main.dart with start/lib/main.dart. It already compiles: you can
swipe the slides, but nothing is animated yet.

## Tasks (TODOs in lib/main.dart)

- TODO(1) Page dots: turn each dot into an AnimatedContainer (250 ms). The
  active dot is 24 wide in the primary colour; others are 8 wide in
  outlineVariant.
- TODO(2) Next button: animate to the next page with
  _pager.nextPage(duration: 350 ms, curve: Curves.easeOutCubic).
- TODO(3) Button label: wrap it in an AnimatedSwitcher and give the Text a
  ValueKey(_isLast) so "Next" cross-fades to "Get started".
- TODO(4) SlideView: create an AnimationController (700 ms) with
  SingleTickerProviderStateMixin, start it in initState and dispose it.
  The icon uses ScaleTransition with Curves.elasticOut; the texts use
  SlideTransition (from Offset(0, 0.4)) plus FadeTransition.
- TODO(5) "Get started": pushReplacement a PageRouteBuilder that fades to
  HomePage over 600 ms. Wrap the last slide's icon and the HomePage app bar
  icon in Hero(tag: 'logo').

## Acceptance criteria

- The active dot is visibly wider and slides between positions as you swipe.
- Tapping Next moves one slide with an eased animation (no jump).
- On the last slide the button reads "Get started" and Skip is disabled.
- Each slide's icon pops in with a small overshoot when the slide appears.
- Get started fades to the home screen and the logo flies into the app bar.
- Closing the app shows no "Ticker was active" errors in the console.
