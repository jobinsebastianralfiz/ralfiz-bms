# Meta App Review: Ralfiz Social

App ID `2618682961963846`. Business verification: done (2026-10-12).

## 0. Before requesting anything

**App settings → Basic**
- App icon: 1024×1024 (the Ralfiz Social mark).
- Category: Business and pages.
- Privacy Policy URL: `https://ralfizdigital.in/privacy/`
- Terms of Service URL: `https://ralfizdigital.in/terms/`
- User data deletion: choose "Data deletion instructions URL", `https://ralfizdigital.in/data-deletion/`
- App domains: `ralfizdigital.in`

**Access verification (Tech Provider)**
- The banner over the second permission list links to it.
- Describe the business as: "We are a digital agency. Our clients connect their own Facebook Pages and Instagram accounts to our social media tool, Ralfiz Social, so our team can plan, approve and publish their posts and answer their comments and messages."

**Reviewer login (for "Instructions for reviewers")**
- Create it on production:
  ```
  railway ssh -s ralfiz-bms -- python manage.py social_review_login
  ```
- That prints a username and password for a hub-only login that manages one empty test client, "App Review Test Client". It cannot see any BMS page.
- After the review, run the same command with `--disable`.

Paste this into "Instructions for reviewers":

> 1. Go to https://ralfizdigital.in/login/ and sign in with the username and password above.
> 2. You land in Ralfiz Social. Click **Accounts** in the left rail, then **Connect** → **Facebook** (or **Instagram**), and log in with a Facebook test user who manages a Page (and an Instagram professional account linked to it).
> 3. Pick the Page. It appears under Accounts.
> 4. Click **Create post**, write a caption, add an image, tick the Page and Instagram account, pick a time a few minutes ahead, and click **Schedule**. The post is published at that time; open **Posts** to see it with its link.
> 5. **Inbox** shows comments and messages on the Page and Instagram account; type a reply and click **Send**.
> 6. **Analytics** shows reach, engagement and followers for the connected accounts.

## 1. Permissions to request (advanced access), with the usage text

Request only these 13. Leave every other permission on Standard access.

| Permission | "How will your app use this permission?" |
| --- | --- |
| `pages_show_list` | When a business connects Facebook, we list the Pages they manage so they can choose which Page to add to Ralfiz Social. |
| `pages_manage_posts` | We publish and schedule posts (text, photos, videos, links) to the Page after a person in the business has approved them in Ralfiz Social. |
| `pages_read_engagement` | We read the Page's posts, follower count and the likes, comments and shares on posts we published, to show them on the post calendar and in reports. |
| `pages_read_user_content` | We read comments and visitor posts on the Page, including the commenter's name, so the business can see and answer them in the Ralfiz Social inbox. |
| `pages_manage_engagement` | We send the replies the business writes to comments on its Page from the Ralfiz Social inbox. |
| `pages_messaging` | We show Messenger conversations with the Page in the Ralfiz Social inbox and send the replies the business writes, inside the 24-hour window. |
| `read_insights` | We read Page insights (reach, impressions, engagement) to show charts and a monthly PDF report for the business. |
| `business_management` | Pages owned by a Business portfolio are only listed through the Business Manager API, so we need it to find and connect those Pages. We do not change any business settings. |
| `instagram_basic` | We read the Instagram professional account linked to the Page (username, profile picture, followers) and its posts, to show them in Ralfiz Social. |
| `instagram_content_publish` | We publish feed photos, videos, Reels and carousels to the Instagram account after a person in the business has approved them. |
| `instagram_manage_comments` | We read comments on the account's posts and send the replies the business writes from the Ralfiz Social inbox. |
| `instagram_manage_insights` | We read reach, impressions, engagement and follower figures for the account and its posts to show charts and the monthly report. |
| `instagram_manage_messages` | We show Instagram Direct messages to the account in the Ralfiz Social inbox and send the replies the business writes. |

## 2. Screen recordings

Record at 1080p with English UI, captions or narration, and the browser address bar visible. One recording can cover several permissions; upload the same file to each one it shows.

1. **Connect** (`pages_show_list`, `business_management`, `instagram_basic`):
   - Log in to Ralfiz Social, then go to Accounts → Connect → Facebook.
   - Show the Facebook login and permission dialog in full, pick the Page, and show it listed under Accounts with its Instagram account.
2. **Publish** (`pages_manage_posts`, `instagram_content_publish`):
   - Create post → caption + image → tick the Page and Instagram → Schedule a couple of minutes ahead.
   - Wait, then open the post on Facebook and Instagram to show it went out.
3. **Inbox** (`pages_read_user_content`, `pages_manage_engagement`, `instagram_manage_comments`):
   - From a second account, comment on the post.
   - In Ralfiz Social → Inbox, show the comment, type a reply, click Send, then show the reply on Facebook and Instagram.
4. **Messages** (`pages_messaging`, `instagram_manage_messages`):
   - From a second account, message the Page and the Instagram account.
   - Show them in the Inbox, reply, and show the reply arriving in Messenger and Instagram.
5. **Insights** (`pages_read_engagement`, `read_insights`, `instagram_manage_insights`):
   - Open Analytics, switch between Facebook and Instagram, and show the charts and post table.
   - Then go to Reports and download the monthly PDF.

## 3. After approval

- Switch **App Mode** to **Live**.
- Disable the reviewer login: `railway ssh -s ralfiz-bms -- python manage.py social_review_login --disable`.
