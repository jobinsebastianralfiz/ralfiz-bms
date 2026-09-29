// Lab 4.1 - Products by hand, then with class (solution)
// Run: node index.js

// Part 1: constructor functions and prototypes
function Product(title, price) {
  this.title = title;
  this.price = price;
}
Product.prototype.label = function () {
  return `${this.title} - Rs ${this.price}`;
};

function DigitalProduct(title, price, sizeMb) {
  Product.call(this, title, price);
  this.sizeMb = sizeMb;
}
DigitalProduct.prototype = Object.create(Product.prototype);
DigitalProduct.prototype.constructor = DigitalProduct;
DigitalProduct.prototype.label = function () {
  const base = Product.prototype.label.call(this);
  return `${base} (${this.sizeMb} MB)`;
};

// Part 2: helpers that reveal the chain
function chainOf(obj) {
  const names = [];
  for (let p = Object.getPrototypeOf(obj); p; p = Object.getPrototypeOf(p)) {
    names.push(Object.hasOwn(p, 'constructor') ? p.constructor.name : '?');
  }
  return names;
}

function whereIs(obj, key) {
  if (Object.hasOwn(obj, key)) return 'own';
  return key in obj ? 'inherited' : 'missing';
}

const pen = new Product('Gel pen', 20);
const bag = new Product('Laptop bag', 899);
const course = new DigitalProduct('JS course', 999, 850);

console.log(pen.label());
console.log(course.label());
console.log('Shared label:', pen.label === bag.label);
console.log('Chain:', chainOf(course).join(' > '));
for (const key of ['title', 'label', 'discount']) {
  console.log(`${key}: ${whereIs(course, key)}`);
}

// Methods added later are found at call time
Product.prototype.isFree = function () {
  return this.price === 0;
};
console.log('pen.isFree() was added later and still works:', pen.isFree());

// Part 3: the same thing with class
class ClassProduct {
  constructor(title, price) {
    this.title = title;
    this.price = price;
  }
  label() {
    return `${this.title} - Rs ${this.price}`;
  }
}

class ClassDigital extends ClassProduct {
  constructor(title, price, sizeMb) {
    super(title, price);
    this.sizeMb = sizeMb;
  }
  label() {
    return `${super.label()} (${this.sizeMb} MB)`;
  }
}

const classCourse = new ClassDigital('JS course', 999, 850);
console.log('\nClass version:', classCourse.label());
console.log('Chain:', chainOf(classCourse).join(' > '));
console.log('instanceof ClassProduct:', classCourse instanceof ClassProduct);
console.log('Same own keys:',
  Object.keys(course).join(',') === Object.keys(classCourse).join(','));
console.log('typeof ClassDigital:', typeof ClassDigital);
