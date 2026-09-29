// Lab 0.1 - Profile card (solution)
const profile = {
  name: 'Anjali Menon',
  role: 'Front-end mentor · Ralfiz Academy',
  initials: 'AM',
  stats: { courses: 12, followers: 4800, rating: 4.9 },
  skills: ['JavaScript', 'DOM', 'Accessibility', 'CSS'],
};

// With defer, parsing has finished, so this says 'interactive'.
console.log('top of app.js, readyState =', document.readyState);
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOMContentLoaded, readyState =', document.readyState);
});
window.addEventListener('load', () => {
  console.log('load, readyState =', document.readyState);
});

const card = document.querySelector('#profile');
console.log('card found?', card !== null);

function compact(n) {
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
}

function setText(selector, value) {
  card.querySelector(selector).textContent = value;
}

// Fill the card from data. textContent is safe for any string.
setText('#name', profile.name);
setText('#role', profile.role);
setText('#initials', profile.initials);
setText('#courses', profile.stats.courses);
setText('#followers', compact(profile.stats.followers));
setText('#rating', profile.stats.rating);

const tags = card.querySelector('.tags');
for (const skill of profile.skills) {
  const span = document.createElement('span');
  span.textContent = skill;
  tags.append(span);
}

const followBtn = card.querySelector('#follow');
followBtn.addEventListener('click', () => {
  const isFollowing = followBtn.getAttribute('aria-pressed') === 'true';
  followBtn.setAttribute('aria-pressed', String(!isFollowing));
  followBtn.textContent = isFollowing ? 'Follow' : 'Following';
  profile.stats.followers += isFollowing ? -1 : 1;
  setText('#followers', compact(profile.stats.followers));
  console.log(isFollowing ? 'Unfollowed' : 'Followed', '-> followers:', profile.stats.followers);
});

document.title = `${profile.name} · Ralfiz Academy`;
