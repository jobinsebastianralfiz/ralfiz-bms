# Lab 1.5 - Grade Book

Build a console grade book for a Ralfiz Academy batch using only branches and
loops (no map, filter, reduce or sort yet: that is lesson 3.1).

## Run it

    cd javascript/js7/start
    node index.js

students.json holds each student's marks for maths, science and english.
null means the student was absent for that subject.

## Tasks

1. TODO(1) gradeFor(score): guard clauses, then A+ 90+, A 80+, B 70+,
   C 60+, D 50+, otherwise F. Invalid input returns 'Invalid'.
2. TODO(2) average(marks): for...of over Object.values, skip null with
   continue, return null when there are no marks.
3. TODO(3) remarkFor(grade): a switch with grouped cases.
4. TODO(4) the report table: one aligned line per student.
5. TODO(5) topper (no sort) and a counts object per grade.
6. TODO(6) the grade chart with for...in and '#'.repeat().
7. TODO(7) the first student with a subject below 40, using break.

## Acceptance criteria

- The table shows Anu 91.7 A+ Excellent and Esha 43.3 F Needs support
- Gita is shown as Absent and is not counted in the chart or the class average
- Topper: Hari (94.3)
- Class average: 73.3 over 7 graded students
- The chart has one line per grade, for example A+ ## 2
- First student who needs support: Esha (english: 38)
