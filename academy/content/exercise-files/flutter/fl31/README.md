# Lab 5.2: Shop Catalog with go_router

Upgrade the Shop Catalog so every screen has a URL.

## Setup
1. flutter create shop_router
2. cd shop_router
3. flutter pub add go_router
4. Replace lib/main.dart with start/lib/main.dart (pubspec.yaml here shows the expected dependencies).

## Tasks
- TODO(1) Add the sub-route product/:id (name: 'product') under '/'. Parse the id with int.tryParse.
- TODO(2) Navigate from the catalog with context.goNamed.
- TODO(3) Wrap '/', '/cart' and '/account' in StatefulShellRoute.indexedStack (one branch each).
- TODO(4) Build the NavigationBar in HomeShell with shell.currentIndex and shell.goBranch.
- TODO(5) Add a redirect: signed-out users going to /account go to /login?from=/account.
  Signed-in users on /login go to the from value (or '/'). Set refreshListenable: auth.
- TODO(6) Add an errorBuilder that shows NotFoundScreen.

## Acceptance criteria
- Tapping "Steel Bottle" opens /product/2 with a back arrow to the catalog.
- The NavigationBar stays visible on the product page, and switching to Cart and back to Shop keeps the product page open.
- Tapping Account while signed out shows the Sign in screen. Tapping Sign in opens the Account tab.
- Tapping Sign out on the Account tab returns to the Sign in screen without any Navigator call.
- On Chrome, /#/product/99 shows "Product not found" and /#/nowhere shows the not-found screen.
