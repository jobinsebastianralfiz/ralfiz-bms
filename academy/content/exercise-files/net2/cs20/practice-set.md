# Practice set 3.3: Object-oriented programming and C++

15 exam-level problems. Pace: about 90 seconds for each problem. Predict every output on paper before you check it.

Every program compiles cleanly with g++ -std=c++17 -Wall -Wextra and has no undefined behaviour.

---

**1.** What is the output?

    #include <iostream>
    using namespace std;
    void inc(int &r) { r++; }
    void inc2(int v) { v++; }
    int main() {
        int x = 5;
        int &y = x;
        y += 2;
        inc(x);
        inc2(x);
        cout << x << " ";
        int *p = &y;
        *p *= 2;
        cout << x;
        return 0;
    }

(1) 7 14 (2) 8 16 (3) 9 18 (4) 5 10

**2.** What is the output?

    #include <iostream>
    using namespace std;
    int vol(int l, int w = 2, int h = 3) { return l * w * h; }
    int main() {
        cout << vol(4) << " " << vol(4, 5) << " " << vol(4, 5, 6);
        return 0;
    }

(1) 24 60 120 (2) 24 20 120 (3) 4 20 120 (4) Compilation error

**3.** What is the output?

    #include <iostream>
    using namespace std;
    int x = 1;
    namespace N { int x = 2; }
    int main() {
        int x = 3;
        cout << x << " " << ::x << " " << N::x;
        return 0;
    }

(1) 3 3 3 (2) 1 1 2 (3) 3 1 2 (4) Compilation error

**4.** What is the output?

    #include <iostream>
    using namespace std;
    class K {
        mutable int calls = 0;
        int v;
    public:
        K(int x) : v(x) {}
        int get() const { calls++; return v; }
        int n() const { return calls; }
    };
    int main() {
        const K k(7);
        k.get();
        int s = k.get() + k.get();
        cout << s << " " << k.n();
        return 0;
    }

(1) 14 3 (2) 14 2 (3) Compilation error, because get() changes a member inside a const function (4) 21 3

**5.** What is the output? Would the statement cout << d.pub; compile if it were added to main?

    #include <iostream>
    using namespace std;
    class Base {
        int secret = 1;
    protected:
        int prot = 2;
    public:
        int pub = 3;
        int getSecret() const { return secret; }
    };
    class Derived : private Base {
    public:
        int sum() const { return prot + pub + getSecret(); }
    };
    int main() {
        Derived d;
        cout << d.sum();
        return 0;
    }

(1) 6, and yes (2) 5, and no (3) 6, and no (4) Compilation error in sum()

**6.** What is the output?

    #include <iostream>
    using namespace std;
    struct Shape {
        virtual int area() const = 0;
        virtual ~Shape() {}
    };
    struct Sq : Shape {
        int s;
        Sq(int x) : s(x) {}
        int area() const override { return s * s; }
    };
    struct Rect : Shape {
        int w, h;
        Rect(int a, int b) : w(a), h(b) {}
        int area() const override { return w * h; }
    };
    int main() {
        Shape *sh[3] = {new Sq(3), new Rect(2, 5), new Sq(1)};
        int t = 0;
        for (Shape *p : sh) {
            t += p->area();
            delete p;
        }
        cout << t;
        return 0;
    }

(1) 16 (2) 20 (3) 11 (4) Compilation error, because Shape is abstract

**7.** What is the output?

    #include <iostream>
    using namespace std;
    struct X {
        X() { cout << "x"; }
        ~X() { cout << "~"; }
    };
    int main() {
        X *a = new X[3];
        delete[] a;
        X b[2];
        cout << "|";
        return 0;
    }

(1) xxx~~~xx|~~ (2) xxx~xx|~~ (3) xxx~~~xx~~| (4) xxx~~~|

**8.** What is the output?

    #include <iostream>
    using namespace std;
    class Acc {
        int bal = 0;
    public:
        Acc &dep(int x) { bal += x; return *this; }
        friend int peek(const Acc &a);
    };
    int peek(const Acc &a) { return a.bal; }
    int main() {
        Acc a;
        a.dep(10).dep(20).dep(5);
        cout << peek(a);
        return 0;
    }

(1) 10 (2) 30 (3) 35 (4) Compilation error, because peek is not a member

**9.** What is the output?

    #include <iostream>
    #include <stack>
    #include <queue>
    using namespace std;
    int main() {
        stack<int> st;
        queue<int> q;
        for (int i = 1; i <= 4; i++) {
            st.push(i);
            q.push(i * 10);
        }
        st.pop();
        q.pop();
        cout << st.top() << " " << q.front() << " " << st.size() + q.size();
        return 0;
    }

(1) 4 10 6 (2) 3 20 6 (3) 3 10 8 (4) 1 40 6

**10.** What is the output?

    #include <iostream>
    #include <string>
    using namespace std;
    int main() {
        string s = "exam";
        s += "s";
        s.insert(0, "NET ");
        cout << s << " " << s.length() << " " << s.substr(4, 4) << " " << s.find('x');
        return 0;
    }

(1) NET exams 9 exam 5 (2) NET exams 8 exam 5 (3) NET exams 9 exam 1 (4) NETexams 8 Texa 4

**11.** What is the output?

    #include <iostream>
    #include <vector>
    #include <algorithm>
    #include <functional>
    using namespace std;
    int main() {
        vector<int> v = {4, 1, 3, 5, 2};
        sort(v.begin(), v.end());
        cout << v[0] << v[4] << " ";
        sort(v.begin(), v.end(), greater<int>());
        for (int x : v) cout << x;
        return 0;
    }

(1) 15 12345 (2) 41 54321 (3) 15 54321 (4) 51 54321

**12.** What is the output? What would happen if D’s constructor tried to print a member declared in A without a qualifier?

    #include <iostream>
    using namespace std;
    struct A { A() { cout << "A "; } };
    struct B : A { B() { cout << "B "; } };
    struct C : A { C() { cout << "C "; } };
    struct D : B, C { D() { cout << "D "; } };
    int main() {
        D d;
        return 0;
    }

(1) A B C D (2) A B A C D (3) B C D (4) A A B C D

**13.** Match List I with List II.

| List I (Situation) | List II (Function called) |
|---|---|
| A. X b = a; | I. Destructor |
| B. b = a; (b already exists) | II. Copy constructor |
| C. A pointer p = new X; is followed by delete p; | III. Copy assignment operator |
| D. X *p = new X; | IV. Default constructor |

(1) A-II, B-III, C-I, D-IV (2) A-III, B-II, C-I, D-IV (3) A-II, B-III, C-IV, D-I (4) A-II, B-I, C-III, D-IV

**14.** Assertion (A): In a diamond hierarchy (B and C derive from A, D derives from B and C), declaring B and C with virtual public A removes the ambiguity when a D object uses a member of A.
Reason (R): With virtual inheritance, a D object contains only one shared subobject of A.

(1) Both (A) and (R) are true and (R) is the correct explanation of (A) (2) Both (A) and (R) are true but (R) is NOT the correct explanation of (A) (3) (A) is true but (R) is false (4) (A) is false but (R) is true

**15.** Which of the following statements are correct?

- A. Function overloading is resolved at compile time.
- B. Two overloaded functions may differ only in their return type.
- C. A pure virtual function makes its class abstract.
- D. A derived class function with the same name as a non-virtual base function overrides it for calls through a base pointer.
- E. A friend function is called with the object’s dot operator, like a member.

(1) A and C only (2) A, C and D only (3) B and C only (4) A, B, C and E only
