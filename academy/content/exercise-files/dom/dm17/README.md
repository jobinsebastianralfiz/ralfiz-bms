# Lab 4.7 - Ralfiz Deals page

Build a promo page that uses the browser's platform APIs, with a fallback for each one.

## Run it

These APIs need a secure context, so serve the folder from localhost:

- VS Code: right-click `start/index.html` and choose **Open with Live Server**, or
- a terminal in `dom/dm17/start`: `npx serve` and open the printed URL.

Opening the file directly (`file://`) will not work for the clipboard or geolocation.

## Tasks (in start/app.js)

1. TODO(1) `copyText(text)`: Clipboard API with a select-the-input fallback.
2. TODO(2) Share button: Web Share when available (ignore AbortError), else copy the URL.
3. TODO(3) `applyTheme()`: System / Light / Dark saved in localStorage, following
   `prefers-color-scheme` live when the choice is System.
4. TODO(4) Offline banner using `navigator.onLine` and the online/offline events;
   disable the Claim button while offline.
5. TODO(5) Countdown: compute the remaining time from the end date; skip updates while
   the tab is hidden and refresh immediately when it becomes visible.
6. TODO(6) Store finder (Geolocation) and Deal alerts (Notifications), only from clicks.

## Test with DevTools

- Network panel: switch to **Offline** and back.
- Rendering panel (More tools): **Emulate CSS media feature prefers-color-scheme**.
- Sensors panel (More tools): pick a city under **Location**.

## Acceptance criteria

- Copy code puts RALFIZ20 on the clipboard and the status says so; if the clipboard is
  blocked, the code is selected and the status tells the user to press Ctrl+C.
- The theme buttons show which one is pressed; on System the page follows the OS setting.
- Going offline shows the banner and disables Claim; going online hides it again.
- Denying location shows "Location blocked" and a manual store list is still usable.
