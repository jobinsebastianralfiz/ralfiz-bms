# Solutions: Web programming practice set

**1. Option (1): A-II, B-IV, C-III, D-I.** A declaration becomes a class member (field). A scriptlet becomes a statement in _jspService(). An expression becomes out.print(...). A JSP comment is dropped at translation. Option (3) swaps B and C.

**2.** (a) Border box = 180 + 2 × 8 + 2 × 2 = **200 px**. (b) Space = 200 + 2 × 10 = **220 px**. Trap: giving 180 (the content width only).

**3. Option (1): 71 6 14 NaN.** + with a string concatenates: "71". − and * convert to numbers: 6 and 14. "a" cannot become a number, so "a" * 2 is NaN.

**4.** object object number undefined. typeof null is "object" (a historic bug), an array is an object, NaN is of type number.

**5.** (i) ul#list li.active: IDs 1, classes 1, elements 2 → (0,1,1,2). (ii) .menu .item a:hover: classes/pseudo-classes 3, elements 1 → (0,0,3,1). (iii) body div ul li a → (0,0,0,5). The ID column decides first, so **(i) wins**.

**6.** load-on-startup creates the instance at start-up, but init() is still called **once**. service() runs **12** times (once per request, whatever the number of users). destroy() runs **once**.

**7. Both true, and R explains A (option 1).** The translation and compilation happen only when the page is first requested or changed, so later requests go directly to the compiled servlet's _jspService().

**8. A, C and D.** B is false: the fragment is used only by the browser. E is false: PUT is idempotent (putting the same representation twice gives the same state).

**9.** **Well-formed:** yes (one root, closed and nested tags, quoted attributes). **Valid:** no. The attribute role is an enumeration (lead | dev), and "tester" is not in the list. Changing it to dev, or adding tester to the enumeration, makes it valid. (Checked with lxml using the DTD.)

**10. A, B, C and E break it.** A: case mismatch between Price and price. B: improper nesting. C: unquoted attribute value. E: more than one root. D is fine: &lt; is the predefined entity for <.

**11. Output: 7 5.** i == "3" converts "3" to 3, so the value 3 is skipped: s = 1 + 2 + 4 = 7. The loop ends when i becomes 5, and var i is still visible after the loop. (Run with node.)

**12. B, E, A, C, F, D.** init() once, start(), stop() when leaving, start() again on return, stop() when closing, destroy() last. stop() is always called before destroy().

**13. Statement I true, Statement II false.** ID attributes must have unique values. The include directive copies the source at translation time; the jsp:include action includes the output at request time.

**14.** Vertical margins of blocks collapse: gap = max(24, 16) = **24 px**. Horizontal margins never collapse: side by side the gap is 24 + 16 = **40 px**.

**15.** (a) HttpSession (session.setAttribute), backed by a cookie or URL rewriting. (b) RequestDispatcher.forward(). (c) response.sendRedirect(url). (d) request.getParameter("roll").
