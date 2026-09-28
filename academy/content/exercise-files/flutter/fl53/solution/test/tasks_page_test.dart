import 'package:flutter_test/flutter_test.dart';
import 'package:taskflow/main.dart';

class FakeTaskRepository implements TaskRepository {
  FakeTaskRepository({this.fail = false});
  final bool fail;

  @override
  Future<List<Task>> fetchTasks() async {
    if (fail) throw Exception('offline');
    return const [
      Task(id: 1, title: 'Fake task A', completed: false),
      Task(id: 2, title: 'Fake task B', completed: true),
    ];
  }
}

void main() {
  Future<void> setUpWith(TaskRepository repository, AppEnv env) async {
    await getIt.reset();
    setupDependencies(
      AppConfig(env: env, apiBaseUrl: 'http://fake'),
      taskRepository: repository,
    );
  }

  testWidgets('shows tasks from the injected repository', (tester) async {
    await setUpWith(FakeTaskRepository(), AppEnv.dev);
    await tester.pumpWidget(const App());
    await tester.pumpAndSettle();

    expect(find.text('Fake task A'), findsOneWidget);
    expect(find.text('Fake task B'), findsOneWidget);
    expect(find.text('DEV · http://fake'), findsOneWidget);
  });

  testWidgets('prod builds show no banner', (tester) async {
    await setUpWith(FakeTaskRepository(), AppEnv.prod);
    await tester.pumpWidget(const App());
    await tester.pumpAndSettle();

    expect(find.textContaining('http://fake'), findsNothing);
    expect(find.text('Fake task A'), findsOneWidget);
  });

  testWidgets('a failing repository shows Retry', (tester) async {
    await setUpWith(FakeTaskRepository(fail: true), AppEnv.dev);
    await tester.pumpWidget(const App());
    await tester.pumpAndSettle();

    expect(find.text('Could not load tasks.'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
  });
}
