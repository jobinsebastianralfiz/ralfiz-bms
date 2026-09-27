# cmpHeader component spec (library: Campus UI)

## Custom properties
| Property | Kind | Data type | Default | Purpose |
|----------|------|-----------|---------|---------|
| Title | Input | Text | "Campus Help Desk" | Text shown in the header |
| Colour | Input | Color | ColorValue("#1F4E9A") | Header fill, so each app can pass its theme |
| ShowBack | Input | Boolean | true | Hide the back icon on the home screen |
| IsMenuOpen | Output | Boolean | | Tells the app whether the menu is open |
| OnBack | Behavior | | | Event the app handles, for example Back() |

If the Behavior property kind is not offered, check the app settings for the component
property features under upcoming features and turn them on.

## Controls inside the component (width 640, height 64)
| Control | Property | Formula |
|---------|----------|---------|
| recBar | Fill | cmpHeader.Colour |
| recBar | Width | cmpHeader.Width |
| icoBack | Visible | cmpHeader.ShowBack |
| icoBack | OnSelect | cmpHeader.OnBack() |
| icoBack | AccessibleLabel | "Go back" |
| lblTitle | Text | cmpHeader.Title |
| lblTitle | Color | Color.White |
| icoMenu | OnSelect | Set(varMenuOpen, !varMenuOpen) |
| icoMenu | AccessibleLabel | If(varMenuOpen, "Close menu", "Open menu") |
| icoMenu | X | cmpHeader.Width - Self.Width - 8 |
| (component) | IsMenuOpen output | varMenuOpen |

A variable set inside a component belongs to that component only. The component never
reads app variables or data sources; everything it needs arrives through input properties.

## Use in the student app
| Screen | Title | ShowBack | OnBack |
|--------|-------|----------|--------|
| scrHome | "My tickets" | false | (none) |
| scrNew | "New ticket" | true | Back() |
| scrDetail | "Ticket details" | true | Back() |
| scrSaved | "Saved for later" | true | Back() |

Set the header Width to Parent.Width on every screen.

## Design-quality checklist
- [ ] Scale to fit is off and the home screen uses containers
- [ ] Home screen works at 360 px wide (phone preview) without controls overlapping
- [ ] Every icon and image has an AccessibleLabel
- [ ] Priority is shown as text, not colour only
- [ ] App checker shows 0 accessibility errors
- [ ] OnStart only contains Concurrent(...) with the two loads
- [ ] Monitor session recorded before and after the OnStart change
