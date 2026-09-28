import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:taskflow/models/task.dart';

const samplePage = '''
{"todos":[
  {"id":1,"todo":"Do something nice for someone you care about","completed":false,"userId":152},
  {"id":2,"todo":"Memorize a poem","completed":true,"userId":13,"priority":"high"},
  {"id":3,"todo":"Watch a classic movie","completed":false,"userId":68,"priority":"urgent"}],
 "total":254,"skip":0,"limit":3}
''';

void main() {
  late TodosPage page;

  setUp(() {
    page = TodosPage.fromJson(jsonDecode(samplePage) as Map<String, dynamic>);
  });

  test('parses the page and renames todo to title', () {
    expect(page.todos, hasLength(3));
    expect(page.total, 254);
    expect(page.todos.first.title,
        'Do something nice for someone you care about');
    expect(page.todos[1].completed, isTrue);
    expect(page.hasMore, isTrue);
  });

  test('priority: missing -> normal, known -> value, unknown -> normal', () {
    expect(page.todos[0].priority, TaskPriority.normal);
    expect(page.todos[1].priority, TaskPriority.high);
    expect(page.todos[2].priority, TaskPriority.normal);
  });

  test('value equality and copyWith', () {
    final task = page.todos.first;
    final done = task.copyWith(completed: true);
    expect(done, isNot(task));
    expect(done, task.copyWith(completed: true));
    expect(task.completed, isFalse, reason: 'the original never changes');
  });

  test('copyWith can clear a nullable field', () {
    final withDate = page.todos.first.copyWith(dueDate: DateTime(2020, 1, 1));
    expect(withDate.isOverdue, isTrue);
    final cleared = withDate.copyWith(dueDate: null);
    expect(cleared.dueDate, isNull);
    expect(cleared.isOverdue, isFalse);
  });

  test('toJson uses the API key names and round-trips', () {
    final task = page.todos[1];
    final json = task.toJson();
    expect(json['todo'], 'Memorize a poem');
    expect(json['priority'], 'high');
    expect(Task.fromJson(json), task);
  });

  test('a whole page survives jsonEncode and jsonDecode', () {
    final text = jsonEncode(page.toJson());
    final again = TodosPage.fromJson(jsonDecode(text) as Map<String, dynamic>);
    expect(again, page);
  });

  test('the union can be switched exhaustively', () {
    expect(describeState(const TasksState.loading()), 'Loading');
    expect(describeState(TasksState.loaded(page.todos)), 'Tasks: 3');
    expect(describeState(const TasksState.failure('offline')), 'Error: offline');
  });
}
