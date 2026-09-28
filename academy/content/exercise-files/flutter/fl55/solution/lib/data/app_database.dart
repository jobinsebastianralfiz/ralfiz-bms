import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'app_database.g.dart';

// SOLUTION - lesson 10.1: the TaskFlow local database with Drift.
// After every change to this file run: dart run build_runner build -d

enum Priority { low, normal, high }

@DataClassName('ProjectRow')
class Projects extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get name => text().withLength(min: 1, max: 60)();
}

@DataClassName('TaskRow')
class Tasks extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get title => text().withLength(min: 1, max: 200)();
  BoolColumn get done => boolean().withDefault(const Constant(false))();
  IntColumn get projectId => integer()
      .nullable()
      .references(Projects, #id, onDelete: KeyAction.setNull)();
  DateTimeColumn get updatedAt => dateTime().withDefault(currentDateAndTime)();
  // Added in schema version 2. Stored as the enum name, so reordering
  // the enum later cannot scramble existing rows.
  TextColumn get priority =>
      textEnum<Priority>().withDefault(Constant(Priority.normal.name))();
}

/// One row of the joined query: a task plus its project (if any).
typedef TaskWithProject = ({TaskRow task, ProjectRow? project});

@DriftAccessor(tables: [Projects, Tasks])
class TaskDao extends DatabaseAccessor<AppDatabase> with _$TaskDaoMixin {
  TaskDao(super.attachedDatabase);

  /// Emits a new list every time tasks or projects change.
  Stream<List<TaskWithProject>> watchTasks({bool hideDone = false}) {
    final query = select(tasks).join([
      leftOuterJoin(projects, projects.id.equalsExp(tasks.projectId)),
    ]);
    if (hideDone) query.where(tasks.done.equals(false));
    query.orderBy([
      OrderingTerm.asc(tasks.done),
      OrderingTerm.desc(tasks.updatedAt),
    ]);
    return query.watch().map((rows) => [
          for (final row in rows)
            (task: row.readTable(tasks), project: row.readTableOrNull(projects)),
        ]);
  }

  /// Number of open tasks, kept up to date.
  Stream<int> watchOpenCount() {
    final count = tasks.id.count();
    final query = selectOnly(tasks)
      ..addColumns([count])
      ..where(tasks.done.equals(false));
    return query.map((row) => row.read(count) ?? 0).watchSingle();
  }

  Future<int> addProject(String name) =>
      into(projects).insert(ProjectsCompanion.insert(name: name));

  Future<int> addTask(String title,
          {int? projectId, Priority priority = Priority.normal}) =>
      into(tasks).insert(TasksCompanion.insert(
        title: title,
        projectId: Value(projectId),
        priority: Value(priority),
      ));

  Future<void> toggleDone(TaskRow task) =>
      (update(tasks)..where((t) => t.id.equals(task.id))).write(TasksCompanion(
        done: Value(!task.done),
        updatedAt: Value(DateTime.now()),
      ));

  Future<int> deleteDone() =>
      (delete(tasks)..where((t) => t.done.equals(true))).go();

  /// Moves every task of [fromId] into [intoId], then deletes [fromId].
  /// Both steps succeed together or not at all.
  Future<void> mergeProject({required int fromId, required int intoId}) {
    return transaction(() async {
      await (update(tasks)..where((t) => t.projectId.equals(fromId)))
          .write(TasksCompanion(projectId: Value(intoId)));
      await (delete(projects)..where((p) => p.id.equals(fromId))).go();
    });
  }
}

@DriftDatabase(tables: [Projects, Tasks], daos: [TaskDao])
class AppDatabase extends _$AppDatabase {
  // Pass an executor in tests: AppDatabase(NativeDatabase.memory())
  AppDatabase([QueryExecutor? executor])
      : super(executor ?? driftDatabase(name: 'taskflow'));

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        onUpgrade: (m, from, to) async {
          if (from < 2) {
            await m.addColumn(tasks, tasks.priority);
          }
        },
        beforeOpen: (details) async {
          // SQLite ignores foreign keys unless you switch them on per connection.
          await customStatement('PRAGMA foreign_keys = ON');
          if (details.wasCreated) {
            await into(projects).insert(ProjectsCompanion.insert(name: 'Inbox'));
          }
        },
      );
}