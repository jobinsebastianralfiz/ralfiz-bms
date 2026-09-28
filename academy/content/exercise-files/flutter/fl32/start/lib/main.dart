import 'package:flutter/material.dart';
// TODO(3): you will need this import for FilteringTextInputFormatter.
// import 'package:flutter/services.dart';

void main() {
  runApp(MaterialApp(
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
    ),
    home: const RegistrationPage(),
  ));
}

enum TicketType {
  standard('Standard'), student('Student'), vip('VIP');
  const TicketType(this.label);
  final String label;
}

// TODO(2): return an error message, or null when the value is valid.
//   validateName: 'Enter your name' when empty after trim().
//   validateEmail: 'Enter your email' when empty, 'Enter a valid email' when it
//                  does not look like name@domain.tld (use a RegExp).
//   validatePhone: 'Enter a 10-digit phone number' unless exactly 10 digits.
String? validateName(String? value) => null;
String? validateEmail(String? value) => null;
String? validatePhone(String? value) => null;

class RegistrationPage extends StatefulWidget {
  const RegistrationPage({super.key});

  @override
  State<RegistrationPage> createState() => _RegistrationPageState();
}

class _RegistrationPageState extends State<RegistrationPage> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _nameFocus = FocusNode();
  var _ticket = TicketType.standard;

  // TODO(6): override dispose() and dispose the three controllers and _nameFocus.

  Future<void> _submit() async {
    // TODO(5): 1. unfocus the keyboard  2. return if validate() fails
    //          3. show a loading state for one second  4. showDialog with
    //          '$name · $ticket ticket'  5. clear the controllers, reset the form
    //          and move focus back to the name field.
    final name = _name.text;
    final ticket = _ticket.label;
    debugPrint('Register $name for $ticket');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Flutter Meetup Kochi')),
      // TODO(1): wrap the scroll view in Form(key: _formKey, autovalidateMode: ...).
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 16,
          children: [
            // TODO(3): add validator, keyboardType, textInputAction and
            //          inputFormatters to these three fields.
            TextFormField(
              controller: _name,
              focusNode: _nameFocus,
              decoration: const InputDecoration(labelText: 'Full name', prefixIcon: Icon(Icons.person)),
            ),
            TextFormField(
              controller: _email,
              decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email)),
            ),
            TextFormField(
              controller: _phone,
              decoration: const InputDecoration(labelText: 'Phone', prefixIcon: Icon(Icons.phone)),
            ),
            DropdownButtonFormField<TicketType>(
              initialValue: TicketType.standard,
              decoration: const InputDecoration(
                  labelText: 'Ticket type', prefixIcon: Icon(Icons.confirmation_number)),
              items: [
                for (final t in TicketType.values)
                  DropdownMenuItem(value: t, child: Text(t.label)),
              ],
              onChanged: (t) => _ticket = t ?? TicketType.standard,
            ),
            // TODO(4): replace this Text with a FormField<bool> that shows a
            //          CheckboxListTile and the error 'Please accept the code of conduct'.
            const Text('I accept the code of conduct'),
            FilledButton(onPressed: _submit, child: const Text('Register')),
          ],
        ),
      ),
    );
  }
}
