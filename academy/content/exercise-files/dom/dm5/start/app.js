// Lab 2.1 - Events and listeners
// Work through the TODOs in order. Open the console (F12) to see your logs.

const LIMIT = 200;

// TODO(1): select the elements you need with document.querySelector:
//   #like, #like-count, #post-text, #big-heart, #composer, #comment,
//   #counter, #post, #comments, #tip, #tip-ok, #close

// TODO(2): create one AbortController and take its signal.
//   Pass { signal } to every addEventListener call below (except the tip).

// TODO(3): like toggle
//   - keep let liked = false and let count = 41
//   - write setLiked(next): update liked, count, aria-pressed, the count text
//     and add the 'pop' class
//   - click on the like button: log event.target.localName and
//     event.currentTarget.localName, then call setLiked(!liked)
//   - on 'animationend' of the like button, remove the 'pop' class

// TODO(4): double-click on the post text calls setLiked(true) and adds the
//   'show' class to the big heart; remove 'show' on its 'animationend'

// TODO(5): character counter on 'input'
//   - count with Intl.Segmenter (granularity: 'grapheme') so an emoji is 1
//   - show "N left" or "N over", add class 'warn' at 20 left, 'over' past 200
//   - disable the Post button when the box is empty or over the limit

// TODO(6): posting
//   - 'submit' on the form: preventDefault, create an <li> with textContent,
//     append it to #comments, reset the form and update the counter
//   - 'keydown' on the textarea: Ctrl+Enter or Cmd+Enter calls
//     preventDefault() and form.requestSubmit()

// TODO(7): tip and close
//   - Got it: hide #tip with a { once: true } listener
//   - Close discussion: controller.abort(), set form.inert = true,
//     disable the close button and change its text to 'Discussion closed'

console.log('Lab 2.1 loaded. Start with TODO(1).');
