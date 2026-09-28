import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'app_database.g.dart';

// STARTER - lesson 10.1: the TaskFlow local database with Drift.
// Run dart run build_runner build -d once before the first run, and again
// after every change to the tables or annotations in this file.
// The app runs as it is, but the list stays empty until you finish the TODOs.

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

  // TODO(7): schema version 2. AFTER you have added a few tasks with version 1:
  // add enum Priority { low, normal, high } above the tables and a column
  //   TextColumn get priority =>
  //       textEnum<Priority>().withDefault(Constant(Priority.normal.name))();
  // then bump schemaVersion, write onUpgrade and run build_runner again.
}

/// One row of the joined query: a task plus its project (if any).
typedef TaskWithProject = ({TaskRow task, ProjectRow? project});

@DriftAccessor(tables: [Projects, Tasks])
class TaskDao extends DatabaseAccessor<AppDatabase> with _$TaskDaoMixin {
  TaskDao(super.attachedDatabase);

  /// Emits a new list every time tasks or projects change.
  Stream<List<TaskWithProject>> watchTasks({bool hideDone = false}) {
    // TODO(1): select(tasks).join([...]) with a leftOuterJoin on projects,
    // where done is false when hideDone is true, order by done ascending then
    // updatedAt descending, then .watch() and map each row to a record
    // (task: row.readTable(tasks), project: row.readTableOrNull(projects)).
    return Stream.value(const <TaskWithProject>[]);
  }

  /// Number of open tasks, kept up to date.
  Stream<int> watchOpenCount() {
    // TODO(2): selectOnly(tasks) with addColumns([tasks.id.count()]) and a
    // where on done, then map to row.read(count) ?? 0 and watchSingle().
    return Stream.value(0);
  }

  Future<int> addProject(String name) =>
      into(projects).insert(ProjectsCompanion.insert(name: name));

  Future<int> addTask(String title, {int? projectId}) async {
    // TODO(3): insert TasksCompanion.insert(title: ..., projectId: Value(...)).
    return 0;
  }

  Future<void> toggleDone(TaskRow task) async {
    // TODO(4): update(tasks) where id equals task.id, write done: !task.done
    // and updatedAt: DateTime.now() (wrap each in Value).
  }

  Future<int> deleteDone() async {
    // TODO(5): delete(tasks) where done is true, then .go().
    return 0;
  }

  /// Moves every task of [fromId] into [intoId], then deletes [fromId].
  Future<void> mergeProject({required int fromId, required int intoId}) async {
    // TODO(6): inside transaction(() async { ... }): update the tasks'
    // projectId, then delete the old project.
  }
}

@DriftDatabase(tables: [Projects, Tasks], daos: [TaskDao])
class AppDatabase extends _$AppDatabase {
  // Pass an executor in tests: AppDatabase(NativeDatabase.memory())
  AppDatabase([QueryExecutor? executor])
      : super(executor ?? driftDatabase(name: 'taskflow'));

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) => m.createAll(),
        // TODO(7): onUpgrade: if (from < 2) add the priority column.
        beforeOpen: (details) async {
          await customStatement('PRAGMA foreign_keys = ON');
          if (details.wasCreated) {
            await into(projects).insert(ProjectsCompanion.insert(name: 'Inbox'));
          }
        },
      );
}