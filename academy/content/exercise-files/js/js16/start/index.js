// Lab 4.1 - Products by hand, then with class (starter)
// Run: node index.js

function Product(title, price) {
  this.title = title;
  this.price = price;
  // TODO(1): move this method to Product.prototype
  this.label = function () {
    return `${this.title} - Rs ${this.price}`;
  };
}

function DigitalProduct(title, price, sizeMb) {
  // TODO(2): call Product with this, title and price
  this.sizeMb = sizeMb;
}

// TODO(3): DigitalProduct.prototype = Object.create(...); fix constructor

// TODO(4): DigitalProduct.prototype.label = function () { ... }

// TODO(5): walk Object.getPrototypeOf until null, collecting constructor names
function chainOf(obj) {
  return [];
}

// TODO(5): return 'own', 'inherited' or 'missing'
function whereIs(obj, key) {
  return 'TODO';
}

const pen = new Product('Gel pen', 20);
const bag = new Product('Laptop bag', 899);
const course = new DigitalProduct('JS course', 999, 850);

console.log(pen.label());
console.log(course.label?.() ?? 'course.label is missing');
console.log('Shared label:', pen.label === bag.label);
console.log('Chain:', chainOf(course).join(' > '));
for (const key of ['title', 'label', 'discount']) {
  console.log(`${key}: ${whereIs(course, key)}`);
}

// TODO(6): class ClassProduct { ... }  class ClassDigital extends ClassProduct { ... }
// then log chainOf(new ClassDigital(...)) and an instanceof check
