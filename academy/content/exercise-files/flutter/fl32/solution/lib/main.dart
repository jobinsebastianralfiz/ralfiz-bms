import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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

// Validators are plain functions: easy to reuse and to unit test.
String? validateName(String? value) {
  final v = value?.trim() ?? '';
  if (v.isEmpty) return 'Enter your name';
  return null;
}

final _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
String? validateEmail(String? value) {
  final v = value?.trim() ?? '';
  if (v.isEmpty) return 'Enter your email';
  if (!_emailPattern.hasMatch(v)) return 'Enter a valid email';
  return null;
}
String? validatePhone(String? value) =>
    (value ?? '').length == 10 ? null : 'Enter a 10-digit phone number';

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
  var _autovalidate = AutovalidateMode.disabled;
  var _ticket = TicketType.standard;
  var _submitting = false;

  @override
  void dispose() {
    for (final c in [_name, _email, _phone]) {
      c.dispose();
    }
    _nameFocus.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) {
      setState(() => _autovalidate = AutovalidateMode.onUserInteraction);
      return;
    }
    setState(() => _submitting = true);
    await Future<void>.delayed(const Duration(seconds: 1)); // pretend network call
    if (!mounted) return;
    setState(() => _submitting = false);

    final name = _name.text.trim();
    final ticket = _ticket.label;
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.celebration),
        title: const Text('You are in!'),
        content: Text('$name · $ticket ticket'),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Done'))],
      ),
    );
    if (!mounted) return;
    _name.clear();
    _email.clear();
    _phone.clear();
    _formKey.currentState!.reset(); // dropdown and checkbox back to initial values
    setState(() {
      _ticket = TicketType.standard;
      _autovalidate = AutovalidateMode.disabled;
    });
    _nameFocus.requestFocus();
  }

  @override
  Widget build(BuildContext context) {
    final errorColor = Theme.of(context).colorScheme.error;
    return Scaffold(
      appBar: AppBar(title: const Text('Flutter Meetup Kochi')),
      body: Form(
        key: _formKey,
        autovalidateMode: _autovalidate,
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 16,
            children: [
              TextFormField(
                controller: _name,
                focusNode: _nameFocus,
                decoration: const InputDecoration(labelText: 'Full name', prefixIcon: Icon(Icons.person)),
                textCapitalization: TextCapitalization.words,
                textInputAction: TextInputAction.next,
                validator: validateName,
              ),
              TextFormField(
                controller: _email,
                decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email)),
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                autofillHints: const [AutofillHints.email],
                validator: validateEmail,
              ),
              TextFormField(
                controller: _phone,
                decoration: const InputDecoration(labelText: 'Phone', prefixIcon: Icon(Icons.phone)),
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.done,
                inputFormatters: [
                  FilteringTextInputFormatter.digitsOnly,
                  LengthLimitingTextInputFormatter(10),
                ],
                validator: validatePhone,
                onFieldSubmitted: (_) => _submit(),
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
              FormField<bool>(
                initialValue: false,
                validator: (v) => v == true ? null : 'Please accept the code of conduct',
                builder: (field) => Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CheckboxListTile(
                      value: field.value ?? false,
                      onChanged: field.didChange,
                      title: const Text('I accept the code of conduct'),
                      controlAffinity: ListTileControlAffinity.leading,
                      contentPadding: EdgeInsets.zero,
                    ),
                    if (field.hasError)
                      Text(field.errorText ?? '', style: TextStyle(color: errorColor)),
                  ],
                ),
              ),
              FilledButton(
                onPressed: _submitting ? null : _submit,
                child: _submitting
                    ? const SizedBox.square(
                        dimension: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
