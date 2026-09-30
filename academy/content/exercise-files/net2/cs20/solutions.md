# Solutions: practice set 3.3

**1.** y is another name for x. y += 2 makes x = 7. inc takes a reference and makes x = 8. inc2 takes a copy, so x stays 8; print 8. p = &y is the address of x, and *p *= 2 makes x = 16. Output: **8 16** (option 2).

**2.** Missing trailing arguments take their defaults: vol(4) = 4 × 2 × 3 = 24, vol(4, 5) = 4 × 5 × 3 = 60, vol(4, 5, 6) = 120. Defaults must be given from the right. Output: **24 60 120** (option 1).

**3.** The local x (3) hides the global one. ::x names the global x (1), and N::x the one in namespace N (2). Output: **3 1 2** (option 3).

**4.** k is a const object, so only const member functions can be called on it. get() is const but may change calls because calls is mutable. get() is called three times (calls = 3), and s = 7 + 7 = 14. Output: **14 3** (option 1).

**5.** Private inheritance makes the public and protected members of Base private in Derived. Inside Derived they are still usable: prot + pub + getSecret() = 2 + 3 + 1 = 6. secret itself is not accessible by name, which is why the public getter is used. In main, d.pub is private in Derived, so cout << d.pub; would not compile. Output: **6** (option 3).

**6.** Each call is dispatched on the dynamic type: 3 × 3 + 2 × 5 + 1 × 1 = 9 + 10 + 1 = 20. Deleting through Shape * is safe because the destructor is virtual. Output: **20** (option 2).

**7.** new X[3] constructs three objects (xxx); delete[] destroys all three (~~~). Using plain delete on an array would be undefined behaviour. X b[2] constructs two (xx), | is printed, and at the end of main the two are destroyed (~~). Output: **xxx~~~xx|~~** (option 1).

**8.** Each dep returns a reference to the same object, so the calls chain on a: 10 + 20 + 5 = 35. peek is a friend, so it may read the private bal. Output: **35** (option 3).

**9.** The stack holds 1 2 3 4 (4 on top) and the queue 10 20 30 40 (10 at the front). pop removes 4 from the stack and 10 from the queue. Top is 3, front is 20, and the sizes are 3 + 3 = 6. Output: **3 20 6** (option 2).

**10.** s becomes "exams" and then "NET exams" (length 9). substr(4, 4) starts at index 4, which is e: "exam". find('x') gives the index of the first x, which is 5. Output: **NET exams 9 exam 5** (option 1).

**11.** After the ascending sort v = {1, 2, 3, 4, 5}: v[0] = 1 and v[4] = 5 print as 15. greater<int>() sorts in descending order: 54321. Output: **15 54321** (option 3).

**12.** Without virtual inheritance a D holds two A subobjects, one inside B and one inside C, so A’s constructor runs twice: A B A C D. A member of A used without a qualifier would be ambiguous and would not compile; write B::name or C::name, or make A a virtual base. Output: **A B A C D** (option 2).

**13.** X b = a creates b, so the copy constructor runs (A-II). b = a changes an existing object: copy assignment (B-III). delete p runs the destructor (C-I). new X runs the default constructor (D-IV). Answer: option 1, **A-II, B-III, C-I, D-IV**.

**14.** Both are true, and R is the reason for A: there is only one A subobject, so a name from A refers to a single member and is no longer ambiguous. Answer: option 1.

**15.** A is true (static polymorphism). B is false: the return type alone cannot distinguish overloads. C is true. D is false: without virtual the derived function only hides the base one; a call through a base pointer still reaches the base version. E is false: a friend is not a member and is called like an ordinary function, f(obj). Answer: option 1, **A and C only**.
