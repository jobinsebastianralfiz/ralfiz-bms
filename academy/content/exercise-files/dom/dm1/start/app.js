// Lab 0.1 - Profile card (starter)
const profile = {
  name: 'Anjali Menon',
  role: 'Front-end mentor · Ralfiz Academy',
  initials: 'AM',
  stats: { courses: 12, followers: 4800, rating: 4.9 },
  skills: ['JavaScript', 'DOM', 'Accessibility', 'CSS'],
};

// TODO(2): log document.readyState here, then add a DOMContentLoaded listener
// on document and a load listener on window that log it again.

// TODO(1): this logs false until you add defer to the script tag. Why?
const card = document.querySelector('#profile');
console.log('card found?', card !== null);

// Formats 4800 as '4.8k'. Use it for the followers stat.
function compact(n) {
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
}

if (card) {
  // TODO(3): fill #name, #role, #initials, #courses, #followers and #rating
  // from the profile object using textContent.

  // TODO(4): for each skill in profile.skills, create a <span>,
  // set its textContent and append it to the .tags element.

  // TODO(5): make #follow a toggle. On click: flip aria-pressed,
  // switch the text between Follow and Following, change
  // profile.stats.followers by +1 or -1 and update #followers.
  console.log('Ready to build the card. Formatted followers:', compact(profile.stats.followers));
}
