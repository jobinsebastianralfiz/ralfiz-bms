// js10 lab: fix the Booking Desk. Run with: node index.js

// Runs fn and prints the result, or a BUG line instead of crashing.
function safely(label, fn) {
  try {
    const result = fn();
    if (result !== undefined) console.log(label + ':', result);
  } catch (err) {
    console.log(`BUG in ${label}: ${err.message}`);
  }
}

class BookingDesk {
  constructor(venue) {
    this.venue = venue;
    this.bookings = [];
  }

  add(name, seats) {
    this.bookings.push({ name, seats });
    return this.bookings.length;
  }

  seatsTaken() {
    return this.bookings.reduce((sum, b) => sum + b.seats, 0);
  }

  describeOne(booking) {
    return `${booking.name} x${booking.seats} at ${this.venue}`;
  }

  // An arrow has no own this, so it uses describeAll's this (the desk).
  describeAll() {
    return this.bookings.map((b) => `${b.name} x${b.seats} at ${this.venue}`);
  }

  remind() {
    console.log(`Reminder: ${this.bookings.length} bookings at ${this.venue}`);
  }
}

function printTicket(label, booking) {
  return `${label} ticket for ${booking.name} (${booking.seats} seats) at ${this.venue}`;
}

const desk = new BookingDesk('Ralfiz Hall A');
desk.add('Asha', 2);
desk.add('Ravi', 4);
desk.add('Meera', 1);

safely('describe', () => desk.describeAll());

// bind returns a new function whose this is always desk
const report = desk.seatsTaken.bind(desk);
safely('seats taken', report);

// The arrow keeps the dot, so remind is called as desk.remind()
setTimeout(() => safely('reminder', () => desk.remind()), 10);

// call runs describeOne now, with this set to the Hall B object
const hallB = { venue: 'Ralfiz Hall B' };
safely('borrowed', () => desk.describeOne.call(hallB, { name: 'Guest', seats: 3 }));

// bind fixes this AND the first argument (partial application)
const printVip = printTicket.bind(desk, 'VIP');
safely('vip', () => printVip(desk.bookings[0]));