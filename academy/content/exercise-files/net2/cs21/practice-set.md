# Practice set: Web programming (UGC NET Paper 2, Unit 3)

Time: 22 minutes for all 15 problems. Every JavaScript and Java output here was produced by running the code.

**1.** Match List I with List II.

| List I (JSP element) | List II (Where its code ends up) |
|---|---|
| A. <%! int n = 0; %> | I. Removed completely, never sent to the client |
| B. <% n++; %> | II. A field of the generated servlet class |
| C. <%= n %> | III. out.print(n) inside _jspService() |
| D. <%-- note --%> | IV. A statement inside _jspService() |

(1) A-II, B-IV, C-III, D-I  (2) A-IV, B-II, C-III, D-I  (3) A-II, B-III, C-IV, D-I  (4) A-II, B-IV, C-I, D-III

**2.** A div has width: 180px; padding: 8px; border: 2px solid; margin: 10px (default box-sizing). Give (a) the width of its border box and (b) the horizontal space it takes including margins.

**3.** What does this JavaScript print?

    console.log("7" + 1, "7" - 1, "7" * 2, "a" * 2);

(1) 71 6 14 NaN  (2) 8 6 14 NaN  (3) 71 71 72 a2  (4) 71 6 72 NaN

**4.** What does this JavaScript print?

    console.log(typeof null, typeof [], typeof NaN, typeof undefined);

**5.** Give the specificity (inline, IDs, classes, elements) of each selector and say which wins for the same element: (i) ul#list li.active  (ii) .menu .item a:hover  (iii) body div ul li a

**6.** A servlet with load-on-startup is deployed. The server starts, receives 12 requests from 5 users, and is shut down. How many times are init(), service() and destroy() called?

**7.** Assertion (A): A JSP page is slower on its very first request than on later requests. Reason (R): On the first request the container translates the JSP into a servlet and compiles it.

**8.** Which of the following are true? A. HTTP/1.1 uses persistent connections by default. B. The URL fragment (after #) is sent to the server. C. 404 means Not Found. D. HTTPS uses port 443 by default. E. PUT is not idempotent.

**9.** Is the following XML well-formed? Is it valid against its DTD? Give every reason.

    <?xml version="1.0"?>
    <!DOCTYPE team [
      <!ELEMENT team (member+)>
      <!ELEMENT member (#PCDATA)>
      <!ATTLIST member role (lead | dev) #REQUIRED>
    ]>
    <team>
      <member role="lead">Asha</member>
      <member role="tester">Ravi</member>
    </team>

**10.** Which of these break XML well-formedness? A. <Price>10</price>  B. <a><b></a></b>  C. <item id=5/>  D. <x>3 &lt; 4</x>  E. Two root elements

**11.** What does this JavaScript print?

    var s = 0;
    for (var i = 1; i <= 4; i++) { if (i == "3") continue; s += i; }
    console.log(s, i);

**12.** Arrange in order the calls made to an applet when a user opens its page, leaves it, returns, and then closes the browser: A. stop()  B. init()  C. start() (second time)  D. destroy()  E. start() (first time)  F. stop() (second time)

**13.** Statement I: A DTD can declare an attribute of type ID whose values must be unique in the document. Statement II: The include directive in JSP includes the output of the other page at request time.

**14.** Two stacked paragraphs have margin-bottom 24px and margin-top 16px. What is the gap? What would it be if they were placed side by side as inline-block elements with margin-right 24px and margin-left 16px?

**15.** Which method or object would you use for each task? (a) Keep a logged-in user's cart across requests. (b) Pass the same request to another servlet without the browser knowing. (c) Make the browser load a different URL. (d) Read a form field named roll.
