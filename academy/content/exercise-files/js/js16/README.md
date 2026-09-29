# Lab 4.1 - Products by hand, then with class

Build the same product hierarchy twice (prototypes by hand, then class)
and write two helpers that reveal how lookups work.

## Run it

    cd javascript/js16/start
    node index.js

Node.js 22 or newer.

## Tasks (TODO markers in start/index.js)

1. TODO(1): move label() out of the Product constructor onto Product.prototype.
2. TODO(2): make DigitalProduct call Product for title and price.
3. TODO(3): link DigitalProduct.prototype to Product.prototype with
   Object.create, and restore constructor.
4. TODO(4): override label() on DigitalProduct.prototype, reusing the parent's
   label() and adding the size, e.g. "JS course - Rs 999 (850 MB)".
5. TODO(5): write chainOf(obj) and whereIs(obj, key).
6. TODO(6): write ClassProduct and ClassDigital with class/extends/super and
   compare the chains.

## Acceptance criteria

- pen.label() prints Gel pen - Rs 20; course.label() prints JS course - Rs 999 (850 MB).
- Shared label: true (both products use one function from the prototype).
- chainOf(course) prints DigitalProduct > Product > Object.
- whereIs prints title: own, label: inherited, discount: missing.
- chainOf(classCourse) prints ClassDigital > ClassProduct > Object,
  and classCourse instanceof ClassProduct is true.

## Think about it

- Why does adding a method to Product.prototype after creating pen still
  make it available on pen?
- What would break if you wrote DigitalProduct.prototype = Product.prototype?
