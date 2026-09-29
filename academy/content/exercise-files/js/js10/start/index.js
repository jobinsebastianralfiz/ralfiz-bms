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

  // TODO(1): the regular function below has its own this. Use an arrow.
  describeAll() {
    return this.bookings.map(function (b) {
      return `${b.name} x${b.seats} at ${this.venue}`;
    });
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

// TODO(2): seatsTaken is passed without its object. Fix it with bind.
const report = desk.seatsTaken;
safely('seats taken', report);

// TODO(3): setTimeout calls remind without desk. Wrap it or bind it.
setTimeout(() => safely('reminder', desk.remind), 10);

// TODO(4): borrow describeOne for Hall B using call:
// describeOne.call({ venue: 'Ralfiz Hall B' }, { name: 'Guest', seats: 3 })
safely('borrowed', () => 'not done yet');

// TODO(5): make printVip = printTicket.bind(desk, 'VIP') and print Asha's ticket.
safely('vip', () => 'not done yet');