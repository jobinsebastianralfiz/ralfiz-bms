# Ralfiz Social: connecting Facebook, Instagram, Google, YouTube and LinkedIn

A plain-language guide. It covers what each platform wants from us, why, and exactly where to click.

Contents
1. [The big picture: why platforms "review" our app](#1-the-big-picture)
2. [Meta (Facebook + Instagram), step by step](#2-meta-facebook--instagram)
2b. [WhatsApp (keep the phone app + use the hub)](#2b-whatsapp)
3. [Google Business Profile + YouTube](#3-google-business-profile--youtube)
4. [LinkedIn](#4-linkedin)
5. [SEO for ralfiz.com](#5-seo-for-ralfizcom)
6. [Railway variables, all in one place](#6-railway-variables)
7. [Glossary](#7-glossary)

---

## 1. The big picture

**Ralfiz Social is an "app" in the eyes of Facebook, Google and LinkedIn.** When it posts to a Page or reads comments, it is the app doing it, using a permission the Page owner gave it.

Every platform works the same way:

| Stage | What it means for us |
| --- | --- |
| **Development / testing** | The app only works for **our own** accounts: people who are admins of the app. This is why Ralfiz's own Facebook and Instagram already work in the hub. |
| **Review / verification** | We prove to the platform that we are a real business, explain why we need each permission, and show a screen recording of the hub using it. |
| **Live / approved** | **Any** business (our clients) can connect its Page, channel or profile. |

So **nothing is broken today**. Reviews are only needed so that **clients'** accounts can be connected, not just ours.

Every platform also asks for three public pages. They are live now:
- Privacy Policy: https://ralfizdigital.in/privacy/
- Terms of Service: https://ralfizdigital.in/terms/
- Data Deletion: https://ralfizdigital.in/data-deletion/

---

## 2. Meta (Facebook + Instagram)

Our Meta app: **Ralfiz Social Dashboard**, App ID `2618682961963846`.
Open it at https://developers.facebook.com/apps → click the app.

### 2.1 Where we are now

| Step | Status |
| --- | --- |
| A. Business verification ("is Ralfiz Technologies a real company?") | ✅ **Done**, verified 12 Oct 2026 |
| B. Basic app settings (icon, policy links) | ⬜ To do, 10 minutes |
| C. Access verification ("do you manage accounts for other businesses?") | ⬜ To do, a short form |
| D. App Review (ask for "advanced access" to 13 permissions) | ⬜ After C is approved |
| E. Switch the app to **Live** | ⬜ After D is approved |

### 2.2 What is that long "Permissions and Features" page?

That's the page in your screenshot (App Review → Permissions and Features). Each row is **one thing the app is allowed to do**, for example "publish posts to a Page".

Each row has an **Access level**:

- **Standard access** (what everything shows now): the permission works, but **only on accounts of people who have a role on our app**, i.e. you. That's why posting to Ralfiz's own Page works.
- **Advanced access**: the permission works on **anyone's** account who connects and agrees. Our clients need this.

The **Status** column says "No App Review requested", meaning we haven't asked yet. The **"Request advanced access"** button is how we ask.

**The page lists about 60 permissions, but we need only 13.** Meta shows every permission that exists. Ignore the rest: don't request them, and don't delete them either. Asking for permissions we don't use is the most common reason Meta rejects an app.

The **second list** on that page has a grey banner at the top: *"Your app only needs advanced access to the following... if your business provides services of a Tech Provider."* A **Tech Provider** is Meta's name for a company that manages accounts for other businesses, which is exactly what an agency is. That's why those buttons have a shield icon and say business verification **and access verification** are required. We have the first; step C gets the second.

### 2.3 The 13 permissions we need, in plain words

Hub feature names are in **bold**.

| Permission (as Meta names it) | What it lets the hub do | Used by |
| --- | --- | --- |
| `pages_show_list` | See the list of Facebook Pages a person manages, so they can pick one to connect | **Accounts → Connect** |
| `business_management` | See Pages owned by a Business portfolio (most business Pages are) | **Accounts → Connect** |
| `pages_manage_posts` | Publish posts (text, photo, video, link) to the Page | **Create post / Calendar** |
| `pages_read_engagement` | Read the Page's posts, followers, likes and shares | **Posts, Calendar, Analytics** |
| `pages_read_user_content` | Read comments and posts other people leave on the Page | **Inbox** |
| `pages_manage_engagement` | Reply to comments on the Page | **Inbox → Reply** |
| `pages_messaging` | Read and answer Messenger messages sent to the Page | **Inbox** |
| `read_insights` | Read the Page's reach and impressions | **Analytics, monthly PDF report** |
| `instagram_basic` | See the Instagram account linked to the Page: name, picture, followers, posts | **Accounts, Posts** |
| `instagram_content_publish` | Publish photos, videos, Reels and carousels to Instagram | **Create post** |
| `instagram_manage_comments` | Read and reply to comments on Instagram posts | **Inbox** |
| `instagram_manage_insights` | Read Instagram reach, impressions and follower numbers | **Analytics, reports** |
| `instagram_manage_messages` | Read and answer Instagram direct messages | **Inbox** |

**Rows to leave alone:**
- anything starting with `ads_`
- `user_birthday`, `user_hometown`, `user_gender`, `user_age_range`, `user_posts` and the other `user_` rows
- `email`, `public_profile`
- `instagram_business_*`, `instagram_manage_events`, `instagram_manage_upcoming_events`, `instagram_creator_marketplace_messaging`, `instagram_manage_engagement`
- `live_shopping_manage_video`, `facebook_branded_content_ads_brand`, `pages_manage_metadata`, `pages_user_gender`
- Page Public Metadata Access, Page Public Content Access, Meta oEmbed Read, Marketing API Access Tier

### 2.4 Step B: Basic app settings (10 minutes)

In the app, left menu → **App settings → Basic**. Fill in:

| Field | What to put |
| --- | --- |
| App icon | A 1024×1024 PNG of the Ralfiz Social logo |
| Category | Business and pages |
| Privacy Policy URL | `https://ralfizdigital.in/privacy/` |
| Terms of Service URL | `https://ralfizdigital.in/terms/` |
| User data deletion | Choose **Data deletion instructions URL** → `https://ralfizdigital.in/data-deletion/` |
| App domains | `ralfizdigital.in` |
| Contact email | Your business email |

Click **Save changes**.

### 2.5 Step C: Access verification (the "Tech Provider" form)

1. Go back to **App Review → Permissions and Features**.
2. Scroll to the second list with the grey banner and click **"Learn about access verification"**. It leads to the form, usually under your business portfolio's **Security Centre** or the app's **Verification** page.
3. When it asks what your business does, you can write:
   > We are a digital agency in Kerala, India. Our clients connect their own Facebook Pages and Instagram professional accounts to our social media management tool, Ralfiz Social, so our team can plan, get approval for, and publish their posts, and answer their comments and messages. Clients can disconnect at any time.
4. Submit. Meta usually answers within a few working days, by email and in the Meta Business Suite notifications bell.

### 2.6 Step D: App Review (asking for advanced access)

Do this for each of the 13 permissions:

1. Click **Request advanced access** on its row. It goes into a "request basket".
2. Meta asks, for each one:
   - **"How will your app use this permission?"** Copy the line for it from section 2.7.
   - **A screen recording** showing the hub using it (section 2.8). One video can be uploaded for several permissions.
   - **Agree** that you'll follow the rules.
3. One section of the form is **"Instructions for reviewers"**, explaining how a Meta employee can try the hub. Use the text in section 2.9.
4. Click **Submit for review**. It usually takes 3 to 10 working days. If they reject one permission, they say why, and you fix that and resubmit only that one.

### 2.7 Text for "How will your app use this permission?"

| Permission | Paste this |
| --- | --- |
| `pages_show_list` | When a business connects Facebook, we list the Pages they manage so they can choose which Page to add to Ralfiz Social. |
| `business_management` | Pages owned by a Business portfolio are only listed through the Business Manager API, so we need it to find and connect those Pages. We do not change any business settings. |
| `pages_manage_posts` | We publish and schedule posts (text, photos, videos, links) to the Page after a person in the business has approved them in Ralfiz Social. |
| `pages_read_engagement` | We read the Page's posts, follower count and the likes, comments and shares on posts we published, to show them on the post calendar and in reports. |
| `pages_read_user_content` | We read comments and visitor posts on the Page, including the commenter's name, so the business can see and answer them in the Ralfiz Social inbox. |
| `pages_manage_engagement` | We send the replies the business writes to comments on its Page from the Ralfiz Social inbox. |
| `pages_messaging` | We show Messenger conversations with the Page in the Ralfiz Social inbox and send the replies the business writes, inside the 24-hour window. |
| `read_insights` | We read Page insights (reach, impressions, engagement) to show charts and a monthly PDF report for the business. |
| `instagram_basic` | We read the Instagram professional account linked to the Page (username, profile picture, followers) and its posts, to show them in Ralfiz Social. |
| `instagram_content_publish` | We publish feed photos, videos, Reels and carousels to the Instagram account after a person in the business has approved them. |
| `instagram_manage_comments` | We read comments on the account's posts and send the replies the business writes from the Ralfiz Social inbox. |
| `instagram_manage_insights` | We read reach, impressions, engagement and follower figures for the account and its posts to show charts and the monthly report. |
| `instagram_manage_messages` | We show Instagram Direct messages to the account in the Ralfiz Social inbox and send the replies the business writes. |

### 2.8 The screen recordings

Meta wants to **see** each permission being used. **Five short videos (1 to 3 minutes each) cover all 13.**

Tips:
- Record on a laptop at full screen with the **address bar visible**.
- Use **English** for the Facebook and browser language.
- Talk over it, or add short captions ("Now I connect the Page…").
- On Mac: **Cmd + Shift + 5 → Record entire screen**.
- You need a second Facebook/Instagram account (a friend's or a staff member's) to leave a comment and send a message.

| Video | What to do on screen | Upload it for |
| --- | --- | --- |
| **1. Connect** | Log in to ralfizdigital.in/social/ → **Accounts** → **Connect** → **Facebook** → Facebook's login and permission screens appear (let them show fully) → pick the Page → back in the hub, the Page and its Instagram account appear in the list. | `pages_show_list`, `business_management`, `instagram_basic` |
| **2. Publish** | **Create post** → write a caption → add a photo → tick the Facebook Page and the Instagram account → choose a time 2 minutes ahead → **Schedule** (or Send for approval, then Approve). Wait, then open the Page and the Instagram profile and show the post is there. | `pages_manage_posts`, `instagram_content_publish` |
| **3. Comments** | From the second account, comment on that post on Facebook and on Instagram. In the hub, open **Inbox** → show the comment → click **Reply** → type → **Send**. Then show the reply on Facebook and Instagram. | `pages_read_user_content`, `pages_manage_engagement`, `instagram_manage_comments` |
| **4. Messages** | From the second account, send a message to the Page (Messenger) and to the Instagram account (DM). In the hub's **Inbox**, show both → reply → show the reply arriving on the phone or in the browser. | `pages_messaging`, `instagram_manage_messages` |
| **5. Insights** | Open **Analytics** → switch between Facebook and Instagram → show the charts and post table → open **Reports** → download the monthly PDF and show it. | `pages_read_engagement`, `read_insights`, `instagram_manage_insights` |

### 2.9 The reviewer login and "Instructions for reviewers"

A Meta employee will log in to our hub to try it. A special login has been made for them:

- It can **only** see the Social Hub. It's blocked from invoices, clients and every other BMS page (verified on the live site).
- It manages one empty test client called **"App Review Test Client"**, so it can't see real client data.
- The username is `meta_reviewer`. The password is not stored in this file; it was given in the chat. Make a new one at any time with:
  `railway ssh -s ralfiz-bms -- python manage.py social_review_login`

Paste into **Instructions for reviewers**, adding the username and password:

> 1. Go to https://ralfizdigital.in/login/ and sign in with the username and password below.
> 2. You land in Ralfiz Social. Click **Accounts** in the left rail, then **Connect** → **Facebook** (or **Instagram**), and log in with a Facebook test user who manages a Page (and an Instagram professional account linked to it).
> 3. Pick the Page. It appears under Accounts.
> 4. Click **Create post**, write a caption, add an image, tick the Page and Instagram account, pick a time a few minutes ahead, and click **Schedule**. The post is published at that time; open **Posts** to see it with its link.
> 5. **Inbox** shows comments and messages on the Page and Instagram account; type a reply and click **Send**.
> 6. **Analytics** shows reach, engagement and followers for the connected accounts.
>
> Username: meta_reviewer · Password: (paste here)

### 2.10 Step E: going Live

When all 13 are approved:
1. At the top of the app page, flip **App Mode: Development → Live**.
2. Turn off the reviewer login: `railway ssh -s ralfiz-bms -- python manage.py social_review_login --disable`.
3. Clients can now connect their own Pages from **Accounts → Connect**.

### 2.11 Also flagged in your Meta Security Centre

- **Two-factor authentication**: 0 of 1 people have it on. Turn it on in Facebook → Settings → Accounts Centre → Password and security → Two-factor authentication.
- **Add another admin**: you're the only admin. If you lose access to your Facebook account, nobody can recover the business. Add a trusted person in Business Settings → People.

---

## 2b. WhatsApp

### What you get
The hub connects to WhatsApp with **coexistence**: the number **keeps working in the WhatsApp Business app on your phone**, and the same chats also appear in the hub's **Inbox**.
- Messages customers send show in the Inbox.
- You can reply from the hub **or** the phone.
- Messages you send from the phone also appear in the hub, marked "Replied from the WhatsApp app".

The hub side is **built and live**. It stays hidden until you finish the steps below.

### Before you start
- Update the **WhatsApp Business app** on the phone. Meta needs version 2.24.17 or newer.
- The number should have been in use on the app for at least about a week.
- You need the Facebook account that manages the Ralfiz business portfolio. It is already verified ✅.

### Step 1: Add WhatsApp to the Meta app (5 minutes)
1. Open https://developers.facebook.com/apps and choose **Ralfiz Social Dashboard**.
2. Left menu → **Add product** → **WhatsApp** → **Set up**.
3. Pick the Ralfiz Technologies business portfolio when asked.

### Step 2: Create the "Connect WhatsApp" configuration (5 minutes)
This tells Meta what the popup should ask for. Meta gives you a **Configuration ID**, which is the only new value the hub needs.
1. Left menu → **Facebook Login for Business** → **Configurations** → **Create configuration**.
2. Name: `WhatsApp signup`.
3. Login variation: **WhatsApp Embedded Signup**.
4. Permissions: tick `whatsapp_business_management` and `whatsapp_business_messaging`, plus `business_management` if offered.
5. Click **Create**, then copy the **Configuration ID** (a long number).
6. Still under Facebook Login for Business → **Settings**:
   - **Login with the JavaScript SDK**: turn **On**.
   - **Allowed domains for the JavaScript SDK**: add `https://ralfizdigital.in`.
   - **Valid OAuth redirect URIs**: make sure `https://ralfizdigital.in/` is listed.
   - Click **Save**.

### Step 3: Put the Configuration ID in Railway
In Railway, add `META_WHATSAPP_CONFIG_ID` = the number you copied, on **both** services (`ralfiz-bms` and `social-worker`).

### Step 4: Turn on WhatsApp webhooks (how messages reach the hub)
1. Meta app → **WhatsApp** → **Configuration** → **Webhook** → **Edit**:
   - Callback URL: `https://ralfizdigital.in/social/webhooks/meta/`
   - Verify token: the same value as `META_WEBHOOK_VERIFY_TOKEN` in Railway.
2. **Webhook fields** → **Subscribe** to:
   - `messages`: customers' messages.
   - `smb_message_echoes`: messages you send from the phone app.

### Step 5: Connect
1. Hub → **Accounts** → **Connect** → **WhatsApp**.
2. Choose **"A number already on the WhatsApp Business app"**.
3. Click **Connect with Facebook** and follow Meta's popup. It asks you to confirm on the phone, so keep it close. It may also offer to share your chat history.
4. When the popup closes, pick the number. It now shows under Accounts.

**A new number (no phone app):** choose **"A new number, used only here"** instead. That number then works only in the hub.

**Fallback:** the page also has **"Enter details by hand"**, which takes the phone number ID, WhatsApp account ID and a System User token.

### For clients' WhatsApp numbers
Your own number works as soon as the steps above are done. For **clients'** numbers, add two more permissions to the App Review request in section 2.6:

| Permission | Paste this |
| --- | --- |
| `whatsapp_business_management` | When a business connects WhatsApp through Embedded Signup, we read its WhatsApp Business Account and phone number and subscribe to its message webhooks so its customer chats appear in the Ralfiz Social inbox. |
| `whatsapp_business_messaging` | We send the replies the business writes in the Ralfiz Social inbox to its customers on WhatsApp, and receive the customers' messages. |

**Recording for these:** Accounts → Connect → WhatsApp → the popup end to end → the number listed. Then send a WhatsApp message from another phone, show it in the Inbox, reply, and show the reply arriving on that phone.

### Costs and limits
- **Replies within 24 hours** of a customer's last message are free and can say anything.
- **After 24 hours**, or when **you** start the conversation, you must use a **message template** that Meta has approved. Meta charges per template message, in rupees, by category: marketing, utility or authentication.
- Some WhatsApp Business app features may change on a coexistence number (Meta lists them in the popup). Reported examples are disappearing messages and view-once messages.

### Not yet verified
- This has only been tested against simulated Meta responses. The **first real connection** is the real test, so do it while I can watch.
- Bringing in old chat history (if you agree to share it) is **not** imported into the hub yet. Only new messages from the moment of connecting appear.

---

## 3. Google Business Profile + YouTube

One Google setup covers both.

### 3.1 What these are
- **Google Business Profile** is your listing on Google Search and Maps ("Ralfiz Technologies, Perinthalmanna"), with reviews, photos, posts and hours. The hub can read reviews, reply to them, publish updates and show views and calls.
- **YouTube**: the hub can upload videos to your channel and show views and subscribers.

### 3.2 Steps

1. **Create a Google Cloud project**
   - Go to https://console.cloud.google.com and sign in with the Google account that owns the YouTube channel and Business Profile.
   - At the top, click the project picker → **New project** → name it "Ralfiz Social" → **Create**.

2. **Turn on the APIs.** An "API" is the door Google opens for apps.
   - Left menu → **APIs & Services → Library**.
   - Search for each of these and click **Enable**:
     - YouTube Data API v3
     - YouTube Analytics API
     - My Business Account Management API
     - My Business Business Information API
     - Business Profile Performance API

3. **OAuth consent screen.** This is the screen people see when they click "Connect YouTube", saying "Ralfiz Social wants to access your account".
   - **APIs & Services → OAuth consent screen** → User type **External** → **Create**.
   - App name: **Ralfiz Social**. Support email: yours. Logo: the Ralfiz Social logo.
   - App home page: `https://ralfizdigital.in`
   - Privacy policy: `https://ralfizdigital.in/privacy/`
   - Terms of service: `https://ralfizdigital.in/terms/`
   - Authorised domain: `ralfizdigital.in`. Google will ask you to prove you own it in Search Console (section 5).
   - **Scopes** (what we're asking permission for): add
     - `youtube.upload`
     - `youtube.force-ssl`
     - `youtube.readonly`
     - `yt-analytics.readonly`
     - `business.manage`
   - **Test users**: add your own Gmail.

4. **Create the keys**
   - **APIs & Services → Credentials → Create credentials → OAuth client ID**.
   - Application type: **Web application**. Name: Ralfiz Social.
   - Authorised redirect URIs, which is where Google sends people back after they say yes. Add both:
     - `https://ralfizdigital.in/social/oauth/callback/youtube/`
     - `https://ralfizdigital.in/social/oauth/callback/google_business/`
   - Click **Create**. Copy the **Client ID** and **Client secret**.

5. **Put the keys in Railway** (section 6), on **both** services.

6. **Connect.** Hub → **Accounts → Connect → YouTube**, then again for **Google Business**.

### 3.3 Google's approvals and limits

| Thing | Why | What to do |
| --- | --- | --- |
| **Testing mode** | While the consent screen is "Testing", only test users can connect, and the connection **expires every 7 days** | Consent screen → **Publish app** → submit for **verification**. Google checks the privacy page and may ask for a YouTube video of the connect flow (same idea as Meta). |
| **Business Profile API access** | Every new project starts with **0 requests allowed** for Business Profile | Fill in Google's "Business Profile API access request" form (search that name). Your own Business Profile for Ralfiz must be verified first. |
| **YouTube audit** | Until audited, videos uploaded by the app are forced to **Private**, and the daily limit is about 6 uploads | Fill in the "YouTube API Services: Audit and Quota Extension" form. |

---

## 4. LinkedIn

### 4.1 What it does
The hub posts to the **Ralfiz Technologies company page** (and clients' company pages) and shows followers and post stats.

### 4.2 Steps

1. Go to https://www.linkedin.com/developers/apps → **Create app**.
   - App name: Ralfiz Social.
   - **LinkedIn Page**: pick Ralfiz Technologies. A page admin gets a request and must **approve** it (Page admin view → notifications).
   - Privacy policy URL: `https://ralfizdigital.in/privacy/`. Upload the logo.
2. **Products** tab → **Request access** on **Community Management API**. LinkedIn wants this to be the **only** product on this app, so don't add "Sign In with LinkedIn" etc. to the same app. Fill in their short form about your business.
3. **Auth** tab:
   - Authorised redirect URL: `https://ralfizdigital.in/social/oauth/callback/linkedin/`
   - Copy the **Client ID** and **Primary Client Secret**.
4. Put the keys in Railway (section 6).
5. Hub → **Accounts → Connect → LinkedIn**.

### 4.3 LinkedIn's tiers
- **Development tier** (after the product is approved): works on pages you're admin of.
- **Standard tier**: needed for clients' pages. LinkedIn asks for a **screen recording** of the hub posting to a page, and a description, similar to Meta.

---

## 5. SEO for ralfiz.com

These aren't part of the hub, but they make ralfiz.com show up better in Google. Search Console is also needed for the Google setup in section 3.

1. **Google Search Console**: tells you what people search to find you, and shows problems Google sees.
   - https://search.google.com/search-console → **Add property** → **Domain** → `ralfiz.com`.
   - Google gives you a **TXT record**. Add it in your domain registrar's DNS settings (GoDaddy, Hostinger, etc.). It can take a few minutes to an hour, then click **Verify**.
   - Left menu → **Sitemaps** → submit `sitemap.xml` (usually `https://ralfiz.com/sitemap.xml`).
   - **Do the same for `ralfizdigital.in`.** Google's OAuth consent screen (section 3) needs it.
2. **Google Business Profile**: https://business.google.com
   - Claim or verify **Ralfiz Technologies, Perinthalmanna**. Google verifies by postcard, phone or video.
   - Website: `https://ralfiz.com`. Add services, hours and photos, and ask happy clients for reviews.
3. **Google Analytics 4**: https://analytics.google.com → create a property for ralfiz.com → add the tag it gives you to the site's `<head>`.
4. **Bing Webmaster Tools**: https://www.bing.com/webmasters → sign in → **Import from Google Search Console**. One click, done.

---

## 6. Railway variables

Railway → project **rafizbms** → add each variable to **both** services, **ralfiz-bms** and **social-worker**. Railway redeploys by itself after you save.

| Variable | Where you get it | Status |
| --- | --- | --- |
| `META_APP_ID`, `META_APP_SECRET` | Meta app → App settings → Basic | ✅ already set |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | Google Cloud → Credentials (section 3.2, step 4) | ⬜ |
| `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | LinkedIn app → Auth tab | ⬜ |
| `META_WHATSAPP_CONFIG_ID` | Meta app → Facebook Login for Business → Configurations (section 2b, step 2) | ⬜ |

---

## 7. Glossary

| Word | Meaning |
| --- | --- |
| **App** | Ralfiz Social, as registered with Meta, Google or LinkedIn |
| **Permission / scope** | One specific thing the app may do, like "publish to a Page" |
| **Standard access** | The permission works only on the app owner's own accounts |
| **Advanced access** | The permission works on any account whose owner agrees: needed for clients |
| **App Review** | Meta checking our reasons and videos before giving advanced access |
| **Business verification** | Proving Ralfiz Technologies is a real company (done) |
| **Access verification / Tech Provider** | Proving we manage accounts on behalf of other businesses |
| **OAuth / consent screen** | The "Ralfiz Social wants to access your account. Allow?" screen |
| **Redirect URI** | The hub address the platform sends people back to after they click Allow |
| **Client ID / secret** | The app's username and password with the platform. Keep the secret private; it only goes into Railway. |
| **Quota** | How many requests the platform lets the app make per day |
| **Token** | The key the hub gets when someone clicks Allow, stored encrypted |
